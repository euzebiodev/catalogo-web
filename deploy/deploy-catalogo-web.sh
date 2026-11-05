#!/usr/bin/env sh
# Instala o catalogo-web como serviço systemd no um1.
#
# Fica em /opt/catalogo-web/deploy-catalogo-web.sh, dono do root, e o Jenkins
# o executa com sudo. Assim o job não consegue alterar o que roda como root.
# Pré-requisito: /etc/catalogo-web/catalogo-web.env já criado (DATABASE_URL, CAPAS_DIR).
set -eu

if [ "$#" -ne 1 ]; then
    echo "Informe o diretorio do workspace do catalogo-web."
    exit 2
fi

WORKSPACE="$(readlink -f "$1")"

case "$WORKSPACE" in
    /var/lib/jenkins/jobs/catalogo-web/workspace)
        ;;
    *)
        echo "Workspace nao permitido: $WORKSPACE"
        exit 2
        ;;
esac

if [ ! -f "$WORKSPACE/run.py" ] || [ ! -f "$WORKSPACE/setup_db.py" ] || [ ! -f "$WORKSPACE/requirements.txt" ]; then
    echo "Workspace invalido: $WORKSPACE"
    exit 2
fi

SERVICE_USER="catalogo-web"
APP_DIR="/opt/catalogo-web"
RELEASE_DIR="$APP_DIR/app"
VENV_DIR="$APP_DIR/venv"
CONFIG_DIR="/etc/catalogo-web"
ENV_FILE="$CONFIG_DIR/catalogo-web.env"
PORTA="8092"
TMP_RELEASE="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_RELEASE"
}
trap cleanup EXIT

if [ ! -f "$ENV_FILE" ]; then
    echo "Arquivo de configuracao ausente: $ENV_FILE"
    exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

install -d -o root -g root -m 0755 "$APP_DIR"

tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='.venv-ci' \
    --exclude='__pycache__' \
    --exclude='dados' \
    --exclude='.env' \
    -C "$WORKSPACE" \
    -cf - . | tar -C "$TMP_RELEASE" -xf -

rm -rf "$RELEASE_DIR"
install -d -o root -g root -m 0755 "$RELEASE_DIR"
cp -a "$TMP_RELEASE/." "$RELEASE_DIR/"
chown -R root:root "$RELEASE_DIR"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
"$VENV_DIR/bin/python" -m pip install --quiet -r "$RELEASE_DIR/requirements.txt"
chown -R root:root "$VENV_DIR"

# Aplica o esquema se o banco ainda não tiver as tabelas. Com o esquema
# já existente, o setup_db.py só informa e não altera nada.
runuser -u "$SERVICE_USER" -- sh -c 'set -a; . "$1"; set +a; cd "$2" && "$3" setup_db.py' \
    sh "$ENV_FILE" "$RELEASE_DIR" "$VENV_DIR/bin/python"

cat > /etc/systemd/system/catalogo-web.service <<EOF
[Unit]
Description=Catalogo web (leitura do catalogo pessoal)
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$RELEASE_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/gunicorn --workers 2 --threads 4 --timeout 60 --bind 0.0.0.0:$PORTA run:app
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadOnlyPaths=$RELEASE_DIR $VENV_DIR

[Install]
WantedBy=multi-user.target
EOF

# Libera a porta só para a rede local, como os demais serviços do um1.
ufw allow from 192.168.0.0/24 to any port "$PORTA" proto tcp comment 'catalogo-web LAN'

systemctl daemon-reload
systemctl enable catalogo-web.service
systemctl restart catalogo-web.service

for tentativa in $(seq 1 24); do
    if systemctl is-active --quiet catalogo-web.service && curl -fsS "http://127.0.0.1:$PORTA/livros" >/dev/null; then
        echo "catalogo-web no ar em http://192.168.0.229:$PORTA"
        exit 0
    fi
    sleep 5
done

systemctl status catalogo-web.service --no-pager -l
exit 1
