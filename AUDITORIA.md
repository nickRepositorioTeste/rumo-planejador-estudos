# Prompt 4 — Auditoria completa inicial (somente leitura do código)

**Data da análise:** 02/11/2026. **Base:** código disponível em `app.py` e templates. Esta é uma auditoria estática; não foram realizados testes funcionais, de segurança dinâmicos ou de concorrência. O código não foi alterado como parte desta auditoria. Não há banco de produção acessível.

## Principais achados confirmados, por risco

1. **ALTO — conflito de horários:** a restrição em `sessions` impede mesmo `start_at`, mas não intervalos sobrepostos. Uma sessão concluída pode ocupar parcialmente um intervalo gerado (linhas 22, 368–379), e a edição de sessão não verifica sobreposições (387–410).
2. **MÉDIO — segredo de sessão opcional:** sem `SECRET_KEY` no ambiente, a aplicação cria segredo efêmero. Isso invalida sessões em reinícios, inadequado para publicação (linha 30).
3. **MÉDIO — arquivo único e acoplamento:** `app.py` tem 512 linhas e reúne rotas, SQL, validações e algoritmo (linhas 27–511), dificultando manutenção e testes.
4. **MÉDIO — disponibilidade alterada não revalida agenda:** editar o horário semanal não valida nem atualiza as sessões já existentes (linhas 278–317, 323–379). Usuário deve regenerar; isso precisa ficar claro na interface.
5. **MÉDIO — sem suíte de integração:** `tests/` ainda não possui cenários implementados e dependência Flask não está disponível neste ambiente; os resultados não podem ser declarados como aprovados.

## 1. Integração

| Achado | Risco | Arquivo/linha | Correção sugerida |
|---|---|---|---|
| Ausência de testes integrados executáveis; nenhuma contagem real de aprovação/reprovação | Médio | `tests/` vazio; `requirements.txt:2` | Após aprovação dos cenários, criar pytest com SQLite temporário por teste e rodar `python -m pytest` |
| Separação de bancos de teste/produção | Não verificado | `app.py:29–32` | `create_app(test_config)` permite caminho distinto, mas não há fixture implementada ou resultado de isolamento |
| Testes unitários com mocks, integração com banco e E2E | Não verificado | — | Não há testes; não inventar cobertura |

**Comando previsto:** `python -m pytest`. **Execução:** não realizada. **Aprovados/reprovados:** não disponível. **Motivo:** instalação de Flask bloqueada por DNS; planejamento acadêmico exige aprovação dos cenários antes do Prompt 3.

## 2. Confiança no cliente, segredos e isolamento

| Achado | Risco | Arquivo/linha | Correção sugerida |
|---|---|---|---|
| Segredo de sessão gerado na inicialização quando variável ausente | Médio | `app.py:30` | Exigir variável configurada em produção; manter conveniência somente no desenvolvimento |
| Os cálculos dos simulados estão no servidor com Decimal e validação | Baixo | `app.py:424–466` | Testar com entradas negativas, penalidades e metas |
| Autorização por usuário aparece nas consultas de concurso, disciplina, sessão e simulado | Baixo | `app.py:53–83` | Confirmar com testes de isolamento entre usuários |
| CSRF em todos POST por token de sessão, escape automático em `.html` Jinja | Baixo | `app.py:118–124`, `templates/base.html` | Testar rejeição sem token e tentativa XSS |
| RLS/Supabase, service_role ou banco exposto em API pública | Não se aplica | SQLite usado em servidor | Avaliar permissão de arquivo e hospedagem |
| Exposição de `instance/rumo.sqlite3` no diretório estático | Baixo | `app.py:29–33`, `.gitignore` | Banco está fora de `static`; verificar configuração real do deploy |

Não foi encontrado token público ou secreto hardcoded nos arquivos inspecionados. A variável de exemplo não é segredo verdadeiro.

## 3. Concorrência

| Achado | Risco | Arquivo/linha | Correção sugerida |
|---|---|---|---|
| UNIQUE por horário inicial não impede intervalos sobrepostos | Alto | `app.py:22,368–379,387–410` | Validar conflitos entre início/fim na transação e testar duplicações |
| Regeneração usa `BEGIN IMMEDIATE` e INSERT OR IGNORE | Médio | `app.py:373–379` | Testar clientes paralelos e verificar resultado/contagem real, inclusive sessões concluídas |
| Dupla submissão de outros formulários cria registros repetidos | Médio | `app.py:183–202,421–464` | Definir idempotência específica ou botão desabilitado; testar repetição |
| Alteração concorrente de registros usa última gravação | Baixo | `app.py:206–226,387–410` | Considerar versão/timestamp se exigido |

## 4. Idempotência

A regeração tenta ser idempotente quanto a sessões futuras pendentes e mantém concluídas, mas a ausência de detecção de sobreposição e testes simultâneos impede afirmar segurança completa. A conclusão de sessão repete um UPDATE com estado explícito, sem contador cumulativo. Webhooks e pagamentos: **não se aplica**.

## 5. Responsabilidades

`app.py` tem 512 linhas; mistura rotas, SQL, validação de formulários, cálculo de simulado e geração de agenda. Candidato real à refatoração futura: extrair cálculo do cronograma/simulados para serviço simples. **Não refatorar antes dos testes e aprovação do Prompt 2.**

## Próxima prioridade

**Primeiro:** corrigir o risco de sessões sobrepostas, pois pode tornar o cronograma incorreto mesmo com disponibilidade configurada. **Segundo:** definir `SECRET_KEY` estável em produção. Ambas as mudanças exigem plano e aprovação na etapa do Prompt 1; nenhuma correção foi aplicada durante esta auditoria.
