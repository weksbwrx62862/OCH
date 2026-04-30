"""Subagent Executor — 双线程池子代理执行引擎.

参考 DeerFlow SubagentExecutor 的设计:
- 调度池 + 执行池分离（避免调度阻塞执行）
- 并发限制控制
- 超时保护
- 流式结果收集
- 工具过滤（allowlist / denylist）
- 状态机: PENDING → RUNNING → COMPLETED/FAILED/TIMED_OUT
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SubagentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass
class SubagentTask:
    """子代理任务定义."""
    task_id: str
    agent_id: str
    prompt: str
    parent_trace_id: Optional[str] = None
    tools_allowlist: Optional[List[str]] = None
    tools_denylist: Optional[List[str]] = None
    model_override: Optional[str] = None
    timeout_seconds: float = 900.0  # 15 分钟默认超时
    metadata: Dict[str, Any] = field(default_factory=dict)

    status: SubagentStatus = SubagentStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class SubagentConfig:
    """子代理执行器配置."""
    max_concurrent: int = 3
    scheduler_workers: int = 3
    execution_workers: int = 3
    default_timeout_seconds: float = 900.0
    enable_streaming: bool = True


class DualPoolSubagentExecutor:
    """双线程池子代理执行器.

    架构:
        任务提交 → 调度池(排队) → 执行池(运行) → 结果收集

    用法:
        executor = DualPoolSubagentExecutor(SubagentConfig())
        task = await executor.submit(prompt="审查这段代码")
        result = await executor.get_result(task.task_id)
    """

    def __init__(self, config: Optional[SubagentConfig] = None):
        self._config = config or SubagentConfig()
        self._tasks: Dict[str, SubagentTask] = {}
        self._lock = Lock()

        # 调度线程池：负责任务排队和状态管理
        self._scheduler_pool = ThreadPoolExecutor(
            max_workers=self._config.scheduler_workers,
            thread_name_prefix="subagent-sched",
        )

        # 执行线程池：负责实际子代理执行
        self._execution_pool = ThreadPoolExecutor(
            max_workers=self._config.execution_workers,
            thread_name_prefix="subagent-exec",
        )

        # 运行中的任务追踪（用于并发限制）
        self._running_count = 0
        self._running_lock = Lock()

        logger.info(
            "双线程池子代理执行器初始化完成 (调度=%d, 执行=%d, 并发上限=%d)",
            self._config.scheduler_workers,
            self._config.execution_workers,
            self._config.max_concurrent,
        )

    @property
    def config(self) -> SubagentConfig:
        return self._config

    def submit(self, task: SubagentTask) -> SubagentTask:
        """提交子代理任务到调度池."""
        with self._lock:
            if task.task_id in self._tasks:
                raise ValueError(f"Task {task.task_id} already exists")
            self._tasks[task.task_id] = task

        future = self._scheduler_pool.submit(self._schedule_task, task)
        task._future = future
        logger.info("提交子代理任务: %s (agent=%s)", task.task_id[:8], task.agent_id)
        return task

    def _schedule_task(self, task: SubagentTask) -> None:
        """调度任务 — 等待可用槽位后提交到执行池."""
        with self._running_lock:
            while self._running_count >= self._config.max_concurrent:
                time.sleep(0.5)
            self._running_count += 1

        task.status = SubagentStatus.RUNNING
        task.started_at = time.time()

        try:
            future = self._execution_pool.submit(self._execute_task, task)
            future.result(timeout=task.timeout_seconds)
        except FuturesTimeoutError:
            task.status = SubagentStatus.TIMED_OUT
            task.error = f"Timeout after {task.timeout_seconds}s"
            logger.warning("子代理任务超时: %s", task.task_id[:8])
        except Exception as e:
            task.status = SubagentStatus.FAILED
            task.error = str(e)
            logger.exception("子代理任务失败: %s", task.task_id[:8])
        finally:
            with self._running_lock:
                self._running_count -= 1
            task.completed_at = time.time()

    def _execute_task(self, task: SubagentTask) -> None:
        """在执行池中实际运行子代理."""
        logger.info(
            "开始执行子代理: %s (prompt=%s)",
            task.task_id[:8],
            task.prompt[:50],
        )

        # 模拟执行（实际对接 LLM Agent Loop）

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = []
            for i, chunk in enumerate(_mock_agent_stream(task.prompt)):
                results.append(chunk)
                if i < 2:
                    time.sleep(0.05)

            task.result = {
                'task_id': task.task_id,
                'agent_id': task.agent_id,
                'status': 'completed',
                'output': ''.join(results),
                'chunks': len(results),
                'duration_sec': round(time.time() - (task.started_at or 0), 2),
            }
            task.status = SubagentStatus.COMPLETED
        except Exception as e:
            task.status = SubagentStatus.FAILED
            task.error = str(e)
        finally:
            loop.close()

    def get_task(self, task_id: str) -> Optional[SubagentTask]:
        """获取任务状态和结果."""
        return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消等待中的任务."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != SubagentStatus.PENDING:
                return False
            task.status = SubagentStatus.CANCELLED
            return True

    def list_tasks(
        self,
        status_filter: Optional[SubagentStatus] = None,
    ) -> List[Dict[str, Any]]:
        """列出所有任务."""
        tasks = []
        for t in self._tasks.values():
            if status_filter and t.status != status_filter:
                continue
            tasks.append({
                'task_id': t.task_id,
                'agent_id': t.agent_id,
                'status': t.status.value,
                'prompt_preview': t.prompt[:80],
                'created_at': t.created_at,
                'started_at': t.started_at,
                'completed_at': t.completed_at,
                'error': t.error,
            })
        return sorted(tasks, key=lambda x: x['created_at'], reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        """获取执行器统计信息."""
        total = len(self._tasks)
        by_status = {}
        for t in self._tasks.values():
            s = t.status.value
            by_status[s] = by_status.get(s, 0) + 1

        total_duration = sum(
            ((t.completed_at or 0) - (t.started_at or 0))
            for t in self._tasks.values()
            if t.completed_at and t.started_at
        )

        return {
            'total_tasks_submitted': total,
            'by_status': by_status,
            'currently_running': self._running_count,
            'max_concurrent': self._config.max_concurrent,
            'scheduler_queue_size': self._scheduler_pool._work_queue.qsize(),
            'execution_queue_size': self._execution_pool._work_queue.qsize(),
            'avg_duration_sec': round(total_duration / max(total - by_status.get('pending', 0), 1), 2),
            'config': {
                'scheduler_workers': self._config.scheduler_workers,
                'execution_workers': self._config.execution_workers,
                'default_timeout': self._config.default_timeout_seconds,
            },
        }

    def shutdown(self, wait: bool = True):
        """关闭执行器."""
        self._scheduler_pool.shutdown(wait=wait)
        self._execution_pool.shutdown(wait=wait)
        logger.info("子代理执行器已关闭")


def _mock_agent_stream(prompt: str):
    """模拟 Agent 流式输出."""
    yield f"[subagent] 分析请求: {prompt[:40]}...\n"
    yield "[subagent] 执行工具调用...\n"
    yield "[subagent] 生成响应...\n"
    yield f"[subagent] 完成: 处理了 {len(prompt)} 字符的输入\n"


# 全局实例
_global_executor: Optional[DualPoolSubagentExecutor] = None
_executor_lock = Lock()


def get_subagent_executor() -> DualPoolSubagentExecutor:
    """获取全局子代理执行器实例."""
    global _global_executor
    with _executor_lock:
        if _global_executor is None:
            _global_executor = DualPoolSubagentExecutor(SubagentConfig())
    return _global_executor
