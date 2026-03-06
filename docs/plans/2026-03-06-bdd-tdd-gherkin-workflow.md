# BDD + TDD Gherkin Workflow Implementation Plan

| Metadata | Details |
| :--- | :--- |
| **Status** | Implemented |
| **Created** | 2026-03-06 |

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade `pb-spec` so generated downstream workflows use Gherkin BDD as the outer acceptance loop and TDD as the inner implementation loop.

**Architecture:** Keep `pb-spec`'s current adapter/template architecture intact and evolve the shared markdown templates plus their contract tests. `pb-plan` will generate spec-native `.feature` assets and scenario mappings, `pb-build` will enforce the double loop, and `pb-refine` will keep `.feature`, `design.md`, and `tasks.md` synchronized.

**Tech Stack:** Python 3.12, Click CLI, markdown templates, pytest

---

## Task 1: Add failing reference-template tests for BDD/TDD planning fields

**Files:**

- Modify: `tests/test_templates.py`
- Modify: `src/pb_spec/templates/skills/pb-plan/references/design_template.md`
- Modify: `src/pb_spec/templates/skills/pb-plan/references/tasks_template.md`
- Test: `tests/test_templates.py`

**Step 1: Write the failing test**

```python
def test_pb_plan_reference_templates_require_bdd_tdd_fields():
    refs = load_references("pb-plan")
    design = refs["design_template.md"]
    tasks = refs["tasks_template.md"]

    assert "BDD/TDD Strategy" in design
    assert "BDD Scenario Inventory" in design
    assert "BDD Runner" in design
    assert "BDD Command" in design
    assert "Unit Test Command" in design

    assert "Scenario Coverage" in tasks
    assert "Loop Type" in tasks
    assert "BDD Verification" in tasks
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py -k "pb_plan_reference_templates_require_bdd_tdd_fields" -v`
Expected: FAIL because the current reference templates do not contain the new BDD/TDD fields.

**Step 3: Write minimal implementation**

Update the two reference templates so they explicitly include:

```markdown
## BDD/TDD Strategy

- **BDD Runner:** ...
- **BDD Command:** ...
- **Unit Test Command:** ...
```

and:

```markdown
- **Scenario Coverage:** [Feature/scenario names]
- **Loop Type:** BDD+TDD / TDD-only
- [ ] **BDD Verification:** [Run scenario command and confirm expected outcome]
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_templates.py -k "pb_plan_reference_templates_require_bdd_tdd_fields" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_templates.py src/pb_spec/templates/skills/pb-plan/references/design_template.md src/pb_spec/templates/skills/pb-plan/references/tasks_template.md
git commit -m "test(plan): add bdd tdd template fields"
```

### Task 2: Add failing `pb-plan` template tests and implement spec-native `.feature` planning

**Files:**

- Modify: `tests/test_templates.py`
- Modify: `tests/test_template_contracts.py`
- Modify: `src/pb_spec/templates/skills/pb-plan/SKILL.md`
- Modify: `src/pb_spec/templates/prompts/pb-plan.prompt.md`
- Test: `tests/test_templates.py`
- Test: `tests/test_template_contracts.py`

**Step 1: Write the failing test**

```python
def test_pb_plan_templates_require_gherkin_feature_generation():
    for content in (load_skill_content("pb-plan"), load_prompt("pb-plan")):
        assert "features/*.feature" in content
        assert "Gherkin" in content
        assert "@cucumber/cucumber" in content
        assert "behave" in content
        assert "cucumber" in content
        assert "Scenario Coverage" in content
```

Add a companion contract assertion to keep these keywords present in installed templates.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "gherkin_feature_generation or bdd_tdd" -v`
Expected: FAIL because the current `pb-plan` skill/prompt still describe only `design.md` and `tasks.md`.

**Step 3: Write minimal implementation**

Update the `pb-plan` skill and prompt to:

```markdown
- Produce `design.md`, `tasks.md`, and `features/*.feature`
- Detect the project's primary language and recommend:
  - TypeScript/JavaScript -> `@cucumber/cucumber`
  - Python -> `behave`
  - Rust -> `cucumber`
- Add `BDD/TDD Strategy` and `BDD Scenario Inventory`
- Require `Scenario Coverage`, `Loop Type`, and `BDD Verification` in tasks
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "gherkin_feature_generation or bdd_tdd" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_templates.py tests/test_template_contracts.py src/pb_spec/templates/skills/pb-plan/SKILL.md src/pb_spec/templates/prompts/pb-plan.prompt.md
git commit -m "feat(plan): generate gherkin bdd specs"
```

### Task 3: Add failing `pb-build` tests and implement the double-loop execution contract

**Files:**

- Modify: `tests/test_templates.py`
- Modify: `tests/test_template_contracts.py`
- Modify: `src/pb_spec/templates/skills/pb-build/SKILL.md`
- Modify: `src/pb_spec/templates/prompts/pb-build.prompt.md`
- Modify: `src/pb_spec/templates/skills/pb-build/references/implementer_prompt.md`
- Test: `tests/test_templates.py`
- Test: `tests/test_template_contracts.py`

**Step 1: Write the failing test**

```python
def test_pb_build_templates_require_bdd_outer_loop_before_tdd():
    for content in (
        load_skill_content("pb-build"),
        load_prompt("pb-build"),
        load_references("pb-build")["implementer_prompt.md"],
    ):
        assert "Scenario Coverage" in content
        assert "run the BDD scenario and confirm the outer loop is red" in content
        assert "Re-run the BDD scenario until it passes" in content
        assert "BDD+TDD" in content
