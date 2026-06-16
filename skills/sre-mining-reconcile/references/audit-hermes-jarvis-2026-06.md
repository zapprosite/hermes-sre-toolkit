# Reference: AUDIT_HERMES_JARVIS_2026-06 — caso de calibração

> **Quando ler:** exemplo vivo de como aplicar `sre-mining-reconcile` numa stack
> real (Hermes Jarvis voice no PC2). Não é template; é o output completo da
> primeira execução da skill em 2026-06-16, usado para validar formato e refinar
> o checklist.

## Contexto da sessão

- **Will pediu**: "voce entendeu seu objetivo? ler toda bagunca que os dev juniores deixaram e vamos minerar o que presta definir uma arquitetura hermes cli/tui funcionando com um streme de audio usando audio full gpu sem fall-back de cpu, ja exiter jarvis funcionando e clonado mas e um arquitetura salada voce tem que fazer uma mineracao e entregar algo estavel e profissional sem lixos tecnicos, algo com telemetria SRE dev senior de verdade, planeje e delegue para os subagents no kanban"
- **Output real**: `homelab-context/docs/AUDIT_HERMES_JARVIS_2026-06.md` (341 linhas)
- **Branch**: `agent/audit-jarvis-sota-v2`
- **Commits**: 2 (audit file + BLUEPRINT.md 213 linhas)
- **Decisão arquitetural única**: opção A — in-session estrito

## Inventário típico desta stack (165 .py + 74 .sh + 19 .md)

| Categoria | Qtd | KEEP | CUT | LEGACY | Refactor |
|---|---:|---:|---:|---:|---:|
| `homelab-context/modules/hermes_voice/` (canônico) | 35 .py | 35 | 0 | 0 | 0 |
| `~/.hermes/hermes-agent-next/agent/` (upstream Nous) | 130 .py | 10 voice-core | 0 (intocável) | 0 | 0 |
| `~/.hermes/scripts/` (SRE) | 74 .sh | 35 | 9 | 30 | 0 |
| `homelab-context/docs/` + `~/.hermes/docs/` | 19 .md | 10 | 5 | 4 | 0 |

## Inconsistências canônico↔real↔SOTA (5 detectadas)

1. **Runtime voice**: canônico = in-session, real = daemon active, SOTA = híbrido 24/7 → decisão A (in-session).
2. **Wake model OWW**: canônico = `jarvis_ptbr_user.onnx` em `/home/will/data/...`, real = não encontrado, SOTA = mesmo path → gap P1, despachar card 3.
3. **TTS voice**: canônico = `jarvis-clone-trimmed` fail-closed, real = bate via curl, SOTA = bate → KEEP.
4. **LLM T2**: canônico = MiniMax-M3, real = `api.minimax.io` configurado, SOTA = bate → KEEP, mas prune 3 perfis `:4018` órfãos.
5. **Serviços aposentados**: canônico = aposentado, real = `active`, SOTA = "daemon 24/7" → gap P0, despachar card 2.

## Cards dependentes despachados (4)

- **t_19b630f0** [RECONCILE] coder — SOTA vs. canônico
- **t_10104b00** [WAKE-MODEL] devops — validar OWW
- **t_56ebb1c3** [TELEMETRY] coder — /healthz + circuit breaker
- **t_a7d9df76** [PRUNE] devops — limpeza severa

## Pitfall específico desta sessão (importante!)

**Workers kanban crasharam 2x com `protocol_violation`** porque:
1. `~/.hermes/profiles/{coder,devops,reviewer,researcher}/config.yaml` estavam com `model: MiniMax-M3` + `provider: minimax-oauth` (motor errado).
2. Mesmo após corrigir pra `provider: agy`, o modelo `Gemini 3.5 Flash (High)` via `agy` **não tem tool-calling correto** pra `kanban_complete`/`kanban_block` — termina o trabalho mas não chama a tool de saída.
3. Workaround aplicado: despachar `agy -p` direto em `terminal(background=true)` bypassando o dispatcher kanban, com instrução explícita "CHAME kanban_complete no fim".

→ Ver `delegate-agy` SKILL.md seção "Workaround para `protocol_violation` do `agy` no kanban (2026-06-16)".

## Lições pra próxima auditoria

1. **Pré-validar motor dos profiles kanban** antes de despachar cards. Se profile tem `provider: minimax-oauth`, é problema.
2. **Validar paths do SOTA** no filesystem antes de aceitar como verdade. SOTA avulso de Will pode ter paths/modelos inventados.
3. **Inventário automático primeiro**, classificação depois. Não ler 130 arquivos .py linearmente.
4. **Decisão arquitetural única** justificada. Will odeia indecisão.
5. **Audit file = artefato principal**, não o conhecimento. Commitar em branch dedicado.
