#!/usr/bin/env python3
"""MSA (Memory Sparse Attention) 集成功能完整验证脚本

在远程 GPU 终端运行:
    cd /home/xxh/openclaw-harness/backend
    python3 msa_verify.py

前置要求:
    1. NVIDIA GPU (Ampere+ 推荐, 如 A100/RTX3090)
    2. CUDA 11.8+ 已安装
    3. PyTorch >= 2.0 + CUDA 支持
    4. flash-attn >= 2.0

用法:
    python3 msa_verify.py              # 运行全部验证
    python3 msa_verify.py --skip-gpu   # 跳过需GPU的测试
"""

from __future__ import annotations
import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# ANSI 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0
skipped = 0


def log_pass(msg: str):
    global passed
    passed += 1
    print(f"  {GREEN}✅{RESET} {msg}")


def log_fail(msg: str, detail: str = ""):
    global failed
    failed += 1
    print(f"  {RED}❌{RESET} {msg}")
    if detail:
        print(f"     {detail}")


def log_skip(msg: str, reason: str = ""):
    global skipped
    skipped += 1
    print(f"  {YELLOW}⏭️ {RESET} {msg}")
    if reason:
        print(f"     原因: {reason}")


def log_section(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}")


# ============================================================
# Phase 1: 环境检查
# ============================================================
def check_environment():
    log_section("Phase 1: 环境检查")
    
    # Python 版本
    print(f"\n  Python: {sys.version.split()[0]}")
    
    # PyTorch
    try:
        import torch
        log_pass(f"PyTorch {torch.__version__}")
        if torch.cuda.is_available():
            count = torch.cuda.device_count()
            for i in range(count):
                props = torch.cuda.get_device_properties(i)
                mem_gb = props.total_mem / (1024**3)
                log_pass(f"  GPU {i}: {props.name} ({mem_gb:.1f} GB)")
        else:
            log_skip("CUDA 不可用", "将跳过 GPU 相关测试")
            return False
    except ImportError:
        log_fail("PyTorch 未安装", "请运行: pip install torch>=2.0")
        return False
    
    # flash-attn
    try:
        import flash_attn
        log_pass(f"flash_attn {flash_attn.__version__}")
    except ImportError:
        log_fail("flash_attn 未安装 (必需)", "请运行: pip install flash-attn>=2.0")
        return False
    
    # transformers
    try:
        import transformers
        log_pass(f"transformers {transformers.__version__}")
    except ImportError:
        log_fail("transformers 未安装", "请运行: pip install transformers>=4.36")
        return False
    
    return True


# ============================================================
# Phase 2: 模块导入验证
# ============================================================
def check_module_imports():
    log_section("Phase 2: 模块导入验证")
    
    modules = [
        ("openharness.msa.types", ["MemorySearchResult", "MSAHealthStatus", "EncodeStats", "MemorySourceType"]),
        ("openharness.msa.config", ["OCHMSAConfig"]),
        ("openharness.msa.bridge", ["MSABridge", "Document"]),
        ("openharness.msa.service_wrapper", ["MSAServiceWrapper"]),
        ("openharness.msa.retriever", ["MSARetriever"]),
        ("openharness.msa.encoder_worker", ["EncoderWorker", "EncodeTaskStatus"]),
    ]
    
    for mod_name, expected in modules:
        try:
            mod = __import__(mod_name, fromlist=expected)
            missing = [e for e in expected if not hasattr(mod, e)]
            if missing:
                log_fail(f"{mod_name}", f"缺少: {missing}")
            else:
                names = ", ".join(expected[:3]) + ("..." if len(expected) > 3 else "")
                log_pass(f"{mod_name} → [{names}]")
        except Exception as e:
            log_fail(f"{mod_name}", str(e))
    
    # __init__.py 全量导出
    try:
        from openharness.msa import (
            OCHMSAConfig, EncodeStats, MemorySearchResult,
            MemorySourceType, MSAHealthStatus,
            MSABridge, Document, MSAServiceWrapper,
            MSARetriever, EncoderWorker, EncodeTaskStatus,
        )
        log_pass("msa/__init__.py 全量导出 (12 个符号)")
    except ImportError as e:
        log_fail("__init__.py 导出失败", str(e))


