# Rumo — Publicação no GitHub e no PythonAnywhere

Este guia acompanha a entrega do projeto. **Os passos de GitHub e deploy precisam ser executados na conta da estudante**. Não há push ou URL pública confirmada neste arquivo. Antes de publicar, execute `py -m pytest -q` **após** esta refatoração e confira o resultado.

## A. GitHub (no PowerShell do VS Code, na pasta `rumo-planejador-estudos`)

1. Conferir o banco ignorado (não publicar SQLite pessoal):
   ```powershell
   git --version
   git init
   git branch -M main
   git check-ignore instance/rumo.sqlite3
   git status --short
   ```
   O `check-ignore` deve mostrar `instance/rumo.sqlite3` caso o banco já exista. `.env`, `.venv/` e caches também estão no `.gitignore`.
2. Adicionar e criar primeiro commit:
   ```powershell
   git add .
   git status --short
   git commit -m "Entrega academica Rumo: Flask, auditorias, testes e evidencias"
   ```
   **Confira `git status --short` antes do commit**; não versionar senhas ou dados pessoais.
3. No site `https://github.com/new`, crie um repositório chamado `rumo-planejador-estudos` **sem** marcar README, .gitignore ou licença. Pode ser público para entrega acadêmica.
4. Copie a URL HTTPS exibida na página do GitHub e execute, substituindo o valor em maiúsculas:
   ```powershell
   git remote add origin https://github.com/SEU_USUARIO/rumo-planejador-estudos.git
   git push -u origin main
   ```
   Se a origem já existir, **não adicione novamente**: use `git remote -v` para conferir. O GitHub pode solicitar autenticação pelo navegador. **Nunca envie senhas/tokens para o chat.**
5. Confirme no navegador que README, `tests/`, `docs/` e `validacoes.py` aparecem no repositório, mas que `instance/rumo.sqlite3` **não aparece**. Só então copie o link real para `README.md` e `docs/ENTREGA_CLASSROOM.md`, faça novo commit e `git push`.

## B. PythonAnywhere — opção gratuita compatível com Flask/SQLite

A documentação oficial informa que contas gratuitas incluem uma aplicação web, 512 MiB de disco e, em novas contas, **expiração da aplicação após um mês**, exigindo renovação. SQLite é suportado em arquivo persistente, embora não seja recomendado pela plataforma para produção de maior escala. Para o exercício, pode atender. Confira as condições no cadastro.

1. Crie a conta em `https://www.pythonanywhere.com/`. Abra **Consoles → Bash**.
2. Clone o repositório **público**, usando seu usuário real:
   ```bash
   git clone https://github.com/SEU_USUARIO/rumo-planejador-estudos.git
   cd rumo-planejador-estudos
   ```
3. Crie um ambiente virtual (exemplo para Python 3.13, **somente se essa versão estiver disponível**):
   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 rumo-env
   pip install -r requirements.txt
   ```
4. Crie uma chave **persistente, fora do Git** (execute uma única vez no console; não compartilhe o valor):
   ```bash
   python -c "import secrets,pathlib; p=pathlib.Path.home()/'.rumo_secret_key'; p.write_text(secrets.token_hex(32)) if not p.exists() else None; p.chmod(0o600); print('Chave privada pronta')"
   ```
5. Vá a **Web → Add a new web app → Manual configuration**, selecione a **mesma versão Python** usada no ambiente virtual. Em **Virtualenv**, informe `rumo-env` ou `/home/SEU_USUARIO/.virtualenvs/rumo-env`.
6. Na página Web, abra o arquivo de configuração **WSGI** e substitua seu conteúdo de exemplo pelo seguinte (substitua `SEU_USUARIO` em todos os caminhos):
   ```python
   import os
   import sys
   from pathlib import Path

   folder = '/home/SEU_USUARIO/rumo-planejador-estudos'
   if folder not in sys.path:
       sys.path.insert(0, folder)

   os.environ['RUMO_ENV'] = 'production'
   os.environ['SECRET_KEY'] = Path('/home/SEU_USUARIO/.rumo_secret_key').read_text().strip()
   from app import create_app
   application = create_app()
   ```
   A chave fica em arquivo privado no servidor, não no WSGI nem no repositório. O `create_app()` é necessário: este projeto **não** exporta um objeto `app` global.
7. Configure os arquivos estáticos na aba **Static files**, se necessário: URL `/static/` apontando para `/home/SEU_USUARIO/rumo-planejador-estudos/static/`.
8. Clique **Reload**. Acesse `https://SEU_USUARIO.pythonanywhere.com/`, abra cadastro, crie usuário fictício e teste o CRUD. Reinicie pelo botão Reload e verifique se os dados persistem. Se houver erro, consulte os logs na aba Web.

**Proteção importante:** nunca copie `instance/rumo.sqlite3` do computador para o GitHub. No PythonAnywhere, o banco novo ficará em `/home/SEU_USUARIO/rumo-planejador-estudos/instance/rumo.sqlite3`, um arquivo no armazenamento da conta. Mantenha esse arquivo privado. Em produção, `RUMO_ENV=production` e `SECRET_KEY` persistente são obrigatórios, e a navegação deve usar HTTPS para que o cookie Secure funcione.

## C. Encerrar a entrega

- Confira a URL online acessível, registre print real de login e cronograma, e anote o link GitHub.
- Atualize `README.md` e `docs/ENTREGA_CLASSROOM.md` com **URLs efetivas**, e faça `git add README.md docs/ENTREGA_CLASSROOM.md; git commit -m "Registrar links da entrega"; git push`.
- No Classroom, envie o link do **repositório GitHub**, junto com a URL pública do site e o resumo pedido pelo professor.
- Se a publicação falhar, entregue primeiro o repositório completo com testes/evidências e registre `Publicação pendente`; não invente URL pública.

### Documentação oficial

- GitHub: https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
- PythonAnywhere / Flask: https://help.pythonanywhere.com/pages/Flask
- PythonAnywhere / contas gratuitas: https://help.pythonanywhere.com/pages/FreeAccountsFeatures/
- PythonAnywhere / bancos: https://help.pythonanywhere.com/pages/KindsOfDatabases
