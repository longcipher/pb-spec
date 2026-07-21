---
name: pb-branch-finalization
description: Use when implementation is complete and tests pass, or when a merge/rebase conflict is in progress. Resolves in-progress git merge/rebase conflicts preserving both intents, then guides branch integration (merge / PR / squash / cleanup).
---

# pb-branch-finalization

## Role

You close out a feature branch. First resolve any in-progress conflicts, then decide how to integrate the work.

## Part I — Resolving Merge / Rebase Conflicts

### Core Principle

Both intents matter. Do not blindly prefer "ours" or "theirs". Understand what each side was trying to do, then find a resolution that preserves both intents where possible.

### Workflow

1. `git status` — identify conflicted files and the operation in progress (merge / rebase / cherry-pick).
2. For each conflicted file, read the three versions: ours, theirs, base.
3. Classify the conflict:
   - **Mechanical** (formatting, import order, both sides identical) → pick one, run formatter.
   - **Additive** (both sides add different things) → union both, ensure no duplicate logic.
   - **Semantic** (both sides change the same logic differently) → understand both intents, write a resolution that preserves both behaviors or escalate to user.
4. Apply resolution, `git add <file>`, continue the operation (`git merge --continue` / `git rebase --continue`).
5. Run full verification (`just test` or equivalent) before proceeding.

### Common Anti-Patterns

- `git checkout --ours .` / `git checkout --theirs .` (blind preference).
- Resolving without reading all three versions.
- Skipping verification after resolution.
- Using `git mergetool` without understanding the diff.

### Abort

- If the conflict is semantic and the two intents are genuinely incompatible, STOP and ask the user. Do not guess.
- `git merge --abort` / `git rebase --abort` to return to pre-conflict state.

## Part II — Integrating the Branch

### Pre-Integration Checklist

- All tests pass: `just test` (or equivalent).
- Lint passes: `just lint`.
- Type-check passes: `just type-check`.
- BDD passes: `just bdd`.
- Working tree clean: `git status` shows no uncommitted changes.
- Branch is up to date with remote (if applicable): `git pull --rebase`.

### Integration Options

Present these options to the user. Do NOT auto-merge without explicit approval.

1. **Merge to main** — `git checkout main && git merge --no-ff <branch>` (preserves branch history).
2. **Squash and merge** — `git checkout main && git merge --squash <branch> && git commit` (collapses to one commit).
3. **Rebase and merge** — `git checkout main && git rebase <branch>` (linear history).
4. **Create PR** — `git push -u origin <branch>` then open a PR (do not push to main directly).
5. **Cleanup only** — delete the branch locally and remotely after merge: `git branch -d <branch> && git push origin --delete <branch>`.

### Choice Heuristics

- Short feature branch (≤5 commits, single concern) → squash and merge.
- Long-lived feature branch with meaningful commit history → merge with --no-ff.
- Trivial fix (1 commit) → rebase and merge for linear history.
- Collaborative branch (multiple contributors) → create PR for review.
- Never force-push to main/master.

### Post-Integration

- Run full verification on main: `just test-all`.
- Delete the local and remote branch (if not a PR).
- Update the spec's status in `specs/<spec-dir>/design.md` Metadata table to `Merged` or `Released`.

## Key Principles

1. Both intents matter in conflicts — understand before resolving.
2. Never blindly prefer ours/theirs.
3. Run full verification after every resolution and every integration.
4. Never auto-merge without explicit user approval.
5. Never force-push to main/master.

## Constraints

- Never use `git push --force` to main/master. Warn the user if they request it.
- Never run destructive git commands (`reset --hard`, `clean -f`, `branch -D`) unless the user explicitly requests.
- Never commit unless the user explicitly asks.
- If pre-integration verification fails, STOP and report — do not proceed to integration.

## Stopping Conditions

- Semantic conflict that can't be resolved without user input → STOP and ask.
- Pre-integration verification fails → STOP and report.
- User asks to force-push to main → STOP and warn.
