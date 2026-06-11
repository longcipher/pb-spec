---
name: pb-subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# pb-subagent-driven-development

Execute plans by dispatching fresh subagents per task, with two-stage review between tasks.

**Core principle:** Fresh context per task, independent review, sequential progress.

## When to Use

- Executing a written plan (from `pb-writing-plans` or `pb-improve`)
- Multiple independent tasks that benefit from context isolation
- When quality matters more than speed

**Don't use when:**

- Tasks are tightly coupled (shared state changes)
- Plan is trivial (1-2 small steps)
- No subagent capability available

## The Process

### Step 1: Load Plan

1. Read the plan file
2. Review task dependencies
3. Identify which tasks can run in parallel vs. sequentially

### Step 2: For Each Task

#### 2a. Prepare Context

Extract from the plan:

- Task description and steps
- Files to create/modify
- Verification commands and expected output
- Constraints and boundaries

#### 2b. Dispatch Subagent

Spawn a fresh subagent with:

- Task description only (not full plan)
- Relevant file paths
- Verification commands
- Constraints

**Context Hygiene:** Never pass the full plan or conversation history. Each subagent gets exactly what it needs.

#### 2c. Review Output

When subagent returns:

1. Check: Did it follow the plan steps?
2. Check: Did it run verification?
3. Check: Does output match expected?
4. Spot-check: Read key files for correctness

#### 2d. Mark Complete

Update plan checkbox: `- [x]` for completed steps.

### Step 3: Verify Integration

After all tasks:

1. Run full test suite
2. Run linter and type checker
3. Verify no regressions

## Subagent Prompt Template

```markdown
## Task: [Task Name]

### Goal

[One sentence describing what this builds]

### Steps

1. [Step 1 with exact file paths]
2. [Step 2 with verification command]
3. [Step 3 with commit message]

### Files

- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`

### Verification

Run: `uv run pytest tests/path/test.py -v`
Expected: All tests pass

### Constraints

- Do NOT modify files outside scope
- Follow existing code patterns
- Run verification before completing
```

## Common Mistakes

**❌ Passing full context:** Subagent gets confused by irrelevant information
**✅ Minimal context:** Only what's needed for this specific task

**❌ No verification check:** Trusting subagent report
**✅ Always verify:** Run the commands yourself after subagent completes

**❌ Skipping review:** Moving to next task without checking
**✅ Review every output:** Fresh eyes catch systematic errors

## Integration with pb-spec

- **pb-build:** This IS the pb-build workflow — Generator/Evaluator pattern
- **pb-improve:** Execute generated plans task-by-task
- **Standalone:** Use for any multi-task execution need
