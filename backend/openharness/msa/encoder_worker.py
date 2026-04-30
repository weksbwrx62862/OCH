"""MSA 离线编码工作管理器"""
from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from openharness.msa.types import EncodeStats
from openharness.msa.bridge import Document, MSABridge

log = logging.getLogger(__name__)


class EncodeTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EncodeTask:
    """编码任务"""
    task_id: str
    documents: list[Document] = field(default_factory=list)
    status: EncodeTaskStatus = EncodeTaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    stats: EncodeStats | None = None
    error: str = ""


class EncoderWorker:
    """后台编码任务管理器"""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or (Path.home() / ".openharness" / "msa_cache")
        self._tasks: dict[str, EncodeTask] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._service_wrapper: Any = None

    def set_service(self, service: Any) -> None:
        """设置 MSAServiceWrapper 实例"""
        self._service_wrapper = service

    async def start(self) -> None:
        """启动工作器"""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        log.info("编码工作器已启动")

    async def stop(self) -> None:
        """停止工作器"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        log.info("编码工作器已停止")

    async def submit_encode(
        self,
        documents: list[Document],
        *,
        task_id: str | None = None,
    ) -> EncodeTask:
        """提交编码任务"""
        tid = task_id or str(uuid.uuid4())[:8]

        task = EncodeTask(task_id=tid, documents=documents)
        self._tasks[tid] = task
        await self._queue.put(tid)

        log.info("编码任务已提交: %s (%d 个文档)", tid, len(documents))
        return task

    async def get_task(self, task_id: str) -> EncodeTask | None:
        """获取任务状态"""
        return self._tasks.get(task_id)

    async def list_tasks(self) -> list[EncodeTask]:
        """列出所有任务"""
        return list(self._tasks.values())

    async def _worker_loop(self) -> None:
        """工作循环 - 从队列取任务并执行编码"""
        while self._running:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_task(task_id)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("编码工作器异常: %s", e, exc_info=True)

    async def _process_task(self, task_id: str) -> None:
        """处理单个编码任务"""
        task = self._tasks.get(task_id)
        if task is None:
            return

        task.status = EncodeTaskStatus.RUNNING
        task.started_at = time.time()

        try:
            if self._service_wrapper is None:
                raise RuntimeError("未设置 ServiceWrapper")

            stats = await self._service_wrapper.encode_documents(task.documents)
            task.stats = stats
            task.status = EncodeTaskStatus.COMPLETED

            log.info(
                "编码任务完成: %s (成功=%d, 失败=%d)",
                task_id, stats.success, stats.failed,
            )

        except Exception as e:
            task.status = EncodeTaskStatus.FAILED
            task.error = str(e)
            log.error("编码任务失败 %s: %s", task_id, e, exc_info=True)

        finally:
            task.completed_at = time.time()

    def get_progress(self) -> dict[str, Any]:
        """获取整体进度信息"""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == EncodeTaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == EncodeTaskStatus.FAILED)
        running = sum(1 for t in self._tasks.values() if t.status == EncodeTaskStatus.RUNNING)
        pending = sum(1 for t in self._tasks.values() if t.status == EncodeTaskStatus.PENDING)

        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "is_running": self._running,
        }

    def save_state(self) -> None:
        """保存状态到磁盘"""
        state_path = self._cache_dir / "encoder_state.json"
        state = {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "status": t.status.value,
                    "created_at": t.created_at,
                    "error": t.error,
                    "stats": {
                        "total_documents": t.stats.total_documents,
                        "success": t.stats.success,
                        "failed": t.stats.failed,
                    } if t.stats else None,
                }
                for t in self._tasks.values()
            ],
            "saved_at": time.time(),
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def load_state(self) -> bool:
        """从磁盘加载状态"""
        state_path = self._cache_dir / "encoder_state.json"
        if not state_path.exists():
            return False

        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            for ts in state.get("tasks", []):
                task = EncodeTask(
                    task_id=ts["task_id"],
                    status=EncodeTaskStatus(ts["status"]),
                    created_at=ts.get("created_at", 0),
                    error=ts.get("error", ""),
                )
                self._tasks[ts["task_id"]] = task

            log.info("从磁盘加载了 %d 个历史任务记录", len(state.get("tasks", [])))
            return True
        except Exception as e:
            log.warning("加载编码状态失败: %s", e)
            return False