```

Add contract checks for scenario-aware DCR evidence.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "pb_build_templates_require_bdd_outer_loop_before_tdd or scenario-aware" -v`
Expected: FAIL because the current build templates only enforce TDD and runtime verification.

**Step 3: Write minimal implementation**

Update the build templates so they require:

```markdown
1. Read `Scenario Coverage`
2. Run the referenced BDD scenario and confirm it fails
3. Execute inner-loop TDD
4. Re-run the BDD scenario until it passes
5. Include scenario name and failing step in DCR packets
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "pb_build_templates_require_bdd_outer_loop_before_tdd or scenario-aware" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_templates.py tests/test_template_contracts.py src/pb_spec/templates/skills/pb-build/SKILL.md src/pb_spec/templates/prompts/pb-build.prompt.md src/pb_spec/templates/skills/pb-build/references/implementer_prompt.md
git commit -m "feat(build): enforce bdd and tdd double loop"
```

### Task 4: Add failing `pb-refine` tests and implement `.feature` synchronization

**Files:**

- Modify: `tests/test_templates.py`
- Modify: `tests/test_template_contracts.py`
- Modify: `src/pb_spec/templates/skills/pb-refine/SKILL.md`
- Modify: `src/pb_spec/templates/prompts/pb-refine.prompt.md`
- Test: `tests/test_templates.py`
- Test: `tests/test_template_contracts.py`

**Step 1: Write the failing test**

```python
def test_pb_refine_templates_update_feature_files_with_design_changes():
    for content in (load_skill_content("pb-refine"), load_prompt("pb-refine")):
        assert "specs/<spec-dir>/features/" in content
        assert "update `.feature` first" in content
        assert "Scenario Coverage" in content
        assert "feature-file changes" in content
```

Add companion contract assertions so the installed templates cannot regress.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "update_feature_files_with_design_changes or feature-file" -v`
Expected: FAIL because current refine templates only mention `design.md` and `tasks.md`.

**Step 3: Write minimal implementation**

Update refine templates to:

```markdown
- Load `specs/<spec-dir>/features/`
- Update `.feature` files when behavior changes
- Cascade scenario changes into `design.md` and `tasks.md`
- Mention feature-file updates in the refinement summary
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -k "update_feature_files_with_design_changes or feature-file" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_templates.py tests/test_template_contracts.py src/pb_spec/templates/skills/pb-refine/SKILL.md src/pb_spec/templates/prompts/pb-refine.prompt.md
git commit -m "feat(refine): sync gherkin feature files"
```

### Task 5: Add failing docs regression checks and refresh project docs

**Files:**

- Modify: `tests/test_templates.py`
- Modify: `README.md`
- Modify: `docs/design.md`
- Test: `tests/test_templates.py`

**Step 1: Write the failing test**

```python
def test_project_docs_describe_bdd_and_tdd_workflow():
    readme = Path("README.md").read_text(encoding="utf-8")
    design = Path("docs/design.md").read_text(encoding="utf-8")

    assert "Gherkin" in readme
    assert "BDD" in readme
    assert ".feature" in readme
    assert "outer loop" in design
    assert "inner loop" in design
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_templates.py -k "project_docs_describe_bdd_and_tdd_workflow" -v`
Expected: FAIL because the current docs describe strict TDD but not the new BDD outer loop.

**Step 3: Write minimal implementation**

Update `README.md` and `docs/design.md` so they document:

```markdown
- Spec output now includes `features/*.feature`
- `pb-build` uses BDD outer loop + TDD inner loop
- `pb-refine` keeps feature files, design, and tasks in sync
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_templates.py -k "project_docs_describe_bdd_and_tdd_workflow" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_templates.py README.md docs/design.md
git commit -m "docs: describe bdd and tdd workflow"
```

### Task 6: Run full verification and review rendered output expectations

**Files:**

- Verify only

**Step 1: Run the focused template test suite**

Run: `uv run pytest tests/test_templates.py tests/test_template_contracts.py -v`
Expected: PASS

**Step 2: Run the full test suite**

Run: `uv run pytest -v`
Expected: PASS

**Step 3: Run lint**

Run: `uv run ruff check .`
Expected: PASS

**Step 4: Spot-check rendered installs**

Run: `uv run pytest tests/test_template_contracts.py -v`
Expected: PASS and rendered templates still have valid frontmatter and markdown fences.

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add bdd and tdd gherkin workflow"
```
