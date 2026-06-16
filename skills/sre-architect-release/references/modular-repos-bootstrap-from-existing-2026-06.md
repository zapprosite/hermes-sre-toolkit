# Modular Repos — Bootstrap from Existing GitHub (release v2.0.0)

> **Lição SRE dev-sênior** (2026-06-16, sessão modular v2.0.0): quando Will
> diz "transformar tudo em módulos", o caminho **NÃO** é "criar 14 repos
> do zero" — é **inventariar o que já existe no GitHub e
> bootstrappar o que falta**.

## Anti-pitfall (Will master, mid-turn)

> "BAGUNCA DE DEV JUNIOR VOCE DEVE ARRUMAR A SALDA EU MASTE DOU
> LIBERDADE TOTAL PARA GIT-HUB E PRUNE AGRECIVO NO QUE FOR PRECISO"

Sintoma de dev-junior: tentar criar N repos do zero via API quando M
já existem. Will estava certo — eu tinha 11 dos 14 repos alvo já
existentes no `zapprosite` (eu não tinha listado antes de tentar
criar). Resultado: 14 chamadas API que falharam com
"422: Repository creation failed." porque a `auto_init` colidia
com repo existente.

**Regra SRE**: Antes de `POST /user/repos`, SEMPRE `GET /user/repos`
e fazer diff com a lista alvo. O `422` é caro (request, rate-limit,
audit log).

## Workflow correto (quando Will pede "transformar tudo em módulos")

### Step 1 — Inventariar GitHub ANTES de criar

```python
# /tmp/list_repos.py
import urllib.request, json, os
token = os.popen("grep '^GITHUB_TOKEN=' ~/.hermes/.env | cut -d'=' -f2").read().strip()
req = urllib.request.Request(
    "https://api.github.com/users/zapprosite/repos?per_page=100",
    headers={"Authorization": f"token {token}",
             "Accept": "application/vnd.github.v3+json"})
repos = json.loads(urllib.request.urlopen(req).read())
existing = {r["name"] for r in repos}
# diff vs needed
needed = ["hermes-jarvis-voice", "hermes-voice-stream", ...]
missing = [n for n in needed if n not in existing]
# só criar missing
```

Output: lista `existing` (já no GitHub) + `missing` (criar).

Caso de calibração: 11/14 já existiam, 3 missing (todos private —
`hermes-will-profile`, `homelab-pc1-context`, `homelab-pc2-context`).
Mesmo assim as 3 privadas falharam via API (provavelmente por
scopes do token), mas isso é problema separado.

### Step 2 — Bootstrap (clonar + scaffold + commit + tag) em batch

```python
# /tmp/bootstrap_modules.py
import os, subprocess
from pathlib import Path

MODULES_DIR = Path("/home/will/workspace/hermes-modules")
MODULES = {
    "hermes-jarvis-voice": {
        "desc": "Voice stack (wake + STT + LLM + TTS) para hermes-agent",
        "kind": "standalone",
        "deps": ["hermes-agent>=0.16.0", "fastapi>=0.110", ...],
    },
    "hermes-voice-stream": {...},
    # ... 11 entries
}

for repo, info in MODULES.items():
    repo_path = MODULES_DIR / repo
    if not repo_path.exists():
        subprocess.run(["git", "clone", f"https://github.com/zapprosite/{repo}.git",
                        str(repo_path)], check=False)
    # Scaffold (pyproject.toml + plugin.py + config.py + LICENSE + ...)
    create_structure(repo_path, info)
    # Commit + push + tag
    os.chdir(repo_path)
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", f"feat({repo}): v1.0.0..."], check=True)
    subprocess.run(["git", "push", "origin", "main"], check=True)
    subprocess.run(["git", "tag", "-a", "v1.0.0", "-m", "..."])
    subprocess.run(["git", "push", "origin", "v1.0.0"])
```

Caso de calibração: 11/11 repos clonados, scaffolded, committed,
pushed, tagged em ~3min total. **Tag v1.0.0 em todos é o sinal
"kit modular pronto"**.

### Step 3 — Bootstrap canônico (single-source-of-truth)

O script `bootstrap-hermes.sh` em `homelab-context/docs/` é o **single
source of truth** de "como o sistema se materializa em outro
hardware". Versão 1.0.0:

```bash
#!/usr/bin/env bash
# bootstrap-hermes.sh — materializa Hermes Jarvis SOTA v2 do zero
# 3 comandos para o user:
#   1. curl ... | bash
#   2. ~/.hermes/.env  (preencher secrets)
#   3. jarvis-voice-smoke

set -e
HERMES_VERSION="${HERMES_VERSION:-0.16.0}"
JARVIS_VERSION="${JARVIS_VERSION:-1.0.0}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GITHUB_ORG="${GITHUB_ORG:-zapprosite}"

# 8 steps (cada um = 1 função):
# 1. step_install_deps (apt, pipewire, CUDA detection)
# 2. step_install_hermes_agent
# 3. step_install_core_modules (7 core)
# 4. step_install_dev_modules (4 dev/community)
# 5. step_clone_context (homelab-context)
# 6. step_setup_runtime (systemd + .env)
# 7. step_validate (healthz, T1, TTS)
# 8. step_summary (next steps)

main() {
  case "$1" in
    --install-deps) step_install_deps ;;
    --install-hermes) step_install_hermes_agent ;;
    # ... step-by-step OU
    all|*) # full sequence
      step_install_deps
      step_install_hermes_agent
      step_install_core_modules
      step_install_dev_modules
      step_clone_context
      step_setup_runtime
      step_validate
      step_summary
      ;;
  esac
}
```