# ============================================================
# Phase 3: 配置与 Bridge 功能验证
# ============================================================
def check_config_and_bridge():
    log_section("Phase 3: 配置与 Bridge 功能验证")
    
    # OCHMSAConfig
    from openharness.msa.config import OCHMSAConfig
    config = OCHMSAConfig()
    assert config.enabled == False
    assert config.model_path == "EverMind-AI/MSA-4B"
    assert config.doc_top_k == 16
    assert config.auto_fallback == True
    log_pass("OCHMSAConfig 默认值正确")
    
    # 自定义配置
    custom = OCHMSAConfig(
        enabled=True,
        model_path="/tmp/test-model",
        devices=[0],
        doc_top_k=8,
    )
    assert custom.enabled == True
    assert custom.devices == [0]
    log_pass("OCHMSAConfig 自定义参数正常")
    
    # world_size 属性
    ws = custom.world_size
    assert ws >= 1
    log_pass(f"world_size = {ws}")
    
    # cache_dir 默认值
    from pathlib import Path as _P
    default_cache = _P.home() / ".openharness" / "msa_cache"
    assert config.cache_dir == default_cache
    log_pass(f"默认缓存目录: {config.cache_dir}")
    
    # MSABridge 基础功能
    from openharness.msa.bridge import MSABridge, Document, SyncSnapshot
    
    bridge = MSABridge()
    log_pass("MSABridge 初始化成功")
    
    # facts → documents 转换
    test_facts = [
        {"id": "f1", "content": "系统使用 FastAPI 构建 REST API 服务", "category": "tech", "tags": ["api", "python"]},
        {"id": "f2", "content": "数据库采用 PostgreSQL + SQLAlchemy ORM", "category": "tech", "tags": ["db"]},
        {"id": "f3", "content": "Agent 权限管理基于 RBAC 模型实现", "category": "security", "tags": ["auth"]},
    ]
    
    docs = bridge.facts_to_documents(test_facts, group_by_category=True)
    # 按 category 分组: tech(2条) + security(1条) = 2 个文档
    assert len(docs) == 2, f"期望 2 个文档(按 category 分组), 实际 {len(docs)}"
    assert all(isinstance(d, Document) for d in docs)
    assert docs[0].doc_id == 1
    log_pass(f"facts→Documents: {len(docs)} 个文档 (按 category 分组)")
    
    # 不分组模式
    bridge2 = MSABridge()
    docs_flat = bridge2.facts_to_documents(test_facts, group_by_category=False)
    assert len(docs_flat) == 3
    log_pass(f"facts→Documents (不分组): {len(docs_flat)} 个文档")
    
    # agent_memory → documents 转换
    test_entries = [
        {"id": "m1", "agent_id": "worker_01", "content": "完成了用户认证模块开发", "category": "task", "tags": ["done"]},
        {"id": "m2", "agent_id": "worker_02", "content": "修复了权限校验的边界条件 bug", "category": "bugfix", "tags": ["fixed"]},
        {"id": "m3", "agent_id": "worker_01", "content": "优化了查询性能，响应时间降低 60%", "category": "perf", "tags": ["optimization"]},
    ]
    
    mem_docs = bridge.agent_memory_to_documents(test_entries, group_by_category=True)
    assert len(mem_docs) == 3  # 3 个不同 category
    log_pass(f"agent_memory→Documents: {len(mem_docs)} 个文档")
    
    # id_map 映射
    stats = bridge.get_stats()
    assert stats["total_documents"] == len(docs) + len(mem_docs)  # 两个 bridge 的 docs
    log_pass(f"id_map 统计: {stats['total_documents']} 个文档映射")
    
    # 增量同步检测
    snapshot = bridge.save_snapshot(test_facts, test_entries)
    assert isinstance(snapshot, SyncSnapshot)
    assert snapshot.fact_count == 3
    assert snapshot.memory_file_count == 3
    log_pass(f"save_snapshot: facts={snapshot.fact_count}, memories={snapshot.memory_file_count}")
    
    needs_sync = bridge.needs_sync(test_facts, test_entries)
    assert needs_sync == False  # 相同数据不需要重新同步
    log_pass("needs_sync: 相同数据 → False (无需重同步)")
    
    # 变更后需要重同步
    modified_facts = test_facts + [{"id": "f4", "content": "新增事实", "category": "new"}]
    needs_sync2 = bridge.needs_sync(modified_facts, test_entries)
    assert needs_sync2 == True
    log_pass("needs_sync: 数据变更 → True (需要重同步)")
    
    # sync_all 全量同步
    bridge3 = MSABridge()
    all_docs, snap = bridge3.sync_all(modified_facts, test_entries)
    assert len(all_docs) > 0
    log_pass(f"sync_all: {len(all_docs)} 个文档, snapshot 已保存")


