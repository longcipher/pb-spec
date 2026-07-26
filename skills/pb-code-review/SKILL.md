---
name: pb-code-review
description: Two-direction code review discipline. Requesting review runs two axes in parallel subagents — Standards (does the code follow this repo's coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Receiving review demands technical rigor and verification, not performative agreement or blind implementation. Use when completing tasks, before merging, when given review feedback, or when pb-build's Evaluator rejects a task.
---

# pb-code-review

## Part I — Requesting Review

### When

Mandatory: after completing a task, before merging, before pushing to main.
Optional: when stuck, before refactoring, after complex bug fix.

### Two-Axis Review (parallel subagents)

Pin the fixed point first: `git diff <fixed-point>...HEAD`. Confirm diff is non-empty before spawning.

1. **Standards axis** — does code conform to `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`? Plus Fowler smell baseline: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Speculative Generality, Message Chains, Middle Man. Repo standards override baseline. Skip anything tooling enforces.
2. **Spec axis** — does code faithfully implement the originating spec? Look under `specs/` matching branch name or issue refs in commits. If no spec, report "no spec available".

### Output

Present two reports under `## Standards` and `## Spec` headings verbatim. Don't merge or rerank.

| axis | pass/fail | findings | evidence |
|---|---|---|---|
| Standards | pass/fail | worst issue + count | file:line |
| Spec | pass/fail | worst issue + count | spec line + file:line |

One-line summary: total findings per axis + worst issue. Don't pick a winner.

## Part II — Receiving Review

Technical rigor, not performative agreement. Reviewer may be wrong. Verify before implementing.

Forbidden responses: "You're absolutely right!", "Great point!", "Let me implement that now" (before verification), gratitude/social padding.

### Response Pattern

1. READ: Complete feedback without reacting.
2. UNDERSTAND: Restate requirement in own words (or ask).
3. VERIFY: Check against codebase reality.
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback.
6. IMPLEMENT: One item at a time, test each.

### Decision Tree (per item)

1. Correct? Verify with code reading, tests, docs.
2. Correct → implement fix, run verification, respond with evidence.
3. Incorrect → push back with counter-evidence (file:line, test output, doc link).
4. Unclear → ask, don't guess. If any item unclear: STOP, ask all unclear items before starting.

### Source-Specific Handling

- **From user:** Trusted. Implement after understanding. Still ask if scope unclear.
- **From external (Evaluator, CI):** Verify before implementing. Check: technically correct? breaks existing? reason for current implementation? works on all platforms? reviewer has full context? If conflicts with user's prior decisions → discuss with user first.

### YAGNI Check

If reviewer says "implement properly": grep for actual usage. Unused → propose removal. Used → implement properly.

### Push Back When

Suggestion breaks functionality · reviewer lacks full context · violates YAGNI · technically incorrect · legacy reasons · conflicts with user's architectural decisions.

If you pushed back and were wrong: "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing." No apology.

### Integration with pb-build

When Evaluator rejects a task, that IS code review feedback. Generator follows the decision tree above. 3 consecutive rejections → Build Blocked → escalate to `/pb-refine`.

## Constraints

- Never merge without explicit user approval.
- Reviewer subagents do not modify code; they only report findings.
- All findings need evidence (file:line).
- One fix at a time, test each, verify no regressions.
- If spec ambiguous → escalate to `/pb-refine`, don't guess in review.

---

name: pb-code-review

## description: Two-direction code review discipline. Requesting review runs two axes in parallel subagents — Standards (does the code follow this repo's coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Receiving review demands technical rigor and verification, not performative agreement or blind implementation. Use when completing tasks, before merging, when given review feedback, or when pb-build's Evaluator rejects a task
