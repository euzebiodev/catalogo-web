import math
import time

import qrcode
import qrcode.image.svg

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from psycopg.errors import UndefinedTable, UniqueViolation

from . import auth, catalogo, edicao

bp = Blueprint("catalogo", __name__)


@bp.get("/")
def inicio():
    return redirect(url_for("catalogo.lista", tipo="livros"))


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    proxima = auth.proxima_segura(request.values.get("proxima", ""))
    if not auth.edicao_disponivel(current_app):
        return render_template("entrar.html", abas=catalogo.TIPOS, tipo_ativo=None,
                               proxima=proxima, indisponivel=True, erro=None)

    erro = None
    if request.method == "POST":
        auth.conferir_csrf()
        usuario = request.form.get("usuario", "")
        senha = request.form.get("senha", "")
        if auth.conferir_senha(current_app, usuario, senha):
            session.clear()
            session["logado"] = True
            session.permanent = True
            return redirect(proxima)
        # Pausa curta a cada senha errada, para dificultar tentativas em série.
        time.sleep(1)
        erro = "Usuário ou senha inválidos."

    return render_template("entrar.html", abas=catalogo.TIPOS, tipo_ativo=None,
                           proxima=proxima, indisponivel=False, erro=erro)


@bp.post("/sair")
def sair():
    auth.conferir_csrf()
    session.clear()
    return redirect(url_for("catalogo.inicio"))


@bp.route("/alterar-senha", methods=["GET", "POST"])
@auth.exige_login
def alterar_senha():
    erro = None
    sucesso = False
    if request.method == "POST":
        auth.conferir_csrf()
        atual = request.form.get("senha_atual", "")
        nova = request.form.get("senha_nova", "")
        confirmacao = request.form.get("senha_confirmacao", "")

        if not auth.senha_correta(current_app, atual):
            # Mesma pausa do login, para não servir de teste de senha.
            time.sleep(1)
            erro = "A senha atual está errada."
        elif len(nova) < 8:
            erro = "A nova senha precisa ter pelo menos 8 caracteres."
        elif nova != confirmacao:
            erro = "A confirmação não é igual à nova senha."
        elif nova == atual:
            erro = "A nova senha precisa ser diferente da atual."
        else:
            try:
                auth.trocar_senha(current_app, nova)
                sucesso = True
            except UndefinedTable:
                erro = "A troca de senha ainda não está disponível neste servidor (migração 004 pendente)."

    return render_template(
        "alterar_senha.html",
        abas=catalogo.TIPOS,
        tipo_ativo=None,
        erro=erro,
        sucesso=sucesso,
    ), (400 if erro else 200)


def _pagina_editar(tipo, codigo, capa_erro=None, capa_trocada=False):
    valores = edicao.ler_para_edicao(current_app, tipo, codigo)
    if valores is None:
        abort(404)
    return render_template(
        "editar.html",
        abas=catalogo.TIPOS,
        tipo_ativo=tipo,
        tipo=tipo,
        codigo=codigo,
        campos=edicao.campos_formulario(tipo),
        valores=valores,
        erros=[],
        salvo=request.args.get("salvo"),
        capa_arquivo=edicao.capa_atual(current_app, tipo, codigo),
        capa_erro=capa_erro,
        capa_trocada=capa_trocada,
        figurinhas=edicao.figurinhas_do_album(current_app, codigo) if tipo == "album" else None,
        figurinhas_salvas=bool(request.args.get("figurinhas")),
        extras=edicao.extras_do_album(current_app, codigo) if tipo == "album" else None,
        extras_salvos=bool(request.args.get("extras")),
        serie=edicao.serie_do_gibi(current_app, codigo) if tipo == "gibis" else None,
        serie_salva=bool(request.args.get("serie")),
    )


@bp.get("/<tipo>/<codigo>/editar")
@auth.exige_login
def editar(tipo, codigo):
    if tipo not in catalogo.TIPOS:
        abort(404)
    return _pagina_editar(tipo, codigo, capa_trocada=bool(request.args.get("capa")))


@bp.post("/<tipo>/<codigo>/capa")
@auth.exige_login
def trocar_capa(tipo, codigo):
    if tipo not in catalogo.TIPOS:
        abort(404)
    auth.conferir_csrf()

    arquivo = request.files.get("capa")
    if arquivo is None or not arquivo.filename:
        erro = "Escolha um arquivo de imagem."
    else:
        # Lê um byte além do limite, para saber se o arquivo passou dele.
        dados = arquivo.read(edicao.TAMANHO_MAX_CAPA + 1)
        try:
            if not edicao.trocar_capa(current_app, tipo, codigo, dados):
                abort(404)
            return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, capa=1))
        except ValueError as falha:
            erro = str(falha)

    return _pagina_editar(tipo, codigo, capa_erro=erro), 400


