# Closing the Loop — reconcile, issues

The advisor's job doesn't end at the spec. This file covers the follow-through flows: keeping the spec backlog alive (`reconcile`) and publishing specs where work gets picked up (`--issues`).

The founding rule survives unchanged: **the advisor never edits source code.** To execute specs, use `/pb-build <feature-name>` — it handles the Generator/Evaluator loop with BDD+TDD verification.

---

## Execution

After writing specs, inform the user:

```text
✅ Specs created: specs/<spec-dir>/
Mode: <Lightweight | Full>

Files:
  - specs/<spec-dir>/design.md
  - specs/<spec-dir>/tasks.md
  - specs/<spec-dir>/features/*.feature

To execute: /pb-build <feature-name>
```

The builder will:

1. Resolve `<feature-name>` → `<spec-dir>` under `specs/`
2. Validate the spec contract
3. Execute tasks sequentially with Generator/Evaluator isolation
4. Update tasks.md status as work completes

---

## `reconcile` — keep `specs/` alive

Process what happened since the last session. Read `specs/README.md` and every spec's `tasks.md`, then per status:

- **DONE** — spot-check that the done criteria still hold on the current HEAD (cheap ones only). Mark verified in the index. Don't delete spec files — they're the record.
- **BLOCKED** — read the reason. Investigate the underlying obstacle in the codebase. Either rewrite the spec around it (new directory if the approach changed fundamentally, in-place refresh otherwise) or mark REJECTED with one line of rationale.
- **IN PROGRESS** (stale) — flag it to the user; a builder probably died mid-run. Check if `/pb-build` was interrupted.
- **TODO** — run the drift check. If drifted: re-verify the finding still exists (it may have been fixed in passing), then refresh the "Current state" excerpts and `Planned at` SHA. If the finding is gone, mark REJECTED ("fixed independently").

Finish with a short report: what's verified done, what was refreshed, what's rejected, and what's executable right now via `/pb-build`.

---

## `--issues` — publish specs as GitHub issues

Modifier on any planning invocation (`/pb-improve --issues`, `/pb-improve security --issues`). The flag is the user's authorization to create issues — never create them without it.

1. Preflight: `gh auth status` succeeds and the repo has a GitHub remote. If either fails, write the spec files as normal and say why issues were skipped.
2. Show the list of titles about to become issues; confirm once if interactive.
3. Per spec: `gh issue create --title "<spec title>" --body-file specs/<spec-dir>/design.md`. Labels: `improve` plus the category — apply only if the labels exist or can be created without erroring; skip labels rather than fail.
4. Record each issue URL in the spec's design.md Metadata block and the index.

The spec files remain the source of truth; the issue is distribution. The self-containment rule pays off here — the issue body needs no edits to make sense to whoever (or whatever) picks it up.
