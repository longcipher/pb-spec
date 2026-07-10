---
name: pb-merge-conflicts
description: Use when you need to resolve an in-progress git merge/rebase conflict. Guides systematic resolution preserving both intents where possible.
---

# pb-merge-conflicts

Resolve merge/rebase conflicts systematically. Always resolve; never `--abort`.

## Process

### 1. See the current state

Check git history, and the conflicting files:

```bash
git status
git log --oneline -5
```

Identify whether this is a merge or a rebase, and which files have conflicts.

### 2. Find the primary sources for each conflict

For each conflicting file, understand deeply why each change was made:

- Read the commit messages from both sides
- Check PRs or issue references if available
- Understand the original intent behind each change

### 3. Resolve each hunk

For each conflict marker (`<<<<<<<`, `=======`, `>>>>>>>`):

- Preserve both intents where possible
- Where incompatible, pick the one matching the merge's stated goal and note the trade-off
- Do **not** invent new behaviour
- Always resolve; never `--abort`

### 4. Run automated checks

Discover the project's automated checks and run them — typically typecheck, then tests, then format:

```bash
uv run ruff check
uv run ty check
uv run pytest
```

Fix anything the merge broke.

### 5. Finish the merge/rebase

Stage everything and commit. If rebasing, continue the rebase process until all commits are rebased:

```bash
git add -A
git commit  # or git rebase --continue
```

## Red Flags

- `git merge --abort` or `git rebase --abort` without trying to resolve
- Picking one side without understanding the other's intent
- Skipping automated checks after resolving
- Inventing new behavior that neither side intended

## Integration with pb-spec

- **During pb-build:** If a task causes merge conflicts with concurrent work, use this skill
- **Standalone:** Use for any merge/rebase conflict
