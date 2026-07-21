---
name: pb-code-review
description: Two-direction code review discipline. Requesting review runs two axes in parallel subagents — Standards (does the code follow this repo's coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Receiving review demands technical rigor and verification, not performative agreement or blind implementation. Use when completing tasks, before merging, when given review feedback, or when pb-build's Evaluator rejects a task.
---

# pb-code-review

## Role

Code review is a two-direction discipline. You request it when your work is ready, and you receive it when your work is questioned. Both directions share the same model: claims need evidence, the spec is source of truth, and agreement without verification is a failure mode.

## Part I — Requesting Code Review

### When to Request

**Mandatory:**

- After completing a task, before marking it DONE.
- Before merging a feature branch.
- Before pushing to main/master.

**Optional but valuable:**

- When stuck (fresh perspective).
- Before refactoring (baseline check).
- After fixing a complex bug.
- Whenever the change is non-trivial and the user wants verification.

### Two-Axis Review

Run BOTH axes in parallel subagents so they don't pollute each other's context, then aggregate.

1. **Standards axis** — does the code conform to this repo's documented coding standards? Sources: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`. On top of documented rules, carry the smell baseline (Fowler): Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. Repo standards override the baseline; baseline smells are always judgement calls; skip anything tooling enforces.
2. **Spec axis** — does the code faithfully implement the originating issue / PRD / spec? Look under `specs/` matching the branch name, a path the user passed, or issue refs in commit messages. If no spec, the Spec subagent reports "no spec available".

**Pin the fixed point first:** `git diff <fixed-point>...HEAD` (three-dot, against merge-base). Confirm the ref resolves and the diff is non-empty before spawning subagents.

### Output Format

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings — the axes are deliberately separate.

| axis | pass/fail | findings | evidence |
|------|-----------|----------|----------|
| Standards | pass/fail | worst issue + count | file:line |
| Spec | pass/fail | worst issue + count | spec line + file:line |

End with a one-line summary: total findings per axis and the worst issue within each axis. Don't pick a single winner across axes.

### Common Failure Modes

- Standards pass but spec fails: code is clean but does the wrong thing.
- Spec passes but standards fail: code works but doesn't fit the repo.
- Both pass: ship it.
- Both fail: major rework needed.

## Part II — Receiving Code Review

### Core Principle

Technical rigor, not performative agreement. The reviewer may be wrong. Verify before implementing. Ask before assuming. Technical correctness over social comfort.

**Forbidden responses:** "You're absolutely right!", "Great point!", "Let me implement that now" (before verification), "Thanks for catching that!", or any gratitude/social padding. Just state the technical requirement or act — the code itself shows you heard the feedback.

### Response Pattern

```text
1. READ:      Complete feedback without reacting.
2. UNDERSTAND: Restate requirement in own words (or ask).
3. VERIFY:    Check against codebase reality.
4. EVALUATE:  Technically sound for THIS codebase?
5. RESPOND:   Technical acknowledgment or reasoned pushback.
6. IMPLEMENT: One item at a time, test each.
```

### Decision Tree (per feedback item)

1. Is the feedback technically correct? Verify with code reading, tests, or documentation.
2. If correct: implement the fix, run verification, respond with evidence.
3. If incorrect: push back with concrete counter-evidence (file:line, test output, doc link).
4. If unclear: ask for clarification, do not guess.

**If any item is unclear:** STOP. Do not implement anything yet. Ask for clarification on all unclear items before starting — items may be related, and partial understanding produces wrong implementation.

### Source-Specific Handling

- **From the user:** Trusted; implement after understanding. Still ask if scope is unclear. No performative agreement.
- **From external reviewers (Evaluator, CI, etc.):** Verify before implementing — technically correct for this codebase? breaks existing functionality? reason for current implementation? works on all platforms/versions? does reviewer have full context? If it conflicts with the user's prior decisions, stop and discuss with the user first.

### YAGNI Check

If a reviewer suggests "implementing properly": grep the codebase for actual usage. If unused, propose removal (YAGNI). If used, then implement properly.

### When To Push Back

Push back when:

- Suggestion breaks existing functionality.
- Reviewer lacks full context.
- Violates YAGNI (unused feature).
- Technically incorrect for this stack.
- Legacy/compatibility reasons exist.
- Conflicts with the user's architectural decisions.

**How to push back:** technical reasoning (not defensiveness), specific questions, reference working tests/code, involve the user if architectural.

**If you pushed back and were wrong:** "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing." State the correction factually — no apology, no defence, no over-explanation.

### Common Anti-Patterns

- "Agreeing" without verifying (performative agreement).
- Implementing feedback that contradicts the spec (spec drift).
- Blindly trusting the reviewer's reputation.
- Pushing back defensively without evidence.
- Implementing partial feedback and silently dropping the rest.
- Batching fixes without testing each one.
- Can't verify but proceeding anyway — state the limitation and ask for direction.

### Integration with pb-build

- When pb-build's Evaluator subagent rejects a task, that IS code review feedback.
- The Generator's response follows the Receiving Code Review decision tree above.
- 3 consecutive rejections → Build Blocked → escalate to `/pb-refine`.

## Key Principles

1. Two-axis review: Standards + Spec, both required, never merged or reranked.
2. Receiving review: verify before implementing, push back with evidence when wrong.
3. Evidence before claims: every assertion needs a file:line, test output, or doc link.
4. Spec is source of truth: feedback that contradicts the spec is wrong unless the spec is being revised.
5. Reviewer subagents do not modify code; they only report findings.

## Constraints

- Never merge without explicit user approval.
- Never push to main/master without explicit user approval.
- Reviewer subagents do not modify code; they only report findings.
- All findings need evidence (file:line).
- One fix at a time, test each, verify no regressions.

## Stopping Conditions

- If the spec itself is ambiguous, escalate to `/pb-refine` rather than guessing in review.
- If the reviewer and reviewee disagree on a factual point, run the verification command together and let the output decide.
- If you can't verify a claim, say so and ask for direction — do not proceed on assumption.
