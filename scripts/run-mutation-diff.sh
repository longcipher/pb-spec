#!/usr/bin/env bash
# scripts/run-mutation-diff.sh — Spec-marked, change-scoped mutation testing.
#
# Mutation runs ONLY when all of these hold:
#   1. the latest specs/*/tasks.md declares one or more `Mutation: <src-glob>` fields;
#   2. files changed against the merge base match those declared globs;
#   3. the changed-file count and mutation budget stay within the hard caps.
#
# Otherwise the script exits 2 (skip). Exceeding a cap exits 3 (failure).
# Whole-repo mutation is never attempted; a bare `mutmut run` / `cargo mutants`
# invocation is not part of this gate.
#
# Supports Python (mutmut), Rust (cargo-mutants), and TypeScript (StrykerJS).
#
# This script is a reference implementation for pb-spec's own repo and for
# projects that install the pb-spec CLI. The authoritative policy for skill
# users lives in skills/pb-build/SKILL.md; downstream projects should prefer
# native commands (`cargo mutants --in-diff <diff-file>`, `mutmut '<module>.*'`,
# `stryker run --mutate ... --since ...`).
#
# Usage:
#   ./scripts/run-mutation-diff.sh
#   ./scripts/run-mutation-diff.sh --against <ref>
#   ./scripts/run-mutation-diff.sh --threshold 90
#
# Exit codes:
#   0 — all selected mutants killed or score >= threshold
#   1 — surviving mutants below threshold, or a tooling failure
#   2 — skipped: no spec marker, no eligible changes, or no configured tool
#   3 — scope exceeded the hard budget

set -euo pipefail

THRESHOLD=85
MAX_FILES=3
MAX_MUTANTS=60
MAX_SECONDS=300
AGAINST=""
OVERALL_EXIT=0

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

PYTHON=(python3)
MUTMUT=()

usage() {
    echo "Usage: $0 [--against <ref>] [--threshold <N>]"
}

skip_gate() {
    echo "SKIP: $1"
    exit 2
}

budget_fail() {
    echo "BUDGET EXCEEDED: $1"
    echo "  Narrow the spec's Mutation: targets or split the task. Full-repo runs are forbidden."
    exit 3
}

run_with_timeout() {
    local seconds="$1"
    shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "$seconds" "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$seconds" "$@"
    else
        # macOS has no GNU timeout by default; perl ships with the OS.
        perl -e 'alarm shift; exec @ARGV' "$seconds" "$@"
    fi
}

select_python() {
    if command -v uv >/dev/null 2>&1 && [[ -f pyproject.toml ]]; then
        PYTHON=(uv run python)
    else
        PYTHON=(python3)
    fi
}

resolve_base() {
    for ref in main master origin/main origin/master; do
        if git rev-parse --verify "$ref" >/dev/null 2>&1; then
            AGAINST="$ref"
            break
        fi
    done
    if [[ -z "$AGAINST" ]]; then
        AGAINST="HEAD"
    fi

    if MERGE_BASE=$(git merge-base HEAD "$AGAINST" 2>/dev/null); then
        :
    else
        MERGE_BASE="$AGAINST"
    fi
}

latest_spec_dir() {
    local dir name key
    if [[ ! -d specs ]]; then
        return 0
    fi
    find specs -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while IFS= read -r dir; do
        name=$(basename "$dir")
        case "$name" in
            [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*) key="1" ;;
            *) key="0" ;;
        esac
        printf '%s %s\n' "$key" "$dir"
    done | sort | tail -1 | cut -d' ' -f2-
}

resolve_spec_targets() {
    local raw
    SPEC_DIR=$(latest_spec_dir)
    if [[ -z "$SPEC_DIR" || ! -f "$SPEC_DIR/tasks.md" ]]; then
        skip_gate "no specs/*/tasks.md; mutation is spec-marked only"
    fi

    raw=$(
        grep -E '^[[:space:]]*Mutation:' "$SPEC_DIR/tasks.md" \
            | sed -E 's/^[[:space:]]*Mutation:[[:space:]]*//' || true
    )
    SPEC_TARGETS=$(
        printf '%s\n' "$raw" \
            | tr ',' '\n' \
            | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' \
            | grep -v '^$' \
            | grep -Ev '^(N/A|n/a|none|exempt)$' || true
    )
    if [[ -z "$SPEC_TARGETS" ]]; then
        skip_gate "no task declares 'Mutation: <src-glob>' in the latest spec"
    fi
}

