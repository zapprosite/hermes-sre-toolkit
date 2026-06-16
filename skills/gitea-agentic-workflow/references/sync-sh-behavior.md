# sync.sh — Behavior and Failure Modes (2026-05-27)

## What sync.sh actually does

1. **Always generates CLAUDE.md first** — even if Gitea is down, the local commit succeeds
2. **Always attempts local `git add` and `git commit`** — this step is NOT blocked by Gitea being down
3. **`--mirror-only` then tries to push to BOTH remotes** (Gitea primary + GitHub mirror)
4. **Gitea failure does NOT block GitHub push** — mirror-only continues to push to GitHub even when Gitea fails

## Failure pattern

```
✓ CLAUDE.md gerado
✓ Sem mudanças staged para commit
fatal: não foi possível acessar 'http://100.87.53.54:3000/...': Failed to connect
```

**This is NOT a commit failure** — the commit is already local. The failure is ONLY at the Gitea push step.

## GitHub fallback always works

When Gitea is down:
```bash
git push github  # pushes to GitHub mirror even when Gitea is down
git push origin  # fails (Gitea is down)
```

GitHub (origin or github remote) is always reachable when Gitea local is not.

## When to use --mirror-only

- After any significant commit to local repo
- Before opening PR (syncs both remotes)
- After PR merge (syncs state to Gitea mirror)

## When Gitea is down and local commits exist

Use git bundle as preservation strategy:
```bash
git bundle create backups/jarvis-backend-$(date +%Y%m%d).bundle --all
git bundle verify backups/jarvis-backend-20260527.bundle
```

## Session context

During `jarvis-next-shell` branch `agent/jarvis-backend-hardening` validation (2026-05-27):
- Backend refactoring complete, committed to local branch
- `./sync.sh --mirror-only` run at end of session to push to Gitea
- Gitea was reachable at that moment — sync succeeded to both remotes
- Branch remains open awaiting PR human review per GitOps policy