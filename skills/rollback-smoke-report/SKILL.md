---
name: rollback-smoke-report
description: "Gera relatório de rollback e smoke test após mudanças críticas em produção. #rollback"
category: devops
platforms: [linux]
---

# Relatório rollback + smoke

## Quando usar
Depois de testes, falhas, rollback, mudança runtime ou validação de hooks/skills.

## Objetivo
Produzir evidência curta e auditável que distingue PASS, FAIL, SKIP e BLOCKED.

## Procedimento
1. Registrar escopo.
2. Listar comandos/testes executados.
3. Separar PASS/FAIL/SKIP/BLOCKED.
4. Incluir rollback testado ou rollback exemplo.
5. Não criar POST snapshot se smoke falhou.
6. Redigir secrets.

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
Relatório reproduzível, sem SKIP mascarado como PASS, com rollback claro e sem secrets.

## Rollback se aplicável
Não aplicável; se arquivo local/config PC2 for alterado, restaurar backup explicitado no relatório.
