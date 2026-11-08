# Restauração completa do catálogo a partir do Google Drive criptografado (Windows).
#
# Faz, nesta ordem:
#   1. instala o rclone (winget), se faltar, e confere o PostgreSQL;
#   2. cria o remoto "cripto" com as senhas do arquivo de configuração;
#   3. baixa o backup mais recente (dump do banco e capas);
#   4. cria o banco (vazio) e restaura estrutura e dados;
#   5. cria os usuários catalogo_leitura e catalogo_escrita se faltarem;
#   6. extrai as capas e mostra as contagens para conferência.
#
# Pré-requisito: PostgreSQL instalado (com pg_restore e psql), na mesma versão do backup.
# Uso (PowerShell):  .\restaurar.ps1 -Conf .\restauracao.conf

param(
    [string]$Conf = ".\restauracao.conf"
)

$ErrorActionPreference = "Stop"

function Passo($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Falha($texto) { Write-Host "ERRO: $texto" -ForegroundColor Red; exit 1 }

# ---------- Configuração ----------
if (-not (Test-Path $Conf)) {
    Falha "arquivo de configuração não encontrado: $Conf (copie restauracao.exemplo.conf para restauracao.conf)"
}
$cfg = @{}
Get-Content $Conf -Encoding UTF8 | ForEach-Object {
    $linha = $_.Trim()
    if ($linha -match '^\s*#' -or $linha -eq '') { return }
    if ($linha -match '^([A-Z0-9_]+)\s*=\s*"(.*)"\s*$') { $cfg[$matches[1]] = $matches[2] }
}
function Cfg($chave) { if ($cfg.ContainsKey($chave)) { $cfg[$chave] } else { "" } }

$DbHost = Cfg "DB_HOST"; $DbPort = Cfg "DB_PORT"; $DbNome = Cfg "DB_NAME"
$AdminUsuario = Cfg "DB_ADMIN_USUARIO"; $AdminSenha = Cfg "DB_ADMIN_SENHA"
$LeituraUsuario = Cfg "LEITURA_USUARIO"; $LeituraSenha = Cfg "LEITURA_SENHA"
$EscritaUsuario = Cfg "ESCRITA_USUARIO"; $EscritaSenha = Cfg "ESCRITA_SENHA"
$CriptoSenha = Cfg "CRIPTO_SENHA"; $CriptoSenha2 = Cfg "CRIPTO_SENHA2"
$GdriveRemoto = Cfg "GDRIVE_REMOTO"
$PastaDownload = Cfg "PASTA_DOWNLOAD"; $DumpEscolhido = Cfg "DUMP_ESCOLHIDO"
$PastaCapas = Cfg "PASTA_CAPAS_DESTINO"; $Sobrescrever = Cfg "SOBRESCREVER"

if (-not $DbNome) { Falha "DB_NAME não está preenchido em $Conf" }

# ---------- Programas ----------
function Instalar-Programas {
    Passo "Verificando programas"
    if (-not (Get-Command rclone -ErrorAction SilentlyContinue)) {
        Write-Host "Instalando rclone (winget)..."
        winget install --id Rclone.Rclone -e --accept-source-agreements --accept-package-agreements
        Write-Host "Feche e abra o PowerShell de novo (o PATH muda) e rode o script outra vez."
        exit 0
    }
    foreach ($ferramenta in @("psql", "pg_restore")) {
        if (-not (Get-Command $ferramenta -ErrorAction SilentlyContinue)) {
            Falha "$ferramenta não encontrado. Instale o PostgreSQL (versão do backup, 18) pelo instalador oficial, marque 'Command Line Tools', e rode o script de novo."
        }
    }
    Write-Host "rclone: $(rclone version | Select-Object -First 1)"
    Write-Host "pg_restore: $(pg_restore --version)"
}

# ---------- Banco ----------
function Admin-Sql($sql) {
    $env:PGPASSWORD = $AdminSenha
    psql -h $DbHost -p $DbPort -U $AdminUsuario -d postgres -v ON_ERROR_STOP=1 -tAc $sql
}
function Sql-Banco($banco, $sql) {
    $env:PGPASSWORD = $AdminSenha
    psql -h $DbHost -p $DbPort -U $AdminUsuario -d $banco -v ON_ERROR_STOP=1 -tAc $sql
}

# ---------- Google Drive criptografado ----------
function Configurar-Rclone {
    Passo "Configurando o acesso ao Google Drive"
    $remotos = rclone listremotes
    if (-not ($remotos -match "^$GdriveRemoto`:")) {
        Falha "o remoto '$GdriveRemoto' não existe. Rode 'rclone config', crie um remoto Google Drive com esse nome (tipo drive) e rode este script de novo."
    }
    if ($remotos -match '^cripto:') {
        Write-Host "Remoto 'cripto' já configurado."
        return
    }
    if (-not $CriptoSenha -or -not $CriptoSenha2) { Falha "preencha CRIPTO_SENHA e CRIPTO_SENHA2 em $Conf" }
    $ofus1 = rclone obscure $CriptoSenha
    $ofus2 = rclone obscure $CriptoSenha2
    rclone config create cripto crypt remote "$GdriveRemoto`:catalogo-backup" password $ofus1 password2 $ofus2 filename_encryption standard directory_name_encryption true | Out-Null
    Write-Host "Remoto 'cripto' criado."
}

function Baixar-Backup {
    Passo "Procurando o backup mais recente"
    if ($DumpEscolhido) {
        $nome = $DumpEscolhido
    } else {
        $nome = (rclone lsf cripto: | Where-Object { $_ -match '^catalogo-.*\.dump$' } | Sort-Object | Select-Object -Last 1)
    }
    if (-not $nome) { Falha "nenhum dump encontrado no remoto cripto:" }
    $sufixo = $nome -replace '^catalogo-', '' -replace '\.dump$', ''
    Write-Host "Backup escolhido: $sufixo"

    New-Item -ItemType Directory -Force -Path $PastaDownload | Out-Null
    rclone copy cripto: $PastaDownload --include "catalogo-$sufixo.dump" --include "capas-$sufixo.tar.gz"

    $script:Dump = Join-Path $PastaDownload "catalogo-$sufixo.dump"
    $script:CapasTar = Join-Path $PastaDownload "capas-$sufixo.tar.gz"
    if (-not (Test-Path $script:Dump)) { Falha "o dump não foi baixado: $script:Dump" }
    if (-not (Test-Path $script:CapasTar)) { Falha "o arquivo de capas não foi baixado: $script:CapasTar" }
    Write-Host "Baixados: $script:Dump e $script:CapasTar"
}

# ---------- Restauração ----------
function Criar-Papeis {
    Passo "Verificando os usuários do site"
    foreach ($par in @(@($LeituraUsuario, $LeituraSenha), @($EscritaUsuario, $EscritaSenha))) {
        $usr = $par[0]; $pwd = $par[1]
        $existe = Admin-Sql "SELECT 1 FROM pg_roles WHERE rolname = '$usr'"
        if ($existe) {
            Write-Host "Usuário $usr já existe."
        } else {
            if (-not $pwd) { Falha "a senha de $usr está vazia em $Conf." }
            Admin-Sql "CREATE ROLE ""$usr"" LOGIN PASSWORD '$pwd'" | Out-Null
            Write-Host "Usuário $usr criado."
        }
    }
}

function Restaurar-Banco {
    Passo "Restaurando o banco '$DbNome'"
    $existe = Admin-Sql "SELECT 1 FROM pg_database WHERE datname = '$DbNome'"
    if ($existe) {
        $tabelas = Sql-Banco $DbNome "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
        if ($tabelas -ne "0") {
            if ($Sobrescrever -ne "sim") {
                Falha "o banco '$DbNome' já tem $tabelas tabelas. Use outro DB_NAME ou SOBRESCREVER=""sim"" (apaga o banco atual)."
            }
            Write-Host "Apagando o banco atual '$DbNome' (SOBRESCREVER=sim)..."
            Admin-Sql "DROP DATABASE ""$DbNome""" | Out-Null
            Admin-Sql "CREATE DATABASE ""$DbNome""" | Out-Null
        }
    } else {
        Admin-Sql "CREATE DATABASE ""$DbNome""" | Out-Null
        Write-Host "Banco '$DbNome' criado vazio."
    }

    # O dump traz estrutura (tabelas, índices, sequências) e dados.
    $env:PGPASSWORD = $AdminSenha
    cmd /c "pg_restore -h $DbHost -p $DbPort -U $AdminUsuario --no-owner -d $DbNome < ""$script:Dump"""
    if ($LASTEXITCODE -ne 0) { Falha "pg_restore terminou com erro (código $LASTEXITCODE)" }
    Write-Host "Estrutura e dados restaurados."
}

function Restaurar-Capas {
    Passo "Extraindo as capas"
    New-Item -ItemType Directory -Force -Path $PastaCapas | Out-Null
    tar -xzf $script:CapasTar -C $PastaCapas
    $n = (Get-ChildItem -Recurse -File (Join-Path $PastaCapas "capas")).Count
    Write-Host "Capas extraídas em: $(Join-Path $PastaCapas 'capas') ($n arquivos)"
}

function Conferir {
    Passo "Conferência das contagens"
    foreach ($tabela in @("livro", "gibi", "lp_vinil", "album_figurinha", "gibi_serie_item")) {
        $n = Sql-Banco $DbNome "SELECT count(*) FROM $tabela"
        "{0,-18} {1}" -f $tabela, $n | Write-Host
    }
    Write-Host "`nRestauração concluída."
    Write-Host "Se for o servidor de produção, copie manualmente o env-*.env do backup para /etc/catalogo-web/catalogo-web.env (dono root, permissão 0640)."
}

Instalar-Programas
Configurar-Rclone
Baixar-Backup
Criar-Papeis
Restaurar-Banco
Restaurar-Capas
Conferir
