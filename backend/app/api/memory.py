"""Memory API — 结构化记忆管理 (DB + MEMORY.md 双轨).

参考 DeerFlow MemoryUpdater 的设计:
- Facts 表: category / confidence / source / tags
- 纠错信号: correction_detected → 高置信度记录正确做法
- 正反馈: reinforcement_detected → 记录为偏好
- 去重: casefold 内容匹配
- 容量: 按 confidence 淘汰低质量条目
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import select, func, and_, case, literal_column
from collections import Counter
import re

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth
from app.models.memory_fact import MemoryFact

logger = logging.getLogger(__name__)
memory_bp = Blueprint('memory', __name__)

MAX_FACTS_DEFAULT = 500



# ============================================================
# Facts CRUD
# ============================================================

@memory_bp.route('/facts', endpoint='facts', methods=['GET'])
@require_auth
def list_facts():
    """
    列出记忆事实（支持分类/标签/搜索过滤 + 分页）
    ---
    tags:
      - Memory
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: category
        type: string
        description: 按分类筛选 (knowledge/preference/behavior)
      - in: query
        name: source
        type: string
        description: 按来源筛选 (manual/correction/reinforcement)
      - in: query
        name: tag
        type: string
        description: 按标签筛选
      - in: query
        name: search
        type: string
        description: 关键词搜索（模糊匹配 content）
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: 记忆事实分页列表
      401:
        description: 未认证
    """
    return run_async(_list_facts_impl())


async def _list_facts_impl():
    category = request.args.get('category')
    source = request.args.get('source')
    tag = request.args.get('tag')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    async with await get_db() as db:
        query = select(MemoryFact).where(MemoryFact.is_active.is_(True))

        if category:
            query = query.where(MemoryFact.category == category)
        if source:
            query = query.where(MemoryFact.source == source)
        if tag:
            query = query.where(MemoryFact.tags.contains([tag]))
        if search:
            query = query.where(MemoryFact.content.ilike(f"%{search}%"))

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(
                MemoryFact.confidence.desc(),
                MemoryFact.importance.desc(),
                MemoryFact.created_at.desc(),
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        facts = [f.to_dict() for f in result.scalars().all()]

        return jsonify({'data': facts, 'total': total, 'page': page})


@memory_bp.route('/facts', endpoint='facts_post', methods=['POST'])
@require_auth
def create_fact():
    """
    创建新的记忆事实（自动去重 + 容量管理）
    ---
    tags:
      - Memory
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
              description: 记忆内容（相同内容忽略大小写不重复创建）
            category:
              type: string
              default: "knowledge"
              enum: [knowledge, preference, behavior]
            confidence:
              type: number
              default: 0.8
              minimum: 0
              maximum: 1
            source:
              type: string
              default: "manual"
            tags:
              type: array
              items:
                type: string
            importance:
              type: integer
              default: 5
              minimum: 1
              maximum: 10
            session_id:
              type: string
            metadata:
              type: object
            expires_in_days:
              type: integer
              description: 过期天数（null=永不过期）
            max_facts:
              type: integer
              default: 500
              description: 最大容量上限（超出淘汰低置信度条目）
    responses:
      201:
        description: 记忆事实创建成功
      400:
        description: 缺少必填字段或重复内容
      401:
        description: 未认证
    """
    return run_async(_create_fact_impl())


async def _create_fact_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('content'):
        raise ValidationError('content is required', field='content')

    content = data['content'].strip()

    # 去重检查：相同内容（忽略大小写）不重复创建
    async with await get_db() as db:
        existing = await db.execute(
            select(MemoryFact).where(
                and_(
                    MemoryFact.is_active.is_(True),
                    func.lower(MemoryFact.content) == content.lower(),
                )
            ).limit(1)
        )
        if existing.scalar_one_or_none():
            raise ValidationError('Duplicate fact (same content exists)', field='content')

        fact = MemoryFact(
            id=str(uuid.uuid4()),
            content=content,
            category=data.get('category', 'knowledge'),
            confidence=float(data.get('confidence', 0.8)),
            source=data.get('source', 'manual'),
            tags=data.get('tags', []),
            importance=data.get('importance', 5),
            session_id=data.get('session_id'),
            metadata_=data.get('metadata', {}),
            expires_at=_parse_expiry(data.get('expires_in_days')),
        )

        db.add(fact)

        count_result = await db.execute(
            select(func.count()).select_from(select(MemoryFact).where(MemoryFact.is_active.is_(True)).subquery())
        )
        total = count_result.scalar() or 0
        max_facts = int(data.get('max_facts', MAX_FACTS_DEFAULT))

        if total >= max_facts:
            oldest = await db.execute(
                select(MemoryFact).where(MemoryFact.is_active.is_(True))
                .order_by(MemoryFact.confidence.asc(), MemoryFact.created_at.asc())
                .limit(1)
            )
            to_remove = oldest.scalar_one_or_none()
            if to_remove:
                to_remove.is_active = False
                logger.info("淘汰低置信度记忆: %s (conf=%.2f)", to_remove.id[:8], to_remove.confidence)

        await db.commit()
        await db.refresh(fact)

    logger.info("创建记忆事实: [%s] %s", fact.category, fact.content[:50])
    return jsonify({'fact': fact.to_dict()}), 201


@memory_bp.route('/facts/<fact_id>', endpoint='facts_fact_id', methods=['GET'])
@require_auth
def get_fact(fact_id: str):
    """获取记忆事实详情."""
    return run_async(_get_fact_impl(fact_id))


async def _get_fact_impl(fact_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(MemoryFact).where(MemoryFact.id == fact_id)
        )
        fact = result.scalar_one_or_none()
        if not fact:
            raise NotFoundError('MemoryFact', fact_id)
        return jsonify(fact.to_dict())


@memory_bp.route('/facts/<fact_id>', endpoint='facts_fact_id_put', methods=['PUT'])
@require_auth
def update_fact(fact_id: str):
    """更新记忆事实."""
    return run_async(_update_fact_impl(fact_id))


async def _update_fact_impl(fact_id: str):
    data = request.get_json(silent=True) or {}

    async with await get_db() as db:
        result = await db.execute(select(MemoryFact).where(MemoryFact.id == fact_id))
        fact = result.scalar_one_or_none()
        if not fact:
            raise NotFoundError('MemoryFact', fact_id)

        for field in ('content', 'category', 'confidence', 'tags', 'importance', 'metadata_', 'is_active'):
            if field in data:
                setattr(fact, field, data[field])

        fact.updated_at = datetime.now(timezone.utc)
        await db.commit()

    return jsonify({'message': f'Fact {fact_id} updated'})


@memory_bp.route('/facts/<fact_id>', endpoint='facts_fact_id_delete', methods=['DELETE'])
@require_auth
def delete_fact(fact_id: str):
    """软删除记忆事实."""
    return run_async(_delete_fact_impl(fact_id))


async def _delete_fact_impl(fact_id: str):
    async with await get_db() as db:
        result = await db.execute(select(MemoryFact).where(MemoryFact.id == fact_id))
        fact = result.scalar_one_or_none()
        if not fact:
            raise NotFoundError('MemoryFact', fact_id)

        fact.is_active = False
        await db.commit()

    return jsonify({'message': f'Fact {fact_id} deleted'})


# ============================================================
# 统计与搜索
# ============================================================

@memory_bp.route('/stats', endpoint='stats', methods=['GET'])
@require_auth
def memory_stats():
    """
    记忆统计 — 按类别/来源/置信度分组 + 最近10条
    ---
    tags:
      - Memory
    security:
      - BearerAuth: []
    responses:
      200:
        description: 统计数据（总数/分组/置信度分布/最近记录）
      401:
        description: 未认证
    """
    return run_async(_stats_impl())


async def _stats_impl():
    async with await get_db() as db:
        total_result = await db.execute(
            select(func.count()).select_from(
                select(MemoryFact).where(MemoryFact.is_active.is_(True)).subquery()
            )
        )
        total = total_result.scalar() or 0

        by_category = {}
        by_source = {}
        confidence_buckets = {'high_90+': 0, 'mid_70_90': 0, 'low_<70': 0}

        if total > 0:
            rows = await db.execute(
                select(MemoryFact.category, MemoryFact.source, MemoryFact.confidence)
                .where(MemoryFact.is_active.is_(True))
            )

            for cat, src, conf in rows.all():
                by_category[cat] = by_category.get(cat, 0) + 1
                by_source[src] = by_source.get(src, 0) + 1
                if conf >= 0.9:
                    confidence_buckets['high_90+'] += 1
                elif conf >= 0.7:
                    confidence_buckets['mid_70_90'] += 1
                else:
                    confidence_buckets['low_<70'] += 1

        # 最近 10 条
        recent_rows = await db.execute(
            select(MemoryFact).where(MemoryFact.is_active.is_(True))
            .order_by(MemoryFact.created_at.desc()).limit(10)
        )

        return jsonify({
            'total_facts': total,
            'by_category': by_category,
            'by_source': by_source,
            'confidence_distribution': confidence_buckets,
            'recent': [f.to_dict() for f in recent_rows.scalars().all()],
        })


@memory_bp.route('/recall', endpoint='recall', methods=['POST'])
@require_auth
def recall_facts():
    """
    语义相关记忆检索（关键词匹配 + 标签补充）
    ---
    tags:
      - Memory
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - query
          properties:
            query:
              type: string
              description: 检索关键词
            limit:
              type: integer
              default: 5
              maximum: 20
            category:
              type: string
              description: 限定类别范围
    responses:
      200:
        description: 相关记忆列表（按重要性+置信度排序）
      400:
        description: 缺少必填参数 query
      401:
        description: 未认证
    """
    return run_async(_recall_impl())


async def _recall_impl():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    limit = min(data.get('limit', 5), 20)
    category = data.get('category')
    backend = request.args.get('backend', 'keyword')  # 支持 keyword / msa / auto

    if not query:
        raise ValidationError('query is required', field='query')

    # MSA 语义检索路径
    if backend in ('msa', 'auto'):
        try:
            from openharness.msa.retriever import MSARetriever

            retriever = MSARetriever.get_instance()
            if retriever is not None and retriever.is_available:
                results = await retriever.search(
                    query,
                    top_k=limit,
                    categories=[category] if category else None,
                    force_backend=backend if backend == 'msa' else None,
                )

                return jsonify({
                    'query': query,
                    'backend': 'msa',
                    'results': [
                        {
                            'id': r.source_id,
                            'content': r.content,
                            'score': r.score,
                            'source_type': r.source_type.value,
                            'category': r.category,
                            'tags': r.tags,
                        }
                        for r in results
                    ],
                    'total_found': len(results),
                })
        except Exception as e:
            logger.warning("MSA 检索失败，回退到关键词模式: %s", e)
            if backend == 'msa':
                raise ValidationError(f'MSA 检索不可用: {e}', field='backend')

    # 关键词检索路径（默认）
    async with await get_db() as db:
        base_query = select(MemoryFact).where(MemoryFact.is_active.is_(True))

        if category:
            base_query = base_query.where(MemoryFact.category == category)

        # 关键词匹配 + 置信度排序
        search_filter = f"%{query}%"
        result = await db.execute(
            base_query.where(MemoryFact.content.ilike(search_filter))
            .order_by(MemoryFact.importance.desc(), MemoryFact.confidence.desc())
            .limit(limit)
        )
        facts = [f.to_dict() for f in result.scalars().all()]

        # 如果关键词匹配不足，按标签补充
        if len(facts) < limit:
            tag_result = await db.execute(
                base_query.where(MemoryFact.tags.contains([query]))
                .order_by(MemoryFact.confidence.desc())
                .limit(limit - len(facts))
            )
            for f in tag_result.scalars().all():
                if f.id not in {x['id'] for x in facts}:
                    facts.append(f.to_dict())

        return jsonify({
            'query': query,
            'backend': 'keyword',
            'results': facts,
            'total_found': len(facts),
        })


# ============================================================
# P1-4 特殊操作: 纠错/正反馈信号
# ============================================================

@memory_bp.route('/signal/correction', endpoint='signal_correction', methods=['POST'])
@require_auth
def signal_correction():
    """纠错信号 — 用户纠正 AI 行为时调用，以高置信度记录正确做法.

    POST body: {"content": "正确的做法是...", "wrong_content": "被纠正的错误做法"}
    """
    return run_async(_signal_correction_impl())


async def _signal_correction_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('content'):
        raise ValidationError('content is required', field='content')

    fact = MemoryFact(
        id=str(uuid.uuid4()),
        content=data['content'].strip(),
        category=data.get('category', 'behavior'),
        confidence=min(float(data.get('confidence', 0.95)), 1.0),
        source='correction',
        tags=['corrected'] + (data.get('tags') or []),
        importance=9,
        metadata_={'wrong_content': data.get('wrong_content', '')},
    )

    async with await get_db() as db:
        db.add(fact)
        await db.commit()
        await db.refresh(fact)

    logger.info("纠错信号记录: %s (conf=%.2f)", fact.content[:50], fact.confidence)
    return jsonify({'fact': fact.to_dict()}), 201


@memory_bp.route('/signal/reinforcement', endpoint='signal_reinforcement', methods=['POST'])
@require_auth
def signal_reinforcement():
    """正反馈信号 — 用户确认 AI 的行为时调用，记录为偏好模式.

    POST body: {"content": "用户喜欢这种代码风格..."}
    """
    return run_async(_signal_reinforcement_impl())


async def _signal_reinforcement_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('content'):
        raise ValidationError('content is required', field='content')

    fact = MemoryFact(
        id=str(uuid.uuid4()),
        content=data['content'].strip(),
        category=data.get('category', 'preference'),
        confidence=min(float(data.get('confidence', 0.90)), 1.0),
        source='reinforcement',
        tags=['confirmed'] + (data.get('tags') or []),
        importance=8,
    )

    async with await get_db() as db:
        db.add(fact)
        await db.commit()
        await db.refresh(fact)

    logger.info("正反馈信号记录: %s (conf=%.2f)", fact.content[:50], fact.confidence)
    return jsonify({'fact': fact.to_dict()}), 201


def _parse_expiry(days: Optional[int]) -> Optional[datetime]:
    if days is None:
        return None
    try:
        return datetime.now(timezone.utc) + timedelta(days=int(days))
    except (TypeError, ValueError):
        return None


# ============================================================
# MSA 语义记忆服务端点
# ============================================================

@memory_bp.route('/msa/init', endpoint='msa_init', methods=['POST'])
@require_auth
def init_msa_service():
    """初始化 MSA 服务"""
    from openharness.msa.retriever import MSARetriever
    from openharness.config.settings import Settings

    settings = Settings.load()
    if not settings.msa.enabled:
        raise ValidationError('MSA 未在配置中启用', field='msa')

    retriever = MSARetriever.get_instance()
    if retriever is None:
        from openharness.msa.config import OCHMSAConfig
        from openharness.msa.bridge import MSABridge
        from openharness.msa.service_wrapper import MSAServiceWrapper

        config = settings.msa
        bridge = MSABridge(cache_dir=config.cache_dir)
        wrapper = MSAServiceWrapper(config)
        retriever = MSARetriever(config=config, wrapper=wrapper, bridge=bridge)
        MSARetriever.set_instance(retriever)

    return run_async(_msa_init_impl(retriever))


async def _msa_init_impl(retriever):
    status = await retriever.initialize()
    return jsonify({
        'status': 'initialized' if status.model_loaded else 'failed',
        'health': {
            'model_loaded': status.model_loaded,
            'model_path': status.model_path,
            'gpu_available': status.gpu_available,
            'error': status.error,
        }
    })


@memory_bp.route('/msa/recall', endpoint='msa_recall', methods=['POST'])
@require_auth
def msa_recall_endpoint():
    """MSA 语义检索"""
    from openharness.msa.retriever import MSARetriever

    retriever = MSARetriever.get_instance()
    if retriever is None or not retriever.is_available:
        raise ValidationError('MSA 服务未初始化或不可用', field='msa')

    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    top_k = data.get('top_k', 5)

    return run_async(_msa_recall_impl(retriever, query, top_k))


async def _msa_recall_impl(retriever, query, top_k):
    results = await retriever.search(query, top_k=top_k)

    return jsonify({
        'query': query,
        'total': len(results),
        'results': [
            {
                'content': r.content,
                'score': r.score,
                'source_id': r.source_id,
                'source_type': r.source_type.value,
                'category': r.category,
                'tags': r.tags,
            }
            for r in results
        ]
    })


@memory_bp.route('/msa/status', endpoint='msa_status', methods=['GET'])
@require_auth
def msa_status_endpoint():
    """获取 MSA 服务状态"""
    from openharness.msa.retriever import MSARetriever

    retriever = MSARetriever.get_instance()
    if retriever is None:
        return jsonify({'status': 'not_configured'})

    return run_async(_msa_status_impl(retriever))


async def _msa_status_impl(retriever):
    health = await retriever.health_check()
    stats = retriever.get_stats()

    return jsonify({
        'status': 'available' if retriever.is_available else 'unavailable',
        'health': {
            'initialized': health.initialized,
            'model_loaded': health.model_loaded,
            'model_path': health.model_path,
            'cache_dir': health.cache_dir,
            'total_documents': health.total_documents,
            'gpu_available': health.gpu_available,
            'gpu_name': health.gpu_name,
            'gpu_memory_used_mb': health.gpu_memory_used_mb,
            'gpu_memory_total_mb': health.gpu_memory_total_mb,
            'error': health.error,
        },
        'stats': stats,
    })


@memory_bp.route('/msa/encode', endpoint='msa_encode', methods=['POST'])
@require_auth
def msa_encode_endpoint():
    """触发文档编码"""
    from openharness.msa.retriever import MSARetriever

    retriever = MSARetriever.get_instance()
    if retriever is None or not retriever.is_available:
        raise ValidationError('MSA 服务未初始化', field='msa')

    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'incremental')  # full | incremental

    # TODO: 从数据库获取 facts 和 agent memories，通过 Bridge 转换为 Documents
    # 然后提交给 EncoderWorker 执行编码任务

    return jsonify({
        'status': 'scheduled',
        'mode': mode,
        'message': '编码任务已提交（待实现完整流程）',
    })


@memory_bp.route('/msa/shutdown', endpoint='msa_shutdown', methods=['DELETE'])
@require_auth
def msa_shutdown_endpoint():
    """关闭 MSA 服务"""
    from openharness.msa.retriever import MSARetriever

    retriever = MSARetriever.get_instance()
    if retriever is None:
        return jsonify({'status': 'not_running'})

    return run_async(_msa_shutdown_impl(retriever))


async def _msa_shutdown_impl(retriever):
    await retriever.shutdown()
    MSARetriever.set_instance(None)

    return jsonify({'status': 'shutdown'})
