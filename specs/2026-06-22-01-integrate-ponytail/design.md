# Design: Integrate Ponytail Philosophy into pb-spec Skills

| Metadata | Details |
| :--- | :--- |
| **Status** | Draft |
| **Created** | 2026-06-22 |
| **Scope** | Full |

## Summary

The ponytail project proves that a 101-line decision ladder (YAGNI → stdlib → native → existing dep → one-liner → minimum) achieves 54% code reduction with 100% safety. Currently pb-spec skills mention YAGNI and "simplification" generically but lack the concrete decision reflex. This design fuses the ponytail ladder into pb-plan (design phase), pb-build (implementation phase), and pb-improve (audit phase) so agents naturally produce minimal code.

## Why this matters

pb-spec skills currently say "prefer explicit readable solutions over clever compact ones" (pb-plan:24) and "follow YAGNI" (pb-build:546). These are vague. The ponytail ladder is specific: 6 rungs to climb before writing code, with clear escalation criteria. Embedding it turns "be simple" from a suggestion into a decision framework.

## Approach

### Integration Points

**pb-plan (skills/pb-plan/SKILL.md):**

1. **Execution contract** (line 24): Replace generic "code-simplification lens" with ponytail ladder reference
2. **Step 2 Architecture Decision Snapshot** (line 115-127): Add "prefer stdlib/native" as mandatory evaluation criterion
3. **Step 4a/4b design.md template**: Add "Simplification Strategy" section with ponytail ladder
4. **Code Simplification Constraints** (line 298-304): Replace generic with ponytail specifics (ladder, `ponytail:` comment convention)
5. **Key Principles** (line 478-501): Add "Ponytail-first" principle

**pb-build (skills/pb-build/SKILL.md + references/):**

1. **implementer_prompt.md** (line 100-105, GREEN step): Add ladder check before writing code
2. **implementer_prompt.md** (line 155-158, Scope Check): Add Simplicity Check
3. **evaluator_prompt.md** (line 70-76, Check A): Add over-engineering detection
4. **evaluator_prompt.md**: Add Check D — Simplicity Audit using ponytail criteria
5. **pb-build SKILL.md** (line 546): Expand "ALWAYS follow YAGNI" to full ladder

**pb-improve (skills/pb-improve/SKILL.md + references/):**

1. **audit-playbook.md** (section 5): Add "Over-engineering" finding category
2. **pb-improve SKILL.md** (line 284): Replace generic Code Simplification Constraints with ponytail ladder
3. **Phase 4 spec writing**: Generated design.md includes ponytail ladder
4. **references/plan-template.md**: Add ponytail ladder section

**Templates (references/):**

1. **design_template.md**: Add "Simplification Strategy" section
2. **tasks_template.md**: Simplification Focus field references ladder

### What NOT to change

- Don't rename skills or add new skills
- Don't change the pb-spec workflow contract
- Don't remove existing validation, error handling, or security requirements
- Don't add dependencies
- Don't change the BDD/TDD cycle structure

## Requirements (EARS Notation)

- **[REQ-01]:** pb-plan *shall* apply the ponytail ladder when evaluating architecture decisions.
- **[REQ-02]:** pb-build Generator *shall* climb the ponytail ladder before writing any implementation code.
- **[REQ-03]:** pb-build Evaluator *shall* detect and flag over-engineering using ponytail criteria.
- **[REQ-04]:** pb-improve *shall* audit for over-engineering as a finding category.
- **[REQ-05]:** All generated design.md files *shall* include a "Simplification Strategy" section with the ponytail ladder.
- **[REQ-06]:** The ponytail ladder *shall not* override security, validation, or error handling requirements.
- **[REQ-07]:** The `ponytail:` comment convention *shall* be recommended for tracked deferrals in generated code.

## Architecture Decisions

### AD-01: Embed Ladder as Decision Framework, Not Rule

- **Status:** `Accepted`

**Context:** The ponytail ladder is a 6-rung decision tree. It should be a reflex agents apply automatically, not an optional suggestion.

**Decision:** Embed the ladder at decision points (architecture selection, code writing, evaluation) as a mandatory checklist item. The ladder is: (1) Does this need to exist? (2) Stdlib? (3) Native platform? (4) Existing dep? (5) One line? (6) Minimum code.

**Consequences:**

- Positive: Agents produce minimal code by default
- Negative: None — the ladder has explicit carve-outs for security/validation
- Neutral: Matches ponytail's empirically proven approach

### AD-02: `ponytail:` Comment Convention for Generated Code

- **Status:** `Accepted`

