# Catálogo web

Página pública (sem login) que lê um catálogo pessoal no PostgreSQL e mostra livros, gibis e vinis em grade de capas, paginada. Clicar numa capa abre um popup com os dados do item.

## Stack

- **Python 3.12** e **Flask 3** (padrão mais usado para apps pequenos em Python)
- **psycopg 3** com **psycopg-pool** (driver oficial do PostgreSQL para Python e pool de conexões)
- **Jinja2** para as páginas no servidor, sem framework de front-end
- JavaScript puro para o popup, usando `<dialog>` nativo

Estrutura:

```
app/
  __init__.py     fábrica do app (create_app) e configuração
  db.py           pool de conexões e helpers de consulta
  catalogo.py     consultas SQL por tipo, paginação e formatação do popup
  routes.py       rotas: abas, paginação, API do popup e capas
  templates/      base.html e lista.html
  static/         css/style.css e js/app.js
db/
  schema.sql      esquema do banco (só estrutura, sem dados)
setup_db.py       aplica o esquema no banco configurado
run.py            ponto de entrada do servidor
dados/capas/      cópia local das capas (fica fora do git)
```

## Instalação

1. Crie o `.env` a partir do exemplo e preencha a senha do banco:

   ```powershell
   Copy-Item .env.example .env
   ```

   O `.env` não vai para o git. Ele guarda a `DATABASE_URL` com usuário e senha.

2. Crie o ambiente virtual e instale as dependências:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Aplique o esquema no banco. O comando cria as tabelas no schema da `DATABASE_URL` e não apaga nada. Se a tabela `livro` já existir, ele não faz alterações:

   ```powershell
   .\.venv\Scripts\python.exe setup_db.py
   ```

   Antes disso, o banco e o usuário precisam existir e o usuário precisa ter permissão para criar tabelas. O esquema não inclui dados. Para trazer um catálogo existente, restaure os dados separadamente.

4. Suba o servidor:

   ```powershell
   .\.venv\Scripts\python.exe run.py
   ```

5. Abra http://127.0.0.1:5000

## Banco de dados

- **Schema:** `db/schema.sql` foi gerado com `pg_dump --schema-only`. Para atualizá-lo depois de mudar o banco, gere o dump de novo e remova a linha `SELECT pg_catalog.set_config('search_path', '', false);`, que zera o `search_path` e impede o `setup_db.py` de criar as tabelas.
- **Schema de destino:** o script usa o `search_path` da `DATABASE_URL`. Sem o parâmetro `options`, o schema é `public`. Para usar outro schema, como em uma cópia de teste, adicione `?options=-csearch_path%3Dnome_do_schema`.
- **Capas:** ficam em `CAPAS_DIR` (padrão `dados/capas`), com caminhos relativos como `livro/L0049.jpg`, iguais aos gravados na coluna `capa_arquivo`. Para usar as capas de um servidor, aponte `CAPAS_DIR` para a pasta delas. As capas não vão para o git.

## Endpoints

| Rota | O que faz |
|---|---|
| `/` | redireciona para `/livros` |
| `/livros`, `/gibis`, `/vinil` | aba com a grade de capas paginada (`?pagina=N`) |
| `/api/<tipo>/<codigo>` | JSON com os dados do item, usado pelo popup |
| `/capas/<arquivo>` | serve as imagens de capa |

## Ajustes

- Itens por página: `ITENS_POR_PAGINA` em `app/__init__.py` (padrão 24).
- Campos do popup e seus rótulos: `CAMPOS_POPUP` em `app/catalogo.py`.
- Tema claro e escuro: variáveis CSS em `app/static/css/style.css`.

## Observações

- Não há autenticação. A página é só de leitura. Ao publicar fora da rede local, coloque o app atrás de um proxy (nginx) com controle de acesso.
- A senha do banco fica só no `.env`, que está no `.gitignore`.
