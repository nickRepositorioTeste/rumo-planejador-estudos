# Rumo — Planejador de Estudos

Aplicação acadêmica para cadastrar concursos e disciplinas, configurar horários, gerar um cronograma de estudos e registrar simulados com notas calculadas conforme regras informadas pelo usuário.

**Publicação: pendente.** **Repositório GitHub: pendente.** Não há URL pública confirmada.

## Funcionalidades

- Registro e login com senha armazenada por hash; cada pessoa acessa somente os próprios concursos.
- CRUD de concursos e disciplinas com questões, pesos, penalidade, mínimos e metas.
- Cadastro, atualização e exclusão de horários semanais; bloqueio de datas.
- Geração de sessões até a véspera da prova, edição, exclusão e conclusão com tempo real e notas.
- Cadastro, edição, exclusão e histórico de simulados, com regras de pontuação armazenadas em cada registro.
- Dashboard com concursos, sessões, minutos realizados e simulados recentes.

## Tecnologias

Python, Flask, SQLite, Jinja, HTML/CSS/JavaScript e pytest. **Ferramenta de IA: ChatGPT** para gerar esta versão; o Codex foi planejado, mas a extensão não funcionou nesta execução. Não atribuir o código ao Codex indevidamente.

## Execução no Windows (PowerShell, na pasta raiz do projeto)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SECRET_KEY = "defina-uma-chave-aleatoria-grande-e-privada"
python app.py
```

Abra http://127.0.0.1:5000/ e crie uma conta. Para interromper, use Ctrl+C. Caso o PowerShell bloqueie a ativação, use `cmd` e `.venv\Scripts\activate.bat`. Para gerar uma chave aleatória: `python -c "import secrets; print(secrets.token_hex(32))"` e defina o valor no ambiente, nunca no código ou no Git.

Banco SQLite criado automaticamente em `instance/rumo.sqlite3` ao iniciar; os dados persistem no arquivo. Esse diretório é ignorado pelo Git. Não compartilhe arquivo do banco real.

**Ambiente de produção — obrigatório:** configure `RUMO_ENV=production` e uma `SECRET_KEY` aleatória, longa e **persistente** nas variáveis de ambiente da hospedagem. Sem essa chave, o aplicativo agora **recusa iniciar** em produção, impedindo sessões inválidas após reinício. O atributo `Secure` do cookie fica ativado automaticamente em produção; portanto, use **HTTPS**. `HttpOnly` e `SameSite=Lax` são mantidos. Não habilite `COOKIE_SECURE=1` ao usar `http://127.0.0.1:5000` no desenvolvimento local, para não impedir o envio do cookie. O arquivo `.env.example` é apenas modelo e **não é carregado automaticamente**. O fallback de chave aleatória só existe em ambiente local de desenvolvimento.

A publicação exige disco persistente para SQLite, instalação de `requirements.txt`, servidor WSGI compatível e `debug=False`. As condições gerais da opção PythonAnywhere foram consultadas em sua documentação oficial; ainda não há URL real nem deploy confirmados. Não use filesystem efêmero afirmando que preservará os registros.

## Testes

**21 testes de integração foram escritos após aprovação dos cenários**, usando cliente HTTP real do Flask e banco SQLite temporário por teste, sem tocar `instance/rumo.sqlite3`:

```powershell
py -m pytest -q
```

Para registrar a evidência no Windows (na raiz do projeto):

```powershell
py -m pytest -q 2>&1 | Tee-Object -FilePath docs/evidencias/pytest_windows.txt
```

**Execução confirmada no Windows da estudante em 02/11/2026:** `21 passed in 11.38s` — **21 testes aprovados e 0 falhas**. Evidência visual real em `docs/evidencias/08_pytest_21_aprovados.png`; o comando também salvou a saída em `docs/evidencias/pytest_windows.txt` no computador da estudante. A tentativa anterior no ambiente de geração falhou por falta de Flask, antes da coleta; não representa o resultado dos testes no Windows. As 7 verificações SQLite isoladas da correção 1 também passaram, mas são testes distintos.

