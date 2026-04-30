"""Hook Service — manages HookExecutor for lifecycle events."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_hook_executor = None


def get_hook_executor():
    """获取全局 HookExecutor 实例（延迟初始化）."""
    global _hook_executor
    if _hook_executor is None:
        try:
            from openharness.hooks.executor import HookExecutor, HookExecutionContext
            from openharness.hooks.loader import HookRegistry

            registry = HookRegistry()
            context = HookExecutionContext(
                cwd=Path.cwd(),
                api_client=None,
                default_model="default",
            )
            _hook_executor = HookExecutor(registry=registry, context=context)
            logger.info("HookExecutor 初始化完成")
        except Exception as e:
            logger.warning(f"HookExecutor 初始化失败（降级为空执行器）: {e}")
            _hook_executor = _NullHookExecutor()
    return _hook_executor


class _NullHookExecutor:
    """空 HookExecutor 降级实现（当 openharness.hooks 不可用时）."""

    async def execute(self, event, payload):
        from openharness.hooks.types import AggregatedHookResult
        return AggregatedHookResult(results=[])


async def trigger_hook(event_name: str, payload: dict) -> dict:
    """触发 Hook 事件并返回聚合结果.

    Args:
        event_name: 事件名称 ('pre_tool_use', 'post_tool_use' 等)
        payload: 事件负载数据

    Returns:
        {
            'blocked': bool,
            'results': list,
            'blocked_reason': str
        }
    """
    executor = get_hook_executor()
    try:
        from openharness.hooks.events import HookEvent

        event = HookEvent(event_name)
        result = await executor.execute(event, payload)

        blocked = any(r.blocked for r in result.results)
        blocked_reason = ""
        for r in result.results:
            if r.blocked:
                blocked_reason = r.reason or "Hook blocked operation"
                break

        return {
            'blocked': blocked,
            'results_count': len(result.results),
            'results': [
                {'type': str(r.hook_type), 'success': r.success, 'output': (r.output or "")[:200]}
                for r in result.results
            ],
            'blocked_reason': blocked_reason,
        }
    except Exception as e:
        logger.warning(f"Hook 触发异常 ({event_name}): {e}")
        return {'blocked': False, 'results_count': 0, 'results': [], 'blocked_reason': ''}
