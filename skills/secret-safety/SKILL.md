---
name: secret-safety
description: "Protege secrets e credenciais sensíveis entre PC1 e PC2 do homelab. #protege-secrets"
category: devops
platforms: [linux]
---

# Segurança de secrets PC2/PC1

## Quando usar
Qualquer tarefa com env, config, DSN, token, API key, senha, tunnel, auth, provider, LiteLLM, PostgreSQL ou MCP.

## Objetivo
Evitar exposição, cópia ou commit de secrets; toda saída deve redigir valores sensíveis.

## Procedimento
1. Não abrir arquivos de secrets reais.
2. Não copiar DSN do PC1 para PC2.
3. Não ler /srv/infra/env/master.env.
4. Usar exemplos redigidos.
5. Secret scan mínimo: DSN PostgreSQL, sk-, api_key, token, password, secret.
6. Relatar só caminho, tipo e status limpo/redigido/bloqueado.

## Tools MCP permitidas
hermes.health, hermes.services.status, hermes.qdrant.search_staging, hermes.postgres.status, hermes.postgres.query_readonly somente SELECT, hermes.fs.read_doc, hermes.redis.status, hermes.skills.list.

## Comandos proibidos
git push; git clone; reinstalar Hermes Agent; alterar provider/model/API; copiar DSN/secret; abrir portas; mexer em PC1 runtime; SQL diferente de SELECT; Qdrant production; ler/copiar env master; mascarar SKIP como PASS.

## Saída esperada
- Estado observado com fonte: MCP, arquivo local, git ou teste.
- Riscos e bloqueios explícitos.
- Próximo passo seguro.
- Secrets sempre como `[REDACTED]`.

## Critérios de sucesso
Nenhum valor sensível aparece em stdout, arquivo, diff, commit ou relatório; achados são `[REDACTED]`.

## Rollback se aplicável
Não aplicável; se arquivo local/config PC2 for alterado, restaurar backup explicitado no relatório.