**Context:** Ponytail uses `ponytail:` comments to mark deliberate simplifications with known ceilings. This makes shortcuts visible as intent, not ignorance.

**Decision:** Recommend `ponytail:` comments in generated code when a simplification has a known upgrade path. The comment names the ceiling and the trigger: `# ponytail: global lock, per-account locks if throughput matters`.

**Consequences:**

- Positive: Simplifications are tracked, not hidden debt
- Negative: None — comments are optional
- Neutral: Aligns with ponytail's debt-tracking philosophy

### AD-03: Over-Engineering as Evaluation Criterion

- **Status:** `Accepted`

**Context:** The Evaluator currently checks scope, architecture, code quality, and edge cases. It doesn't explicitly check for unnecessary complexity.

**Decision:** Add Check D (Simplicity Audit) to the Evaluator. Criteria: unnecessary abstractions, interfaces with one implementation, factories for one product, config for values that never change, boilerplate "for later".

**Consequences:**

- Positive: Over-engineering is caught and corrected
- Negative: Slightly longer evaluation per task
- Neutral: The Evaluator already has 4 checks; one more is proportional

## Code Simplification Constraints

**Ponytail Ladder (applied at every decision point):**

1. Does this need to exist at all? (YAGNI)
2. Stdlib does it? Use it.
3. Native platform feature covers it? Use it.
4. Already-installed dependency? Use it.
5. One line? One line.
6. Only then: minimum code that works.

**Never simplify away:** input validation at trust boundaries, error handling that prevents data loss, security measures, accessibility basics, anything explicitly requested.

**`ponytail:` comment convention:** Mark deliberate simplifications with the ceiling and upgrade path. Example: `# ponytail: naive O(n²) sort, use sorted() with key if n > 1000`.

**One runnable check:** Non-trivial logic leaves ONE check behind — the smallest thing that fails if the logic breaks. Trivial one-liners need no test.

## BDD/TDD Strategy

- **Primary Language:** Markdown (skill files) + Python (templates)
- **Verification:** `wc -l` for line counts, `grep` for ladder presence, manual review for behavior preservation

## BDD Scenario Inventory

| Feature File | Scenario Name | Business Outcome | Task Coverage |
| :--- | :--- | :--- | :--- |
| `features/integrate-ponytail.feature` | pb-plan applies ladder to arch decisions | Minimal architecture choices | Task 1.1 |
| `features/integrate-ponytail.feature` | design template includes ponytail section | Generated specs have simplification strategy | Task 2.1 |
| `features/integrate-ponytail.feature` | pb-build Generator applies ladder | Minimal code in implementation | Task 1.2 |
| `features/integrate-ponytail.feature` | pb-build Evaluator detects over-engineering | Over-engineering caught at eval time | Task 1.2 |
| `features/integrate-ponytail.feature` | pb-improve audits for over-engineering | Over-engineering found in existing code | Task 1.3 |
| `features/integrate-ponytail.feature` | Generated specs include ponytail ladder | All specs carry the ladder forward | Task 2.2 |

## Existing Components to Reuse

| Component | Location | How to Reuse |
| :--- | :--- | :--- |
| Code Simplification Constraints | pb-plan:298, pb-improve:284 | Replace generic with ponytail ladder |
| YAGNI reference | pb-build:546, implementer_prompt:235 | Expand to full ladder |
| Over-engineering check | evaluator_prompt:75 | Expand to full Check D |
| design_template.md | pb-plan/references/ | Add Simplification Strategy section |
| tasks_template.md | pb-plan/references/ | Simplification Focus references ladder |
| audit-playbook.md | pb-improve/references/ | Add Over-engineering category |

## Verification

| Step | Command | Success |
| :--- | :--- | :--- |
| VP-01 | `grep -c "ponytail" skills/pb-plan/SKILL.md` | ≥ 3 |
| VP-02 | `grep -c "ponytail" skills/pb-build/SKILL.md` | ≥ 2 |
| VP-03 | `grep -c "ponytail" skills/pb-build/references/implementer_prompt.md` | ≥ 1 |
| VP-04 | `grep -c "ponytail" skills/pb-build/references/evaluator_prompt.md` | ≥ 1 |
| VP-05 | `grep -c "ponytail" skills/pb-improve/SKILL.md` | ≥ 2 |
| VP-06 | `grep -c "ponytail" skills/pb-improve/references/audit-playbook.md` | ≥ 1 |
| VP-07 | `grep -c "Simplification Strategy" skills/pb-plan/references/design_template.md` | ≥ 1 |
| VP-08 | Manual review: all existing behavior preserved | No behavior loss |