@bp.post("/<tipo>/<codigo>/figurinhas")
@auth.exige_login
def salvar_figurinhas(tipo, codigo):
    if tipo != "album":
        abort(404)
    auth.conferir_csrf()
    marcadas = []
    for bruto in request.form.getlist("numero"):
        if bruto.isdigit():
            marcadas.append(int(bruto))
    if not edicao.salvar_figurinhas(current_app, codigo, marcadas):
        abort(404)
    return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, figurinhas=1))


@bp.post("/<tipo>/<codigo>/extras")
@auth.exige_login
def salvar_extras(tipo, codigo):
    if tipo != "album":
        abort(404)
    auth.conferir_csrf()
    marcados = [int(bruto) for bruto in request.form.getlist("numero") if bruto.isdigit()]
    if not edicao.salvar_extras(current_app, codigo, marcados):
        abort(404)
    return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, extras=1))


@bp.post("/<tipo>/<codigo>/serie")
@auth.exige_login
def salvar_serie(tipo, codigo):
    if tipo != "gibis":
        abort(404)
    auth.conferir_csrf()
    marcados = {int(bruto) for bruto in request.form.getlist("numero") if bruto.isdigit()}
    capas = {}
    for chave, arquivo in request.files.items(multi=True):
        if not chave.startswith("capa_") or not arquivo.filename:
            continue
        numero = chave[len("capa_"):]
        if numero.isdigit():
            # Lê um byte além do limite, para saber se passou dele.
            capas[int(numero)] = arquivo.read(edicao.TAMANHO_MAX_CAPA + 1)
    # ISBNs de cada número: campos isbn10_<n> e isbn13_<n>; vazio vira None.
    isbns = {}
    for chave in request.form:
        if chave.startswith(("isbn10_", "isbn13_")):
            tipo_isbn, _, numero = chave.partition("_")
            if numero.isdigit():
                par = list(isbns.get(int(numero), (None, None)))
                valor = request.form.get(chave, "").strip() or None
                par[0 if tipo_isbn == "isbn10" else 1] = valor
                isbns[int(numero)] = tuple(par)
    try:
        if not edicao.salvar_serie(current_app, codigo, marcados, capas, isbns):
            abort(404)
    except ValueError as falha:
        return _pagina_editar(tipo, codigo, capa_erro=str(falha)), 400
    return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, serie=1))


@bp.post("/<tipo>/<codigo>/editar")
@auth.exige_login
def salvar_edicao(tipo, codigo):
    if tipo not in catalogo.TIPOS:
        abort(404)
    auth.conferir_csrf()

    valores, erros = edicao.ler_formulario(tipo, request.form)
    if not erros:
        try:
            if not edicao.salvar(current_app, tipo, codigo, valores):
                abort(404)
        except UniqueViolation:
            erros.append("Já existe outro item com este ISBN.")

    if erros:
        # Mostra o que foi digitado, para não perder a edição.
        return render_template(
            "editar.html",
            abas=catalogo.TIPOS,
            tipo_ativo=tipo,
            tipo=tipo,
            codigo=codigo,
            campos=edicao.campos_formulario(tipo),
            valores={chave: request.form.get(chave, "") for chave in valores_brutos(tipo)},
            erros=erros,
            salvo=None,
        ), 400

    return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, salvo=1))


@bp.post("/<tipo>/<codigo>/excluir")
@auth.exige_login
def excluir_item(tipo, codigo):
    """Exclusão lógica: o item some do site, mas o registro continua no banco."""
    if tipo not in catalogo.TIPOS:
        abort(404)
    auth.conferir_csrf()
    if not edicao.excluir(current_app, tipo, codigo):
        abort(404)
    return redirect(url_for("catalogo.lista", tipo=tipo))


def valores_brutos(tipo):
    return [campo["chave"] for campo in edicao.campos_formulario(tipo)]


def _pagina_novo(tipo, codigo, valores, erros):
    return render_template(
        "novo.html",
        abas=catalogo.TIPOS,
        tipo_ativo=tipo,
        tipo=tipo,
        codigo=codigo,
        campos=edicao.campos_formulario(tipo),
        valores=valores,
        erros=erros,
    )


@bp.route("/<tipo>/novo", methods=["GET", "POST"])
@auth.exige_login
def novo(tipo):
    if tipo not in catalogo.TIPOS:
        abort(404)

    if request.method == "GET":
        codigo = edicao.proximo_codigo(current_app, tipo)
        valores = {chave: "" for chave in valores_brutos(tipo)}
        return _pagina_novo(tipo, codigo, valores, [])

    auth.conferir_csrf()
    codigo, erro_codigo = edicao.validar_codigo(request.form.get("codigo", ""))
    valores, erros = edicao.ler_formulario(tipo, request.form)
    if erro_codigo:
        erros.insert(0, erro_codigo)

    capa = None
    arquivo = request.files.get("capa")
    if arquivo is not None and arquivo.filename:
        # Confere a capa antes de gravar o item, para não criar item sem capa por erro de arquivo.
        dados = arquivo.read(edicao.TAMANHO_MAX_CAPA + 1)
        if len(dados) > edicao.TAMANHO_MAX_CAPA:
            erros.append("Capa: a imagem passa de 5 MB.")
        elif edicao.tipo_da_imagem(dados) is None:
            erros.append("Capa: use uma imagem JPG, PNG ou WEBP.")
        else:
            capa = dados

    if not erros:
        try:
            edicao.criar(current_app, tipo, codigo, valores)
        except UniqueViolation:
            erros.append("Já existe um item com este código ou com este ISBN.")
        else:
            if capa is not None:
                edicao.trocar_capa(current_app, tipo, codigo, capa)
            return redirect(url_for("catalogo.editar", tipo=tipo, codigo=codigo, salvo=1, novo=1))

    # Mostra o que foi digitado, para não perder o cadastro.
    digitados = {chave: request.form.get(chave, "") for chave in valores_brutos(tipo)}
    return _pagina_novo(tipo, codigo, digitados, erros), 400


