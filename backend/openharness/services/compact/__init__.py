"""Conversation compaction — microcompact and full LLM-based summarization.

Faithfully translated from Claude Code's compaction system:
- Microcompact: clear old tool result content to reduce token count cheaply
- Full compact: call the LLM to produce a structured summary of older messages
- Auto-compact: trigger compaction automatically when token count exceeds threshold
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from openharness.engine.messages import (
    ConversationMessage,
    ContentBlock,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from openharness.services.compact.cached_compact import (
    CachedToolResult,
    CompactCache,
    CompactCacheConfig,
)
from openharness.services.token_estimation import estimate_tokens

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (from Claude Code microCompact.ts / autoCompact.ts)
# ---------------------------------------------------------------------------

COMPACTABLE_TOOLS: frozenset[str] = frozenset(
    {
        "read_file",
        "bash",
        "grep",
        "glob",
        "web_search",
        "web_fetch",
        "edit_file",
        "write_file",
    }
)

TIME_BASED_MC_CLEARED_MESSAGE = "[Old tool result content cleared]"

# Auto-compact thresholds
AUTOCOMPACT_BUFFER_TOKENS = 13_000
MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000
MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3

# Microcompact defaults
DEFAULT_KEEP_RECENT = 5
DEFAULT_GAP_THRESHOLD_MINUTES = 60.0


# 时间感知微压缩配置
@dataclass
class MicrocompactConfig:
    """微压缩配置（支持轮次和时间双重模式）"""

    keep_recent_turns: int = DEFAULT_KEEP_RECENT
    gap_threshold_minutes: float = DEFAULT_GAP_THRESHOLD_MINUTES
    enable_time_aware: bool = True

    def should_compact_by_time(
        self,
        message_index: int,
        total_messages: int,
        message_timestamp: float | None = None,
        current_timestamp: float | None = None,
    ) -> bool:
        """根据轮次或时间判断是否应该压缩该消息"""
        # 基于轮次：保留最近 N 轮的工具输出
        by_turns = (total_messages - message_index) > self.keep_recent_turns

        if not self.enable_time_aware or message_timestamp is None or current_timestamp is None:
            return by_turns

        # 基于时间：超过阈值的消息也压缩
        time_gap_minutes = (current_timestamp - message_timestamp) / 60.0
        by_time = time_gap_minutes > self.gap_threshold_minutes

        return by_turns or by_time


# Token estimation padding (conservative)
TOKEN_ESTIMATION_PADDING = 4 / 3

# Default context windows per model family
_DEFAULT_CONTEXT_WINDOW = 200_000


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


def estimate_message_tokens(messages: list[ConversationMessage]) -> int:
    """Estimate total tokens for a conversation, including the 4/3 padding."""
    total = 0
    for msg in messages:
        for block in msg.content:
            if isinstance(block, TextBlock):
                total += estimate_tokens(block.text)
            elif isinstance(block, ToolResultBlock):
                total += estimate_tokens(block.content)
            elif isinstance(block, ToolUseBlock):
                total += estimate_tokens(block.name)
                total += estimate_tokens(str(block.input))
    return int(total * TOKEN_ESTIMATION_PADDING)


def estimate_conversation_tokens(messages: list[ConversationMessage]) -> int:
    """Alias kept for backward compatibility."""
    return estimate_message_tokens(messages)


# ---------------------------------------------------------------------------
# Microcompact — clear old tool results to reduce tokens cheaply
# ---------------------------------------------------------------------------


def _collect_compactable_tool_ids(messages: list[ConversationMessage]) -> list[str]:
    """Walk messages and collect tool_use IDs whose results are compactable."""
    ids: list[str] = []
    for msg in messages:
        if msg.role != "assistant":
            continue
        for block in msg.content:
            if isinstance(block, ToolUseBlock) and block.name in COMPACTABLE_TOOLS:
                ids.append(block.id)
    return ids


def microcompact_messages(
    messages: list[ConversationMessage],
    *,
    keep_recent: int = DEFAULT_KEEP_RECENT,
) -> tuple[list[ConversationMessage], int]:
    """Clear old compactable tool results, keeping the most recent *keep_recent*.

    This is the cheap first pass — no LLM call required. Tool result content
    is replaced with :data:`TIME_BASED_MC_CLEARED_MESSAGE`.

    Returns:
        (messages, tokens_saved) — messages are mutated in place for efficiency.
    """
    keep_recent = max(1, keep_recent)  # never clear ALL results
    all_ids = _collect_compactable_tool_ids(messages)

    if len(all_ids) <= keep_recent:
        return messages, 0

    keep_set = set(all_ids[-keep_recent:])
    clear_set = set(all_ids) - keep_set

    tokens_saved = 0
    for msg in messages:
        if msg.role != "user":
            continue
        new_content: list[ContentBlock] = []
        for block in msg.content:
            if (
                isinstance(block, ToolResultBlock)
                and block.tool_use_id in clear_set
                and block.content != TIME_BASED_MC_CLEARED_MESSAGE
            ):
                tokens_saved += estimate_tokens(block.content)
                new_content.append(
                    ToolResultBlock(
                        tool_use_id=block.tool_use_id,
                        content=TIME_BASED_MC_CLEARED_MESSAGE,
                        is_error=block.is_error,
                    )
                )
            else:
                new_content.append(block)
        msg.content = new_content

    if tokens_saved > 0:
        log.info(
            "Microcompact cleared %d tool results, saved ~%d tokens", len(clear_set), tokens_saved
        )

    return messages, tokens_saved


def microcompact_messages_time_aware(
    messages: list[ConversationMessage],
    *,
    config: MicrocompactConfig | None = None,
    message_timestamps: list[float] | None = None,
    cache: CompactCache | None = None,
) -> tuple[list[ConversationMessage], int]:
    """时间感知版本的微压缩（增强版）

    除了基于轮次判断，还支持基于时间间隔压缩：
    - 如果用户离开超过 gap_threshold_minutes（默认 60 分钟），
      即使只有 2-3 轮对话，也会触发对旧工具输出的压缩
    - 可选传入 cache 参数，在清除时自动记录被删除的内容到缓存

    参考 Claude Code src/services/compact/timeBasedMCConfig.ts

    Args:
        messages: 消息列表
        config: 微压缩配置（可选，使用默认值）
        message_timestamps: 每条消息的时间戳列表（可选，长度应与 messages 相同）
        cache: 缓存管理器（可选，传入时在清除时记录缓存条目）

    Returns:
        (messages, tokens_saved)

    示例:
        >>> import time
        >>> msgs = [...]
        >>> now = time.time()
        >>> timestamps = [now - 3600, now - 3590, now - 10]  # 第一条是1小时前
        >>> result, saved = microcompact_messages_time_aware(
        ...     msgs,
        ...     message_timestamps=timestamps,
        ... )
    """
    if config is None:
        config = MicrocompactConfig()

    keep_recent = max(1, config.keep_recent_turns)
    all_ids = _collect_compactable_tool_ids(messages)

    if len(all_ids) <= keep_recent:
        return messages, 0

    if message_timestamps and len(message_timestamps) == len(messages):
        current_time = (message_timestamps or [time.time()])[-1]

        clear_set = set()
        for idx, tool_id in enumerate(all_ids):
            msg_idx = _find_message_index_for_tool_id(messages, tool_id)
            if msg_idx is not None:
                timestamp = (
                    message_timestamps[msg_idx] if msg_idx < len(message_timestamps) else None
                )

                if config.should_compact_by_time(
                    message_index=msg_idx,
                    total_messages=len(messages),
                    message_timestamp=timestamp,
                    current_timestamp=current_time,
                ):
                    clear_set.add(tool_id)
            else:
                if (len(all_ids) - all_ids.index(tool_id)) > keep_recent:
                    clear_set.add(tool_id)
    else:
        keep_set = set(all_ids[-keep_recent:])
        clear_set = set(all_ids) - keep_set

    if not clear_set:
        return messages, 0

    tokens_saved = 0
    for msg in messages:
        if msg.role != "user":
            continue
        new_content: list[ContentBlock] = []
        for block in msg.content:
            if (
                isinstance(block, ToolResultBlock)
                and block.tool_use_id in clear_set
                and block.content != TIME_BASED_MC_CLEARED_MESSAGE
            ):
                # 缓存记录：在清除前将原始内容存入缓存
                if cache is not None:
                    tool_name = _get_tool_name_for_tool_id(messages, block.tool_use_id)
                    cache.record_cleared(block.tool_use_id, tool_name, block.content)

                tokens_saved += estimate_tokens(block.content)
                new_content.append(
                    ToolResultBlock(
                        tool_use_id=block.tool_use_id,
                        content=TIME_BASED_MC_CLEARED_MESSAGE,
                        is_error=block.is_error,
                    )
                )
            else:
                new_content.append(block)
        msg.content = new_content

    if tokens_saved > 0:
        log.info(
            "Time-aware microcompact cleared %d tool results, saved ~%d tokens "
            "(gap_threshold=%.1fmin)",
            len(clear_set),
            tokens_saved,
            config.gap_threshold_minutes,
        )

    return messages, tokens_saved


def _find_message_index_for_tool_id(
    messages: list[ConversationMessage],
    tool_id: str,
) -> int | None:
    """查找包含指定 tool_use ID 的消息索引"""
    for idx, msg in enumerate(messages):
        if msg.role == "assistant":
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and block.id == tool_id:
                    return idx
    return None


def _get_tool_name_for_tool_id(
    messages: list[ConversationMessage],
    tool_id: str,
) -> str:
    """根据 tool_use ID 查找对应的工具名称"""
    for msg in messages:
        if msg.role == "assistant":
            for block in msg.content:
                if isinstance(block, ToolUseBlock) and block.id == tool_id:
                    return block.name
    return "unknown"


# ---------------------------------------------------------------------------
# Full compact — LLM-based summarization
# ---------------------------------------------------------------------------

NO_TOOLS_PREAMBLE = """\
CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.

