# pb-spec (Plan-Build Spec) - Implementation Tasks

| Metadata | Details |
| :--- | :--- |
| **Epic/Design** | [docs/design.md](design.md) |
| **Owner** | akagi201 |
| **Start Date** | 2025-02-11 |
| **Status** | Planning |

## 1. Executive Summary & Phasing

- **Phase 1: Project Scaffolding** — uv project initialization, CLI skeleton, basic commands.
- **Phase 2: Platform Abstraction** — Platform configuration system, template rendering engine.
- **Phase 3: Skill Templates** — Markdown template writing for three core skills.
- **Phase 4: Init Command** — Complete implementation and testing of `pb-spec init`.
- **Phase 5: Polish & Release** — Documentation, CI, PyPI release.

---

## Phase 1: Project Scaffolding

### Task 1.1: uv Project Initialization

> **Context:** Use uv to create Python project structure, configure pyproject.toml.
> **Verification:** `uv run pb-spec --help` outputs help information.

- **Priority:** P0
- **Est. Time:** 1h
- **Status:** � DONE
- [ ] **Step 1:** Run `uv init --lib` to initialize project.
- [ ] **Step 2:** Edit `pyproject.toml`:
  - Set `name = "pb-spec"`, minimum Python version `>=3.12`.
  - Add `click>=8.1` dependency.
  - Configure `[project.scripts]` entry: `pb-spec = "pb.cli:main"`.
  - Configure `[tool.uv]` dev dependencies: `pytest>=8.0`.
- [ ] **Step 3:** Create directory structure:

  ```text
  src/pb/__init__.py
  src/pb/cli.py
  src/pb/commands/__init__.py
  src/pb/platforms/__init__.py
  src/pb/templates/  (Empty directory, populated later)
  tests/__init__.py
  ```

- [ ] **Step 4:** Set `__version__` in `src/pb/__init__.py`.
- [ ] **Verification:** Run `uv sync && uv run pb-spec --help`, confirm CLI is executable.

### Task 1.2: CLI Entry & Basic Commands

> **Context:** Use click to build CLI framework, implement `version` and `update` commands.
> **Verification:** `pb-spec version` outputs version number, `pb-spec update` calls uv upgrade.

- **Priority:** P0
- **Est. Time:** 2h
- **Status:** � DONE
- [x] **Step 1:** Write `src/pb/cli.py`:
  - Create `click.Group` main command `pb`.
  - Register `init`, `version`, `update` subcommands.
- [ ] **Step 2:** Implement `src/pb/commands/version.py`:
  - Read `importlib.metadata.version("pb-spec")` and output version.
- [ ] **Step 3:** Implement `src/pb/commands/update.py`:
  - Call `subprocess.run(["uv", "tool", "upgrade", "pb-spec"])`.
  - Handle error case where uv is missing.
- [ ] **Step 4:** Write tests `tests/test_cli.py`:
  - Test `pb --help` output contains `init`, `version`, `update`.
  - Test `pb version` output contains version number.
- [ ] **Verification:** `uv run pytest tests/test_cli.py -v` passes all tests.

---

## Phase 2: Platform Abstraction

### Task 2.1: Platform Base Class & Configuration

> **Context:** Define platform abstract base class, providing unified interface for Claude/Copilot/OpenCode.
> **Verification:** Unit tests verify correct path generation for each platform.

- **Priority:** P0
- **Est. Time:** 3h
- **Status:** � DONE
- [ ] **Step 1:** Implement `src/pb/platforms/base.py`:
  - Define `Platform` ABC: `name`, `get_skill_path()`, `render_skill()`, `install()`.
  - Implement generic `install()` logic (iterate skill_names, check file existence, write).
- [ ] **Step 2:** Implement `src/pb/platforms/claude.py`:
  - Path: `.claude/skills/<name>/SKILL.md`.
  - Render: YAML frontmatter + markdown body.
  - Support `references/` subdirectory.
- [ ] **Step 3:** Implement `src/pb/platforms/copilot.py`:
  - Path: `.github/prompts/<name>.prompt.md`.
  - Render: Pure markdown (no frontmatter).
  - Inline content from `references/` into prompt file.
- [ ] **Step 4:** Implement `src/pb/platforms/opencode.py`:
  - Path: `.opencode/skills/<name>/SKILL.md`.
  - Render: YAML frontmatter + markdown body (same as Claude).
  - Support `references/` subdirectory.
