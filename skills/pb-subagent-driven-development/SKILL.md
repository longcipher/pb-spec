---
name: pb-subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# pb-subagent-driven-development

Execute plans by dispatching fresh subagents per task, with two-stage review between tasks.

**Core principle:** Fresh context per task, independent review, sequential progress.

**Narration:** Between tool calls, narrate at most one short line — the ledger and the tool results carry the record.

**Continuous execution:** Do not pause to check in between tasks. Execute all tasks from the plan without stopping. The only reasons to stop are: BLOCKED status you cannot resolve, ambiguity that genuinely prevents progress, or all tasks complete.

## When to Use

- Executing a written plan (from `pb-plan` or `pb-improve`)
- Multiple independent tasks that benefit from context isolation
- When quality matters more than speed

**Don't use when:**

- Tasks are tightly coupled (shared state changes)
- Plan is trivial (1-2 small steps)
- No subagent capability available

## Pre-Flight Plan Review

Before dispatching Task 1, scan the plan once for conflicts:

- Tasks that contradict each other or the plan's Global Constraints
- Anything the plan explicitly mandates that the review rubric treats as a defect

Present everything you find as one batched question — each finding beside the plan text that mandates it, asking which governs — before execution begins. If the scan is clean, proceed without comment.

## Model Selection

Use the least powerful model that can handle each role to conserve cost and increase speed.

**Mechanical implementation tasks** (isolated functions, clear specs, 1-2 files): use a fast, cheap model. Most implementation tasks are mechanical when the plan is well-specified.

**Integration and judgment tasks** (multi-file coordination, pattern matching, debugging): use a standard model.

**Architecture and design tasks**: use the most capable available model.

**Review tasks**: choose the model with the same judgment, scaled to the diff's size, complexity, and risk.

**Always specify the model explicitly when dispatching a subagent.** An omitted model inherits your session's model — often the most capable and most expensive.

**Turn count beats token price.** Wall-clock and context cost scale with how many turns a subagent takes, and the cheapest models routinely take 2-3× the turns on multi-step work. Use a mid-tier model as the floor for reviewers and for implementers working from prose descriptions.

**Task complexity signals (implementation tasks):**

- Touches 1-2 files with a complete spec → cheap model
- Touches multiple files with integration concerns → standard model
- Requires design judgment or broad codebase understanding → most capable model

## The Process

### Step 1: Load Plan

1. Read the plan file
2. Review task dependencies
3. Identify which tasks can run in parallel vs. sequentially
4. Create todos for all tasks

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

#### 2c. Handle Implementer Status

Implementer subagents report one of four statuses:

**DONE:** Proceed to review.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If about correctness or scope, address them before review. If observations (e.g., "this file is getting large"), note them and proceed.

**NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch.

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:

1. If it's a context problem, provide more context and re-dispatch
2. If the task requires more reasoning, re-dispatch with a more capable model
3. If the task is too large, break it into smaller pieces
4. If the plan itself is wrong, escalate

**Never** ignore an escalation or force the same model to retry without changes.

#### 2d. Review Output

When subagent returns:

1. Check: Did it follow the plan steps?
2. Check: Did it run verification?
3. Check: Does output match expected?
4. Spot-check: Read key files for correctness

#### 2e. Handling Reviewer Items

The task reviewer may report "Cannot verify from diff" items — requirements that live in unchanged code or span tasks. These do not block the rest of the review, but you must resolve each one yourself before marking the task complete. If you confirm an item is a real gap, treat it as a failed spec review — send it back to the implementer and re-review.

#### 2f. Mark Complete

Update plan checkbox: `- [x]` for completed steps.

### Step 3: Verify Integration

After all tasks:

1. Run full test suite: `uv run pytest`
2. Run linter: `uv run ruff check`
3. Run type checker: `uv run ty check`
4. Verify no regressions

## File Handoffs

Everything you paste into a dispatch prompt stays resident in your context for the rest of the session. Hand artifacts over as files when possible.

- **Task brief:** Extract the task's full text to a file. Your dispatch should contain: (1) one line on where this task fits in the project; (2) the brief path; (3) interfaces and decisions from earlier tasks; (4) your resolution of any ambiguity; (5) the report-file path and report contract.
- **Report file:** Name the implementer's report file after the brief and put it in the dispatch prompt. The implementer writes the full report there and returns only status, commits, a one-line test summary, and concerns.
- **Reviewer inputs:** The task reviewer gets the brief file, the report file, and the global constraints.

## Durable Progress

Conversation memory does not survive compaction. Track progress in a ledger file, not only in todos.

- At skill start, check for a ledger: `cat "$(git rev-parse --show-toplevel)/.pb-spec/sdd/progress.md"`. Tasks listed there as complete are DONE — do not re-dispatch them; resume at the first task not marked complete.
- When a task's review comes back clean, append one line to the ledger: `Task N: complete (commits <base7>..<head7>, review clean)`.
- The ledger is your recovery map: the commits it names exist in git even when your context no longer remembers creating them. After compaction, trust the ledger and `git log` over your own recollection.

## Constructing Reviewer Prompts

- Do not add open-ended directives like "check all uses" without a concrete, task-specific reason
- Do not ask a reviewer to re-run tests the implementer already ran
- Do not pre-judge findings for the reviewer — never instruct a reviewer to ignore or not flag a specific issue
- The global-constraints block you hand the reviewer is its attention lens. Copy binding requirements verbatim from the plan's Global Constraints section
- A dispatch prompt describes one task, not the session's history. A fresh subagent needs its task, the interfaces it touches, and the global constraints. Nothing else.
- Dispatch fix subagents for Critical and Important findings. Record Minor findings as you go.

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

**❌ Dispatching without diff file:** Reviewer needs to see the changes
**✅ Generate diff first:** Reviewer gets the actual code changes

**❌ Re-dispatching completed tasks:** Wastes time, creates conflicts
**✅ Check progress ledger:** Resume at first incomplete task

## Red Flags

**Never:**

- Skip task review, or accept a report missing either verdict
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make a subagent read the whole plan file (hand it its task brief)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues = implementer fixes = review again)
- Let implementer self-review replace actual review (both are needed)
- Move to next task while the review has open Critical/Important issues

## Integration with pb-spec

- **pb-build:** This IS the pb-build workflow — Generator/Evaluator pattern
- **pb-improve:** Execute generated plans task-by-task
- **Standalone:** Use for any multi-task execution need
