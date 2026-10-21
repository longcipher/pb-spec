---
name: pb-goal
description: Goal-driven execution mode. Lock one explicit objective, persist state to disk so it survives compaction, and keep working turn after turn until the objective is verifiably achieved or genuinely blocked. Use when the user says "pb-goal" or gives a large objective meant to run to completion without hand-holding.
---

# pb-goal

Drive the session by a single explicit goal. Inspired by goal mode: the agent does not stop
between turns waiting for permission — it continues until the objective is met or truly blocked.
No token/time budget: work as long as the goal needs.

## 1. Establish the goal

- Restate the user's objective as one measurable statement with acceptance criteria
  (what done means, verifiable by commands/tests/artifacts).
- Define scope: what is in, what is explicitly out (non-goals).
- Persist everything to `.pb-goal.md` at the project root:

```markdown
# Goal: <measurable objective>
Status: ACTIVE | COMPLETE | BLOCKED
Started: YYYY-MM-DD  Updated: YYYY-MM-DD

## Acceptance criteria
- [ ] <verifiable criterion>

## Plan
1. <step> — DONE | IN_PROGRESS | TODO

## Evidence log
- <date> <criterion/step> — <command output, test result, or artifact proving it>

## Blockers
- <none, or what is missing and why>
```

## 2. Execute without stopping

- Work the plan top-down. At the end of every turn, if the goal is not COMPLETE or BLOCKED,
  immediately continue with the next unblocked work in the same or next turn — do not end the
  session asking "shall I continue?". The answer is always yes.
- Update `.pb-goal.md` after every meaningful step: plan status, evidence, date. This file is
  the source of truth; on session resume or after compaction, read it first and continue.
- Track decisions inline in the evidence log (decision + one-line rationale).

## 3. Completion is evidence-driven

- Mark `Status: COMPLETE` only when every acceptance criterion has fresh, verifiable evidence
  in the log (command output, passing tests, real files, merged PR). No evidence → not done.
- Acceptance criteria may not be silently weakened or dropped. If a criterion turns out to be
  wrong or impossible, say so explicitly, propose the change, and apply it only with user
  confirmation (or, if purely mechanical and strictly harder than the original, record it and
  meet the harder bar).

## 4. Stop only on real blockers

Stop and ask the user ONLY when:

- An acceptance criterion is ambiguous in a way that changes what gets built and no best
  interpretation exists (per the decision protocol — otherwise pick the reasonable one and record it);
- An external dependency is genuinely missing (credentials, third-party decision, unavailable system);
- The user interrupts.

Everything else — errors, failing tests, design uncertainty, long runtimes — is work to push
through, not a reason to stop. On repeated no-progress turns, change the approach rather than
repeating it; record the pivot in the evidence log.

## 5. Wrap-up

- COMPLETE → summarize what was achieved with the evidence.
- BLOCKED → state the exact blocker, what was already done, and the smallest input that unblocks.

## Constraints

- Same rules as the rest of the workflow: strict TDD when implementing, match `AGENTS.md`,
  never commit/push unless explicitly asked.
- Never edit `.pb-goal.md` history destructively — append evidence, update statuses.