- [ ] **Step 5:** Implement factory functions `get_platform(name: str) -> Platform` and `resolve_targets(ai: str) -> list[str]`.
- [ ] **Step 6:** Write tests `tests/test_platforms.py`:
  - Test `get_skill_path()` returns correct paths for each platform.
  - Test `render_skill()` outputs correct format.
  - Test `resolve_targets("all")` returns 3 platforms.
- [ ] **Verification:** `uv run pytest tests/test_platforms.py -v` passes all tests.

### Task 2.2: Template Loading System

> **Context:** Implement mechanism to read template files from `src/pb/templates/`, supporting access after `importlib.resources` packaging.
> **Verification:** Unit tests verify template loading and variable substitution.

- **Priority:** P0
- **Est. Time:** 2h
- **Status:** � DONE
- [ ] **Step 1:** Implement `src/pb/templates/__init__.py`:
  - `load_template(skill_name: str, filename: str) -> str` — Load template file content.
  - `load_skill_content(skill_name: str) -> str` — Load SKILL.md template.
  - `load_references(skill_name: str) -> dict[str, str]` — Load all files in `references/` subdirectory.
  - Use `importlib.resources` to ensure templates are accessible after packaging.
- [ ] **Step 2:** Create `src/pb/templates/skills/` directory structure (placeholders first):

  ```text
  skills/pb-init/SKILL.md
  skills/pb-plan/SKILL.md
  skills/pb-plan/references/design_template.md
  skills/pb-plan/references/tasks_template.md
  skills/pb-build/SKILL.md
  skills/pb-build/references/implementer_prompt.md
  ```

- [ ] **Step 3:** Create `src/pb/templates/prompts/` directory (for Copilot):

  ```text
  prompts/pb-init.prompt.md
  prompts/pb-plan.prompt.md
  prompts/pb-build.prompt.md
  ```

- [ ] **Step 4:** Ensure `pyproject.toml` configures `[tool.setuptools.package-data]` (or equivalent) to include template files.
- [ ] **Step 5:** Write tests `tests/test_templates.py`:
  - Test `load_template()` can load files.
  - Test `load_references()` returns correct file dictionary.
- [ ] **Verification:** `uv run pytest tests/test_templates.py -v` passes all tests.

---

## Phase 3: Skill Templates

### Task 3.1: pb-init Skill Template

> **Context:** Write SKILL.md template for pb-init, defining project initialization agent behavior.
> **Verification:** Correct template syntax, correct format for each platform after rendering.

- **Priority:** P0
- **Est. Time:** 3h
- **Status:** � DONE
- [ ] **Step 1:** Write `src/pb/templates/skills/pb-init/SKILL.md`:
  - Define agent behavior: Scan project → Detect language/framework → Generate AGENTS.md.
  - Define AGENTS.md output format template.
  - Define constraints: Read-only analysis, idempotent update, do not modify source code.
  - Include detection rule table (pyproject.toml → Python, Cargo.toml → Rust, etc.).
- [ ] **Step 2:** Write `src/pb/templates/prompts/pb-init.prompt.md`:
  - Copilot format: No frontmatter.
  - Use `#file:` syntax for reference paths.
- [ ] **Step 3:** Verify template rendering:
  - Claude: Has frontmatter, references/ directory.
  - Copilot: No frontmatter, content inlined.
  - OpenCode: Has frontmatter, references/ directory.
- [ ] **Verification:** Manually check rendered output complies with platform specs.

### Task 3.2: pb-plan Skill Template

> **Context:** Write SKILL.md and references templates for pb-plan, defining design generation agent behavior.
> **Verification:** Template covers complete agent behavior spec and output format definition.

- **Priority:** P0
- **Est. Time:** 4h
- **Status:** � DONE
- [ ] **Step 1:** Write `src/pb/templates/skills/pb-plan/SKILL.md`:
  - Define agent behavior: Requirement analysis → Context collection → Generate design.md + tasks.md.
  - Define feature-name generation rules (≤4 words, kebab-case).
  - Emphasize: No confirmation questions, output optimal solution directly.
  - Reference `references/design_template.md` and `references/tasks_template.md`.
- [ ] **Step 2:** Write `src/pb/templates/skills/pb-plan/references/design_template.md`:
  - Simplified based on `docs/design_template.md`, keeping core sections.
  - Remove Rust-specific content, make template language-agnostic.
  - Retain: Summary, Requirements, Architecture, Detailed Design, Verification.
