# Problemas e correções

| Problema real | Evidência | Ação | Situação |
|---|---|---|---|
| Erro de sintaxe, parêntese excedente no INSERT de mocks | `python -m compileall -q app.py` apontou `SyntaxError: unmatched ')'` | Removido parêntese excedente | Corrigido; nova compilação concluída sem erros |
| Flask ausente no ambiente de execução | `importlib.util.find_spec('flask')` retornou False | Tentativa de `pip install flask -q` | Não resolvido: acesso ao índice indisponível por erro DNS, sem instalação |

Nenhuma execução de aplicação, navegador ou suíte pytest foi realizada nesta sessão. Problemas potenciais identificados por leitura estática constam em `AUDITORIA.md`.


## Correção 1 — sobreposição de horários (aprovada em 02/11/2026)

| Problema | Evidência | Correção | Estado |
|---|---|---|---|
| Checagem por `UNIQUE(exam_id,start_at)` permitia intervalos sobrepostos, inclusive entre concursos do mesmo usuário | Auditoria inicial `AUDITORIA.md`; código original de `regenerate` e `session_detail` | Verificação de interseção em SQLite dentro de transações `BEGIN IMMEDIATE` antes de inserir/editar | Aplicada; 7 verificações isoladas bem-sucedidas |
| Regeneração podia inserir candidato que se chocava com sessão concluída | Código original só ignorava duplicidade de horário inicial | Pular candidatos conflitantes, jamais excluir concluídas; rollback se nenhum bloco livre | Verificada com registros em SQLite temporário |
| Script auxiliar de verificação assumiu que SQLite nunca reutiliza `rowid` e inicialmente não simulava `render_template` | Primeiras execuções do verificador falharam em asserção do ID e com `NameError` | Ajustado verificador para checar dados efetivos e simular apenas a resposta da interface | Corrigido no verificador; resultado final 7/7 |

Não houve testes de Flask HTTP, testes visuais nem alteração de banco pessoal. Ver `docs/evidencias/` para script reproduzível e saída real.


## 02/11/2026 — Correção 2 de segurança, autorizada

Problema: `SECRET_KEY` temporária era aceita mesmo em produção, invalidando sessões após reinício, e `SESSION_COOKIE_SECURE` dependia de configuração manual. Solução aprovada: produção definida por `RUMO_ENV=production` exige chave persistente e usa cookie Secure; `HttpOnly` e `SameSite=Lax` preservados. Teste funcional preparado em `tests/test_auth_security.py`; **pendente de execução** porque não há Flask no ambiente atual. Verificação de sintaxe passou. Sem dados reais alterados.

## 02/11/2026 — Bloqueio de execução do Prompt 3

21 testes de integração implementados com SQLite temporário e cliente Flask. A execução de `python -m pytest -q` encerrou na importação de `conftest.py` (`ModuleNotFoundError: flask`, saída 4). Tentativa de instalar Flask falhou por DNS. **Não foram executados testes de integração**; usuária precisa executar no Windows onde Flask já está instalado e guardar `pytest_windows.txt`. Não alterar expectativas para conseguir verde; corrigir bugs reais somente em etapa aprovada.
