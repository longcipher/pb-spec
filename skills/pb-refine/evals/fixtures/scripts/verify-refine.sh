#!/bin/bash
# Judge for pb-refine: incremental edit, revision history, completed task preserved, source untouched.
set -u
fail() { echo "FAIL: $1"; exit 1; }

dir=$(ls -d specs/2026-10-21-01-calculator-power 2>/dev/null | head -1)
[ -n "$dir" ] || fail "spec directory specs/2026-10-21-01-calculator-power not found"
design="$dir/design.md"
tasks="$dir/tasks.md"
[ -f "$design" ] && [ -f "$tasks" ] || fail "design.md/tasks.md missing"

# Behavior change must reach the test-matrix section first.
grep -q "math.pow" "$design" || fail "design.md does not mention math.pow / float exponent behavior"

# Revision history entry appended.
grep -qi "Revision History" "$design" || fail "design.md missing Revision History"

# Completed task preserved (Task 1 was DONE before the feedback).
grep -q "Task 1" "$tasks" || fail "Task 1 disappeared from tasks.md"
grep -q "🟢 DONE" "$tasks" || fail "completed task status was modified"

# New or updated work is re-opened as TODO, not silently marked done.
grep -q "🔴 TODO" "$tasks" || fail "no TODO task reflects the new float-exponent work"

# Read-only constraint: no tracked file under src/ or tests/ modified (-uno ignores untracked fixtures).
dirty=$(git status --porcelain -uno -- src tests 2>/dev/null)
[ -z "$dirty" ] || fail "source code was modified: $dirty"

echo "PASS: incremental refine OK (contract updated, history added, DONE task preserved, source untouched)"
