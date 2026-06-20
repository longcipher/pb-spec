---
name: pb-finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---

# pb-finishing-a-development-branch

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Present options → Execute choice → Clean up.

## The Process

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**

```bash
uv run pytest
uv run ruff check
uv run ty check
```

**If tests fail:**

```text
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 2.

### Step 2: Present Options

```text
Implementation complete. What would you like to do?

1. Commit changes locally
2. Push and create a Pull Request
3. Keep working (I'll handle it later)
4. Discard this work

Which option?
```

### Step 3: Execute Choice

#### Option 1: Commit Locally

```bash
git add <files>
git commit -m "feat: <description>"
```

#### Option 2: Push and Create PR

```bash
# Detect remote platform
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

# Push branch
git push -u origin <branch>

# Create PR/MR based on platform
if echo "$REMOTE_URL" | grep -q "github.com"; then
  gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
elif echo "$REMOTE_URL" | grep -q "gitlab"; then
  glab mr create --title "<title>" --description "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
else
  echo "Pushed branch. Create a merge request manually on your platform."
fi
```

#### Option 3: Keep As-Is

Report: "Keeping branch. Changes are ready for you to handle."

#### Option 4: Discard

**Confirm first:**

```text
This will permanently discard uncommitted changes.

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:

```bash
git checkout -- .
git clean -fd
```

## Red Flags

**Never:**

- Proceed to Step 2 with failing tests
- Commit without running verification
- Skip the confirmation step for discard
- Force-push without explicit user consent
- Create PR with incomplete test plan

**Always:**

- Run full verification before presenting options
- List all files that will be committed
- Show the diff before committing
- Confirm destructive actions (discard, force-push)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Committing with lint warnings | Fix warnings first, or acknowledge explicitly |
| Skipping type check | `uv run ty check` is mandatory |
| Vague commit messages | Use conventional commits: `feat:`, `fix:`, etc. |
| PR without test plan | Include verification steps in PR body |
| Discarding without confirming | Always require explicit confirmation |

## Quick Reference

| Option | Commit | Push | Cleanup |
|--------|--------|------|---------|
| 1. Commit locally | yes | - | - |
| 2. Create PR | - | yes | - |
| 3. Keep as-is | - | - | - |
| 4. Discard | - | - | yes (force) |

## Integration with pb-spec

- **pb-build final step:** After all tasks complete, use this skill to finalize
- **Standalone:** Use for any development completion need
