# Gitea Local Audit Pattern — 2026-05-23

## Contexto

O usuário pediu "auditoria Gitea local" para saber o estado da instância Gitea antes de decidir se faz PR no Gitea ou no GitHub. O homelab-context vive no GitHub, o Gitea local está vazio.

## Sequência de auditoria usada

```bash
# 1. Container + IP binding
docker ps | grep gitea
# Resultado: 5d039105a9a3   gitea/gitea:1.26.2 ... 100.87.53.54:3000->3000/tcp, 100.87.53.54:2222->22/tcp

ip addr show | grep -E '100\.|192\.|172\.' | head -5
# Resultado: inet 100.87.53.54/32 scope global tailscale0

# 2. Testar A-P-I pública (sem auth) — determina se Gitea está vazio
curl -s "http://100.87.53.54:3000/api/v1/repos/search?limit=50" | python3 -m json.tool
# Resultado: {"ok": true, "data": []} → vazio, sem repos

# 3. Testar endpoint /explore/repos via browser (visual confirmation)
# Resultado: "No matching results found" + version 1.26.2

# 4. Docker exec — inspect interno do Gitea (app.ini + repos filesystem)
docker exec gitea bash -c "cat /data/gitea/conf/app.ini | grep -E 'ROOT|ADMIN|disabled' | head -10"
# ROOT = /data/git/repositories
# ROOT_URL = http://100.87.53.54:3000/

docker exec gitea bash -c "ls /data/git/repositories"
# Resultado: hermes-agent  (só um repo bare existe internamente)

docker exec gitea bash -c "ls /data/git/repositories/hermes-agent 2>/dev/null | head -10"
# Resultado: hermes-agent.git  (bare repo)

# 5. Testar token válido vs inválido
curl -sS "http://100.87.53.54:3000/api/v1/user" -u "hermes-agent:$TOKEN" | python3 -m json.tool
# Resultado: {"message": "invalid username, password or token"} → 401 inválido

# 6. Comparar com GitHub remote real
git remote -v
# origin  https://github.com/zapprosite/homelab-context.git (fetch)
```

## Padrão de decisão pós-auditoria

| Situação | Ação |
|---|---|
| Gitea vazio + repo no GitHub | Reportar ao usuário, perguntar se cria repo no Gitea ou usa GitHub |
| Gitea com repo + token válido | Fazer push + PR no Gitea via API |
| Token inválido (401) | Reportar, não tentar push às cegas |
| TLS fail em https | Trocar para http:// no remote |

## Distinção importante

- "Gitea vazio" = `/api/v1/repos/search` retorna `data: []`
- "Repo não existe" = endpoint `/api/v1/repos/OWNER/REPO` retorna 404
- "Token inválido" = endpoint `/api/v1/user` retorna 401
- `homelab-context` estar no GitHub não é um erro — é questão de soberania de dados, o usuário decide onde o PR deve ser criado

## Findings desta sessão

- Gitea 1.26.2 rodando via Docker em `100.87.53.54:3000`
- Container healthy mas.instance sem repos públicos ( só `hermes-agent` internamente )
- Credenciais `hermes-agent` em `~/.git-credentials` estão inválidas para a API
- homelab-context está no GitHub, não no Gitea
- Branch `feature/secretaria-jarvis-identity-update` criado e pushado para GitHub
- Questão em aberto: usuário quer PR no Gitea (precisa criar repo primeiro) ou no GitHub (precisa de token válido)