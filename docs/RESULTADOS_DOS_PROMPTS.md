# Resultados dos quatro prompts — ordem obrigatória 4 → 1 → 3 → 2

| Prompt | Objetivo | Resultado real | Status |
|---|---|---|---|
| 4 — Auditoria completa | Inspecionar testes, confiança, concorrência, idempotência, responsabilidades sem mudar código | Achados em `AUDITORIA.md`; cinco achados principais identificados por inspeção estática | Auditoria inicial redigida; testes dinâmicos não executados |
| 1 — Segurança | Auditar segurança e propor correções | Relatório e plano em `docs/SEGURANCA.md`; correção 1 de horários aprovada e aplicada, com verificação isolada 7/7 | Parcial: próximas correções aguardam aprovação |
| 3 — Testes de integração | Propor cenários, confirmar, implementar e executar | 21 cenários automatizados aprovados no Windows em 11,38 s; `docs/TESTES.md` e captura de tela | Concluído para a suíte executada; repetir após refatoração |
| 2 — Refatoração | Extrair validações puras, preservar comportamento e conferir regressões | Quatro funções movidas para `validacoes.py` com AST 4/4 idêntica e sintaxe validada | Autorizada e aplicada; pytest pós-mudança pendente no Windows |

## Evidências reais

- `python -m compileall -q app.py` → executado após correção de sintaxe, saída silenciosa e código de saída 0.
- `python -m pip install flask -q` → falhou por indisponibilidade de DNS/índice de pacotes.
- `git status --short` → falhou porque esta pasta não é um repositório Git.
- Testes de integração, screenshots, commits, push e publicação → **não realizados**.

## Decisões e aprovações

- Planejamento reduzido e desenvolvimento da Etapa 2: **aprovados pelo usuário nesta conversa**.
- Correções do Prompt 1: **correção 1 aprovada expressamente e aplicada**; itens 2 a 4 **não aprovados**.
- Cenários e implantação do Prompt 3: **não aprovados**.
- Refatoração do Prompt 2: **não aprovada**.

## Reflexão pessoal

Pendente de preenchimento da estudante. Perguntas disponíveis em `docs/ENTREGA_CLASSROOM.md`; nenhuma experiência pessoal foi inventada.


## Registro adicional — primeira correção do Prompt 1

- **Aprovação da estudante:** recebida no chat: “Autorizo a primeira correção do Prompt 1: impedir sessões sobrepostas, preservar sessões concluídas e registrar a correção e sua verificação nos arquivos do projeto.”
- **Mudança:** criada verificação de sobreposição entre concursos do mesmo proprietário; geração e edição com `BEGIN IMMEDIATE`, sem criar intervalos conflitantes; concluídas preservadas; rollback se não houver horários disponíveis.
- **Verificação isolada executada:** 7 checagens concluídas sem falhas em SQLite temporário (`docs/evidencias/correcao_01_verificacao.txt`). A ferramenta não usou Flask; não é teste integrado HTTP/pytest.
- **Auditoria inicial:** `AUDITORIA.md` mantida como diagnóstico anterior à correção, sem reescrever achados históricos.
- **Próxima aprovação:** correção 2 sobre chave de sessão estável em produção. Cenários do Prompt 3 e refatoração do Prompt 2 continuam sem aprovação.


## Atualização aprovada — Prompt 1 (correção 2) e Prompt 3

A estudante aprovou, em mensagem explícita nesta conversa, **somente** a exigência de chave estável em produção e configuração segura do cookie (Prompt 1, correção 2), além dos cenários e execução dos testes do Prompt 3. Correções de segurança adicionais e refatoração continuam pendentes de aprovação separada.

- Prompt 1, correção 2: ajustado `create_app()` para exigir `SECRET_KEY` quando `RUMO_ENV=production` e ativar `SESSION_COOKIE_SECURE`; documentado em `docs/SEGURANCA.md`. Não alterar `AUDITORIA.md` original.
- Prompt 3: 21 casos criados em `tests/`, com `tmp_path` e Flask test client. **Execução não concluída:** `python -m pytest -q` retornou código 4 por falta de Flask na máquina de geração; log `docs/evidencias/pytest_execucao_ambiente.txt`. Não há contagem de testes integrados aprovados/reprovados.
- Verificador anterior: `python docs/evidencias/verificar_correcao_01.py` retornou 7/7 checagens SQLite isoladas, **não** equivalentes aos testes integrados.
- Prompt 2: nenhum código refatorado, em cumprimento à exigência de aprovação antes da refatoração.
- Imagens de evidência: 7 capturas de tela reais compartilhadas pela estudante, organizadas em `docs/evidencias/`; não criadas artificialmente.


## Resultado posterior — Prompt 3, Windows, 02/11/2026

A estudante mostrou captura real do terminal executando `py -m pytest -q 2>&1 | Tee-Object -FilePath docs\evidencias\pytest_windows.txt`. Resultado mostrado: **21 passed in 11.38s**, sem falhas. Evidência visual arquivada em `docs/evidencias/08_pytest_21_aprovados.png`. As declarações anteriores de impossibilidade de execução referem-se exclusivamente ao ambiente de geração, que não possuía Flask, e ficam preservadas como histórico.

**Prompt 2 nessa atualização histórica:** plano apresentado e ainda não autorizado naquela etapa. A aprovação e a implementação posteriores estão registradas abaixo. GitHub e publicação seguem pendentes.


## Atualização posterior — Prompt 2 autorizado e implementado

- **Aprovação:** estudante autorizou explicitamente extrair somente as validações do `app.py` conforme o plano.
- **Modificação:** `number`, `integer`, `day_value` e `valid_time` transferidas literalmente para `validacoes.py`; imports ajustados em `app.py`.
- **Verificado neste ambiente:** quatro funções com AST idêntica; sintaxe do app, módulo e testes aprovada. Saída em `docs/evidencias/refatoracao_02_verificacao.txt`.
- **Não verificado aqui:** 21 testes Flask após a refatoração, por ausência de dependência Flask nesta máquina. O resultado anterior de 21/21 refere-se à versão anterior. Rodar no Windows e salvar em `docs/evidencias/pytest_apos_refatoracao.txt` antes do GitHub.
- **Próximo:** publicar repositório, implantar no PythonAnywhere e inserir URLs reais, conforme `docs/GUIA_GITHUB_PUBLICACAO.md`.
