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
- **Migrações:** `db/migracoes/` tem as alterações de estrutura para bancos que já existem. O `setup_db.py` só aplica o esquema em banco vazio, então em um banco existente rode a migração à mão, uma vez, na ordem dos números (por exemplo `psql "$DATABASE_URL" -f db/migracoes/002_faixas_lp.sql`). Os arquivos usam `IF NOT EXISTS` e podem ser reaplicados.
- **Schema de destino:** o script usa o `search_path` da `DATABASE_URL`. Sem o parâmetro `options`, o schema é `public`. Para usar outro schema, como em uma cópia de teste, adicione `?options=-csearch_path%3Dnome_do_schema`.
- **Capas:** ficam em `CAPAS_DIR` (padrão `dados/capas`), com caminhos relativos como `livro/L0049.jpg`, iguais aos gravados na coluna `capa_arquivo`. Para usar as capas de um servidor, aponte `CAPAS_DIR` para a pasta delas. As capas não vão para o git.

## Deploy no um1 (Jenkins + systemd)

O job `catalogo-web` no Jenkins do um1 lê o `Jenkinsfile` deste repositório, verifica o código e chama `/opt/catalogo-web/deploy-catalogo-web.sh`. O script instala o app em `/opt/catalogo-web`, aplica o esquema se preciso e reinicia o serviço `catalogo-web`.

- **Porta:** 8092, liberada no UFW só para a rede local (`192.168.0.0/24`).
- **Usuário do serviço:** `catalogo-web` (sistema, sem login).
- **Configuração:** `/etc/catalogo-web/catalogo-web.env`, com `DATABASE_URL` e `CAPAS_DIR`. Esse arquivo fica só no servidor, com dono `root` e permissão `0640`. Não vai para o git.
- **Banco:** o serviço usa um usuário só de leitura. Para instalar em um banco vazio, use um usuário com permissão para criar tabelas, temporariamente, na `DATABASE_URL`.
- **Script de deploy:** a cópia em `deploy/` serve de referência. O que roda como root é o arquivo em `/opt/catalogo-web/`, que só o root altera.

Logs: `journalctl -u catalogo-web -f`.

## Endpoints

| Rota | O que faz |
|---|---|
| `/` | redireciona para `/livros` |
| `/livros`, `/gibis`, `/vinil` | aba com a grade de capas paginada (`?pagina=N`), filtros opcionais e ordenação (`?ordem=`) |

Ordenação (`ordem`), por aba: `codigo` (padrão), `titulo`, `autor` (autor, equipe ou artista), `editora` (livros e gibis) ou `gravadora` (vinil), `ano_asc` e `ano_desc`. Valor desconhecido cai no padrão.

Filtros aceitos (todos combináveis; a busca de texto usa `ILIKE`, então ignora maiúsculas, mas não acentos):

| Parâmetro | Aba | O que filtra |
|---|---|---|
| `q` | todas | título, código, ISBN e nome de autor, artista ou equipe |
| `ano_de`, `ano_ate` | todas | faixa de ano de publicação |
| `genero` | livros, gibis, vinil | gênero |
| `editora` | livros, gibis | editora |
| `encadernacao` | livros | encadernação (sem diferença de maiúsculas) |
| `categoria` | gibis | categoria (Gibi, Graphic Novel, Mangá) |
| `gravadora` | vinil | gravadora |
| `/api/<tipo>/<codigo>` | JSON com os dados do item, usado pelo popup |
| `/capas/<arquivo>` | serve as imagens de capa |

## Edição manual e login

Cada livro, gibi e vinil tem um link "Editar campos" no popup. A edição mexe nos campos próprios do item (título, editora, ISBN, preço, observações etc.). Nos livros, o campo Autor(es) aceita vários nomes separados por vírgula. Gêneros e faixas ainda não são editados por aqui. Editora, estante e gravadora são informadas pelo nome: se o nome não existir, é cadastrado.

A edição fica **desligada** até que todas estas variáveis estejam no `.env` (ou no arquivo de configuração do servidor):

- `DATABASE_URL_ESCRITA`: conexão do usuário `catalogo_escrita`, que só tem escrita nas colunas editáveis (`db/migracoes/003_permissoes_escrita.sql`).
- `CATALOGO_ADMIN_USUARIO`: nome do usuário que entra.
- `CATALOGO_ADMIN_SENHA_HASH`: hash da senha, não a senha em si. Gere com:
  ```powershell
  .\.venv\Scripts\python.exe -c "from werkzeug.security import generate_password_hash as g; print(g('SUA_SENHA'))"
  ```
- `CATALOGO_SECRET_KEY`: texto longo e aleatório, fixo. Com ele vazio, a edição não liga, porque sem chave fixa o login falha entre os processos do gunicorn.

Na página "Editar campos" também dá para trocar a capa: arrastando o arquivo para a área, clicando nela ou colando uma imagem com Ctrl+V. Aceita JPG, PNG e WEBP, até 5 MB. A capa vai para `CAPAS_DIR` (`livro/`, `gibi/` ou `lp/`), então a pasta precisa ser gravável pelo serviço.

Depois do login, o link "Alterar senha" troca a senha. A nova senha fica guardada no banco, na tabela `admin_senha`, e passa a valer no lugar de `CATALOGO_ADMIN_SENHA_HASH`.

Migrações da edição, em ordem, a aplicar uma vez em cada banco: `003_permissoes_escrita.sql`, `004_senha_admin.sql` e `005_permissao_capa.sql`. O papel `catalogo_escrita` precisa existir antes.

Sem essas variáveis, o site continua só de leitura e a página "Entrar" avisa que a edição não está configurada. A sessão dura 8 horas. Cada senha errada espera 1 segundo. Os formulários têm token contra pedidos forjados.

O site roda em HTTP na rede local, então a senha trafega sem criptografia. Não publique esta porta fora da rede sem HTTPS na frente.

Testes da edição (rodam no banco do `.env`, com um registro temporário T9999 que é removido no fim):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

## Ajustes

- Itens por página: `ITENS_POR_PAGINA` em `app/__init__.py` (padrão 24).
- Campos do popup e seus rótulos: `CAMPOS_POPUP` em `app/catalogo.py`.
- Texto que aparece sob a capa (sinopse nos livros e gibis, observações no vinil e no álbum): `SINOPSE` em `app/catalogo.py`. Ele sai da lista de campos do popup para não aparecer duas vezes.
- Tema claro e escuro: variáveis CSS em `app/static/css/style.css`.

## Observações

- Não há autenticação. A página é só de leitura. Ao publicar fora da rede local, coloque o app atrás de um proxy (nginx) com controle de acesso.
- A senha do banco fica só no `.env`, que está no `.gitignore`.
