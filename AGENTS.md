# High-Performance Python Agent Instructions

## Scope

- This template targets Python projects managed by `uv`.
- `src/` contains the main application package (src layout).
- `tests/` contains all tests.
- No web-framework-specific assumptions.

## uv Project Rules (Critical)

1. Never manually edit dependency versions in `pyproject.toml`; use `uv add`.
2. Add runtime dependencies with:

   ```bash
   uv add <package>
   ```

3. Add development dependencies with:

   ```bash
   uv add --group dev <package>
   ```

4. Always run code through `uv run` to ensure the correct virtual environment.
5. Lock dependencies with `uv lock`; commit `uv.lock` to version control.
6. Use `uv sync --all-groups` to install all dependency groups.

## Preferred Dependencies and Versions

When introducing new dependencies, prefer these unless compatibility requires a change:

- `orjson >= 3.10` — fast JSON serialization/deserialization
- `msgspec >= 0.19` — high-performance struct-based serialization
- `httpx >= 0.28` — async-first HTTP client
- `uvloop >= 0.21` — drop-in asyncio event loop replacement (Linux/macOS)
- `structlog >= 25.1` — structured logging
- `pydantic >= 2.11` — data validation (only when full validation is needed)
- `click >= 8.1` — CLI framework (for complex CLIs; `argparse` for simple ones)
- `polars >= 1.30` — DataFrame operations
- `anyio >= 4.9` — structured concurrency
- `grpcio >= 1.71` — gRPC
- `sqlalchemy >= 2.0` — database ORM (async mode preferred)
- `aiosqlite >= 0.21` — async SQLite
- `asyncpg >= 0.30` — async PostgreSQL
- `redis >= 6.0` — async Redis client
- `prometheus-client >= 0.22` — metrics
- `opentelemetry-api >= 1.33` — OpenTelemetry tracing
- `opentelemetry-sdk >= 1.33` — OpenTelemetry SDK
- `cachetools >= 5.5` — in-process caching utilities

## Dependency Priority and Forbidden Choices

- JSON preference: `orjson` over `json` (stdlib) and `ujson`.
- Serialization preference: `msgspec` over `pydantic` for pure serialization (no validation needed).
- HTTP client preference: `httpx` (with `h2` for HTTP/2) over `requests` and `aiohttp`.
- DataFrame preference: `polars` over `pandas` for new code.
- Event loop preference: `uvloop` over default asyncio loop.
- Logging preference: `structlog` over `logging` (stdlib).
- Forbidden by default: `requests` (sync-only), `pandas` (use `polars`), `print()` for logging.

## Engineering Principles

### Python Implementation Guidelines

1. Type annotations:
   - All public functions and methods must have full type annotations.
   - Use `from __future__ import annotations` at the top of every module.
   - Use modern union syntax (`X | None`) instead of `Optional[X]`.
   - Use `ty` for type checking; code must pass `ty check` with zero errors.
2. Error handling:
   - Define explicit exception hierarchies per module/package.
   - Never use bare `except:` or `except Exception:` without re-raising.
   - Use `contextlib.suppress()` for intentional exception swallowing.
   - Prefer returning typed result objects over raising exceptions in hot paths.
3. Async/Await:
   - Default to `async` for I/O-bound code.
   - Use `asyncio.TaskGroup` (Python 3.11+) for structured concurrency.
   - Never mix `asyncio.run()` with already-running event loops.
4. Observability:
   - Logging: `structlog` with JSON output in production.
   - Metrics/traces: OpenTelemetry OTLP gRPC.
   - Never use `print()` for logging or diagnostics in library code.
5. Configuration:
   - Use environment variables with `pydantic-settings` or `msgspec` for config parsing.
   - Prefer TOML configuration files.
6. Security:
   - Never hardcode secrets; use environment variables or secret managers.
   - Validate all external input at system boundaries.

### Key Design Principles

- Modularity: Design each module so it can be imported independently with clear boundaries and minimal hidden coupling.
- Performance: Prefer zero-copy patterns, memory-mapped I/O when appropriate, vectorized operations, and pre-allocated buffers.
- Extensibility: Use Protocols (`typing.Protocol`) and abstract base classes for pluggable implementations.
- Type Safety: Maintain strong static typing across interfaces and internals; minimize use of `Any`.

### Performance Considerations

- Avoid allocations in hot loops; prefer pre-allocated lists, `array.array`, or NumPy/Polars for bulk data.
- Use `__slots__` on data-heavy classes to reduce per-instance memory overhead.
- Prefer `struct.pack`/`struct.unpack` or `memoryview` for binary protocol parsing.
- Use generator expressions and `itertools` to avoid materializing large intermediate lists.
- Profile before optimizing; use `py-spy`, `scalene`, or `cProfile` to identify real bottlenecks.

### Concurrency and Async Execution

- Use `uvloop` as the event loop policy for production servers.
- Use `asyncio.TaskGroup` for structured concurrent I/O.
- Use `concurrent.futures.ProcessPoolExecutor` for CPU-bound parallelism.
- Use `asyncio.to_thread()` to offload blocking calls from the event loop.
- Prefer `asyncio.Queue` for async producer-consumer patterns.
- Never perform blocking I/O (file reads, DNS, HTTP) directly in async coroutines.
- Use `anyio` when portability across asyncio/trio is required.
- Limit concurrent connections with `asyncio.Semaphore` to prevent resource exhaustion.
- Channel selection:
  - Async-to-Async: `asyncio.Queue` / `anyio.create_memory_object_stream`
  - CPU parallelism: `multiprocessing` or `concurrent.futures.ProcessPoolExecutor`
  - Avoid threading for CPU-bound work due to the GIL (use `multiprocessing` or native extensions)

