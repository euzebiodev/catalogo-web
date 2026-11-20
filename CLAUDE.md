# catalogo-web

Site de leitura do acervo pessoal (livros, gibis, vinis e álbuns de figurinhas), com edição protegida por login. O dono do projeto é o Euzebio, que responde sempre em português.

## Stack

- Python 3.12, Flask 3, psycopg 3 com psycopg-pool, Jinja2, JavaScript puro (sem framework de front-end).
- PostgreSQL. Em produção, o banco fica no servidor um1 (192.168.0.229).
- Deploy: Jenkins no um1 (job `catalogo-web`, `pollSCM` a cada 5 min) executa `/opt/catalogo-web/deploy-catalogo-web.sh`, que instala em `/opt/catalogo-web` e reinicia o serviço systemd `catalogo-web` (gunicorn, porta 8092, acesso só pela LAN).

## Estrutura

- `app/`: `__init__.py` (create_app e configuração), `db.py` (pools de conexão), `catalogo.py` (consultas SQL e formatação do popup), `routes.py` (rotas), `auth.py` (login, senha e CSRF), `edicao.py` (formulários de edição), `templates/`, `static/`.
- `db/schema.sql`: esquema sem dados, usado só em banco vazio.
- `db/migracoes/`: migrações numeradas (002 a 021). Não são aplicadas automaticamente.
- `deploy/deploy-catalogo-web.sh`: cópia de referência do script de deploy. O que roda como root é o arquivo em `/opt`.
- `restauracao/`: scripts de restauração de backup. O `restauracao.conf` real fica fora do git.
- `tests/`: testes de filtros da lista e de edição.
- `setup_db.py`: aplica o esquema em banco vazio. Não altera banco que já tenha a tabela `livro`.
- `run.py`: ponto de entrada.

## Comandos

- Ambiente (Windows): `python -m venv .venv` e `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Servidor local: `.\.venv\Scripts\python.exe run.py`, em http://127.0.0.1:5000.
- Testes: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v`. Os testes rodam no banco do `.env` e criam itens temporários (T9001 etc.) que são removidos no fim. Use o schema de teste.
- Verificação de sintaxe, como no Jenkins: `python -m compileall -q app run.py setup_db.py`.

## Configuração e segredos

- O `.env` fica só na máquina local e está no `.gitignore`. Ele guarda `DATABASE_URL`, `DATABASE_URL_ESCRITA`, `CATALOGO_ADMIN_USUARIO`, `CATALOGO_ADMIN_SENHA_HASH` e `CATALOGO_SECRET_KEY`.
- Em produção, as variáveis ficam em `/etc/catalogo-web/catalogo-web.env` (root, modo 0640), no servidor.
- Nunca grave senha, token ou `DATABASE_URL` com senha em arquivo versionado, em comentário, em exemplo ou no chat. `.env.example` deve ter só placeholders.
- Edição desligada se faltar alguma variável de escrita. Sem `CATALOGO_SECRET_KEY` fixa, o login falha entre os workers do gunicorn.

## Regras de trabalho

- Migrações: aplique em produção só com aval explícito. Elas são aplicadas à mão, uma vez, na ordem numérica. Antes de criar uma nova, use o próximo número livre.
- Banco de produção (um1): não execute escrita, DDL ou migração sem confirmação. Leituras de diagnóstico são aceitáveis quando pedidas.
- Testes: rode a suíte antes de dizer que uma alteração está pronta. Se algo falhar, informe a saída, sem resumir.
- Commit e push: só quando o usuário pedir. Ao criar commit, use o formato de mensagem já usado no histórico (por exemplo, `Editar: ...`, `Filtros: ...`).
- Não há autenticação na leitura (é uma página pública na LAN). Não exponha a porta 8092 nem o site sem proxy com HTTPS e controle de acesso.
- O README tem informações antigas (diz que o serviço usa só usuário de leitura e que não há autenticação). Ao mexer nessas partes, atualize o README.
- Arquivos não versionados atuais: `.vscode/` e `db/migracoes/018_permissao_autores_gibi.sql`. Não os apague nem os inclua em commits sem pedido.
- Capas e dados locais ficam em `dados/` (fora do git) e em `CAPAS_DIR`. Não versione imagens.