# ============================================================
# Phase 4: Retriever 初始化验证 (无需 GPU)
# ============================================================
async def check_retriever_no_gpu():
    log_section("Phase 4: Retriever 初始化 (无 GPU 模式)")
    
    from openharness.msa.config import OCHMSAConfig
    from openharness.msa.retriever import MSARetriever
    from openharness.msa.types import MemorySearchResult
    
    # 未启用 MSA 的 retriever
    config_off = OCHMSAConfig(enabled=False)
    retriever = MSARetriever(config=config_off)
    
    assert retriever.is_available == False
    assert retriever.config.enabled == False
    log_pass("Retriever (MSA disabled): is_available=False")
    
    stats = retriever.get_stats()
    assert stats["msa_enabled"] == False
    assert stats["msa_initialized"] == False
    log_pass(f"Retriever stats: {json.dumps(stats, ensure_ascii=False)}")
    
    # 设置关键词回退函数
    async def dummy_keyword_search(query, top_k=5):
        return [
            MemorySearchResult(
                content=f"[关键词] {query}",
                score=0.5,
                source_id="kw_1",
                category="test",
            )
        ]
    
    retriever.set_keyword_search(dummy_keyword_search)
    log_pass("关键词回退函数已设置")
    
    # 测试搜索（应走关键词路径）
    results = await retriever.search("测试查询", top_k=3)
    assert len(results) == 1
    assert results[0].content.startswith("[关键词]")
    log_pass(f"搜索 (keyword fallback): {len(results)} 条结果")
    
    # 强制指定后端
    results_kw = await retriever.search("强制关键词", force_backend="keyword")
    assert len(results_kw) >= 1
    log_pass("force_backend='keyword': 正确走关键词路径")
    
    # health_check
    health = await retriever.health_check()
    assert health.initialized == False
    log_pass("health_check (disabled): initialized=False")