@bp.get("/<tipo>")
def lista(tipo):
    if tipo not in catalogo.TIPOS:
        abort(404)

    por_pagina = current_app.config["ITENS_POR_PAGINA"]
    pedida = max(request.args.get("pagina", 1, type=int), 1)
    filtros = catalogo.filtros_da_url(tipo, request.args)
    ordem = catalogo.ordem_da_url(tipo, request.args)

    itens, total = catalogo.listar(current_app, tipo, pedida, por_pagina, filtros, ordem)
    total_paginas = max(math.ceil(total / por_pagina), 1)
    pagina = min(pedida, total_paginas)
    if pagina != pedida:
        # Página pedida além do fim: mostra a última em vez de uma grade vazia.
        itens, total = catalogo.listar(current_app, tipo, pagina, por_pagina, filtros, ordem)

    return render_template(
        "lista.html",
        abas=catalogo.TIPOS,
        tipo_ativo=tipo,
        itens=itens,
        total=total,
        pagina=pagina,
        total_paginas=total_paginas,
        numeros_paginas=janela_paginas(pagina, total_paginas),
        filtros=filtros,
        campos_filtro=catalogo.campos_filtro(current_app, tipo, filtros),
        ordem=ordem,
        opcoes_ordem=catalogo.opcoes_ordem(tipo),
    )


@bp.get("/<tipo>/<codigo>")
def item(tipo, codigo):
    """Página de um item: é para onde aponta o QR code das fichas."""
    if tipo not in catalogo.TIPOS:
        abort(404)
    dados = catalogo.detalhe(current_app, tipo, codigo)
    if dados is None:
        abort(404)
    return render_template(
        "item.html",
        abas=catalogo.TIPOS,
        tipo_ativo=tipo,
        tipo=tipo,
        dados=dados,
    )


# Fichas para impressão: 12,5 x 7,5 cm, uma por linha numa A4 deitada (frente e verso lado a lado).
@bp.get("/fichas")
@auth.exige_login
def fichas():
    base = request.host_url.rstrip("/")
    selecionados = []
    for par in request.args.getlist("i"):
        tipo, _, codigo = par.partition(":")
        if tipo not in catalogo.TIPOS or not codigo:
            continue
        dados = catalogo.detalhe(current_app, tipo, codigo)
        if dados is None:
            continue
        link = f"{base}{url_for('catalogo.item', tipo=tipo, codigo=codigo)}"
        selecionados.append({
            "tipo": tipo,
            "dados": dados,
            "qr": _qr_svg(link),
        })
    # Duas fichas por folha (uma por linha).
    folhas = [selecionados[i:i + 2] for i in range(0, len(selecionados), 2)]
    return render_template("fichas.html", folhas=folhas, total=len(selecionados))


def _qr_svg(texto):
    imagem = qrcode.make(
        texto,
        image_factory=qrcode.image.svg.SvgPathImage,
        box_size=10,
        border=1,
    )
    return imagem.to_string(encoding="unicode")


@bp.get("/api/<tipo>/<codigo>")
def api_detalhe(tipo, codigo):
    if tipo not in catalogo.TIPOS:
        abort(404)

    dados = catalogo.detalhe(current_app, tipo, codigo)
    if dados is None:
        abort(404)
    # O popup mostra o link de edição só para quem já entrou.
    dados["editavel"] = auth.edicao_disponivel(current_app) and auth.logado()
    return jsonify(dados)


@bp.get("/capas/<path:arquivo>")
def capa(arquivo):
    return send_from_directory(current_app.config["CAPAS_DIR"], arquivo)


def janela_paginas(pagina, total_paginas, vizinhos=2):
    """Números de página a mostrar; None marca reticências."""
    if total_paginas <= 2 * vizinhos + 5:
        return list(range(1, total_paginas + 1))

    inicio = max(pagina - vizinhos, 2)
    fim = min(pagina + vizinhos, total_paginas - 1)
    numeros = [1]
    if inicio > 2:
        numeros.append(None)
    numeros.extend(range(inicio, fim + 1))
    if fim < total_paginas - 1:
        numeros.append(None)
    numeros.append(total_paginas)
    return numeros
