# Modular Repo Pattern — Hermeticidade via Entry-Points Python

> **Versão**: 1.0.0 · **Data**: 2026-06-16
> **Caso de calibração**: Release v2 modular do Hermes Jarvis (SRE dev-senior)

## TL;DR

O `hermes-agent` v0.16.0 (Nous Research) tem **4 fontes de descoberta de
plugin** + **5 kinds de plugin** + **5 entry-points do Python package**.
**Qualquer modularização que NÃO usa entry-points está fadada a
bifurcação do repo (fork) ou acoplamento manual.**

A receita aqui transforma modificações locais (que ficavam em
`~/.hermes/`, `homelab-context/`, `hermes-agent-next/`) em **7 repos
separados** que coexistem com o upstream **sem fork**.

## 1. As 4 fontes de plugin (do `hermes_cli/plugins.py`)

1. **Bundled plugins** — `<repo>/plugins/<name>/` (shipped com
   `hermes-agent`).
2. **User plugins** — `~/.hermes/plugins/<name>/`.
3. **Project plugins** — `./.hermes/plugins/<name>/` (opt-in via
   `HERMES_ENABLE_PROJECT_PLUGINS`).
4. **Pip plugins** — packages que expõem o
   `hermes_agent.plugins` entry-point group (este é o caminho
   **enterprise**).

**Ordem de precedência**: Later sources override earlier. User/project
plugin com mesmo nome que bundled **substitui** o bundled.

**Cada plugin** = `plugin.yaml` manifest + `__init__.py` com
`register(ctx)`.

## 2. Os 5 kinds de plugin

| Kind | Uso | Caso |
|---|---|---|
| `standalone` | Hooks/tools próprios, opt-in | `jarvis-voice`, `orchestrator` |
| `backend` | Pluggable backend de um core tool existente | `image_gen`, `model-providers` |
| `exclusive` | Categoria com exatamente 1 provider ativo | `memory` (Honcho vs Qdrant vs local) |
| `platform` | Adapter de plataforma de messaging | `telegram`, `discord`, `slack` |
| `model-provider` | LLM provider | `anthropic`, `gemini`, `openai` |

## 3. Os 5 entry-points do Python package

```toml
# pyproject.toml
[project.entry-points."hermes_agent.plugins"]
jarvis_voice = "jarvis_voice.plugin:VoicePlugin"
```

Quando o `hermes-agent` v0.16+ faz `import hermes_agent`, descobre
automaticamente via `importlib.metadata`. **Sem código adicional no
upstream**, **sem fork**, **sem monkey-patch**.

Para 7+ skill packs adicionais, basta criar 7 packages com
entry-points diferentes:

```toml
# hermes-memory-stack/pyproject.toml
[project.entry-points."hermes_agent.plugins"]
memory_stack = "hermes_memory.plugin:MemoryPlugin"

# hermes-skills-pack/pyproject.toml
[project.entry-points."hermes_agent.plugins"]
refrimix_skills = "hermes_refrimix_skills.plugin:RefrimixSkillsPlugin"

# hermes-community-skills/pyproject.toml
[project.entry-points."hermes_agent.plugins"]
community_skills = "hermes_community_skills.plugin:CommunitySkillsPlugin"

# hermes-orchestrator/pyproject.toml
[project.entry-points."hermes_agent.plugins"]
orchestrator = "hermes_orchestrator.plugin:OrchestratorPlugin"

# hermes-sre-toolkit/pyproject.toml
[project.entry-points."hermes_agent.plugins"]
sre_toolkit = "hermes_sre.plugin:SREPlugin"

# hermes-will-profile/ (private, não é plugin mas é loadable)
# Usa symlinks: ~/.hermes/AGENTS.md -> ~/.hermes/Will/AGENTS.md
```

**Hermes-agent descobre todos** ao iniciar. Cada um chama
`register(ctx)` no `__init__`. **Zero coupling entre packages**.

