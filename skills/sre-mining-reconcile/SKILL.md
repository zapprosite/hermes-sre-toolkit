---
name: sre-mining-reconcile
description: "Mineração SRE dev-sênior + reconciliação canônico↔real↔SOTA em stacks existentes. Quando Will entrega um SOTA/spec grande (Hermes Jarvis, homelab, qualquer stack) e pede 'ler a bagunça, minerar o que presta, entregar arquitetura estável', esta é a skill. Output: AUDIT_<TOPIC>_<YYYY-MM>.md com TL;DR + inventário bytes/LOC + inconsistências + gaps P0-P3 + mapa keep/cut/refactor + recomendação de release + critérios de aceite. Princípios: inventário automático via wc/grep/find, classificação em keep/cut/refactor, prune severo sem dó, decisão arquitetural única justificada. **NÃO substitui `delegate-agy`** — esta skill governa a fase de auditoria/mineração; `delegate-agy` governa a execução de code."
tags: [sre, audit, mining, reconcile, architecture, prune, senior]
---

# SRE Mining & Reconcile — auditar stacks existentes

## Purpose

Quando Will entrega um stack grande (Hermes Jarvis, homelab, qualquer sistema) e pede "ler tudo, minerar o que presta, entregar arquitetura limpa", esta skill governa a fase de **auditoria + reconciliação canônica**. Output é um arquivo de auditoria estruturado, e (opcional) a abertura de branch + commits granulares pra PR review.

**Esta skill NÃO é code execution.** Code execution é governada por `delegate-agy`. Aqui o agente (Hermes) faz ele mesmo: lê docs, roda `find/wc/grep`, classifica arquivos, escreve o audit file. Code que apareça na sequência (ex: mudar service units) é delegado via `delegate-agy` ou kanban.

## When to use (sinal claro de Will)

- "voce entendeu seu objetivo? ler toda bagunca"
- "minerar o que presta"
- "arquitetura hermes [...] funcionando com audio full gpu"
- "ja existe jarvis funcionando e clonado mas e um arquitetura salada"
- "voce tem que fazer uma mineracao e entregar algo estavel"
- "telemetria SRE dev senior de verdade"
- "seja severo com os que for prune, prune sem do"

## Princípios SRE (inquebráveis)

1. **Inventário automático antes de classificar.** `find` + `wc -l` + `sha256sum` + `systemctl is-active` em tudo. Não ler arquivos 1 por 1.
2. **Cruzar 3 fontes** antes de aceitar verdade:
   - **Canônico pinado** (docs oficiais, INVENTORY, ADRs, SOUL.md)
   - **Estado real** (filesystem, `ss -ltn`, `systemctl`, `ps`)
   - **SOTA/briefing** (o que Will entrega)
3. **Decisão arquitetural única.** Quando há contradição, escolher A/B/C com justificação, não emaranhar.
4. **Prune severo sem dó.** Mover legados pra `_archive_<ts>/`, deletar lixo, manter só canônicos. Git é o backup.
5. **Telemetria > smoke tests.** Smoke pass ≠ sistema saudável. Exigir P95/P99 + circuit breaker + fail-closed explícito.
6. **Princípio da fronteira upstream.** Se o stack tem 70% upstream intocável (ex: `hermes-agent-next` da Nous) e 30% canônico editável (`homelab-context/modules/`), DOCUMENTAR a fronteira em vez de tentar refatorar o upstream.
7. **Pinned release pin.** Cada release vira branch `release/<nome>-v<n>` com tag. Rollback é consciente, não "rename canary".

## Estrutura do output (canônica, 8 seções)

Arquivo único: `docs/AUDIT_<TOPIC>_<YYYY-MM>.md` (ex: `AUDIT_HERMES_JARVIS_2026-06.md`).

