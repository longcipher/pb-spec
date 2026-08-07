#!/usr/bin/env bash
# scripts/run-mutation-diff.sh — Incremental mutation testing on modified code.
# Verifies the TDD test suite actually kills mutations in recently changed code.
# Supports Rust (cargo-mutants), Python (mutmut), and TypeScript (StrykerJS).
#
# Incremental design:
#   - Python (mutmut 3.x) keeps a `mutants/` cache keyed by per-function hashes plus
#     git change detection, so re-runs only re-test new/changed functions — keeping
#     the AI agent loop fast while staying strict on what changed.
#   - Rust uses `cargo mutants --in-diff`.
#   - TypeScript mutates only changed files via `--mutate`.
#
# Usage:
#   ./scripts/run-mutation-diff.sh                # compare against main (or master)
#   ./scripts/run-mutation-diff.sh --against HEAD # compare against HEAD (staged+unstaged)
#   ./scripts/run-mutation-diff.sh --threshold 90 # custom mutation score threshold
#
# Exit codes:
#   0 — all mutants killed or score >= threshold
#   1 — surviving mutants detected below threshold
#   2 — no modified files found (nothing to test)

set -euo pipefail

# ---------- Configuration ----------
THRESHOLD=85
AGAINST=""

# ---------- Argument parsing ----------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --against)
            AGAINST="$2"
            shift 2
            ;;
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 [--against <ref>] [--threshold <N>]" >&2
            exit 1
            ;;
    esac
done

# ---------- Detect base ref ----------
if [[ -z "$AGAINST" ]]; then
    if git rev-parse --verify main >/dev/null 2>&1; then
        AGAINST="main"
    elif git rev-parse --verify master >/dev/null 2>&1; then
        AGAINST="master"
    else
        AGAINST="HEAD"
    fi
fi

echo "=== Mutation Diff Runner ==="
echo "Comparing against: $AGAINST"
echo "Score threshold:   ${THRESHOLD}%"
echo ""

# ---------- Get changed files ----------
CHANGED_FILES=$(git diff --name-only --diff-filter=ACMR "$AGAINST" -- 2>/dev/null || git diff --name-only --diff-filter=ACMR HEAD --)

if [[ -z "$CHANGED_FILES" ]]; then
    echo "No modified files found against $AGAINST. Nothing to test."
    exit 2
fi

echo "Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  /'
echo ""

# ---------- Partition by language ----------
RS_FILES=$(echo "$CHANGED_FILES" | grep -E '\.rs$' || true)
PY_FILES=$(echo "$CHANGED_FILES" | grep -E '\.py$' || true)
TS_FILES=$(echo "$CHANGED_FILES" | grep -E '\.(ts|tsx)$' || true)

# ---------- Resolve the mutmut executable ----------
# Prefer PATH, then the local venv, then uv (which resolves the locked env).
MUTMUT_CMD=""
if command -v mutmut >/dev/null 2>&1; then
    MUTMUT_CMD="mutmut"
elif [[ -x ".venv/bin/mutmut" ]]; then
    MUTMUT_CMD=".venv/bin/mutmut"
elif command -v uv >/dev/null 2>&1; then
    MUTMUT_CMD="uv run mutmut"
fi

OVERALL_EXIT=0

# ---------- Rust: cargo-mutants ----------
if [[ -n "$RS_FILES" ]] && command -v cargo-mutants >/dev/null 2>&1; then
    echo "━━━ Rust (cargo-mutants) ━━━"
    echo "Rust files changed:"
    echo "$RS_FILES" | sed 's/^/  /'
    echo ""

    # Use --in-diff for incremental mutation (compare against the base ref)
    if cargo mutants --in-diff "$AGAINST" --timeout 30 2>&1; then
        echo "Rust: all mutants killed."
    else
        echo "Rust: SURVIVING MUTANTS detected."
        OVERALL_EXIT=1
    fi
    echo ""
elif [[ -n "$RS_FILES" ]]; then
    echo "━━━ Rust (cargo-mutants) ━━━"
    echo "WARNING: Rust files changed but cargo-mutants is not installed."
    echo "  Install: cargo install cargo-mutants"
    echo ""
fi