## 4. O padrão Plugin class

```python
"""jarvis_voice/plugin.py — entry-point do hermes-agent."""
from __future__ import annotations
import logging
from hermes_cli.plugins import PluginContext

log = logging.getLogger("jarvis_voice")


class VoicePlugin:
    """Jarvis voice stack como plugin hermes-agent."""

    name = "jarvis-voice"
    kind = "standalone"
    version = "1.0.0"
    description = "Jarvis-like voice stack (OWW + STT + LLM + TTS) com telemetria SRE"
    config_class = "jarvis_voice.config:VoiceConfig"

    def register(self, ctx: PluginContext) -> None:
        # 1. Tools (expostos ao agent loop)
        ctx.register_tool("voice_status", self._tool_voice_status)
        ctx.register_tool("voice_calibrate", self._tool_calibrate)
        ctx.register_tool("voice_toggle", self._tool_toggle)

        # 2. Skills (knowledge pack)
        for skill in self._discover_skills():
            ctx.register_skill(skill.name, skill.path)

        # 3. Hooks de ciclo de vida
        ctx.register_hook("pre_session", self._on_pre_session)
        ctx.register_hook("post_session", self._on_post_session)

        # 4. Service systemd (opcional, idempotente)
        if self.config.telemetry_enabled and not self._service_running():
            self._install_systemd_unit()
            self._enable_service()

        log.info("jarvis-voice v%s registrado", self.version)

    def _discover_skills(self):
        """Descobre skills em skills/<name>/SKILL.md."""
        from pathlib import Path
        skills_dir = Path(__file__).parent.parent.parent / "skills"
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            yield type("Skill", (), {"name": p.parent.name, "path": p})()
```

## 5. Padrão pyproject.toml

```toml
[build-system]
requires = ["setuptools>=77.0,<83"]
build-backend = "setuptools.build_meta"

[project]
name = "hermes-<repo>"
version = "1.0.0"
description = "<1-line description>"
readme = "README.md"
requires-python = ">=3.11,<3.14"
authors = [{ name = "Will Zapprosite" }]
license = "MIT"
license-files = ["LICENSE"]

# Runtime dependencies (apenas o que o código REALMENTE usa)
dependencies = [
  "hermes-agent>=0.16.0",
  # ... outras deps REAIS
]

[project.optional-dependencies]
dev = ["pytest>=9.0", "pytest-asyncio>=0.23", "mypy>=1.10", "ruff>=0.6"]

[project.scripts]
<repo>-bootstrap = "<package>.cli:bootstrap"
<repo>-smoke = "<package>.cli:smoke"

# Entry-point do plugin
[project.entry-points."hermes_agent.plugins"]
<repo> = "<package>.plugin:VoicePlugin"

[tool.setuptools.packages.find]
where = ["src"]
```

## 6. Padrão de testes

```
tests/
├── conftest.py                # Fixtures compartilhados
├── test_plugin.py             # Valida register(ctx)
├── test_config.py             # Valida Pydantic config
├── test_e2e.py                # E2E (se aplicável)
└── audio/                     # Audio fixtures (.ogg, .wav)
```

**Regra SRE**: cada test deve falhar sem o serviço que testa (TDD real).
Audio fixtures commitados (pequenos < 1MB).

## 7. Padrão de docs

```
docs/
├── ARCHITECTURE.md           # SSoT técnico (10-50 páginas)
├── INSTALL.md                # Guia de 3 comandos (5-10 páginas)
├── CONFIG.md                 # Todas as env vars (5-15 páginas)
├── TROUBLESHOOTING.md        # Problemas comuns (5-10 páginas)
└── CHANGELOG.md              # Version history
```

**Máximo 6 docs** por repo. Cada doc tem TL;DR no topo.

## 8. Padrão de CI (GitHub Actions)

