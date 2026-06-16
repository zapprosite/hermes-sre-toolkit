# lang-guard-prevent — Bundled Plugin Reference

## What it does
Injeta reminder ephemeral no user message a cada turn via hook `pre_llm_call`.
Não modifica system prompt (preserva prompt cache warm).
Camada 2 de defesa contra CJK/árabe cirílico não-latinos.

## Location
- Bundled: `/home/will/workspace/homelab-context/plugins/lang-guard-prevent/`
- Local:  `/home/will/.hermes/plugins/lang-guard-prevent/`

## Files
```
lang-guard-prevent/
├── __init__.py      # hook pre_llm_call + PREVENT_CONTEXT constant
└── manifest.yaml    # metadata (name, version, hooks)
```

## Hook signature
```python
def pre_llm_call(**kwargs) -> dict:
    return {"context": PREVENT_CONTEXT}
```

## PREVENT_CONTEXT
```python
PREVENT_CONTEXT = (
    "[REMINDER] Your output must contain ZERO non-Latin characters. "
    "ASCII only. Portuguese or English only. "
    "No CJK (Chinese/Japanese/Korean), no Cyrillic, no Arabic, no Hebrew, "
    "no Thai, no Burmese, no Lao. Not even in code comments, variable names, "
    "file paths, labels, or internal documentation. "
    "Use English or Portuguese for everything."
)
```

## Como adicionar novo plugin bundled
1. Criar diretório em `workspace/homelab-context/plugins/<nome>/`
2. Criar `__init__.py` com hook(s) e `manifest.yaml`
3. Adicionar em `~/.hermes/config.yaml` → `plugins.enabled` se não for bundled auto-load
4. Para auto-load (bundled): colocar em `plugins/` e marcar kind no manifest.yaml

## Verificação
```bash
# Checar se plugin carregou
grep lang-guard-prevent ~/.hermes/state.db 2>/dev/null || echo "not in state"

# Forçar reload de plugins
hermes plugins reload 2>/dev/null || echo "no reload cmd"
# Ou: restart do hermes gateway
```

## Relação com guard-rail-lang
- `guard-rail-lang` usa `transform_llm_output`: after-the-fact, bloqueia saída contaminada
- `lang-guard-prevent` usa `pre_llm_call`: before-the-fact, previne contaminação a cada turn
- Ambos são complementary — não substituem um ao outro

## Labels no guard-rail-lang devem ser ASCII
Nomes em `_BLOCKED_RANGES` devem ser ASCII puro para não contaminar output.
Exemplo de labels limpos: `cirilico-ext`, `CJK-A`, `CJK-simbolos`, `arabe`.
Labels com CJK/árabe (ex: `cirílico扩展`, `CJK扩展A`): CORRIGIR IMEDIATAMENTE.