select_scoped_files() {
    local changed file pattern
    changed=$(
        {
            git diff --name-only --diff-filter=ACMR "$MERGE_BASE" -- 2>/dev/null || true
            git ls-files --others --exclude-standard 2>/dev/null || true
        } | sort -u
    )
    if [[ -z "$changed" ]]; then
        skip_gate "no changed files against $MERGE_BASE"
    fi

    SCOPED_FILES=""
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        while IFS= read -r pattern; do
            [[ -z "$pattern" ]] && continue
            # shellcheck disable=SC2254
            case "$file" in
                $pattern)
                    SCOPED_FILES="${SCOPED_FILES}${file}"$'\n'
                    break
                    ;;
            esac
        done <<< "$SPEC_TARGETS"
    done <<< "$changed"

    SCOPED_FILES=$(printf '%s' "$SCOPED_FILES" | grep -v '^$' || true)
    if [[ -z "$SCOPED_FILES" ]]; then
        skip_gate "changed files do not match the spec's Mutation: targets"
    fi

    SCOPED_COUNT=$(printf '%s\n' "$SCOPED_FILES" | grep -c . || true)
    if [[ "$SCOPED_COUNT" -gt "$MAX_FILES" ]]; then
        budget_fail "$SCOPED_COUNT changed files > ${MAX_FILES}"
    fi
}

has_mutmut_config() {
    [[ -f pyproject.toml ]] && grep -q '^\[tool.mutmut\]' pyproject.toml && return 0
    [[ -f setup.cfg ]] && grep -q '^\[mutmut\]' setup.cfg && return 0
    return 1
}

resolve_mutmut() {
    if has_mutmut_config && command -v uv >/dev/null 2>&1; then
        MUTMUT=(uv run mutmut)
    elif [[ -x .venv/bin/mutmut ]]; then
        MUTMUT=(.venv/bin/mutmut)
    elif command -v mutmut >/dev/null 2>&1; then
        MUTMUT=(mutmut)
    fi
}

python_stats() {
    local globs_file="$1"
    "${PYTHON[@]}" - "$globs_file" <<'PY'
import fnmatch
import json
import pathlib
import sys

globs = [line.strip() for line in open(sys.argv[1], encoding="utf-8") if line.strip()]
killed = 0
total = 0
for meta in pathlib.Path("mutants").rglob("*.meta"):
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    for key, code in data.get("exit_code_by_key", {}).items():
        if code is None:
            continue
        if any(fnmatch.fnmatch(key, glob) for glob in globs):
            total += 1
            if code in (1, 3):
                killed += 1
print(killed, total)
PY
}

run_rust() {
    local total=0 file diff count out rc
    if ! command -v cargo-mutants >/dev/null 2>&1; then
        skip_gate "cargo-mutants is not installed"
    fi

    echo "--- Rust (cargo-mutants) ---"
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        diff="$TMP_DIR/$(printf '%s' "$file" | tr '/' '_').diff"
        if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
            git diff "$MERGE_BASE" -- "$file" > "$diff"
        else
            git diff --no-index -- /dev/null "$file" > "$diff" 2>/dev/null || true
        fi
        out="$TMP_DIR/rust-list.txt"
        if ! cargo mutants --in-diff "$diff" --file "$file" --list --no-times > "$out" 2>&1; then
            cat "$out"
            echo "Rust: cargo-mutants list FAILED in $file."
            OVERALL_EXIT=1
            return
        fi
        count=$(grep -Ec ':[0-9]+:[0-9]+:' "$out" || true)
        total=$((total + count))
    done <<< "$RS_FILES"

    if [[ "$total" -gt "$MAX_MUTANTS" ]]; then
        budget_fail "$total Rust mutants > ${MAX_MUTANTS}"
    fi
    if [[ "$total" -eq 0 ]]; then
        echo "Rust: no mutants in changed lines."
        echo ""
        return
    fi

    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        diff="$TMP_DIR/$(printf '%s' "$file" | tr '/' '_').diff"
        out="$TMP_DIR/rust-run.txt"
        set +e
        run_with_timeout "$MAX_SECONDS" cargo mutants --in-diff "$diff" --file "$file" \
            --timeout-multiplier 2 --no-times > "$out" 2>&1
        rc=$?
        set -e
        if [[ "$rc" -eq 124 || "$rc" -eq 142 ]]; then
            budget_fail "Rust mutation exceeded ${MAX_SECONDS}s"
        fi
        if [[ "$rc" -ne 0 ]] || grep -q 'MISSED' "$out"; then
            cat "$out"
            echo "Rust: SURVIVING MUTANTS detected."
            OVERALL_EXIT=1
        else
            echo "Rust: all mutants killed in $file."
        fi
    done <<< "$RS_FILES"
    echo ""
}

