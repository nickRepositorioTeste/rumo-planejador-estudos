# Progresso — Rumo

**Etapa atual — atualização em 02/11/2026, 23h14 (Brasília):** 21 testes do Prompt 3 executados no Windows da estudante com **21 aprovados, 0 falhas, 11,38 s** (print real em `docs/evidencias/08_pytest_21_aprovados.png`, arquivo `pytest_windows.txt` salvo no Windows). Prompt 2: plano de refatoração apresentado, **ainda não autorizado nem executado**. GitHub e hospedagem pendentes.

## Aprovações e decisões

- Planejamento/MVP (Flask + SQLite, CRUD, disponibilidade, cronograma e simulados): aprovado.
- Desenvolvimento da Etapa 2: autorizado pela estudante.
- **Prompt 1, correção 1 — impedir sobreposições e preservar sessões concluídas:** aprovado explicitamente em conversa em 02/11/2026 e implementado.
- **Prompt 1, correção 2:** expressamente aprovada em conversa, implementada em `app.py` (chave persistente + cookie Secure em produção); correções 3 e 4 seguem pendentes.
- **Prompt 3 — cenários e testes de integração:** aprovados pela estudante; 21 testes implementados em `tests/`, execução bloqueada antes da coleta neste ambiente pela ausência do Flask.
- **Prompt 2 — refatoração:** aguardando sua vez e aprovação.

## Arquivos e mudanças

- `app.py`: verificação de conflito entre todos os concursos do mesmo usuário; transação imediata para escrita na regeneração e edição; rollback se geração resultar em zero blocos livres; concluídas intocadas; mensagem precisa sobre blocos pulados.
- `docs/SEGURANCA.md`, `docs/PROBLEMAS_E_CORRECOES.md`, `docs/RESULTADOS_DOS_PROMPTS.md`, `README.md`: documentação atualizada para refletir o que foi aprovado, alterado e realmente verificado.
- `docs/evidencias/verificar_correcao_01.py`: verificador isolado e reproduzível com SQLite temporário; **não é suite HTTP/pytest**.
- `docs/evidencias/correcao_01_verificacao.txt`: saída de execução do verificador.
- `AUDITORIA.md`: diagnóstico original **preservado sem alteração**.

## Comandos executados nesta etapa

- `python -m py_compile app.py` → **saída 0**, sem erro de sintaxe.
- `python docs/evidencias/verificar_correcao_01.py` → **7 verificações isoladas concluídas sem falhas**, incluindo concorrência com duas conexões SQLite, preservação de concluída, isolamento de usuário, rejeição de conflito na edição e rollback em geração sem vagas.
- Flask e Werkzeug ausentes do **ambiente de geração**; a estudante executou Flask e navegou pelo Rumo em seu Windows (prints reais incluídos). `python -m pytest -q` na máquina de geração: bloqueado na importação (`ModuleNotFoundError: flask`, código de saída 4), antes da coleta. Nenhum teste integrado executado aqui.
- `git status` no workspace anterior → não há repositório Git acessível. Nenhum commit/push foi criado.

## Pendências reais

1. **Concluído:** execução no Windows de `py -m pytest -q` com resultado 21/21 aprovados; evidência `docs/evidencias/08_pytest_21_aprovados.png`. Rodar novamente após futuras mudanças.
2. Pedir aprovação do **plano de refatoração do Prompt 2** em `docs/REFATORACAO.md` antes de alterar código.
3. Inicializar Git, revisar `.gitignore` e arquivos ignorados, publicar código/evidências no GitHub e fazer deploy com banco persistente; documentar URLs verificadas.
4. Correções de segurança 3 e 4 não foram autorizadas; não aplicar sem nova aprovação.

**Próxima ação:** pedir aprovação expressa do plano do Prompt 2 antes de modificar código. Depois repetir 21 testes, criar repositório GitHub e publicar com SQLite persistente. Não alterar o banco `instance/rumo.sqlite3`.


## Registro da execução atual (02/11/2026, fuso da estudante)

- A estudante autorizou explicitamente: (a) **somente** correção 2 do Prompt 1 — `SECRET_KEY` estável em produção e configurações seguras dos cookies; (b) implementação/execução dos cenários do Prompt 3.
- `app.py:28–49`: `RUMO_ENV=production` exige SECRET_KEY, cookie Secure automático, HTTPOnly e SameSite preservados; dev local continua HTTP. `.env.example` e `README.md` atualizados. Nenhum dado nem schema modificado.
- `tests/conftest.py` e três módulos `test_*.py`: **21 casos** com Flask test client, banco SQLite temporário por teste e caminhos de concorrência com clientes/conexões independentes. Não há mocks de banco.
- Comandos reais: `python -m compileall -q app.py tests` → sucesso; `python -m pytest -q` → código 4 por `ModuleNotFoundError: flask` na importação de `conftest`, **nenhum teste integrado rodou**; `python docs/evidencias/verificar_correcao_01.py` → 7/7 verificações isoladas SQLite passaram. Logs em `docs/evidencias/`.
- Flask local Windows e interface/cronograma: fotografias de tela compartilhadas pela estudante; 7 capturas salvas em `docs/evidencias/`. Nenhuma afirmação de publicação, commit ou push.
- AUDITORIA.md mantido como fotografia original de antes das correções; Prompt 2 não iniciado e sem aprovação.


## Evidência de execução do Prompt 3 — 02/11/2026, Windows

- Comando usado pela estudante: `py -m pytest -q 2>&1 | Tee-Object -FilePath docs\evidencias\pytest_windows.txt`.
- Saída visível na captura real: `21 passed in 11.38s` — **21 aprovados, 0 falhas**.
- Captura copiada para `docs/evidencias/08_pytest_21_aprovados.png`.
- Evidência original do terminal `pytest_windows.txt` já criada no computador da estudante, **não incluída nesta atualização**.
- A auditoria original `AUDITORIA.md` não foi alterada.
- Nenhuma refatoração, push GitHub ou publicação foi realizada nesta atualização documental.


## Atualização — Prompt 2 executado após autorização explícita

- **Aprovação recebida:** estudante autorizou a extração apenas das quatro validações previstas e o envio do ZIP.
- **Arquivos modificados:** `app.py` (imports e remoção de funções internas), `validacoes.py` (novo), `docs/REFATORACAO.md`, `docs/TESTES.md`, `docs/RESULTADOS_DOS_PROMPTS.md`, `README.md`, `PROGRESSO.md`. Novo `docs/GUIA_GITHUB_PUBLICACAO.md`.
- **Verificações reais:** AST das quatro funções idêntica à original (ignorando posição); compilação de `app.py`, `validacoes.py` e `tests/` sem erros. Consulte `docs/evidencias/refatoracao_02_verificacao.txt`.
- **Limite:** pytest no ambiente de geração continua bloqueado por ausência do Flask. A suíte pós-refatoração deve ser executada no Windows. Resultado anterior: 21 aprovados em 11,38 s ANTES da mudança.
- **Banco:** nenhum arquivo SQLite pessoal foi copiado ou alterado. O ZIP da atualização não contém `instance/rumo.sqlite3`.
- **Etapa atual:** Prompt 2 executado; executar regressão no Windows e realizar GitHub + PythonAnywhere. Nenhum commit/push ou site público foi criado por este processo.
- **Próxima ação:** `py -m pytest -q 2>&1 | Tee-Object -FilePath docs\evidencias\pytest_apos_refatoracao.txt` e seguir `docs/GUIA_GITHUB_PUBLICACAO.md`. Atualizar URLs reais e evidências após deploy.
