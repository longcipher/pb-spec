# pb-spec Workflow Contract

Single source of truth: `src/pb_spec/validation/contract_sections.toml` + this file.
Prose is minimal; types and tests are the contract.

## Artifact Family

```
specs/<spec-dir>/
├── design.md          # 5 required + 5 optional sections
└── tasks.md           # 4-field task blocks
```

No Gherkin/BDD artifacts. Behavior is captured by the `TDD & Mutation Testing Strategy`
section (type contracts, invariants, test matrix) and by the pytest suite itself.

## Type Contracts

### Design Sections

Source: `contract_sections.toml [design]`

```python
DESIGN_REQUIRED: list[str] = [
    "Summary",
    "Approach",
    "Architecture Decisions",
    "TDD & Mutation Testing Strategy",
    "Verification",
]
DESIGN_OPTIONAL: list[str] = [
    "Requirements & Goals",
    "Architecture Overview",
    "Data Models",
    "Interface Contracts",
    "Implementation Plan",
]
```

`TDD & Mutation Testing Strategy` must state: type contracts (input/output shapes),
invariants, boundary conditions, the test matrix (unit + hypothesis property tests),
and the mutation score target (default ≥ 85%).

### Task Block

```python
@dataclass(frozen=True)
class TaskBlock:
    id: str  # "X.Y" via regex r"Task ([0-9]+)\.([0-9]+)"
    fields: dict[str, str]  # 4 required fields, see below
    content: str  # must contain at least one checkbox (- [ ])


TASK_REQUIRED_FIELDS: list[str] = [
    "Context:",
    "Verification:",
    "Status:",
    "Test Coverage:",
]
ALLOWED_STATUSES: frozenset[str] = {
    "🔴 TODO",
    "🟡 IN_PROGRESS",
    "🟡 IN PROGRESS",
    "🟢 DONE",
    "🔄 DCR",
    "⛔ OBSOLETE",
}
```

Legacy `TODO` (without emoji) and `IN PROGRESS` (with space) are accepted on input,
normalized before execution. `Test Coverage:` lists the pytest test paths that prove
the task, or literal `N/A` for infrastructure-only tasks.

### Block Packets

```python
@dataclass(frozen=True)
class BlockPacket:
    type: str  # "build_blocked" | "dcr"
    fields: dict[str, str]


BLOCK_REQUIRED_FIELDS: frozenset[str] = {"Reason", "Requested Change", "Impact"}
```

Applies to both Build Blocked and Design Change Request packets.

### Validation Result

Source: `src/pb_spec/validation/result.py`

```python
class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ValidationError:
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    file_path: str | None = None
    line_number: int | None = None
    field_name: str | None = None


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

## Validation Interface

```python
class SpecValidator(Protocol):
    def validate_plan(self, spec_dir: Path) -> ValidationResult: ...
    def validate_build(self, spec_dir: Path) -> ValidationResult: ...
    def validate_task(self) -> ValidationResult: ...
```

## Executable Assertions

The following pytest cases ARE the contract. If the code passes these, the contract is satisfied.

```python
def test_design_requires_5_sections():
    """design.md missing any required section -> CRITICAL error."""
    result = validate_design_structure(spec_dir_with_missing_section("Summary"))
    assert not result.is_valid
    assert any(e.severity == ErrorSeverity.HIGH and "Summary" in e.message for e in result.errors)


def test_design_requires_tdd_mutation_strategy():
    """design.md missing 'TDD & Mutation Testing Strategy' -> error."""
    result = validate_design_structure(
        spec_dir_with_missing_section("TDD & Mutation Testing Strategy")
    )
    assert not result.is_valid


def test_task_block_requires_4_fields():
    """Task block missing any of 4 fields -> error."""
    result = validate_tasks_structure(spec_dir_with_missing_field("Context:"))
    assert not result.is_valid
    assert any("Context:" in e.message for e in result.errors)


def test_task_block_requires_test_coverage():
    """Task block missing 'Test Coverage:' -> error."""
    result = validate_tasks_structure(spec_dir_with_missing_field("Test Coverage:"))
    assert not result.is_valid
    assert any("Test Coverage:" in e.message for e in result.errors)


def test_task_block_requires_checkbox():
    """Task block with no checkbox step -> error."""
    result = validate_tasks_structure(spec_dir_without_checkbox())
    assert not result.is_valid
    assert any("checkbox" in e.message for e in result.errors)


def test_duplicate_task_ids_rejected():
    """Two tasks with same X.Y -> HIGH severity error."""
    result = validate_tasks_structure(spec_dir_with_dup_id())
    assert not result.is_valid
    assert any(e.severity == ErrorSeverity.HIGH and "Duplicate" in e.message for e in result.errors)


def test_invalid_status_rejected():
    """Status not in ALLOWED_STATUSES -> error."""
    result = validate_tasks_structure(spec_dir_with_status("🚀 STARTED"))
    assert not result.is_valid
    assert any("invalid Status" in e.message for e in result.errors)


def test_empty_placeholder_rejected():
    """Required field with empty value -> error."""
    result = validate_tasks_structure(spec_dir_with_empty_field("Verification:"))
    assert not result.is_valid
    assert any("empty" in e.message for e in result.errors)


def test_build_blocked_requires_3_fields():
    """Build Blocked missing any field -> error."""
    result = validate_contract_blocks(content_missing_field("Impact"))
    assert any("Impact" in e for e in result)


def test_dcr_requires_3_fields():
    """DCR missing any field -> error."""
    result = validate_contract_blocks(content_missing_dcr_field("Reason"))
    assert any("Reason" in e for e in result)


def test_na_test_coverage_valid():
    """Literal 'N/A' in Test Coverage is valid for infrastructure tasks."""
    result = validate_tasks_structure(spec_dir_with_na_coverage())
    assert result.is_valid


def test_valid_spec_passes():
    """A well-formed spec passes all validations."""
    result = validate_plan(well_formed_spec_dir())
    assert result.is_valid
    assert len(result.warnings) > 0
```

## CLI Parameters

```python
@dataclass(frozen=True)
class CLIParams:
    mode: Literal["plan", "build", "task"]  # exactly one, mutually exclusive
    specs_dir: Path = Path("specs/")
```

CLI commands:

| Command | Behavior | Exit 0 when |
|---|---|---|
| `pb-spec validate --plan` | validate spec structure | all checks pass |
| `pb-spec test [--parallel/--serial] [--coverage]` | run pytest (xdist) | suite green (+ coverage ≥ 80 with `--coverage`) |
| `pb-spec mutate [--against REF] [--threshold N]` | incremental mutation on changed files | score ≥ threshold (default 85) |
| `pb-spec verify [--against REF]` | tests + coverage + mutation gate | all three pass |

## Environment Variables

| Variable | Default | Scope |
|---|---|---|
| `PB_SPEC_GIT_TIMEOUT` | `60` | git command timeout (seconds) |
| `PB_SPEC_RUMDL_CHECK_TIMEOUT` | `10` | rumdl availability check |
| `PB_SPEC_RUMDL_FORMAT_TIMEOUT` | `30` | rumdl formatting |

## Invariants

1. Validator never modifies source files — read-only.
2. Non-zero exit on CRITICAL or HIGH errors.
3. `rumdl` optional: skip gracefully if absent.
4. `contract_sections.toml` is the single config source; project overrides allowed.
5. No BDD artifacts (`.feature`, step definitions, behave) anywhere in the workflow.
6. A surviving mutant on changed code is a test failure, not a warning.