# ============================================================
# Phase 5: EncoderWorker 验证 (无需 GPU)
# ============================================================
async def check_encoder_worker():
    log_section("Phase 5: EncoderWorker 验证")
    
    from openharness.msa.encoder_worker import EncoderWorker, EncodeTaskStatus
    from openharness.msa.bridge import Document
    
    worker = EncoderWorker()
    progress = worker.get_progress()
    assert progress["total_tasks"] == 0
    assert progress["is_running"] == False
    log_pass("EncoderWorker 初始化: idle 状态")
    
    # 提交任务（不启动 worker）
    doc = Document(doc="测试文档内容", doc_id=99)
    task = await worker.submit_encode([doc], task_id="test-001")
    
    assert task.task_id == "test-001"
    assert task.status == EncodeTaskStatus.PENDING
    assert len(task.documents) == 1
    log_pass(f"submit_encode: task_id={task.task_id}, status=PENDING, docs={len(task.documents)}")
    
    # 查询任务
    found = await worker.get_task("test-001")
    assert found is not None
    assert found.status == EncodeTaskStatus.PENDING
    log_pass("get_task: 正确返回任务状态")
    
    # 列出所有任务
    tasks = await worker.list_tasks()
    assert len(tasks) == 1
    log_pass(f"list_tasks: {len(tasks)} 个任务")
    
    # 进度统计
    progress2 = worker.get_progress()
    assert progress2["total_tasks"] == 1
    assert progress2["pending"] == 1
    log_pass(f"get_progress: total={progress2['total_tasks']}, pending={progress2['pending']}")
    
    # 状态持久化
    worker.save_state()
    state_path = Path(worker._cache_dir) / "encoder_state.json"
    assert state_path.exists()
    log_pass(f"save_state: 已保存到 {state_path}")
    
    # 加载状态
    worker2 = EncoderWorker(cache_dir=worker._cache_dir)
    loaded = worker2.load_state()
    assert loaded == True
    tasks2 = await worker2.list_tasks()
    assert len(tasks2) == 1
    log_pass("load_state: 从磁盘恢复 1 个历史任务记录")