- Do NOT use read_file, bash, grep, glob, edit_file, write_file, or ANY other tool.
- You already have all the context you need in the conversation above.
- Tool calls will be REJECTED and will waste your only turn — you will fail the task.
- Your entire response must be plain text: an <analysis> block followed by a <summary> block.

"""

BASE_COMPACT_PROMPT = """\
Your task is to create a detailed summary of the conversation so far. This summary will replace the earlier messages, so it must capture all important information.

First, draft your analysis inside <analysis> tags. Walk through the conversation chronologically and extract:
- Every user request and intent (explicit and implicit)
- The approach taken and technical decisions made
- Specific code, files, and configurations discussed (with paths and line numbers where available)
- All errors encountered and how they were fixed
- Any user feedback or corrections

Then, produce a structured summary inside <summary> tags with these sections:

1. **Primary Request and Intent**: All user requests in full detail, including nuances and constraints.
2. **Key Technical Concepts**: Technologies, frameworks, patterns, and conventions discussed.
3. **Files and Code Sections**: Every file examined or modified, with specific code snippets and line numbers.
4. **Errors and Fixes**: Every error encountered, its cause, and how it was resolved.
5. **Problem Solving**: Problems solved and approaches that worked vs. didn't work.
6. **All User Messages**: Non-tool-result user messages (preserve exact wording for context).
7. **Pending Tasks**: Explicitly requested work that hasn't been completed yet.
8. **Current Work**: Detailed description of the last task being worked on before compaction.
9. **Optional Next Step**: The single most logical next step, directly aligned with the user's recent request.
"""

NO_TOOLS_TRAILER = """
REMINDER: Do NOT call any tools. Respond with plain text only — an <analysis> block followed by a <summary> block. Tool calls will be rejected and you will fail the task."""


def get_compact_prompt(custom_instructions: str | None = None) -> str:
    """Build the full compaction prompt sent to the model."""
    prompt = NO_TOOLS_PREAMBLE + BASE_COMPACT_PROMPT
    if custom_instructions and custom_instructions.strip():
        prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
    prompt += NO_TOOLS_TRAILER
    return prompt


def format_compact_summary(raw_summary: str) -> str:
    """Strip the <analysis> scratchpad and extract the <summary> content."""
    text = re.sub(r"<analysis>[\s\S]*?</analysis>", "", raw_summary)
    m = re.search(r"<summary>([\s\S]*?)</summary>", text)
    if m:
        text = text.replace(m.group(0), f"Summary:\n{m.group(1).strip()}")
    text = re.sub(r"\n\n+", "\n\n", text)
    return text.strip()


def build_compact_summary_message(
    summary: str,
    *,
    suppress_follow_up: bool = False,
    recent_preserved: bool = False,
) -> str:
    """Create the injected user message that replaces compacted history."""
    formatted = format_compact_summary(summary)
    text = (
        "This session is being continued from a previous conversation that ran "
        "out of context. The summary below covers the earlier portion of the "
        "conversation.\n\n"
        f"{formatted}"
    )
    if recent_preserved:
        text += "\n\nRecent messages are preserved verbatim."
    if suppress_follow_up:
        text += (
            "\nContinue the conversation from where it left off without asking "
            "the user any further questions. Resume directly — do not acknowledge "
            "the summary, do not recap what was happening, do not preface with "
            '"I\'ll continue" or similar. Pick up the last task as if the break '
            "never happened."
        )
    return text


# ---------------------------------------------------------------------------
# Auto-compact tracking
# ---------------------------------------------------------------------------


@dataclass
class AutoCompactState:
    """Mutable state that persists across query loop turns."""

    compacted: bool = False
    turn_counter: int = 0
    consecutive_failures: int = 0


# ---------------------------------------------------------------------------
# Context window helpers
# ---------------------------------------------------------------------------


def get_context_window(model: str) -> int:
    """Return the context window size for a model (conservative defaults)."""
    m = model.lower()
    if "opus" in m:
        return 200_000
    if "sonnet" in m:
        return 200_000
    if "haiku" in m:
        return 200_000
    # Kimi / other providers — be conservative
    return _DEFAULT_CONTEXT_WINDOW


def get_autocompact_threshold(model: str) -> int:
    """Calculate the token count at which auto-compact fires."""
    context_window = get_context_window(model)
    reserved = min(MAX_OUTPUT_TOKENS_FOR_SUMMARY, 20_000)
    effective = context_window - reserved
    return effective - AUTOCOMPACT_BUFFER_TOKENS


def should_autocompact(
    messages: list[ConversationMessage],
    model: str,
    state: AutoCompactState,
) -> bool:
    """Return True when the conversation should be auto-compacted."""
    if state.consecutive_failures >= MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES:
        return False
    token_count = estimate_message_tokens(messages)
    threshold = get_autocompact_threshold(model)
    return token_count >= threshold


# ---------------------------------------------------------------------------
# Full compact execution (calls the LLM)
# ---------------------------------------------------------------------------


async def compact_conversation(
    messages: list[ConversationMessage],
    *,
    api_client: Any,
    model: str,
    system_prompt: str = "",
    preserve_recent: int = 6,
    custom_instructions: str | None = None,
    suppress_follow_up: bool = True,
) -> list[ConversationMessage]:
    """Compact messages by calling the LLM to produce a summary.

    1. Microcompact first (cheap token reduction).
    2. Split into older (to summarize) and recent (to preserve).
    3. Call the LLM with the compact prompt to get a structured summary.
    4. Replace older messages with the summary + preserved recent messages.

    Args:
        messages: The full conversation history.
        api_client: An ``AnthropicApiClient`` or compatible for the summary call.
        model: Model ID to use for the summary.
        system_prompt: System prompt for the summary call.
        preserve_recent: Number of recent messages to keep verbatim.
        custom_instructions: Optional extra instructions for the summary prompt.
        suppress_follow_up: If True, instruct the model not to ask follow-ups.

    Returns:
        The new compacted message list.
    """
    from openharness.api.client import ApiMessageRequest, ApiMessageCompleteEvent

    if len(messages) <= preserve_recent:
        return list(messages)

    # Step 1: microcompact to reduce tokens cheaply
    messages, tokens_freed = microcompact_messages(messages, keep_recent=DEFAULT_KEEP_RECENT)

    pre_compact_tokens = estimate_message_tokens(messages)
    log.info("Compacting conversation: %d messages, ~%d tokens", len(messages), pre_compact_tokens)

    # Step 2: split into older (summarize) and newer (preserve)
    older = messages[:-preserve_recent]
    newer = messages[-preserve_recent:]

    # Step 3: build compact request — send older messages + compact prompt
    compact_prompt = get_compact_prompt(custom_instructions)
    compact_messages = list(older) + [ConversationMessage.from_user_text(compact_prompt)]

    summary_text = ""
    async for event in api_client.stream_message(
        ApiMessageRequest(
            model=model,
            messages=compact_messages,
            system_prompt=system_prompt or "You are a conversation summarizer.",
            max_tokens=MAX_OUTPUT_TOKENS_FOR_SUMMARY,
            tools=[],  # no tools for compact call
        )
    ):
        if isinstance(event, ApiMessageCompleteEvent):
            summary_text = event.message.text

    if not summary_text:
        log.warning("Compact summary was empty — returning original messages")
        return messages

    # Step 4: build the new message list
    summary_content = build_compact_summary_message(
        summary_text,
        suppress_follow_up=suppress_follow_up,
        recent_preserved=len(newer) > 0,
    )
    summary_msg = ConversationMessage.from_user_text(summary_content)

    result = [summary_msg, *newer]
    post_compact_tokens = estimate_message_tokens(result)
    log.info(
        "Compaction done: %d -> %d messages, ~%d -> ~%d tokens (saved ~%d)",
        len(messages),
        len(result),
        pre_compact_tokens,
        post_compact_tokens,
        pre_compact_tokens - post_compact_tokens,
    )
    return result


# ---------------------------------------------------------------------------
# Auto-compact integration (called from query loop)
# ---------------------------------------------------------------------------


async def auto_compact_if_needed(
    messages: list[ConversationMessage],
    *,
    api_client: Any,
    model: str,
    system_prompt: str = "",
    state: AutoCompactState,
    preserve_recent: int = 6,
) -> tuple[list[ConversationMessage], bool]:
    """Check if auto-compact should fire, and if so, compact.

    Call this at the start of each query loop turn.

    Returns:
        (messages, was_compacted) — if compacted, messages is the new list.
    """
    if not should_autocompact(messages, model, state):
        return messages, False

    log.info("Auto-compact triggered (failures=%d)", state.consecutive_failures)

    # Try microcompact first — may be enough
    messages, tokens_freed = microcompact_messages(messages)
    if tokens_freed > 0 and not should_autocompact(messages, model, state):
        log.info("Microcompact freed ~%d tokens, auto-compact no longer needed", tokens_freed)
        return messages, True

    # Full compact needed
    try:
        result = await compact_conversation(
            messages,
            api_client=api_client,
            model=model,
            system_prompt=system_prompt,
            preserve_recent=preserve_recent,
            suppress_follow_up=True,
        )
        state.compacted = True
        state.turn_counter += 1
        state.consecutive_failures = 0
        return result, True
    except Exception as exc:
        state.consecutive_failures += 1
        log.error(
            "Auto-compact failed (attempt %d/%d): %s",
            state.consecutive_failures,
            MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES,
            exc,
        )
        return messages, False


# ---------------------------------------------------------------------------
# Legacy compat
# ---------------------------------------------------------------------------


def summarize_messages(
    messages: list[ConversationMessage],
    *,
    max_messages: int = 8,
) -> str:
    """Produce a compact textual summary of recent messages (legacy)."""
    selected = messages[-max_messages:]
    lines: list[str] = []
    for message in selected:
        text = message.text.strip()
        if not text:
            continue
        lines.append(f"{message.role}: {text[:300]}")
    return "\n".join(lines)


def compact_messages(
    messages: list[ConversationMessage],
    *,
    preserve_recent: int = 6,
) -> list[ConversationMessage]:
    """Replace older conversation history with a synthetic summary (legacy)."""
    if len(messages) <= preserve_recent:
        return list(messages)
    older = messages[:-preserve_recent]
    newer = messages[-preserve_recent:]
    summary = summarize_messages(older)
    if not summary:
        return list(newer)
    return [
        ConversationMessage(
            role="user",
            content=[TextBlock(text=f"[conversation summary]\n{summary}")],
        ),
        *newer,
    ]


async def cached_microcompact_messages(
    messages: list[ConversationMessage],
    *,
    config: MicrocompactConfig | None = None,
    cache: CompactCache | None = None,
    message_timestamps: list[float] | None = None,
) -> tuple[list[ConversationMessage], int, CompactCache]:
    """带缓存的微压缩（便捷包装）

    自动创建 cache（如果未提供），执行时间感知微压缩，
    返回结果消息、节省的 token 数和缓存实例。

    Args:
        messages: 消息列表
        config: 微压缩配置
        cache: 缓存实例（可选，未提供则自动创建）
        message_timestamps: 消息时间戳

    Returns:
        (messages, tokens_saved, cache)
    """
    if cache is None:
        cache = CompactCache()
    saved_msgs, tokens_saved = microcompact_messages_time_aware(
        messages, config=config, message_timestamps=message_timestamps, cache=cache
    )
    return saved_msgs, tokens_saved, cache


__all__ = [
    "AUTO_COMPACT_BUFFER_TOKENS",
    "AutoCompactState",
    "CachedToolResult",
    "COMPACTABLE_TOOLS",
    "CompactCache",
    "CompactCacheConfig",
    "TIME_BASED_MC_CLEARED_MESSAGE",
    "auto_compact_if_needed",
    "build_compact_summary_message",
    "cached_microcompact_messages",
    "compact_conversation",
    "compact_messages",
    "estimate_conversation_tokens",
    "estimate_message_tokens",
    "format_compact_summary",
    "get_autocompact_threshold",
    "get_compact_prompt",
    "microcompact_messages",
    "microcompact_messages_time_aware",
    "should_autocompact",
    "summarize_messages",
]
