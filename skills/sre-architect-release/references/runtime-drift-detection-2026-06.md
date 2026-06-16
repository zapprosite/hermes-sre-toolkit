# Runtime Drift Detection — Receita Canônica SRE

> **Aprendizado**: 2026-06-16, caso Hermes Jarvis SOTA v2.
> **Função**: detectar e corrigir drift entre documentação e runtime real.
> **Quando usar**: depois de qualquer release estabilizado, antes de declarar "100% verde".

## Conceito

**Drift SRE** = divergência entre 3 fontes de verdade:

1. **Doc canônica** (ex: `docs/ARCHITECTURE.md` — SSoT declarada)
2. **Runtime real** (ex: `ss -ltn`, `systemctl is-active`, `ps`)
3. **Config do agent** (ex: `~/.hermes/config.yaml`, `~/.gemini/antigravity-cli/settings.json`)

Drift acontece porque:
- Refactor mudou código mas não doc.
- Container/service foi adicionado/removido sem atualizar doc.
- Outro agent (worker paralelo) subiu processo ad-hoc.
- Config foi patchado runtime (`config set bind ...`) sem persistir.

## 4-Phase Drift Detection

### Phase 1 — Inventário de portas em uso

```bash
ss -ltn 2>/dev/null | grep -v "State" | awk '{print $4}' | sed 's/.*://' | sort -u
```

Output esperado: lista de portas (ex: 22 1455 3000 4140 5432 5433 7880 7881 8000 8001 8020 8088 8202 8765 9333 9377 ...).

Cada porta deve ter **um dono** declarado: serviço, container, ou "orphan" (precisa investigação).

### Phase 2 — Diff vs doc canônica

```bash
# Doc canônica
grep -E "^\| \*\*[0-9]+\*\*" docs/ARCHITECTURE.md

# Runtime real
ss -ltn 2>/dev/null | grep -v "State" | awk '{print $4}' | sed 's/.*://' | sort -u

# Diff: portas no runtime mas NÃO na doc (drift = adicione à doc OU prune)
comm -23 <(ss -ltn 2>/dev/null | grep -v "State" | awk '{print $4}' | sed 's/.*://' | sort -u) \
     <(grep -E "^\| \*\*[0-9]+\*\*" docs/ARCHITECTURE.md | grep -oE "[0-9]{4,5}" | sort -u)
```

Output típico do release v2: `20131 43334 5432 5433 7881 8088` — 6 portas no runtime mas não na doc.

### Phase 3 — Investigar cada porta-órfã

Para cada porta-órfã:
1. **Quem está ouvindo?**
   ```bash
   ss -ltnp 2>/dev/null | grep ":$port "
   # mostra PID + binário
   ```
2. **É serviço documentado, container, ou orphan?**
   - `systemctl --user is-active <unit>.service` — se sim, é unit do usuário
   - `docker ps | grep ':$port->'` — se sim, é container
   - `ps -p <pid> -o cmd` — se é nativo
3. **Marcar como KEEP / RETIRED / PRUNE**:
   - **KEEP**: atualizar doc para refletir a realidade.
   - **RETIRED**: doc marca como "RETIRED" mas serviço ainda roda. Decidir:
     se ainda necessário (manter), se deprecated (mover pra `_retired_<ts>/`).
     Caso de calibração: 7880/7881/8088 estavam marcados RETIRED
     no canônico mas ainda active. **Decisão SRE**: aceitar como
     "RETIRED in release v2, still running" (manifesta o status real
     e evita drift futuro).
   - **PRUNE**: parar serviço e mover doc pra refletir remoção.

### Phase 4 — Atualizar doc canônica

Para cada drift resolvido, atualizar `docs/ARCHITECTURE.md`:

1. **Adicionar entrada** se a porta é canônica (com service + status + bind):
   ```markdown
   | **5432** | PostgreSQL 17 Local | `postgres@17-main.service` (native, PC2) |
   ```

2. **Marcar RETIRED** (com nota "RETIRED in release v{N}, still running"):
   ```markdown
   | **7881** | LiveKit WebRTC (UDP+TCP) | LiveKit media transport (Tailscale + Docker) — RETIRED in release v2, still running |
   ```

3. **Corrigir bind errado** (Tailscale → 127.0.0.1):
   ```markdown
   | **8088** | TCP / `127.0.0.1` | `hermes-livekit-agent` control path (RETIRED in release v2, still bound loopback) |
   ```

## Receita: Audit + Fix