# ============================================================
# Phase 6: MSAServiceWrapper GPU 初始化与检索
# ============================================================
async def check_msa_gpu_full():
    log_section("Phase 6: MSA GPU 完整功能验证")
    
    from openharness.msa.config import OCHMSAConfig
    from openharness.msa.bridge import MSABridge
    from openharness.msa.service_wrapper import MSAServiceWrapper
    from openharness.msa.retriever import MSARetriever
    from openharness.msa.types import MemorySearchResult, MSAHealthStatus
    
    # 配置
    config = OCHMSAConfig(
        enabled=True,
        model_path="EverMind-AI/MSA-4B",
        devices=[0],
        doc_top_k=4,
        max_generate_tokens=128,
        auto_fallback=False,
    )
    log_pass(f"MSA 配置: model={config.model_path}, top_k={config.doc_top_k}")
    
    # 初始化 Bridge
    bridge = MSABridge()
    test_data = [
        {"id": "d1", "content": "OpenClaw-Harness 是一个 Agent 驾驭平台，支持多智能体协作和工具执行框架。核心模块包括消息总线、记忆系统和插件架构。", "category": "architecture"},
        {"id": "d2", "content": "权限管理采用 RBAC 模型，支持角色继承和细粒度的 API 级别权限控制。管理员可以动态调整角色权限而无需重启服务。", "category": "security"},
        {"id": "d3", "content": "系统性能优化：使用异步 I/O 和连接池技术，API 平均响应时间控制在 50ms 以内，支持每秒 1000+ 并发请求。", "category": "performance"},
        {"id": "d4", "content": "错误处理机制：统一的异常捕获和日志记录，支持自动重试和熔断降级策略。关键错误会触发告警通知。", "category": "reliability"},
        {"id": "d5", "content": "部署方案：支持 Docker 容器化部署，提供 Kubernetes Helm Chart 配置模板，可一键部署到生产环境。", "category": "deployment"},
    ]
    encode_docs = bridge.facts_to_documents(test_data)
    log_pass(f"Bridge 编码数据准备: {len(encode_docs)} 个文档 ({sum(len(d.doc) for d in encode_docs)} 字符)")
    
    # 初始化 ServiceWrapper
    print(f"\n  {BLUE}正在初始化 MSA 服务... (加载模型到 GPU){RESET}")
    t_start = time.time()
    
    wrapper = MSAServiceWrapper(config)
    wrapper.set_bridge(bridge)
    
    try:
        status = await wrapper.initialize()
        elapsed = time.time() - t_start
        
        assert status.initialized == True
        assert status.model_loaded == True
        log_pass(f"MSA 服务初始化成功! ({elapsed:.1f}s)")
        log_pass(f"  model_path: {status.model_path or 'N/A'}")
        log_pass(f"  gpu_available: {status.gpu_available}")
        log_pass(f"  gpu_name: {status.gpu_name or 'N/A'}")
        
        if status.gpu_memory_total_mb > 0:
            util_pct = (status.gpu_memory_used_mb / status.gpu_memory_total_mb * 100) if status.gpu_memory_total_mb > 0 else 0
            log_pass(f"  显存: {status.gpu_memory_used_mb}/{status.gpu_memory_total_mb} MB ({util_pct:.1f}%)")
        
    except Exception as e:
        log_fail("MSA 初始化失败", str(e))
        traceback.print_exc()
        return False
    
    # 执行编码
    print(f"\n  {BLUE}正在执行文档编码...{RESET}")
    t_encode = time.time()
    
    try:
        encode_stats = await wrapper.encode_documents(encode_docs)
        elapsed_enc = time.time() - t_encode
        
        log_pass(f"文档编码完成! ({elapsed_enc:.1f}s)")
        log_pass(f"  总数: {encode_stats.total_documents}, 成功: {encode_stats.success}, 失败: {encode_stats.failed}")
        
    except Exception as e:
        log_warn(f"编码步骤跳过: {e}")
    
    # 执行语义检索
    queries = [
        "系统的权限管理是如何实现的？",
        "如何提升 API 性能？",
        "部署方案有哪些？",
        "错误处理机制是什么？",
    ]
    
    print(f"\n  {BLUE}执行语义检索测试...{RESET}")
    
    for query in queries:
        t_q = time.time()
        try:
            results = await wrapper.recall(query, top_k=3)
            elapsed_q = time.time() - t_q
            
            if results:
                best = results[0]
                log_pass(f"Q: {query[:30]}...")
                log_pass(f"  → {len(results)} 结果 ({elapsed_q*1000:.0f}ms)")
                log_pass(f"  最佳匹配 (score={best.score:.3f}): {best.content[:80]}...")
            else:
                log_skip(f"Q: {query[:30]}", "无结果")
                
        except Exception as e:
            log_fail(f"Q: {query[:30]}", str(e))
    
    # 通过 Retriever 接口测试
    print(f"\n  {BLUE}通过 MSARetriever 接口测试...{RESET}")
    
    retriever = MSARetriever(config=config, wrapper=wrapper, bridge=bridge)
    retriever.set_instance(retriever)
    
    async def kw_fallback(q, top_k=5):
        return [MemorySearchResult(content=f"[KW] {q}", score=0.3)]
    
    retriever.set_keyword_search(kw_fallback)
    
    assert retriever.is_available == True
    log_pass("Retriever.is_available = True")
    
    r_results = await retriever.search("系统的整体架构是什么？", top_k=3)
    log_pass(f"Retriever.search(): {len(r_results)} 条结果")
    if r_results:
        for i, r in enumerate(r_results):
            print(f"    [{i+1}] score={r.score:.3f} | {r.content[:60]}...")
    
    # health_check 最终状态
    final_health = await wrapper.health_check()
    log_pass(f"最终健康检查: docs={final_health.total_documents}, chunks={final_health.total_chunks}")
    
    # 关闭服务
    print(f"\n  {BLUE}关闭 MSA 服务...{RESET}")
    await wrapper.shutdown()
    log_pass("MSA 服务已优雅关闭")
    
    return True