```markdown
# AUDIT — <topic> · <YYYY-MM-DD>

> **Tipo:** auditoria SRE dev-sênior · **Branch:** agent/audit-<topic>-v<n>
> **Método:** inventário automático + reconciliação canônico↔real↔SOTA + classificação keep/cut/refactor.
> **Política:** prune severo, sem dó. Git é o backup.

## 1. TL;DR
(10 linhas max: estado real, gaps P0, recomendação keep/cut)

## 2. Inventário bytes/LOC por módulo
(Tabela: módulo | LOC | bytes | keep/cut/refactor | motivo)

## 3. Inconsistências canônico ↔ real ↔ SOTA
(Tabela: tópico | canônico diz | real mostra | SOTA diz | decisão)

## 4. Lixo técnico priorizado P0-P3
- P0: bloqueia release (segurança, contrato quebrado, daemon fantasma)
- P1: atrapalha release (duplicação, doc divergente, perfil órfão)
- P2: ruído (script legado, doc redundante)
- P3: cosmético

## 5. Mapa keep/cut/refactor
(Por categoria: código / scripts / systemd / docs)

## 6. Recomendação de release (decisão única)
(A/B/C com justificação)

## 7. Critérios de aceite da auditoria
(Checklist verificável: arquivo criado, tabela cobre 100%, P0-P3 priorizados, recomendação única, branch+commits+PR)

## 8. Próximos passos (cards dependentes)
(Lista de cards filhos, blocked por auditoria)

## 9. Apêndice — comandos de validação rápida
(Bash one-liners: ss, systemctl, find, grep, smoke gates)
```

## Workflow (Hermes sozinho, sem subagent)

### 1. Coletar canônico
Ler docs oficiais em `homelab-context/docs/` + `~/.hermes/docs/`. Identificar INVENTORY (lista de serviços/recursos pinned) e ADRs (decisões imutáveis).

### 2. Coletar real
```bash
# Filesystem
find <stack_path> -name "*.py" -not -path "*__pycache__*" | xargs wc -l | sort -rn | head -20
find <stack_path> -name "*.md" | wc -l
find <stack_path> -name "*.sh" | wc -l

# Services
systemctl --user is-active <unit-1> <unit-2> ...

# Ports
ss -ltn | grep -E ':<port-1>|:<port-2>'

# Processes
ps -eo pid,pcpu,pmem,etime,cmd | grep -E '<proc-1>|<proc-2>' | grep -v grep

# GPU/Resources
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv

# Health gates
~/.hermes/scripts/hermes-gpu-hardgate.sh
~/.hermes/scripts/hermes-router-guardrail-smoke.sh
~/.hermes/scripts/hermes-wake-e2e-gate.sh
~/.hermes/scripts/hermes-voice-healthcheck.sh
```

### 3. Cruzar SOTA avulso
Will entrega SOTA como bloco Markdown (ex: `# SOTA Jarvis-like Voice Architecture`). Antes de aceitar:
- (a) `ls <cada path absoluto>` — confirma existência
- (b) `find /home/will -name "<modelo>.bin"` — descobre o path real
- (c) `systemctl --user is-active <cada unit>` — confirma o que está rodando
- (d) cruzar com INVENTORY pinned

Se SOTA diverge do canônico, sinalizar como gap P0/P1 e despachar card de reconciliação, NÃO codar SOTA direto.

### 4. Classificar em keep/cut/refactor
Tabela por arquivo:
- **KEEP**: canônico, runtime, in-use. Manter.
- **CUT**: upstream intocável. Marcar como "CUT-CANDIDATE" e flagar upstream (não deletar).
- **CUT-LEGACY**: legados, mover pra `_archive_<ts>/`. Se for puro lixo, deletar com `trash`.
- **REFACTOR**: candidato a consolidar (ex: 2 arquivos com 80% de overlap).

Critério de severidade: se há 30% ou mais de CUT-LEGACY em qualquer categoria, prune é justificado.

### 5. Decisão arquitetural única
Quando canônico diz X, real mostra Y, SOTA diz Z, escolher UM caminho. Padrão:
- Se canônico está pinned e validado (smoke OK), **escolher canônico (opção A)** e realinhar runtime/docs.
- Se canônico está obsoleto e SOTA é melhor, **escolher SOTA (opção B)** e atualizar doc.
- Se ambos têm mérito, **dual pinado (opção C)** com 1 modo primário e 1 secundário.

### 6. Escrever o audit file
Output único, 300+ linhas, com as 8 seções acima. Commitar em branch `agent/audit-<topic>-v<n>` com 1 commit grande (audit file) + 1 commit de BLUEPRINT.md (se for despachar sequência de cards).

### 7. Despachar cards dependentes (se aplicável)
Cards filhos (RECONCILE / WAKE-MODEL / TELEMETRY / PRUNE etc) devem ser `todo` com `parents=[audit-card-id]`. O dispatcher promove automaticamente quando o pai vira `done`. Will aprova cada card no PR.

## Pitfalls (vividos)