```bash
# 1. Detectar drift
ss -ltn 2>/dev/null | grep -v "State" | awk '{print $4}' | sed 's/.*://' | sort -u > /tmp/ports_runtime.txt
grep -E "^\| \*\*[0-9]+\*\*" docs/ARCHITECTURE.md | grep -oE "[0-9]{4,5}" | sort -u > /tmp/ports_doc.txt
comm -23 /tmp/ports_runtime.txt /tmp/ports_doc.txt  # drift
comm -13 /tmp/ports_runtime.txt /tmp/ports_doc.txt  # doc only (sem runtime)

# 2. Investigar cada porta-órfã
for port in $(comm -23 /tmp/ports_runtime.txt /tmp/ports_doc.txt); do
  echo "=== port $port ==="
  ss -ltnp 2>/dev/null | grep ":$port "
  # docker? systemctl? ps?
done

# 3. Para cada porta RETIRED ainda rodando, atualizar doc:
#    | **<porta>** | <description> | <config> — RETIRED in release v2, still running |
# Para cada porta KEEP nova, adicionar entrada canônica.

# 4. Re-validar
python3 ~/.hermes/scripts/audit-ports-drift.py 2>&1 | tail -3
# esperado: "100% SUCESSO. Sem desvios detectados."

# 5. Regenerar CHECKSUMS.md (mudou SHA256 de ARCHITECTURE.md)
cd /home/will/workspace/homelab-context
# (re-run the original generation loop)
git add docs/ARCHITECTURE.md docs/CHECKSUMS.md
git commit -m "fix(arch): corrigir drift de portas (release v{N})"
```

## Pattern: Sub-checks do audit-ports-drift.py

O `audit-ports-drift.py` (em `~/.hermes/scripts/`) tem 3 sub-checks:

1. **Portas locais esperadas** (`config["local_only"]`): cada porta documentada
   deve estar listening. Se FAIL = serviço não está rodando.
2. **Exposição externa** (`config["external"]`): cada porta exposta deve estar
   na allowlist. Se FAIL = porta exposta sem autorização.
3. **Paridade da doc** (`DOC_CANDIDATES`): doc deve mencionar todas as portas.
   Se FAIL = doc desatualizada.

A Fase 1 do release v2 (Card 5) já patchou `audit-ports-drift.py` pra preferir
`ARCHITECTURE.md` antes do legacy `CANONICAL_ARCHITECTURE.md`. Se o gate 7 ainda
reporta DRIFT, **2 motivos prováveis**:

1. **Porta não está em `DOC_CANDIDATES`** — adicionar manualmente.
2. **Porta ESTÁ no doc mas runtime não está listening** — serviço caiu,
   investigar `systemctl is-active` ou `docker ps`.

## Caso de calibração (Hermes Jarvis SOTA v2, 2026-06-16)

| Drift detectado | Origem | Fix |
|---|---|---|
| `5432` no runtime mas não na doc | Postgres PC2 nativo (`postgres@17-main.service`) | Adicionar entrada canônica |
| `5433` no runtime mas não na doc | Honcho Postgres (docker) | Adicionar entrada canônica |
| `7880/7881` na doc como RETIRED, ainda active | LiveKit SFU active (docker + system) | Marcar "RETIRED in release v2, still running" |
| `8088` na doc como Tailscale, na verdade 127.0.0.1 | hermes-livekit-agent bind loopback | Corrigir bind pra 127.0.0.1 |
| `20131` no runtime mas não na doc | OmniRoute next-server sub-processo | Adicionar entrada canônica |
| `6379` tinha Tailscale leak | `redis-server` bind poluído | `redis-cli config set bind "127.0.0.1 -::1"` + nota "Tailscale leak corrigido em release v2" |

## Pattern geral: 5 perguntas SRE para drift

Antes de declarar "release estabilizado", responder:

1. **Inventário**: todas as portas listening estão documentadas?
2. **Binds**: todos os binds estão em 127.0.0.1 (ou Tailscale explicitamente autorizado)?
3. **Services**: todos os `systemctl --user is-active` retornam `active` (ou `inactive` se aposentado)?
4. **Containers**: `docker ps` lista apenas containers documentados?
5. **Configs**: `~/.hermes/config.yaml` bate com `~/.gemini/antigravity-cli/settings.json` bate com `~/.hermes/profiles/*/config.yaml`?

Se qualquer resposta é "não sei" ou "drift", abrir card de follow-up.