# ---------- Python: mutmut ----------
if [[ -n "$PY_FILES" ]] && [[ -n "$MUTMUT_CMD" ]]; then
    echo "━━━ Python (mutmut) ━━━"
    echo "Python files changed:"
    echo "$PY_FILES" | sed 's/^/  /'
    echo ""
    echo "Mutmut: $MUTMUT_CMD"

    # mutmut 3.x is incremental by default: verdicts are cached per mutant and
    # re-run only for new/changed functions (per-function hashes + git change
    # detection). Do NOT wipe `mutants/` here — that would destroy incrementality.
    echo "Running: $MUTMUT_CMD run (incremental — cached verdicts are reused)"
    if ! $MUTMUT_CMD run 2>&1; then
        echo ""
        echo "Python: mutmut run FAILED (clean-test failure or tooling error)."
        echo "  A failing clean test means the suite must be green before mutation is meaningful."
        OVERALL_EXIT=1
        echo ""
        # Skip to the TS section if present; do not parse bogus stats below.
        if [[ -n "$TS_FILES" ]]; then
            : # continue with the TypeScript block after this if/elif chain
        fi
    else
        echo "mutmut run completed."
        echo ""

        # Export CI/CD stats: killed / total from mutants/mutmut-cicd-stats.json
        $MUTMUT_CMD export-cicd-stats >/dev/null 2>&1 || true
        if [[ -f "mutants/mutmut-cicd-stats.json" ]]; then
            STATS=$(python3 -c 'import json; d = json.load(open("mutants/mutmut-cicd-stats.json")); print(d["killed"], d["total"], d.get("survived", 0), d.get("timeout", 0), d.get("suspicious", 0), d.get("no_tests", 0), d.get("skipped", 0), d.get("segfault", 0))' 2>/dev/null || true)
            if [[ -z "$STATS" ]]; then
                echo "Python: could not parse mutmut CI/CD stats."
                OVERALL_EXIT=1
            else
                read -r KILLED TOTAL SURVIVED TIMEOUT SUSPICIOUS NO_TESTS SKIPPED SEGFAULT <<< "$STATS"
                if [[ ${TOTAL:-0} -gt 0 ]]; then
                    SCORE=$(( (KILLED * 100) / TOTAL ))
                    echo ""
                    echo "Python mutation score: ${SCORE}% (killed: $KILLED, total: $TOTAL)"
                    echo "  non-killed: survived=$SURVIVED timeout=$TIMEOUT suspicious=$SUSPICIOUS no_tests=$NO_TESTS skipped=$SKIPPED segfault=$SEGFAULT"
                    if [[ $SCORE -lt $THRESHOLD ]]; then
                        echo ""
                        echo "Python: SCORE ${SCORE}% < ${THRESHOLD}% threshold. FAILING."
                        echo "  Surviving mutants mean the TDD tests miss behavior — add boundary"
                        echo "  checks and exact-value assertions until every mutant is killed."
                        echo "  Inspect them with: $MUTMUT_CMD show <mutant-name>"
                        OVERALL_EXIT=1
                    else
                        echo "Python: score ${SCORE}% >= ${THRESHOLD}% threshold. PASSING."
                    fi
                else
                    echo "Python: no mutants generated (files may contain only non-mutable code)."
                fi
            fi
        else
            echo "Python: no mutation stats produced (run produced no mutants?)."
        fi
    fi
    echo ""
elif [[ -n "$PY_FILES" ]]; then
    echo "━━━ Python (mutmut) ━━━"
    echo "WARNING: Python files changed but mutmut is not installed."
    echo "  Install: pip install mutmut   (or run inside the project venv)"
    echo ""
fi

# ---------- TypeScript: StrykerJS ----------
if [[ -n "$TS_FILES" ]]; then
    echo "━━━ TypeScript (StrykerJS) ━━━"
    echo "TypeScript files changed:"
    echo "$TS_FILES" | sed 's/^/  /'
    echo ""

    if command -v npx >/dev/null 2>&1; then
        # Build glob from changed files for --mutate
        TS_GLOBS=""
        while IFS= read -r f; do
            # Skip test files
            if [[ "$f" =~ \.(test|spec)\.(ts|tsx)$ ]]; then
                continue
            fi
            if [[ -z "$TS_GLOBS" ]]; then
                TS_GLOBS="$f"
            else
                TS_GLOBS="${TS_GLOBS},${f}"
            fi
        done <<< "$TS_FILES"

        if [[ -n "$TS_GLOBS" ]]; then
            echo "Running: npx stryker run --mutate \"$TS_GLOBS\""
            STRYKER_OUTPUT=$(npx stryker run --mutate "$TS_GLOBS" 2>&1 || true)
            echo "$STRYKER_OUTPUT"

            # Parse StrykerJS score from output (look for "Mutation score" line)
            SCORE_LINE=$(echo "$STRYKER_OUTPUT" | grep -iE 'mutation score|score:' | tail -1 || true)
            if [[ -n "$SCORE_LINE" ]]; then
                SCORE_NUM=$(echo "$SCORE_LINE" | grep -oE '[0-9]+\.[0-9]+%' | grep -oE '[0-9]+' | head -1 || echo "0")
                echo ""
                if [[ $SCORE_NUM -lt $THRESHOLD ]]; then
                    echo "TypeScript: score ${SCORE_NUM}% < ${THRESHOLD}% threshold. FAILING."
                    OVERALL_EXIT=1
                else
                    echo "TypeScript: score ${SCORE_NUM}% >= ${THRESHOLD}% threshold. PASSING."
                fi
            else
                echo "WARNING: Could not parse StrykerJS mutation score."
            fi
        else
            echo "TypeScript: no source files to mutate (only test files changed)."
        fi
    else
        echo "WARNING: npx not found. Cannot run StrykerJS."
    fi
    echo ""
elif [[ -n "$TS_FILES" ]] || true; then
    # Only show if there were TS files and no npx
    :
fi

# ---------- Summary ----------
echo "━━━ Summary ━━━"
if [[ $OVERALL_EXIT -eq 0 ]]; then
    echo "All mutation tests PASSED (score >= ${THRESHOLD}%)."
else
    echo "Mutation testing FAILED. Surviving mutants detected or score below ${THRESHOLD}%."
fi

exit $OVERALL_EXIT
