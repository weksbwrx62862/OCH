---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

**vs. Executing Plans (parallel session):**
- Same session (no context switch)
- Fresh subagent per task (no context pollution)
- Two-stage review after each task: spec compliance first, then code quality
- Faster iteration (no human-in-loop between tasks)

## The Process

1. Read plan, extract all tasks with full text, note context, create TodoWrite
2. Per Task:
   - Dispatch implementer subagent
   - Implementer subagent implements, tests, commits, self-reviews
   - Dispatch spec reviewer subagent
   - Dispatch code quality reviewer subagent
   - Mark task complete in TodoWrite
3. After all tasks: Dispatch final code reviewer subagent
4. Use finishing-a-development-branch
