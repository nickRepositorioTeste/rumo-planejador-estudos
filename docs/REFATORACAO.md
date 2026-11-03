# Prompt 2 — Refatoração segura

**Autorização:** concedida explicitamente pela estudante após apresentação e aprovação do plano anterior. 02/11/2026. **Estado:** extração de validações implementada; regressão Flask no Windows ainda pendente após esta mudança.

## Escopo aprovado e executado

O arquivo `app.py` concentra rotas, SQLite, regras de negócio e validações. Para reduzir esta concentração, foram extraídas somente quatro funções **puras** para `validacoes.py`: `number`, `integer`, `day_value` e `valid_time`.

- `app.py` passou a importar as quatro funções de `validacoes.py`.
- As implementações foram movidas **literalmente**, sem alteração de assinatura, conteúdo lógico, exceções ou mensagens.
- Não foram modificadas URLs, templates, consultas SQL, schema, banco, algoritmo de cronograma, cálculo dos simulados ou controles de segurança.
- Não foi adicionada dependência.

## Mapa de responsabilidades

| Responsabilidade | Antes | Depois |
|---|---|---|
| Conversão/limites de números e validação de datas/horários | Funções internas em `create_app()` dentro de `app.py` | Funções de módulo em `validacoes.py` |
| Rotas Flask e formulários | `app.py` | `app.py` — mantido |
| SQLite, transações e propriedade | `app.py` | `app.py` — mantido |
| Cronograma e pontuação | `app.py` | `app.py` — mantido |

## Verificações e resultados observados

1. **Antes da refatoração, Windows da estudante:** `21 passed in 11.38s` por `py -m pytest -q`, evidência `docs/evidencias/08_pytest_21_aprovados.png`.
2. **Depois, no ambiente de geração:** comparação automática das árvores de sintaxe (`AST`) das quatro funções: **4/4 idênticas**, excetuados números de linha; comando de compilação de `app.py`, `validacoes.py` e `tests/`: **sucesso**. Evidência de execução em `docs/evidencias/refatoracao_02_verificacao.txt`.
3. **Depois, tentativa de `python -m pytest -q` neste ambiente:** importação de Flask indisponível; suíte não coletada aqui, portanto **não há nova contagem de 21 aprovados pós-refatoração** neste ambiente.
4. **Regressão pós-refatoração no Windows:** **PENDENTE**. Executar na pasta principal: `py -m pytest -q 2>&1 | Tee-Object -FilePath docs\evidencias\pytest_apos_refatoracao.txt`. Verificar resultado antes do envio ao GitHub.

## Riscos e limites

A equivalência estrutural reduz a chance de regressão nessas funções, mas não substitui a execução dos testes HTTP no Windows. A alteração deve ser verificada também pela estudante antes da publicação. O arquivo `AUDITORIA.md` (diagnóstico do Prompt 4) permaneceu intacto como fotografia inicial. Correções de segurança não autorizadas não foram feitas.
