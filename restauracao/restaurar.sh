#!/usr/bin/env bash
# Restauração completa do catálogo a partir do Google Drive criptografado (Linux).
#
# Faz, nesta ordem:
#   1. instala rclone e o cliente PostgreSQL (se faltarem);
#   2. cria o remoto "cripto" com as senhas do arquivo de configuração;
#   3. baixa o backup mais recente (dump do banco, capas e configuração);
#   4. cria o banco (vazio) e restaura estrutura e dados;
#   5. cria os usuários catalogo_leitura e catalogo_escrita se faltarem;
#   6. extrai as capas e mostra as contagens para conferência.
#
# Uso:  ./restaurar.sh [restauracao.conf]

set -euo pipefail

CONF="${1:-restauracao.conf}"
if [ ! -f "$CONF" ]; then
  echo "Arquivo de configuração não encontrado: $CONF"
  echo "Copie restauracao.exemplo.conf para restauracao.conf e preencha."
  exit 1
fi
# shellcheck disable=SC1090
. "$CONF"

passo() { printf '\n== %s\n' "$*"; }
falha() { echo "ERRO: $*" >&2; exit 1; }

# ---------- Programas ----------
instalar_programas() {
  passo "Verificando programas"
  if ! command -v rclone >/dev/null 2>&1; then
    echo "Instalando rclone..."
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y && sudo apt-get install -y rclone
    else
      curl -fsSL https://rclone.org/install.sh | sudo bash
    fi
  fi
  if ! command -v pg_restore >/dev/null 2>&1 || ! command -v psql >/dev/null 2>&1; then
    echo "Instalando cliente PostgreSQL ($PG_VERSAO)..."
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get install -y "postgresql-client-$PG_VERSAO" || sudo apt-get install -y postgresql-client
    else
      falha "instale o cliente PostgreSQL $PG_VERSAO (psql e pg_restore) e rode de novo"
    fi
  fi
  echo "rclone: $(rclone version | head -1)"
  echo "pg_restore: $(pg_restore --version)"
}

# ---------- Acesso ao banco ----------
# SQL de administração, no banco "postgres".
admin_sql() {
  if [ "$DB_ADMIN_SUDO" = "sim" ]; then
    sudo -u "$DB_ADMIN_USUARIO" psql -v ON_ERROR_STOP=1 -d postgres "$@"
  else
    PGPASSWORD="$DB_ADMIN_SENHA" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USUARIO" \
      -v ON_ERROR_STOP=1 -d postgres "$@"
  fi
}

# SQL em um banco específico: sql_banco <nome> <argumentos do psql>
sql_banco() {
  local banco="$1"; shift
  if [ "$DB_ADMIN_SUDO" = "sim" ]; then
    sudo -u "$DB_ADMIN_USUARIO" psql -v ON_ERROR_STOP=1 -d "$banco" "$@"
  else
    PGPASSWORD="$DB_ADMIN_SENHA" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USUARIO" \
      -v ON_ERROR_STOP=1 -d "$banco" "$@"
  fi
}

# ---------- Google Drive criptografado ----------
configurar_rclone() {
  passo "Configurando o acesso ao Google Drive"
  if ! rclone listremotes | grep -q "^$GDRIVE_REMOTO:"; then
    falha "o remoto '$GDRIVE_REMOTO' não existe. Rode 'rclone config', crie um remoto Google Drive com esse nome (tipo drive) e rode este script de novo."
  fi
  if rclone listremotes | grep -q '^cripto:'; then
    echo "Remoto 'cripto' já configurado."
  else
    [ -n "$CRIPTO_SENHA" ] && [ -n "$CRIPTO_SENHA2" ] || \
      falha "preencha CRIPTO_SENHA e CRIPTO_SENHA2 em $CONF (as senhas guardadas na criação do remoto)."
    local ofus1 ofus2
    ofus1="$(rclone obscure "$CRIPTO_SENHA")"
    ofus2="$(rclone obscure "$CRIPTO_SENHA2")"
    rclone config create cripto crypt \
      remote "$GDRIVE_REMOTO:catalogo-backup" \
      password "$ofus1" password2 "$ofus2" \
      filename_encryption standard directory_name_encryption true >/dev/null
    echo "Remoto 'cripto' criado."
  fi
}

