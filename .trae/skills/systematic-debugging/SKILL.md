---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

## The Four Phases

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
2. **Reproduce Consistently**
3. **Check Recent Changes**
4. **Gather Evidence in Multi-Component Systems**
5. **Trace Data Flow**

### Phase 2: Pattern Analysis

**Find the pattern before fixing:**

1. **Find Working Examples**
2. **Compare Against References**
3. **Identify Differences**
4. **Understand Dependencies**

### Phase 3: Hypothesis and Testing

**Scientific method:**

1. **Form Single Hypothesis** - State clearly: "I think X is the root cause because Y"
2. **Test Minimally** - Make the SMALLEST possible change
3. **Verify Before Continuing**
4. **When You Don't Know** - Say "I don't understand X"

### Phase 4: Implementation

1. **Create Failing Test Case**
2. **Implement Single Fix**
3. **Verify Fix**
4. **If Fix Doesn't Work** - STOP and question the architecture

## Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "One more fix attempt" (when already tried 2+)

**ALL of these mean: STOP. Return to Phase 1.**
