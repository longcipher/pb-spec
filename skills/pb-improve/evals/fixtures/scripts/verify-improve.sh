#!/bin/bash
# Judge for pb-improve: specs produced with evidence, source strictly untouched, no commits.
set -u
fail() { echo "FAIL: $1"; exit 1; }

# A spec directory with design.md + tasks.md exists.
design=$(ls specs/*/design.md 2>/dev/null | head -1)
[ -n "$design" ] || fail "no specs/*/design.md found"
tasks="${design%design.md}tasks.md"
[ -f "$tasks" ] || fail "tasks.md missing next to design.md"

# Spec is pb-plan compatible: 4-field tasks.
for field in "Context:" "Verification:" "Status:" "Test Coverage:"; do
  grep -q "$field" "$tasks" || fail "tasks.md missing required field: $field"
done

# Findings carry evidence (file:line references).
grep -qE "src/[a-z_/]+\.py:[0-9]+|src/calculator/__init__.py" "$design" || fail "design.md findings lack file:line evidence"

# The seeded divide-by-zero bug (or an equivalent correctness finding) surfaced.
grep -qi "divide" "$design" || fail "seeded divide bug not surfaced as a finding"

# Strictly read-only: no tracked file modified (-uno ignores untracked fixtures and new specs/).
dirty=$(git status --porcelain -uno 2>/dev/null | grep -v "specs/" || true)
[ -z "$dirty" ] || fail "files outside specs/ were modified: $dirty"

# No commits.
commits=$(git rev-list --count HEAD 2>/dev/null || echo 0)
[ "$commits" -le 1 ] || fail "agent made git commits (forbidden)"

echo "PASS: specs produced with evidence, source untouched, no commits"