- [ ] **Step 3:** Write `src/pb/templates/skills/pb-plan/references/tasks_template.md`:
  - Simplified based on `docs/tasks_template.md`.
  - Remove Rust-specific content.
  - Retain: Phase grouping, Task structure (Context/Steps/Verification), checkbox format.
- [ ] **Step 4:** Write `src/pb/templates/prompts/pb-plan.prompt.md`:
  - Copilot format: Inline all references content.
  - Use delimiters to mark template areas.
- [ ] **Verification:** Template content fully covers all agent behaviors defined in design.md.

### Task 3.3: pb-build Skill Template

> **Context:** Write SKILL.md and implementer_prompt template for pb-build, defining subagent-driven implementation flow.
> **Verification:** Template contains complete subagent workflow definition.

- **Priority:** P0
- **Est. Time:** 4h
- **Status:** � DONE
- [ ] **Step 1:** Write `src/pb/templates/skills/pb-build/SKILL.md`:
  - Define workflow: Read tasks.md → Assign subagent per task → TDD implementation → Mark completed.
  - Define subagent assignment rules (sequential, fresh context).
  - Define task state tracking mechanism (checkbox).
  - Define progress display format.
  - Define error handling: Subagent failure → Report → User chooses Retry/Skip/Abort.
  - Define constraints: NEVER/ALWAYS rule list.
- [ ] **Step 2:** Write `src/pb/templates/skills/pb-build/references/implementer_prompt.md`:
  - Subagent instruction template: Task Description, Context, TDD steps, Self-Review checklist.
  - Report format: What implemented, Tests, Files changed, Issues.
- [ ] **Step 3:** Write `src/pb/templates/prompts/pb-build.prompt.md`:
  - Copilot format: inline implementer_prompt content.
- [ ] **Verification:** Template contains all key elements of lightspec-loop (fresh context, sequential, TDD, self-review).

---

## Phase 4: Init Command

### Task 4.1: `pb init` Command Implementation

> **Context:** Implement core CLI command to install skill templates into target project.
> **Verification:** `pb-spec init --ai claude` generates correct files in `.claude/skills/`.

- **Priority:** P0
- **Est. Time:** 3h
- **Status:** � DONE
- [ ] **Step 1:** Implement `src/pb/commands/init.py`:
  - Accept `--ai` argument (claude/copilot/opencode/all).
  - Accept `--force` argument.
  - Call `resolve_targets()` → Iterate platforms → Call `platform.install()`.
  - Output installation result summary.
- [ ] **Step 2:** Register init command in `src/pb/cli.py`:
  - `@click.option("--ai", type=click.Choice(["claude", "copilot", "opencode", "all"]), required=True)`
  - `@click.option("--force", is_flag=True, default=False)`
- [ ] **Step 3:** Handle edge cases:
  - Current directory is not git repo: Warn but continue.
  - Target file exists: Skip (no --force) or Overwrite (with --force).
  - Correct copying of `references/` files.
- [ ] **Step 4:** Write integration tests `tests/test_init.py`:
  - Use `tmp_path` fixture to create temporary directory.
  - Test `pb init --ai claude`: Verify file existence and content.
  - Test `pb init --ai copilot`: Verify `.prompt.md` files.
  - Test `pb init --ai opencode`: Verify file existence and content.
  - Test `pb init --ai all`: Verify generation of main files for all 3 platforms.
  - Test `--force` overwrite behavior.
  - Test idempotency of repeated runs.
- [ ] **Verification:** `uv run pytest tests/test_init.py -v` passes all tests.

### Task 4.2: End-to-End Verification

> **Context:** Verify complete workflow in a real project scenario.
> **Verification:** Execute pb init in a temporary project, confirm AI tools correctly identify skills.

- **Priority:** P1
- **Est. Time:** 2h
- **Status:** � DONE
- [ ] **Step 1:** Create E2E test script `tests/e2e_test.sh`:

  ```bash
  # 1. Create temp project
  tmpdir=$(mktemp -d)
  cd "$tmpdir"
  git init
  echo '{"name": "test"}' > package.json

  # 2. Install pb skills
  pb init --ai all

  # 3. Verify file structure
  test -f .claude/skills/pb-init/SKILL.md
  test -f .claude/skills/pb-plan/SKILL.md
  test -f .claude/skills/pb-build/SKILL.md
  test -f .github/prompts/pb-init.prompt.md
  test -f .github/prompts/pb-plan.prompt.md
  test -f .github/prompts/pb-build.prompt.md
  test -f .opencode/skills/pb-init/SKILL.md
  test -f .opencode/skills/pb-plan/SKILL.md
  test -f .opencode/skills/pb-build/SKILL.md

  # 4. Verify frontmatter
  head -1 .claude/skills/pb-init/SKILL.md | grep -q "^---"
  head -1 .github/prompts/pb-init.prompt.md | grep -qv "^---"

  # 5. Cleanup
  rm -rf "$tmpdir"
  echo "✅ E2E test passed"
  ```

