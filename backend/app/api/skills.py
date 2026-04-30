"""Skills Library API — DB + 文件系统双源管理."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, g, jsonify, request

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth
from app.models.skill import Skill
from app.services.skill_service import SkillService
from sqlalchemy import select

logger = logging.getLogger(__name__)
skills_bp = Blueprint('skills', __name__)

_skill_service = SkillService()



@skills_bp.route('', methods=['GET'], endpoint='list_skills')
@require_auth
def list_skills():
    """
    列出所有已安装技能 (DB + 文件系统双源)
    ---
    tags:
      - Skills
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: search
        schema:
          type: string
        description: 搜索关键词（匹配名称或描述）
      - in: query
        name: category
        schema:
          type: string
          enum: [coding, analysis, communication, system, utility]
        description: 按分类筛选
      - in: query
        name: enabled_only
        schema:
          type: boolean
          default: false
        description: 仅显示已启用的技能
      - in: query
        name: source
        schema:
          type: string
          enum: [builtin, file, url]
        description: 技能来源筛选
    responses:
      200:
        description: 技能列表
      401:
        description: 未认证
    """
    return run_async(_list_skills_impl())


async def _list_skills_impl():
    search = request.args.get('search', '')
    category = request.args.get('category')
    enabled_only = request.args.get('enabled', '').lower() in ('true', '1')
    source = request.args.get('source')

    # 从文件系统加载技能
    fs_skills = await _skill_service.list_skills(
        search=search,
        category=category,
        enabled_only=enabled_only,
    )

    # 从数据库获取自定义技能
    db_skills = []
    async with await get_db() as db:
        query = select(Skill).where(Skill.source != 'builtin')

        if search:
            like_pattern = f'%{search}%'
            query = query.where(
                (Skill.name.ilike(like_pattern)) |
                (Skill.description.ilike(like_pattern))
            )
        if category:
            query = query.where(Skill.category == category)
        if enabled_only:
            query = query.where(Skill.enabled.is_(True))
        if source:
            query = query.where(Skill.source == source)

        result = await db.execute(query)
        db_skills = [s.to_dict() for s in result.scalars().all()]

    # 合并去重（DB 优先）
    all_names = {s['name'] for s in db_skills}
    combined = list(db_skills)

    for fs_skill in fs_skills:
        if fs_skill['name'] not in all_names:
            all_names.add(fs_skill['name'])
            combined.append(fs_skill)

    # 统计分类
    categories = {}
    for s in combined:
        cat = s.get('category', 'general')
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    return jsonify({
        'data': combined,
        'total': len(combined),
        'categories': [
            {'id': k, 'name': k.title(), 'count': v}
            for k, v in sorted(categories.items())
        ],
    })


@skills_bp.route('/categories', endpoint='categories', methods=['GET'])
@require_auth
def list_skill_categories():
    """获取技能分类统计."""
    return run_async(_list_categories_impl())


async def _list_categories_impl():
    async with await get_db() as db:
        from sqlalchemy import func
        result = await db.execute(
            select(
                Skill.category,
                func.count(Skill.id).label('count'),
            ).group_by(Skill.category)
        )
        rows = result.all()

        categories = {row[0]: row[1] for row in rows}

        # 加上内置技能的分类
        builtin_cats = {'development': 4, 'planning': 1, 'testing': 1, 'refactoring': 1, 'document': 2}
        for cat, count in builtin_cats.items():
            categories[cat] = categories.get(cat, 0) + count

        return jsonify({
            'categories': sorted(
                [{'id': k, 'name': k.title(), 'count': v} for k, v in categories.items()],
                key=lambda x: x['count'],
                reverse=True,
            ),
        })


@skills_bp.route('/<skill_name>', endpoint='get_skill', methods=['GET'])
@require_auth
def get_skill(skill_name: str):
    """
    获取技能详情（含 Markdown 内容）.

    优先从 DB 查找，其次从文件系统，最后查找内置.
    """
    return run_async(_get_skill_impl(skill_name))


async def _get_skill_impl(skill_name: str):
    # 先查数据库
    async with await get_db() as db:
        result = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = result.scalar_one_or_none()
        if skill:
            # 增加使用计数
            skill.usage_count += 1
            await db.commit()
            return jsonify(skill.to_dict())

    # 再查文件系统 / 内置
    skill_info = await _skill_service.get_skill(skill_name)
    if skill_info:
        return jsonify(skill_info)

    raise NotFoundError('Skill', skill_name)


@skills_bp.route('/<skill_name>/enable', endpoint='enable_skill', methods=['PUT'])
@require_auth
def enable_skill(skill_name: str):
    """启用技能."""
    return run_async(_toggle_skill_impl(skill_name, True))


@skills_bp.route('/<skill_name>/disable', endpoint='disable_skill', methods=['PUT'])
@require_auth
def disable_skill(skill_name: str):
    """禁用技能."""
    return run_async(_toggle_skill_impl(skill_name, False))


async def _toggle_skill_impl(skill_name: str, enabled: bool):
    action = 'enable' if enabled else 'disable'

    async with await get_db() as db:
        result = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = result.scalar_one_or_none()

        if skill:
            skill.enabled = enabled
            skill.updated_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"{action.capitalize()}d skill: {skill_name}")
            return jsonify({
                'message': f"Skill '{skill_name}' {action}d",
                'enabled': enabled,
            })

    # 内置/文件系统技能
    success = await (_skill_service.enable_skill(skill_name) if enabled
                     else _skill_service.disable_skill(skill_name))

    if success:
        return jsonify({'message': f"Skill '{skill_name}' {action}d", 'enabled': enabled})

    raise NotFoundError('Skill', skill_name)


@skills_bp.route('/install', endpoint='install_skill', methods=['POST'])
@require_auth
def install_skill():
    """
    安装新技能（URL 或本地 .md 文件）.

    Request Body:
    {
      "source": "https://example.com/skill.md",
      "source_type": "url",
      "name": "custom-skill"
    }
    """
    return run_async(_install_skill_impl())


async def _install_skill_impl():
    data = request.get_json(silent=True) or {}

    source = data.get('source')
    source_type = data.get('source_type', 'url' if source and source.startswith('http') else 'file')

    if not source:
        raise ValidationError('Source URL or path is required', field='source')

    name = data.get('name', '')

    try:
        skill_info = await _skill_service.install_skill(source, source_type=source_type)
    except Exception as e:
        raise ValidationError(f'Install failed: {str(e)}')

    # 注册到数据库
    async with await get_db() as db:
        existing = await db.execute(select(Skill).where(Skill.name == name or skill_info.get('name', '')))
        if existing.scalar_one_or_none():
            raise ValidationError(f'Skill already exists: {name or skill_info["name"]}')

        skill = Skill(
            id=str(uuid.uuid4()),
            name=name or skill_info.get('name', Path(source).stem),
            description=skill_info.get('description', ''),
            category=skill_info.get('category', 'custom'),
            version=skill_info.get('version', '1.0.0'),
            source=source_type,
            path=skill_info.get('path'),
            url=source if source_type == 'url' else None,
            content_md=skill_info.get('content_md'),
            triggers=skill_info.get('triggers', []),
            dependencies=skill_info.get('dependencies', []),
            installed_by=g.user.get('user_id') if g.user else None,
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)

        logger.info(f"Installed skill: {skill.name}")
        return jsonify({'skill': skill.to_dict()}), 201


@skills_bp.route('/<skill_name>', endpoint='uninstall_skill', methods=['DELETE'])
@require_auth
def uninstall_skill(skill_name: str):
    """卸载并删除技能."""
    return run_async(_uninstall_skill_impl(skill_name))


async def _uninstall_skill_impl(skill_name: str):
    # 从数据库删除
    async with await get_db() as db:
        result = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = result.scalar_one_or_none()

        if skill:
            skill_id = skill.id
            await db.delete(skill)
            await db.commit()

            # 同时删除文件系统中的文件
            await _skill_service.uninstall_skill(skill_name)

            logger.info(f"Uninstalled skill: {skill_name}")
            return jsonify({
                'message': f"Skill '{skill_name}' uninstalled",
                'deleted_id': skill_id,
            })

    # 仅文件系统/内置
    success = await _skill_service.uninstall_skill(skill_name)
    if success:
        return jsonify({'message': f"Skill '{skill_name}' uninstalled"})

    raise NotFoundError('Skill', skill_name)


@skills_bp.route('/scan', endpoint='scan_skills', methods=['POST'])
@require_auth
def scan_skills():
    """
    扫描指定目录发现新技能并导入到数据库.

    Request Body:
    {
      "directory": "/path/to/skills",
      "auto_install": false
    }
    """
    return run_async(_scan_skills_impl())


async def _scan_skills_impl():
    data = request.get_json(silent=True) or {}
    directory = data.get('directory')
    auto_install = data.get('auto_install', False)

    target_dir = Path(directory) if directory else (Path.home() / '.och' / 'skills')
    discovered = []

    if target_dir.exists() and target_dir.is_dir():
        for md_file in target_dir.glob('*.md'):
            skill_info = await _skill_service._parse_skill_file(md_file)
            if skill_info:
                discovered.append({
                    **skill_info,
                    'file_path': str(md_file),
                    'file_size': md_file.stat().st_size,
                })

    if auto_install:
        installed_count = 0
        async with await get_db() as db:
            for info in discovered:
                exists = await db.execute(select(Skill).where(Skill.name == info['name']))
                if not exists.scalar_one_or_none():
                    skill = Skill(
                        id=str(uuid.uuid4()),
                        name=info['name'],
                        description=info.get('description', ''),
                        category=info.get('category', 'scanned'),
                        source='file',
                        path=info.get('path'),
                        content_md=info.get('content_md'),
                        triggers=info.get('triggers', []),
                        dependencies=info.get('dependencies', []),
                    )
                    db.add(skill)
                    installed_count += 1

            await db.commit()

        return jsonify({
            'discovered': len(discovered),
            'installed': installed_count,
            'skipped': len(discovered) - installed_count,
        })

    return jsonify({
        'discovered': len(discovered),
        'skills': discovered,
    })


# 技能详情与安装/卸载逻辑