```yaml
# .github/workflows/ci.yml
- name: Lint
  run: ruff check src/
- name: Type check
  run: mypy src/
- name: Test
  run: pytest tests/ -v
- name: Smoke
  run: <repo>-smoke
- name: Build
  run: python -m build

# .github/workflows/publish.yml
- on: push: tags: ['v*']
- run: |
    pip install build twine
    python -m build
    twine upload dist/*

# .github/workflows/release.yml
- on: push: tags: ['v*']
- uses: softprops/action-gh-release@v1
```

## 9. Os 7 Repos (caso de calibração: release v2 modular)

| # | Repo | Kind | Skills | Status |
|---|---|---|---|---|
| 0 | `NousResearch/hermes-agent` | upstream | 18 bundled | não modificar |
| 1 | `hermes-jarvis-voice` | standalone | 1 (jarvis-voice) | doc BLUEPRINT pronto |
| 2 | `hermes-memory-stack` | exclusive | 8 (Honcho+Qdrant+context) | pendente |
| 3 | `hermes-skills-pack` | standalone | 9 (Refrimix+social) | pendente |
| 4 | `hermes-community-skills` | standalone | ~70 (community) | pendente |
| 5 | `hermes-orchestrator` | standalone | 8 (agy+kanban) | pendente |
| 6 | `hermes-sre-toolkit` | standalone | 10 (sre-*) | pendente |
| 7 | `hermes-will-profile` | private | 0 (SOUL.md only) | pendente |

**Total**: 7 packages + 1 upstream, todos com entry-points
`hermes_agent.plugins` separados.

## 10. Como reproduzir em outro hardware (8 steps, ~30min)

```bash
# 1. Upstream
pip install hermes-agent==0.16.0
agy --version  # 0.16.0

# 2. Core
pip install hermes-jarvis-voice hermes-memory-stack hermes-skills-pack

# 3. Community + dev
pip install hermes-community-skills hermes-orchestrator hermes-sre-toolkit

# 4. Will's profile (private)
git clone git@github.com:willzapprosite-private/hermes-will-profile.git ~/.hermes

# 5. Secrets
cp ~/.hermes/.env.example ~/.hermes/.env
# Preencher: OPENAI_API_KEY, ANTHROPIC_API_KEY, HONCHO_API_KEY, etc

# 6. Validar
agy pull jarvis-voice
jarvis-voice-bootstrap
jarvis-voice-smoke  # 11/11 checks

# 7. Ativar
systemctl --user start voice-telemetry.service
hermes voice status --json  # readiness: OK

# 8. Testar
hermes chat -q "oi Jarvis, que horas são?"
```

## 11. Por que entry-points > fork (lição SRE)

| Aspecto | Fork | Entry-points |
|---|---|---|
| **Manutenção** | Atrasada em N dias quando upstream atualiza | Zero atraso |
| **Compatibilidade** | Quebrada com upgrade | Pinada em `>= 0.16.0` |
| **Distribuição** | Manual via `git clone` | `pip install` |
| **Versionamento** | Manual | CalVer semântico |
| **Reversibilidade** | `git reset --hard` | `pip uninstall` |
| **Upstream fixes** | Demora merge | Automático |
| **Customização** | Total (pode quebrar) | Imediata (entry-point) |
| **Testes upstream** | Quebrados | Continua passando |

**Conclusão SRE**: para qualquer modularização de `~/.hermes/` em repos
separados, **SEMPRE usar entry-points Python**, nunca fork.

## 12. Pendências (caso de calibração: 2026-06-16)

- [ ] Will cria 7 repos vazios no GitHub
- [ ] Despachar implementação via agy-pr (5-10 commits cada)
- [ ] Publicar Test PyPI → smoke em VM limpa → Production
- [ ] Setup de backup (state.db criptografado + SOUL.md versionado)
- [ ] Migrar runtime atual de `~/.hermes/` para `pip install`

Refs: `hermes-jarvis-voice` SKILL.md, `delegate-agy` SKILL.md, `kanban-orchestrator` SKILL.md