- [ ] **Step 2:** Run E2E test and fix discovered issues.
- [ ] **Step 3:** Test in an actual Claude Code project if pb-init skill is correctly loaded.
- [ ] **Verification:** E2E test script runs successfully, skill visible in AI tools.

---

## Phase 5: Polish & Release

### Task 5.1: Documentation & README

> **Context:** Write user documentation so project can be used by other developers.
> **Verification:** README contains installation and usage instructions.

- **Priority:** P1
- **Est. Time:** 2h
- **Status:** � DONE
- [ ] **Step 1:** Update `README.md`:
  - Project introduction and feature overview.
  - Installation methods (`uv tool install pb-spec` / `pipx install pb-spec`).
  - Quick Start Guide (3 steps: install → init → use).
  - List of supported AI tools.
  - CLI command reference.
  - Workflow example (pb-init → pb-plan → pb-build).
- [ ] **Step 2:** Add `LICENSE` file (MIT).
- [ ] **Step 3:** Add `.gitignore` (Python project standard template).
- [ ] **Verification:** README is readable and contains all necessary info.

### Task 5.2: CI Configuration

> **Context:** Setup GitHub Actions CI for automated testing.
> **Verification:** CI pipeline runs tests automatically on push.

- **Priority:** P2
- **Est. Time:** 1h
- **Status:** � DONE
- [ ] **Step 1:** Create `.github/workflows/ci.yml`:
  - Trigger: push to main, pull_request.
  - Matrix: Python 3.12, 3.13.
  - Steps: checkout → install uv → uv sync → uv run pytest.
- [ ] **Step 2:** Add `[tool.pytest.ini_options]` to pyproject.toml.
- [ ] **Step 3:** Add test coverage report (pytest-cov).
- [ ] **Verification:** CI config syntax is correct (validate with `act` locally).

### Task 5.3: PyPI Release Configuration

> **Context:** Configure project for PyPI publication.
> **Verification:** `uv build` successfully generates wheel containing all template files.

- **Priority:** P2
- **Est. Time:** 1h
- **Status:** � DONE
- [ ] **Step 1:** Confirm `pyproject.toml` contains:
  - `[project]` full metadata (name, version, description, authors, license, urls).
  - `[build-system]` using hatchling.
  - Template files included in wheel (`[tool.hatch.build.targets.wheel]`).
- [ ] **Step 2:** Run `uv build` to generate wheel.
- [ ] **Step 3:** Check wheel content for templates:

  ```bash
  unzip -l dist/pb_spec-*.whl | grep templates
  ```

- [ ] **Step 4:** Publication test:

  ```bash
  uv publish --repository testpypi
  uv tool install --index-url https://test.pypi.org/simple/ pb-spec
  pb-spec version
  ```

- [ ] **Step 4:** Publication test:

  ```bash
  uv publish --repository testpypi
  uv tool install --index-url https://test.pypi.org/simple/ pb
  pb version
  ```

- [ ] **Verification:** Wheel build successful and contains all template files.

---

## Summary & Timeline

| Phase | Tasks | Est. Hours | Target |
| :--- | :---: | :---: | :--- |
| **1. Scaffolding** | 2 | 3h | Day 1 |
| **2. Platform Abstraction** | 2 | 5h | Day 1-2 |
| **3. Skill Templates** | 3 | 11h | Day 2-3 |
| **4. Init Command** | 2 | 5h | Day 3-4 |
| **5. Polish & Release** | 3 | 4h | Day 4-5 |
| **Total** | **12** | **~28h** | **~5 days** |

## Definition of Done (DoD)

1. [ ] **Tests pass:** `uv run pytest` passes all.
2. [ ] **Lint clean:** `ruff check` no errors.
3. [ ] **Formatted:** `ruff format` applied.
4. [ ] **E2E verified:** End-to-end test script passes.
5. [ ] **Documented:** README contains install/usage instructions.
6. [ ] **Packaged:** `uv build` successful, wheel contains all templates.