## Regras principais

Nota por disciplina = acertos × pontos por acerto − erros × penalidade. Brancos valem zero; notas negativas são mantidas; cálculos usam `Decimal`, armazenamento como texto numérico e exibem precisão completa da representação. O simulado preserva pesos e mínimos da data do registro. Os resultados mostram separadamente o alcance dos mínimos configurados e das metas pessoais, sem prometer classificação.

O cronograma cria blocos de até 50 minutos e intervalos de 10 minutos, até a véspera da prova. Rodízio ponderado por `questões × pontos por acerto` (peso mínimo de alocação igual a 1). Sessões concluídas são preservadas na regeneração. Novas sessões não se sobrepõem às sessões de nenhum dos seus concursos: blocos conflitantes são ignorados e comunicados, e, caso não exista horário livre, a geração é revertida para preservar registros anteriores. A edição de sessões também rejeita horários conflitantes. Consulte a auditoria inicial e o acompanhamento das correções antes do uso real.

## Limitações e links da documentação

Projeto acadêmico local, ainda sem deploy, com 21 testes de integração aprovados no Windows, com capturas de validação visual manual compartilhadas pela estudante e sem suporte a múltiplas janelas no mesmo dia, indicadores gráficos avançados, recuperação de senha, registros de pontuação em módulos ou sessões automáticas específicas de simulados. A edição de sessões valida conflitos no servidor. Verificação isolada SQLite passou e há capturas reais de telas; os testes HTTP/Flask foram executados com 21 aprovações no Windows; ainda faltam publicação e regressão após eventual refatoração. Apenas um intervalo por dia da semana.

- [Planejamento](docs/PLANEJAMENTO.md)
- [Auditoria inicial](AUDITORIA.md)
- [Segurança](docs/SEGURANCA.md)
- [Testes](docs/TESTES.md)
- [Refatoração](docs/REFATORACAO.md)
- [Problemas e correções](docs/PROBLEMAS_E_CORRECOES.md)
- [Resultado dos prompts](docs/RESULTADOS_DOS_PROMPTS.md)
- [Entrega Classroom](docs/ENTREGA_CLASSROOM.md)
- [Progresso](PROGRESSO.md)


## Verificação da correção 1 (isolada, sem Flask)

Na pasta raiz, execute `python docs/evidencias/verificar_correcao_01.py`. Este script usa somente a biblioteca padrão e um SQLite temporário. O resultado de referência está em `docs/evidencias/correcao_01_verificacao.txt` e contém 7 verificações bem-sucedidas. **Não substitui** os testes de integração do Prompt 3 nem o teste da aplicação no navegador.

O arquivo `AUDITORIA.md` conserva os achados originais. A aprovação e implementação da correção de horários estão registradas em `docs/SEGURANCA.md`, `docs/PROBLEMAS_E_CORRECOES.md` e `PROGRESSO.md`.


## Evidências de interface

Sete capturas reais fornecidas pela estudante (VS Code, Flask rodando, dashboard, concurso e cronograma) estão em `docs/evidencias/`. Elas atestam os fluxos visíveis nas imagens, **não** toda a suíte de testes, a persistência após reinício ou a publicação. Confira `docs/evidencias/INDICE.md`.


## Refatoração (Prompt 2) e publicação

Após autorização explícita, quatro funções de validação puras saíram de `app.py` para `validacoes.py`, sem mudar a lógica. A comparação estrutural e a compilação foram concluídas com sucesso. **Os 21 testes aprovados no Windows são anteriores à refatoração. Reexecute agora** `py -m pytest -q` e registre `docs/evidencias/pytest_apos_refatoracao.txt` antes de publicar. O registro completo está em `docs/REFATORACAO.md`.

**Guia passo a passo:** [GitHub e deploy PythonAnywhere](docs/GUIA_GITHUB_PUBLICACAO.md). A publicação é pendente até confirmar URLs e persistência.
