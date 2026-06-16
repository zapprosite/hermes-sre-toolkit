# Gitea Repo Audit — 2026-05-23

## What Was Found

**Container**: `gitea/gitea:1.26.2`, healthy, exposed at `100.87.53.54:3000` + `2222->22`.

**Docker network**: `172.17.0.1` (docker0 bridge), container internal `172.17.0.x:3000`.

**Gitea API search** (public, no auth): `GET /api/v1/repos/search?limit=50` returns `{"ok": true, "data": []}` — empty instance.

**Credentials tested** (from `~/.git-credentials`):
- `http://hermes-agent:***@100.87.53.54%3a3000` → API returns `invalid username, password or token`
- `http://hermes-agent:***@localhost:3000` → connection refused (different binding)

**Two repos found inside container** (`/data/git/repositories/hermes-agent/`):
```
hermes-agent/hermes-agent.git   (bare, created May 20)
hermes-agent/.hermes.git        (bare, created May 21)
```

**`hermes-agent.git`** — git log shows active dev commits:
- `496115cd` — fix(delegation): ignore unresolved endpoint placeholders
- `faf50101` — feat(delegation): apply architect fan-out policy
- Branches: `agent/stage-director-showcase`, `agent/voice-jarvis-queue`, `main`
- This repo was tracking Gitea (origin remote = Gitea), not upstream Nous Research

**`.hermes.git`** — git log:
- `9dc7779` — Merge PR #1 agent/hermes-secretaria-brain-guardrails
- One branch merged, no active development

**Gitea app.ini flags**:
| Flag | Value | Note |
|------|-------|------|
| DISABLE_SSH | false | SSH port 2222 exposed |
| DISABLE_REGISTRATION | false | Open self-registration |
| REQUIRE_SIGNIN_VIEW | false | Public read |
| INSTALL_LOCK | true | Setup locked |
| REVERSE_PROXY_TRUSTED_PROXIES | `*` | ⚠️ Any IP can spoof |
| ROOT_URL | `http://100.87.53.54:3000/` | HTTP only |

**Users in Gitea** (from gitea.db):
- `will` / `will@local`
- `hermes-agent` / `agent@local`

## Root Cause of Duplication

The `hermes-agent/` clone at `~/.hermes/hermes-agent/` had `origin` remote pointing to Gitea instead of GitHub (`https://github.com/NousResearch/hermes-agent`). This caused the local clone to track Gitea, not the upstream.

Two agent workflows created repos on consecutive days:
- May 20: `hermes-agent.hermes-agent.git` (active dev)
- May 21: `hermes-agent..hermes.git` (config merge)

Neither repo is useful as a Gitea mirror. The `hermes-agent.git` is a duplicate of the upstream that should live on GitHub. The `.hermes.git` is config that lives in `homelab-context` on GitHub.

## Audit Commands Run

```bash
docker exec gitea bash -c "ls -la /data/git/repositories/"
docker exec gitea bash -c "ls /data/git/repositories/hermes-agent/"
docker exec gitea bash -c "find /data/git/repositories -name '*.git' | sort"
docker exec gitea bash -c "git --git-dir=/data/git/repositories/hermes-agent/hermes-agent.git log --oneline -20"
docker exec gitea bash -c "git --git-dir=/data/git/repositories/hermes-agent/.hermes.git log --oneline -10"
docker exec gitea bash -c "git --git-dir=/data/git/repositories/hermes-agent/hermes-agent.git branch -a"
docker exec gitea bash -c "cat /data/gitea/conf/app.ini | grep -E 'DISABLE|REQUIRE|INSTALL|ROOT|PROXY'"
docker exec gitea bash -c "ls /data/git/repositories/hermes-agent/hermes-agent.git/"
```

## Audit Template (reusable)

```bash
# Container alive?
docker ps | grep gitea

# API public probe
curl -s "http://100.87.53.54:3000/api/v1/repos/search?limit=50"

# Credential test
curl -s "http://hermes-agent:TOKEN@100.87.53.54:3000/api/v1/user"

# Docker exec — full repo listing
docker exec gitea bash -c "find /data/git/repositories -type d -name '*.git' | sort"

# Docker exec — git log per repo
docker exec gitea bash -c "for r in /data/git/repositories/hermes-agent/*.git; do echo === \$r; git --git-dir=\$r log --oneline -5 2>/dev/null; done"

# Docker exec — config flags
docker exec gitea bash -c "cat /data/gitea/conf/app.ini | grep -E 'DISABLE|REQUIRE|INSTALL|ROOT|PROXY'"

# Docker exec — active branches
docker exec gitea bash -c "git --git-dir=/data/git/repositories/hermes-agent/hermes-agent.git branch -a 2>/dev/null"
```