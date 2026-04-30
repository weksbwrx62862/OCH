---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development (TDD)

## Overview

Write the test first. Watch it fail. Write minimal code to pass.

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over.

## Red-Green-Refactor

### RED - Write Failing Test

Write one minimal test showing what should happen.

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

### GREEN - Minimal Code

Write simplest code to pass the test.

### Verify GREEN - Watch It Pass

**MANDATORY.**

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

## Good Tests

| Quality | Good |
|---------|------|
| **Minimal** | One thing |
| **Clear** | Name describes behavior |
| **Shows intent** | Demonstrates desired API |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks |
| "I'll test after" | Tests passing immediately prove nothing |
| "Already manually tested" | Ad-hoc ≠ systematic |