baixar_backup() {
  passo "Procurando o backup mais recente"
  local nome
  if [ -n "$DUMP_ESCOLHIDO" ]; then
    nome="$DUMP_ESCOLHIDO"
  else
    nome="$(rclone lsf cripto: | grep -E '^catalogo-.*\.dump$' | sort | tail -1 || true)"
  fi
  [ -n "$nome" ] || falha "nenhum dump encontrado no remoto cripto:"
  local sufixo="${nome#catalogo-}"
  sufixo="${sufixo%.dump}"
  echo "Backup escolhido: $sufixo"

  mkdir -p "$PASTA_DOWNLOAD"
  rclone copy cripto: "$PASTA_DOWNLOAD" \
    --include "catalogo-$sufixo.dump" \
    --include "capas-$sufixo.tar.gz" \
    --include "env-$sufixo.env"

  DUMP="$PASTA_DOWNLOAD/catalogo-$sufixo.dump"
  CAPAS_TAR="$PASTA_DOWNLOAD/capas-$sufixo.tar.gz"
  [ -f "$DUMP" ] || falha "o dump não foi baixado: $DUMP"
  [ -f "$CAPAS_TAR" ] || falha "o arquivo de capas não foi baixado: $CAPAS_TAR"
  echo "Baixados: $DUMP e $CAPAS_TAR"
}

# ---------- Banco ----------
criar_papeis() {
  passo "Verificando os usuários do site"
  local par usr pwd existe
  for par in "$LEITURA_USUARIO:$LEITURA_SENHA" "$ESCRITA_USUARIO:$ESCRITA_SENHA"; do
    usr="${par%%:*}"
    pwd="${par#*:}"
    existe="$(admin_sql -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$usr'")"
    if [ -n "$existe" ]; then
      echo "Usuário $usr já existe."
    else
      [ -n "$pwd" ] || falha "a senha de $usr está vazia em $CONF."
      admin_sql -c "CREATE ROLE \"$usr\" LOGIN PASSWORD '$pwd'" >/dev/null
      echo "Usuário $usr criado."
    fi
  done
}

restaurar_banco() {
  passo "Restaurando o banco '$DB_NAME'"
  local existe tabelas
  existe="$(admin_sql -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'")"
  if [ -n "$existe" ]; then
    tabelas="$(sql_banco "$DB_NAME" -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")"
    if [ "$tabelas" != "0" ]; then
      [ "$SOBRESCREVER" = "sim" ] || falha "o banco '$DB_NAME' já tem $tabelas tabelas. Use outro DB_NAME ou SOBRESCREVER=\"sim\" (apaga o banco atual)."
      echo "Apagando o banco atual '$DB_NAME' (SOBRESCREVER=sim)..."
      admin_sql -c "DROP DATABASE \"$DB_NAME\"" >/dev/null
      admin_sql -c "CREATE DATABASE \"$DB_NAME\"" >/dev/null
    fi
  else
    admin_sql -c "CREATE DATABASE \"$DB_NAME\"" >/dev/null
    echo "Banco '$DB_NAME' criado vazio."
  fi

  # O dump traz a estrutura (tabelas, índices, sequências) e os dados.
  # --no-owner: os objetos ficam com o usuário que restaura; os GRANTs são mantidos.
  if [ "$DB_ADMIN_SUDO" = "sim" ]; then
    sudo -u "$DB_ADMIN_USUARIO" pg_restore --no-owner -d "$DB_NAME" < "$DUMP"
  else
    PGPASSWORD="$DB_ADMIN_SENHA" pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USUARIO" \
      --no-owner -d "$DB_NAME" < "$DUMP"
  fi
  echo "Estrutura e dados restaurados."
}

# ---------- Capas ----------
restaurar_capas() {
  passo "Extraindo as capas"
  mkdir -p "$PASTA_CAPAS_DESTINO"
  tar -xzf "$CAPAS_TAR" -C "$PASTA_CAPAS_DESTINO"
  echo "Capas extraídas em: $PASTA_CAPAS_DESTINO/capas ($(find "$PASTA_CAPAS_DESTINO/capas" -type f | wc -l) arquivos)"
}

# ---------- Conferência ----------
conferir() {
  passo "Conferência das contagens"
  for tabela in livro gibi lp_vinil album_figurinha gibi_serie_item; do
    local n
    n="$(sql_banco "$DB_NAME" -tAc "SELECT count(*) FROM $tabela")"
    printf '%-18s %s\n' "$tabela" "$n"
  done
  echo
  echo "Restauração concluída."
  echo "Se for o servidor de produção, o arquivo de configuração do site (env-*.env do backup)"
  echo "deve ser copiado manualmente para /etc/catalogo-web/catalogo-web.env, com dono root e permissão 0640."
}

instalar_programas
configurar_rclone
baixar_backup
criar_papeis
restaurar_banco
restaurar_capas
conferir