run_python() {
    local globs_file est_out out rc stats killed total score mutant_count est_ms est_seconds module glob
    if ! has_mutmut_config; then
        skip_gate "mutmut is not configured (add [tool.mutmut] to pyproject.toml)"
    fi
    resolve_mutmut
    if [[ ${#MUTMUT[@]} -eq 0 ]]; then
        skip_gate "mutmut is not installed"
    fi

    echo "--- Python (mutmut) ---"
    globs_file="$TMP_DIR/python-globs.txt"
    GLOB_ARGS=()
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        module="${file#src/}"
        module="${module%.py}"
        module="${module//\//.}"
        [[ "$file" == */__init__.py ]] && module="${module%.__init__}"
        glob="${module}.*"
        GLOB_ARGS+=("$glob")
        printf '%s\n' "$glob" >> "$globs_file"
    done <<< "$PY_FILES"

    est_out="$TMP_DIR/python-estimates.txt"
    set +e
    run_with_timeout "$MAX_SECONDS" "${MUTMUT[@]}" print-time-estimates "${GLOB_ARGS[@]}" > "$est_out" 2>&1
    rc=$?
    set -e
    if [[ "$rc" -eq 124 || "$rc" -eq 142 ]]; then
        budget_fail "Python mutation pre-flight exceeded ${MAX_SECONDS}s"
    fi
    if [[ "$rc" -ne 0 ]]; then
        if grep -q "Filtered for specific mutants, but nothing matches" "$est_out"; then
            skip_gate "selected Python files produced no mutants"
        fi
        cat "$est_out"
        echo "Python: mutmut pre-flight FAILED."
        exit 1
    fi

    mutant_count=$(grep -E -c '^(<no tests>|[0-9]+ms) ' "$est_out" || true)
    est_ms=$(awk '/^[0-9]+ms/ {gsub("ms", "", $1); total += $1} END {print total + 0}' "$est_out")
    if [[ "$mutant_count" -eq 0 ]]; then
        skip_gate "selected Python files produced no mutants"
    fi
    if [[ "$mutant_count" -gt "$MAX_MUTANTS" ]]; then
        budget_fail "$mutant_count Python mutants > ${MAX_MUTANTS}"
    fi
    est_seconds=$(( (est_ms + 999) / 1000 ))
    if [[ "$est_seconds" -gt "$MAX_SECONDS" ]]; then
        budget_fail "estimated ${est_seconds}s > ${MAX_SECONDS}s"
    fi

    echo "Selected mutants: ${mutant_count} (estimated ${est_seconds}s)"
    out="$TMP_DIR/python-run.txt"
    set +e
    run_with_timeout "$MAX_SECONDS" "${MUTMUT[@]}" run "${GLOB_ARGS[@]}" \
        --max-children "$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)" > "$out" 2>&1
    rc=$?
    set -e
    if [[ "$rc" -eq 124 || "$rc" -eq 142 ]]; then
        budget_fail "Python mutation exceeded ${MAX_SECONDS}s"
    fi
    if [[ "$rc" -ne 0 ]]; then
        cat "$out"
        echo "Python: mutmut run FAILED (clean-test failure or tooling error)."
        exit 1
    fi

    stats=$(python_stats "$globs_file")
    read -r killed total <<< "$stats"
    if [[ "${total:-0}" -eq 0 ]]; then
        skip_gate "no test-backed Python mutants were evaluated"
    fi

    score=$(( (killed * 100) / total ))
    echo ""
    echo "Python mutation score: ${score}% (killed: ${killed}, total: ${total})"
    if [[ "$score" -lt "$THRESHOLD" ]]; then
        echo "Python: SCORE ${score}% < ${THRESHOLD}% threshold. FAILING."
        echo "  Inspect survivors with: ${MUTMUT[*]} show <mutant-name>"
        OVERALL_EXIT=1
    else
        echo "Python: score ${score}% >= ${THRESHOLD}% threshold. PASSING."
    fi
    echo ""
}

has_stryker_config() {
    compgen -G "stryker.conf.*" >/dev/null 2>&1 && return 0
    compgen -G "stryker.config.*" >/dev/null 2>&1 && return 0
    [[ -f package.json ]] && grep -q '"stryker"' package.json && return 0
    return 1
}

run_typescript() {
    local ts_globs out rc score_line score report stats killed total
    if ! command -v npx >/dev/null 2>&1; then
        skip_gate "npx is not installed"
    fi
    if ! has_stryker_config; then
        skip_gate "Stryker is not configured"
    fi

    echo "--- TypeScript (StrykerJS) ---"
    ts_globs=""
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        [[ "$file" =~ \.(test|spec)\.(ts|tsx)$ ]] && continue
        ts_globs="${ts_globs:+$ts_globs,}$file"
    done <<< "$TS_FILES"
    if [[ -z "$ts_globs" ]]; then
        skip_gate "only test files changed"
    fi

    out="$TMP_DIR/stryker.txt"
    set +e
    run_with_timeout "$MAX_SECONDS" npx stryker run --mutate "$ts_globs" --since "$AGAINST" \
        --incremental --reporters clear-text,json > "$out" 2>&1
    rc=$?
    set -e
    cat "$out"
    if [[ "$rc" -eq 124 || "$rc" -eq 142 ]]; then
        budget_fail "TypeScript mutation exceeded ${MAX_SECONDS}s"
    fi

    score=""
    score_line=$(grep -i 'mutation score' "$out" | tail -1 || true)
    if [[ -n "$score_line" ]]; then
        score=$(printf '%s\n' "$score_line" | sed -nE 's/.*([0-9]+(?:\.[0-9]+)?)%.*/\1/p' | head -1)
    fi

    report="reports/mutation/mutation.json"
    if [[ -f "$report" ]]; then
        stats=$(
            "${PYTHON[@]}" - "$report" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
killed = 0
total = 0
for file_data in data.get("files", {}).values():
    for mutant in file_data.get("mutants", []):
        status = mutant.get("status")
        if status in ("Ignored", "Pending"):
            continue
        total += 1
        if status == "Killed":
            killed += 1
print(killed, total)
PY
        )
        read -r killed total <<< "$stats"
        if [[ "${total:-0}" -gt "$MAX_MUTANTS" ]]; then
            budget_fail "$total TypeScript mutants > ${MAX_MUTANTS}"
        fi
        if [[ -z "$score" && "${total:-0}" -gt 0 ]]; then
            score=$(( (killed * 100) / total ))
        fi
    fi

    if [[ -z "$score" ]]; then
        echo "TypeScript: could not determine the mutation score."
        OVERALL_EXIT=1
    elif awk -v s="$score" -v t="$THRESHOLD" 'BEGIN { exit !(s < t) }'; then
        echo "TypeScript: score ${score}% < ${THRESHOLD}% threshold. FAILING."
        OVERALL_EXIT=1
    else
        echo "TypeScript: score ${score}% >= ${THRESHOLD}% threshold. PASSING."
    fi
    echo ""
}

main() {
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
            -h | --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown argument: $1" >&2
                usage >&2
                exit 1
                ;;
        esac
    done

    select_python
    resolve_base
    resolve_spec_targets
    select_scoped_files

    RS_FILES=$(printf '%s\n' "$SCOPED_FILES" | grep -E '\.rs$' || true)
    PY_FILES=$(printf '%s\n' "$SCOPED_FILES" | grep -E '\.py$' || true)
    TS_FILES=$(printf '%s\n' "$SCOPED_FILES" | grep -E '\.(ts|tsx)$' || true)

    echo "=== Mutation Gate ==="
    echo "Diff base:       $MERGE_BASE (against $AGAINST)"
    echo "Score threshold: ${THRESHOLD}%"
    echo "Hard budget:     ${MAX_FILES} files / ${MAX_MUTANTS} mutants / ${MAX_SECONDS}s"
    echo "Spec targets:"
    echo "$SPEC_TARGETS" | sed 's/^/  /'
    echo ""
    echo "Scoped changed files:"
    echo "$SCOPED_FILES" | sed 's/^/  /'
    echo ""

    if [[ -z "$RS_FILES$PY_FILES$TS_FILES" ]]; then
        skip_gate "scoped files contain no mutable source"
    fi
    if [[ -n "$RS_FILES" ]]; then
        run_rust
    fi
    if [[ -n "$PY_FILES" ]]; then
        run_python
    fi
    if [[ -n "$TS_FILES" ]]; then
        run_typescript
    fi

    echo "=== Summary ==="
    if [[ "$OVERALL_EXIT" -eq 0 ]]; then
        echo "Mutation gate PASSED (score >= ${THRESHOLD}%)."
    else
        echo "Mutation gate FAILED. Surviving mutants or score below ${THRESHOLD}%."
    fi
    exit "$OVERALL_EXIT"
}

main "$@"