### Memory and Allocation

- Use `__slots__` on frequently instantiated classes; can reduce memory by 40–60%.
- Use `msgspec.Struct` over `dataclasses` / `pydantic.BaseModel` for high-throughput data objects.
- Prefer `bytes` / `bytearray` / `memoryview` over `str` for binary data; avoid repeated encode/decode.
- Use `orjson` for JSON serialization — it returns `bytes` directly, avoiding intermediate string allocation.
- For large datasets, use memory-mapped files (`mmap`) or Arrow-backed DataFrames (`polars`).
- Use `sys.getsizeof()` and `tracemalloc` to profile memory usage.
- Prefer `array.array` over `list` for homogeneous numeric data.
- Use weak references (`weakref`) for caches that should not prevent garbage collection.

### Type and Data Layout

- Use `msgspec.Struct` with `frozen=True` for immutable data transfer objects.
- Use `dataclasses` with `slots=True, frozen=True` for simple value types.
- Use `enum.IntEnum` over `enum.Enum` for performance-critical flag/state types.
- Prefer `typing.NamedTuple` over plain tuples for self-documenting return types.
- Keep error types lightweight; avoid attaching large payloads to exception instances.
- Use `typing.TypeAlias` for complex type expressions to improve readability.

### C Extension and Native Interop

- Use `cffi` or `ctypes` for calling C libraries; prefer `cffi` for new code.
- Use `pyo3` / `maturin` for writing performance-critical modules in Rust.
- Use `Cython` only when interfacing with existing C/C++ codebases.
- Keep the Python ↔ native boundary coarse-grained; minimize per-call overhead.
- Always release the GIL (`nogil` in Cython, `py.allow_threads` in PyO3) for long-running native computations.

### Tooling and Quality

- Lint with `ruff` — all code must pass `ruff check` with zero errors.
- Format with `ruff format` — consistent style, no debates.
- Type check with `ty` — all code must pass `ty check` with zero errors.
- Use Gherkin + `behave` for outer-loop acceptance tests.
- Use `pytest` for inner-loop TDD — tests must pass before claiming completion.
- Use Hypothesis under `tests/` when you need generated coverage for invariants; these tests must run through the normal `uv run pytest` path.
- Use `pytest-benchmark` for performance-sensitive code.
- Use `pytest-cov` to track test coverage.

### Common Pitfalls

- Do not block the event loop with synchronous I/O.
- Do not use mutable default arguments (`def f(x=[]):`).
- Do not catch broad exceptions without re-raising.
- Do not use `global` or module-level mutable state in library code.
- Do not import inside functions unless lazy loading is intentional and documented.
- Handle `KeyboardInterrupt` and `SystemExit` separately from `Exception`.

### What to Avoid

- Incomplete implementations: finish features before submitting.
- Large, sweeping changes: keep changes focused and reviewable.
- Mixing unrelated changes: keep one logical change per commit.
- Using `# type: ignore` without a specific error code and justification comment.

## Development Workflow

When fixing failures, identify root cause first, then apply idiomatic fixes instead of suppressing warnings or patching symptoms.

Use outside-in development for behavior changes:

- **Git Restrictions:** NEVER use `git worktree`. All code modifications MUST be made directly on the current branch in the existing working directory.
- start with a failing Gherkin scenario under `features/`,
- drive implementation with failing `pytest` tests,
- keep example-based `pytest` tests as the default inner loop for named cases and edge cases,
- add Hypothesis properties under `tests/` when the rule is an invariant instead of a single named example,
- treat Atheris as conditional planning work rather than baseline template scaffolding,
- keep step definitions thin and reuse Python domain modules.

After each feature or bug fix, run:

```bash
just format
just lint
just test
just bdd
just test-all
```

If any command fails, report the failure and do not claim completion.

## Testing Requirements

- BDD scenarios: place Gherkin features under `features/` and step definitions under `features/steps/`.
- Use BDD to define acceptance behavior first, then use `pytest` for the inner TDD loop.
- Keep example-based and Hypothesis-based tests together under `tests/`; `just test` must exercise both without a separate property-test command.
- Unit tests: place in `tests/` mirroring the source structure.
- Integration tests: place in `tests/integration/`.
- Fuzz tests: only plan or add Atheris when a module parses hostile text or binary input, decodes file or protocol formats, or wraps native extensions where crash resistance matters.
- Fuzz workflow: when fuzzing is justified, keep the harness targeted to the affected module instead of adding a default workspace-wide fuzz command to every starter.
- Performance tests: use `pytest-benchmark` with `@pytest.mark.benchmark` only for code with an explicit latency SLA, throughput target, or hot-path requirement.
- Treat benchmark work as optional planning scope; keep the standard `pytest` loop as the default when no performance requirement exists.
- For `/pb-plan` work, mark fuzzing as `conditional` or `N/A` unless the scope explicitly includes parser-like, protocol, binary-decoding, hostile-input, or native-extension-heavy code.
- Add tests for behavioral changes and public API changes.
- Use `pytest` fixtures for setup/teardown; avoid `setUp`/`tearDown` methods.
- Use `pytest.raises` for exception testing; `pytest.approx` for floating-point comparisons.

## Language Requirement

- Documentation, comments, and commit messages must be English only.
