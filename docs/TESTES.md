# Testes de integração — Prompt 3 (cenários aprovados)

**Status atualizado em 02/11/2026, 23h13–23h14 (horário de Brasília):** os 21 testes `pytest` foram executados no Windows da estudante: **21 aprovados, 0 falhas, em 11,38 segundos**. Evidência: captura real `docs/evidencias/08_pytest_21_aprovados.png` e saída do terminal já salva localmente em `docs/evidencias/pytest_windows.txt` (arquivo não acessível a este ambiente de geração, não reproduzido nem fabricado). Os testes usam rotas Flask e SQLite temporário por teste. A tentativa anterior no ambiente de geração falhou por ausência de Flask; trata-se de **outro ambiente**, e não invalida o resultado confirmado no Windows.

## Cenários propostos

1. Quando cadastrar com dados válidos, então criar usuário; senha não aparece em texto puro no banco.
2. Quando fizer login com senha errada, então não autenticar; quando correta, então permitir acesso.
3. Quando A tentar abrir/editar/excluir concursos, disciplinas, sessões ou simulados de B, então receber 404 e não modificar dados.
4. Quando cadastrar, listar, editar e excluir concurso e disciplina, então persistir mudanças e respeitar chaves estrangeiras.
5. Quando enviar data inválida ou campos inválidos, então não persistir parcialmente.
6. Quando configurar quarta-feira 07h–11h e bloquear uma data, então a geração não ultrapassa 11h nem usa a data bloqueada.
7. Quando prova já passou ou não houver disponibilidade, então mostrar mensagem e não gerar sessões.
8. Quando gerar duas vezes, então não duplicar; quando concluir uma sessão, regenerar preserva a concluída.
9. Quando acertos + erros + brancos diferirem do total, então rejeitar o simulado sem persistir.
10. Quando penalidade for configurada, então descontar erros; brancos valem zero, notas negativas são preservadas.
11. Quando o mínimo for alcançado mas a meta não, então mostrar indicadores distintos.
12. Quando editar regras do concurso após salvar simulado, então manter nota histórica e recalcular edições do simulado com snapshots.
13. Quando enviar POST sem token CSRF, então rejeitar a operação.
14. Quando houver dupla geração simultânea por conexões independentes, então investigar duplicidade e sobreposição; não presumir que SQLite elimina corrida.
15. Quando persistir dados e reiniciar a aplicação com o mesmo arquivo de teste, então os dados continuam presentes.

## Execução prevista

Fixtures com `tmp_path`, `create_app({'TESTING': True,'DATABASE': caminho_temporario,'SECRET_KEY': 'segredo-de-teste'})` e cliente real Flask. Banco real SQLite temporário sem mocks. Comando: `python -m pytest`.

## Implementação após autorização da estudante

Autorização recebida em 02/11/2026 (horário de Brasília) para os cenários do Prompt 3. Foram criados:

- `tests/conftest.py`: app factory `create_app` com configuração de testes, `tmp_path`, cada teste com seu **próprio arquivo SQLite**, sessão Flask e CSRF reais; consultas diretas ao banco apenas para verificação. Nunca usa `instance/rumo.sqlite3`.
- `tests/test_auth_security.py`: seis cenários de registro, login, hash, CSRF, cabeçalhos de cookie, exigência de chave em produção, escape HTML e isolamento entre dois usuários.
- `tests/test_crud_schedule.py`: dez cenários de CRUD, validação, bloqueios, horários, persistência após reabrir app, regeneração, conflito e duas requisições simultâneas com clientes e conexões independentes.
- `tests/test_mock_scores.py`: cinco cenários de pontuação Decimal, penalidade, nota negativa, limites/metas, formulários inválidos e preservação de snapshots históricos.

Total no código-fonte: **21 funções de teste**. Nenhum acesso a produção, sem mock de banco/autorização e sem manipulação do arquivo de dados pessoal. Concorrência não prova ausência de todos os interleavings possíveis. A suíte não executa navegador nem cobre integralmente o layout móvel.

### Tentativas de execução e evidências reais

- `python -m compileall -q app.py tests` → **sucesso (código de saída 0)**, sintaxe de código e testes compilada.
- `python -m pytest -q` → **código de saída 4**: `ImportError while loading conftest`, `ModuleNotFoundError: No module named 'flask'` **antes da coleta**. Registro literal em `docs/evidencias/pytest_execucao_ambiente.txt`. Logo, nenhum resultado positivo de integração foi obtido; os 21 ainda precisam ser rodados.
- `python docs/evidencias/verificar_correcao_01.py` → **7/7 verificações isoladas SQLite passaram** (este verificador **não** usa Flask/pytest); reexecução registrada em `docs/evidencias/correcao_01_reexecucao.txt`.
- Capturas reais da estudante no Windows demonstram que Flask iniciou e que telas de concursos/cronograma foram usadas; não substituem a execução dos testes.

### Execução confirmada — Windows da estudante

Na raiz do projeto, com `requirements.txt` já instalado:

```powershell
py -m pytest -q
```

Para salvar a saída também em arquivo:

```powershell
py -m pytest -q 2>&1 | Tee-Object -FilePath docs/evidencias/pytest_windows.txt
```

**Resultado verificado pela captura do terminal:** `21 passed in 11.38s` (21 aprovados e 0 falhas). O arquivo de evidência `pytest_windows.txt` foi criado no Windows pelo próprio comando, conforme a tela de execução, mas seu conteúdo não foi aberto neste ambiente. O print é a evidência diretamente inspecionada. Em novas alterações, executar novamente a suíte para detectar regressões.



## Regressão obrigatória após a refatoração do Prompt 2

A captura `08_pytest_21_aprovados.png` registra **21/21 antes da refatoração**. Depois da extração de funções para `validacoes.py`, a verificação estrutural e a compilação passaram, mas **a suíte Flask ainda não foi executada na versão atual** no ambiente de geração por falta do Flask. Executar no Windows:

```powershell
py -m pytest -q 2>&1 | Tee-Object -FilePath docs\evidencias\pytest_apos_refatoracao.txt
```

Preencher o resultado realmente exibido, sem presumir 21/21.