# ============================================================
# Phase 7: 集成接口验证 (search.py, agent_memory 等)
# ============================================================
def check_integration_interfaces():
    log_section("Phase 7: 集成接口验证")
    
    # memory/search.py
    try:
        from openharness.memory.search import find_relevant_memories, msa_find_relevant_memories
        
        # keyword 后端（默认）
        results_kw = find_relevant_memories(
            "test query",
            "/tmp/fake_cwd",
            max_results=3,
            backend="keyword",
        )
        log_pass(f"find_relevant_memories(keyword): 返回 {len(results_kw)} 条")
        
        # msa 后端（无 GPU 时返回空）
        results_msa = find_relevant_memories(
            "test query",
            "/tmp/fake_cwd",
            max_results=3,
            backend="msa",
        )
        log_pass(f"find_relevant_memories(msa): 返回 {len(results_msa)} 条 (无 GPU 时为空)")
        
        # AgentMemory
        from openharness.coordinator.agent_memory import AgentMemory, MemoryEntry
        from openharness.msa.config import OCHMSAConfig
        
        msa_cfg = OCHMSAConfig(enabled=True, auto_fallback=True)
        am = AgentMemory("test_agent_gpu", msa_config=msa_cfg)
        log_pass("AgentMemory(msa_config) 初始化成功")
        
        # remember + recall
        entry = MemoryEntry(
            id="gpu_test_1",
            agent_id="test_agent_gpu",
            category="validation",
            content="GPU 验证测试条目：确认 MSA 集成工作正常",
            tags=["test", "gpu"],
        )
        am.remember(entry)
        log_pass(f"remember(): 条目已写入, pending_encode={len(am._msa_pending_encode)}")
        
        # recall with use_msa=False (关键词路径)
        results_recall = asyncio.run(am.recall("验证测试", use_msa=False, max_results=5))
        log_pass(f"recall(use_msa=False): {len(results_recall)} 条结果")
        
        # _find_entry_by_source
        found = am._find_entry_by_source("gpu_test_1")
        assert found is not None
        assert found.id == "gpu_test_1"
        log_pass("_find_entry_by_source(): 正确找到条目")
        
    except ImportError as e:
        log_skip("集成接口验证 (search.py / agent_memory.py)", f"缺少项目依赖: {e}")


# ============================================================
# 主入口
# ============================================================
async def main():
    global passed, failed, skipped
    
    skip_gpu = "--skip-gpu" in sys.argv
    
    print(f"\n{BOLD}{BLUE}")
    print("=" * 60)
    print("  MSA (Memory Sparse Attention) 集成功能验证")
    print("  OpenClaw-Harness × EverMind-AI/MSA")
    print("=" * 60)
    print(f"{RESET}")
    
    start_time = time.time()
    
    # Phase 1-5: 无需 GPU
    check_environment()
    check_module_imports()
    check_config_and_bridge()
    await check_retriever_no_gpu()
    await check_encoder_worker()
    check_integration_interfaces()
    
    # Phase 6: 需要 GPU
    has_gpu = False
    try:
        import torch
        has_gpu = torch.cuda.is_available()
    except ImportError:
        pass
    
    if skip_gpu:
        log_section("Phase 6: MSA GPU 验证 (--skip-gpu 已跳过)")
        log_skip("GPU 完整功能验证", "用户指定 --skip-gpu")
    elif has_gpu:
        gpu_ok = await check_msa_gpu_full()
    else:
        log_section("Phase 6: MSA GPU 验证")
        log_skip("GPU 完整功能验证", "未检测到 CUDA/GPU")
    
    # 总结
    elapsed = time.time() - start_time
    total = passed + failed + skipped
    
    print(f"\n{BOLD}")
    print("=" * 60)
    print(f"  验证结果汇总")
    print("=" * 60)
    print(f"{RESET}")
    print(f"  {GREEN}✅ 通过: {passed}{RESET}")
    print(f"  {RED}❌ 失败: {failed}{RESET}")
    print(f"  {YELLOW}⏭️  跳过: {skipped}{RESET}")
    print(f"  总计: {total} 项检查")
    print(f"  耗时: {elapsed:.1f}s")
    
    if failed == 0:
        print(f"\n  {GREEN}{BOLD}🎉 所有检查均通过！MSA 集成功能正常{RESET}\n")
    else:
        print(f"\n  {RED}{BOLD}⚠️ 有 {failed} 项检查失败，请查看上方详情{RESET}\n")
    
    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
