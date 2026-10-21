#!/bin/bash
# Judge for pb-plan: a clear requirement must yield a complete spec and zero source changes.
set -u
fail() { echo "FAIL: $1"; exit 1; }

design=$(ls specs/*/design.md 2>/dev/null | head -1)
[ -n "$design" ] || fail "no specs/*/design.md found"
tasks="${design%design.md}tasks.md"
[ -f "$tasks" ] || fail "tasks.md missing next to design.md"

for section in "Summary" "Approach" "Architecture Decisions" "TDD & Mutation Testing Strategy" "Verification"; do
  grep -q "$section" "$design" || fail "design.md missing required section: $section"
done

for field in "Context:" "Verification:" "Status:" "Test Coverage:"; do
  grep -q "$field" "$tasks" || fail "tasks.md missing required field: $field"
done

grep -q "power" "$design" || fail "design.md does not cover the requested power function"
grep -q "hypothesis\|property\|property test\|Property" "$design" "$tasks" || fail "test matrix has no property-test layer"

# Decision protocol: an unambiguous requirement must not end in a clarification request.
for phrase in "Could you clarify" "please clarify" "Which option" "How would you like" "Should I proceed"; do
  case "$EVAL_FINAL_MESSAGE" in
    *"$phrase"*) fail "agent asked a clarification question for an unambiguous requirement: $phrase" ;;
  esac
done

# Read-only constraint: no tracked file under src/ or tests/ modified.
# -uno: fixtures are untracked (git init without initial commit), ignore them.
dirty=$(git status --porcelain -uno -- src tests 2>/dev/null)
[ -z "$dirty" ] || fail "source code was modified: $dirty"

echo "PASS: spec complete (design sections + 4-field tasks), source untouched, no unnecessary question"