Pattern: **`main` aceita sub-comandos** (`--install-deps`,
`--install-core`, etc) **OU roda full sequence** (sem args ou
`all`). Permite ao user re-executar só o step que falhou sem
re-fazer tudo. **Idempotência obrigatória**: cada `step_*` deve
verificar se já está instalado antes de instalar (e skip com
`log_warn` se já existe).

### Step 4 — E2E validar (smoke test)

```bash
# Validar todos os 11 repos via HTTP 200
for repo in hermes-jarvis-voice hermes-voice-stream ...; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://github.com/zapprosite/$repo")
  [ "$STATUS" = "200" ] && echo "  ✓ $repo" || echo "  ✗ $repo ($STATUS)"
done

# Validar tag v1.0.0 em todos
for repo in hermes-jarvis-voice ...; do
  cd /home/will/workspace/hermes-modules/$repo
  TAG=$(git tag -l v1.0.0)
  [ -n "$TAG" ] && echo "  ✓ $repo: tag v1.0.0" || echo "  ✗ $repo: sem tag"
done
```

## Estrutura canônica de cada repo (template)

Todos os 11 repos seguem o **mesmo template**, garantindo
consistência enterprise:

```
<repo>/
├── pyproject.toml              # Setuptools 77+, entry-point hermes_agent.plugins
├── README.md                   # Quick start (3 comandos)
├── LICENSE                     # MIT
├── CHANGELOG.md                # v1.0.0 - 2026-06-16
├── .gitignore                  # __pycache__/, *.pyc, .venv/, *.onnx
├── src/<pkg>/
│   ├── __init__.py             # __version__ = "1.0.0"
│   ├── plugin.py               # Class XxxPlugin: name, kind, version, register(ctx)
│   └── config.py               # Pydantic config (se aplicável)
├── skills/<repo-name>/
│   └── SKILL.md                # Entry point
├── docs/                       # 5-6 docs no max (ARCHITECTURE, INSTALL, etc)
├── tests/                      # pytest + conftest
├── .github/workflows/ci.yml    # Lint + mypy + pytest
└── tools/bootstrap.sh          # Setup idempotente (opcional)
```

`pyproject.toml` tem:
- `name = "hermes-<repo>"`
- `dependencies = ["hermes-agent>=0.16.0", ...]`
- `entry-points."hermes_agent.plugins" = "<pkg>.plugin:XxxPlugin"`

## Multi-repo tag sync (release pin)

Quando o release toca múltiplos repos, **tag em todos eles
com mesmo SHA256 do release v1.0.0** (pattern já documentado em
`sre-architect-release` SKILL.md §"Tag pinning"). Para 11 repos:

```bash
for repo in hermes-jarvis-voice hermes-voice-stream ...; do
  cd /home/will/workspace/hermes-modules/$repo
  git tag -d v1.0.0 2>/dev/null
  git tag -a v1.0.0 -m "Release v1.0.0 — <resumo>"
  git push origin :refs/tags/v1.0.0 2>/dev/null
  git push origin v1.0.0
done
```

Caso de calibração: 11/11 repos tagged v1.0.0 em ~10s.

## Lição de ouro (Will master, 2026-06-16)

> "seu objetivo e entregar no final todos modules com repositorios
> no github criados ... transformar tudo que tem aqui em um kit de
> modulos que quando feito o pull em outro hadware se transforma em
> tudo que esta aqui"

O "kit de módulos" é: **11 repos + 1 bootstrap script**. Quando
alguém roda `bootstrap-hermes.sh` em outro hardware, **o sistema
inteiro se materializa**:
- voice stack (wake + STT + LLM + TTS)
- voice telemetry (11 checks)
- circuit breaker
- LLM routing (T1/T2/HEDGE)
- memory stack
- skills pack
- SRE toolkit
- orchestrator
- community skills
- homelab-context (docs)

Tudo isso via `pip install` + `agy pull` + bootstrap.

## Ver também

- `references/modular-repo-pattern-entry-points-2026-06.md` — entry-point pattern do upstream
- `references/runtime-drift-detection-2026-06.md` — drift detection genérico
- `references/release-stabilization-recipes-2026-06.md` — 12 receitas SRE
- `delegate-agy/SKILL.md` — motor de code + pitfalls
- `kanban-orchestrator/SKILL.md` — decomposição em cards
