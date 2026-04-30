"""High-level conversation engine."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncIterator

from openharness.api.client import SupportsStreamingMessages
from openharness.engine.cost_tracker import CostTracker
from openharness.engine.messages import ConversationMessage, ToolResultBlock
from openharness.engine.query import AskUserPrompt, PermissionPrompt, QueryContext, run_query
from openharness.engine.stream_events import StreamEvent
from openharness.hooks import HookExecutor
from openharness.msa.retriever import MSARetriever
from openharness.msa.types import MemorySearchResult
from openharness.permissions.checker import PermissionChecker
from openharness.permissions.denial_tracking import DenialTracker
from openharness.tools.base import ToolRegistry

log = logging.getLogger(__name__)


class QueryEngine:
    """Owns conversation history and the tool-aware model loop."""

    def __init__(
        self,
        *,
        api_client: SupportsStreamingMessages,
        tool_registry: ToolRegistry,
        permission_checker: PermissionChecker,
        cwd: str | Path,
        model: str,
        system_prompt: str,
        max_tokens: int = 4096,
        max_turns: int = 8,
        permission_prompt: PermissionPrompt | None = None,
        ask_user_prompt: AskUserPrompt | None = None,
        hook_executor: HookExecutor | None = None,
        tool_metadata: dict[str, object] | None = None,
        denial_tracker: DenialTracker | None = None,  # Phase 2: 可选的权限拒绝追踪器
        msa_retriever: MSARetriever | None = None,  # MSA 语义检索器
    ) -> None:
        self._api_client = api_client
        self._tool_registry = tool_registry
        self._permission_checker = permission_checker
        self._cwd = Path(cwd).resolve()
        self._model = model
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._max_turns = max_turns
        self._permission_prompt = permission_prompt
        self._ask_user_prompt = ask_user_prompt
        self._hook_executor = hook_executor
        self._tool_metadata = tool_metadata or {}
        self._denial_tracker = denial_tracker or DenialTracker()  # Phase 2 集成
        self._msa_retriever = msa_retriever  # MSA 检索器实例
        self._messages: list[ConversationMessage] = []
        self._cost_tracker = CostTracker()

    @property
    def messages(self) -> list[ConversationMessage]:
        """Return the current conversation history."""
        return list(self._messages)

    @property
    def max_turns(self) -> int:
        """Return the maximum number of agentic turns per user input."""
        return self._max_turns

    @property
    def total_usage(self):
        """Return the total usage across all turns."""
        return self._cost_tracker.total

    @property
    def denial_tracker(self) -> DenialTracker:
        """Return the permission denial tracker (Phase 2)."""
        return self._denial_tracker

    def clear(self) -> None:
        """Clear the in-memory conversation history."""
        self._messages.clear()
        self._cost_tracker = CostTracker()

    def set_system_prompt(self, prompt: str) -> None:
        """Update the active system prompt for future turns."""
        self._system_prompt = prompt

    def set_model(self, model: str) -> None:
        """Update the active model for future turns."""
        self._model = model

    def set_max_turns(self, max_turns: int) -> None:
        """Update the maximum number of agentic turns per user input."""
        self._max_turns = max(1, int(max_turns))

    def set_permission_checker(self, checker: PermissionChecker) -> None:
        """Update the active permission checker for future turns."""
        self._permission_checker = checker

    def load_messages(self, messages: list[ConversationMessage]) -> None:
        """Replace the in-memory conversation history."""
        self._messages = list(messages)

    def has_pending_continuation(self) -> bool:
        """Return True when the conversation ends with tool results awaiting a follow-up model turn."""
        if not self._messages:
            return False
        last = self._messages[-1]
        if last.role != "user":
            return False
        if not any(isinstance(block, ToolResultBlock) for block in last.content):
            return False
        for msg in reversed(self._messages[:-1]):
            if msg.role != "assistant":
                continue
            return bool(msg.tool_uses)
        return False

    async def submit_message(self, prompt: str) -> AsyncIterator[StreamEvent]:
        """Append a user message and execute the query loop."""
        self._messages.append(ConversationMessage.from_user_text(prompt))

        # === 新增：MSA 上下文增强 ===
        msa_context = ""
        if self._msa_retriever and self._msa_retriever.is_available:
            try:
                msa_results = await self._msa_retriever.search(
                    prompt,
                    top_k=3,
                    force_backend="msa",
                )
                if msa_results:
                    context_parts = ["[MSA Context Enhancement]"]
                    for r in msa_results:
                        context_parts.append(f"- [{r.score:.2f}] {r.content[:200]}")
                    msa_context = "\n".join(context_parts)

                    # 将 MSA 上下文追加到消息中
                    if msa_context:
                        enhanced_prompt = f"{prompt}\n\n{msa_context}"
                        # 更新最后一条用户消息
                        self._messages[-1] = ConversationMessage.from_user_text(enhanced_prompt)
            except Exception as e:
                log.debug("MSA 上下文增强跳过: %s", e)

        context = QueryContext(
            api_client=self._api_client,
            tool_registry=self._tool_registry,
            permission_checker=self._permission_checker,
            cwd=self._cwd,
            model=self._model,
            system_prompt=self._system_prompt,
            max_tokens=self._max_tokens,
            max_turns=self._max_turns,
            permission_prompt=self._permission_prompt,
            ask_user_prompt=self._ask_user_prompt,
            hook_executor=self._hook_executor,
            tool_metadata=self._tool_metadata,
        )
        async for event, usage in run_query(context, self._messages):
            if usage is not None:
                self._cost_tracker.add(usage)
            yield event

    async def continue_pending(self, *, max_turns: int | None = None) -> AsyncIterator[StreamEvent]:
        """Continue an interrupted tool loop without appending a new user message."""
        context = QueryContext(
            api_client=self._api_client,
            tool_registry=self._tool_registry,
            permission_checker=self._permission_checker,
            cwd=self._cwd,
            model=self._model,
            system_prompt=self._system_prompt,
            max_tokens=self._max_tokens,
            max_turns=max_turns if max_turns is not None else self._max_turns,
            permission_prompt=self._permission_prompt,
            ask_user_prompt=self._ask_user_prompt,
            hook_executor=self._hook_executor,
            tool_metadata=self._tool_metadata,
        )
        async for event, usage in run_query(context, self._messages):
            if usage is not None:
                self._cost_tracker.add(usage)
            yield event
