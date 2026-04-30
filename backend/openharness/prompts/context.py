"""Higher-level system prompt assembly."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from openharness.config.paths import get_project_issue_file, get_project_pr_comments_file
from openharness.config.settings import Settings
from openharness.memory import find_relevant_memories, load_memory_prompt
from openharness.msa.retriever import MSARetriever
from openharness.prompts.claudemd import load_claude_md_prompt
from openharness.prompts.system_prompt import build_system_prompt
from openharness.skills.loader import load_skill_registry

log = logging.getLogger(__name__)


def _build_skills_section(cwd: str | Path) -> str | None:
    """Build a system prompt section listing available skills."""
    registry = load_skill_registry(cwd)
    skills = registry.list_skills()
    if not skills:
        return None
    lines = [
        "# Available Skills",
        "",
        "The following skills are available via the `skill` tool. "
        'When a user\'s request matches a skill, invoke it with `skill(name="<skill_name>")` '
        "to load detailed instructions before proceeding.",
        "",
    ]
    for skill in skills:
        lines.append(f"- **{skill.name}**: {skill.description}")
    return "\n".join(lines)


async def _inject_msa_memories(
    prompt: str,
    agent_id: str | None = None,
    max_tokens: int = 4000,
) -> str:
    """将 MSA 检索到的相关记忆注入到系统提示中
    
    Args:
        prompt: 原始系统提示文本
        agent_id: 当前 Agent ID（用于过滤）
        max_tokens: MSA 记忆注入的最大 token 预算
        
    Returns:
        注入后的完整系统提示
    """
    retriever = MSARetriever.get_instance()
    if retriever is None or not retriever.is_available:
        return prompt

    if "# Relevant Memories" in prompt or "# MSA" in prompt:
        return prompt  # 已包含记忆，避免重复注入

    try:
        # 从 prompt 中提取关键查询词用于检索
        query = _extract_query_from_prompt(prompt)

        results = await retriever.search(
            query,
            top_k=5,
            force_backend="msa",
        )

        if not results:
            return prompt

        msa_section = _format_msa_results(results)

        if len(msa_section) > max_tokens * 4:  # 粗略估算 token 数
            log.warning("MSA 记忆超出预算，截断输出")
            msa_section = msa_section[:max_tokens * 4]

        return f"{prompt}\n\n{msa_section}"

    except Exception as e:
        log.warning("MSA 记忆注入失败: %s", e, exc_info=True)
        return prompt


def _extract_query_from_prompt(prompt: str) -> str:
    """从系统提示中提取关键查询词"""
    lines = prompt.strip().split('\n')
    keywords = []
    for line in lines[:20]:  # 只看前20行
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            if len(line) > 5:
                keywords.append(line[:100])
    return ' '.join(keywords[-3:]) if keywords else "recent context"


def _format_msa_results(results: list) -> str:
    """格式化 MSA 检索结果为 Markdown 文本"""
    parts = ["# MSA Relevant Memories (语义检索)", ""]
    for i, r in enumerate(results, 1):
        source_label = f"{r.source_type.value}:{r.source_id}" if r.source_id else r.source_type.value
        score_str = f"{r.score:.2f}" if r.score else "N/A"
        category_str = f"[{r.category}]" if r.category else ""

        content_preview = r.content
        if len(content_preview) > 500:
            content_preview = content_preview[:500] + "..."

        part = f"## {source_label} {category_str}(相关度: {score_str})\n{content_preview}"
        parts.append(part)
        parts.append("")

    return "\n".join(parts)


def build_runtime_system_prompt(
    settings: Settings,
    *,
    cwd: str | Path,
    latest_user_prompt: str | None = None,
) -> str:
    """Build the runtime system prompt with project instructions and memory."""
    sections = [build_system_prompt(custom_prompt=settings.system_prompt, cwd=str(cwd))]

    if settings.fast_mode:
        sections.append(
            "# Session Mode\nFast mode is enabled. Prefer concise replies, minimal tool use, and quicker progress over exhaustive exploration."
        )

    sections.append(
        "# Reasoning Settings\n"
        f"- Effort: {settings.effort}\n"
        f"- Passes: {settings.passes}\n"
        "Adjust depth and iteration count to match these settings while still completing the task."
    )

    skills_section = _build_skills_section(cwd)
    if skills_section:
        sections.append(skills_section)

    claude_md = load_claude_md_prompt(cwd)
    if claude_md:
        sections.append(claude_md)

    for title, path in (
        ("Issue Context", get_project_issue_file(cwd)),
        ("Pull Request Comments", get_project_pr_comments_file(cwd)),
    ):
        if path.exists():
            content = path.read_text(encoding="utf-8", errors="replace").strip()
            if content:
                sections.append(f"# {title}\n\n```md\n{content[:12000]}\n```")

    if settings.memory.enabled:
        memory_section = load_memory_prompt(
            cwd,
            max_entrypoint_lines=settings.memory.max_entrypoint_lines,
        )
        if memory_section:
            sections.append(memory_section)

        if latest_user_prompt:
            relevant = find_relevant_memories(
                latest_user_prompt,
                cwd,
                max_results=settings.memory.max_files,
            )
            if relevant:
                lines = ["# Relevant Memories"]
                for header in relevant:
                    content = header.path.read_text(encoding="utf-8", errors="replace").strip()
                    lines.extend(
                        [
                            "",
                            f"## {header.path.name}",
                            "```md",
                            content[:8000],
                            "```",
                        ]
                    )
                sections.append("\n".join(lines))

    final_prompt = "\n\n".join(section for section in sections if section.strip())

    # === 新增：MSA 语义记忆注入 ===
    try:
        if settings.msa.enabled:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()

            final_prompt = loop.run_until_complete(
                _inject_msa_memories(
                    final_prompt,
                    agent_id=None,
                    max_tokens=settings.memory.max_tokens,
                )
            )
    except Exception as e:
        log.debug("MSA 提示注入跳过: %s", e)

    return final_prompt