- **Ler tudo linearmente.** Não. Use `find` + `wc` + `grep` estratégico. Ler 1 arquivo 1k LOC por vez.
- **Aceitar SOTA como verdade.** Sempre validar paths e modelos no filesystem antes de codar.
- **Recomendar opções A/B/C "ambos têm prós e contras".** Will odeia indecisão. Decisão única com justificação.
- **Não classificar upstream intocável como "deletar".** Flaggar como "CUT-CANDIDATE upstream" e seguir. Will não quer que agente mexa em código da Nous Research.
- **Esquecer de commitar o audit file.** O artefato principal é o .md, não só o conhecimento. Sem commit = sem rastreabilidade.
- **Pular o 1º smoke gate.** Antes de declarar "auditoria pronta", rodar `git log --oneline -5` + `wc -l AUDIT_<TOPIC>.md` + `grep -c '^## ' AUDIT_<TOPIC>.md` (deve ser ≥ 8 seções).
- **Confundir auditoria com code execution.** Auditoria é leitura + classificação. Code é `delegate-agy` ou kanban. Se começar a escrever código, pare e despache.
- **Rodar Fase 0 do `sre-architect-release` antes de despachar QUALQUER card** (aprendido em 2026-06-16). Mesmo que o card pareça trivial, validar motor + smoke antes. Sintoma típico: card despacha, dispatcher spawna worker hermes-CLI interno, esse worker tenta usar `MiniMax-M3` default do profile, conecta API cloud Anthropic-compat, recebe 401/timeout, dispatcher mata com exit 1 + `gave_up`. `hermes kanban show <id>` mostra `Diagnostics (1): Agent crash x2: pid X exited with code 1`. **Solução preventiva:** `bash ~/.hermes/skills/delegate-agy/scripts/setup-agy-kanban.sh` (idempotente). Quando o script não existe (cenário virgem), `bash ~/.hermes/skills/delegate-agy/scripts/agy-smoke.sh` é o canário mínimo. Caso de calibração: release v2 SRE dev-senior.
- **A Fase 0 do `sre-architect-release` é BLOQUEANTE** (não opcional). Setup de motor + 4 profiles + custom_providers + smoke test. Sem isso, todos os workers kanban subsequentes vão crashar. Esta skill (mining) deve chamar a skill irmã `sre-architect-release` para validar Fase 0 antes de despachar qualquer card filho. Ver `sre-architect-release/SKILL.md` §"Fase 0 — Detecção do motor errado".
- **Workers `agy` terminam mas não chamam `kanban_complete`** (protocol_violation
  do Gemini Flash sem tool-calling). Isso é o default, não uma falha. Workaround
  padrão: despachar `agy -p` direto via `terminal(background=true,
  notify_on_complete=true)` com wrapper bash e instrução EXPLÍCITA no prompt
  ("ao terminar, chame kanban_complete(...)"). Se o worker sair sem chamar,
  Hermes valida o output real (git log, branch, smoke) e chama
  `kanban_complete` manualmente como agente orquestrador. Detalhes completos
  em `delegate-agy/references/agy-wrapper-dispatch-2026-06.md`. Aprendido em
  release v2 SRE dev-senior, 2026-06-16.

## Quando NÃO usar

- Quando o stack está em **green field** (criar do zero). Use `delegate-agy` direto com BLUEPRINT.
- Quando o pedido é **fix pontual** (1-2 linhas). Use `terminal` + `patch` direto.
- Quando Will pede **research/exploração** de uma tecnologia nova. Use `research` skill.
- Quando o pedido é **deploy/runtime** (subir serviço, restart). Use SRE normal, não auditoria.

## Output esperado (entregável da skill)

- **Arquivo**: `docs/AUDIT_<TOPIC>_<YYYY-MM>.md` (300+ linhas, 8 seções)
- **Branch**: `agent/audit-<topic>-v<n>` (1-2 commits granulares)
- **Commits**: 1 com audit file, 1 com BLUEPRINT.md (se houver cards dependentes)
- **PR**: via Gitea, Will aprova
- **Cards filhos**: lista de `kanban_create` com `parents=[audit-id]` para despachar depois

## Validação rápida

```bash
# 1. Arquivo tem 8 seções?
grep -c '^## ' docs/AUDIT_<TOPIC>_<YYYY-MM>.md  # esperado: >= 8

# 2. Branch + commits?
git -C /path branch --show-current             # esperado: agent/audit-...
git -C /path log --oneline -3                  # esperado: commits granulares

# 3. Tabela de inventário completa?
grep -c '^|' docs/AUDIT_<TOPIC>_<YYYY-MM>.md   # esperado: >= 50 linhas com tabelas

# 4. Decisão arquitetural única?
grep -iE 'opção [AB]|recomendação|decisão única' docs/AUDIT_<TOPIC>_<YYYY-MM>.md
```
