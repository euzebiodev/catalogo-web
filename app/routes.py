import math

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for

from . import catalogo

bp = Blueprint("catalogo", __name__)


@bp.get("/")
def inicio():
    return redirect(url_for("catalogo.lista", tipo="livros"))


@bp.get("/<tipo>")
def lista(tipo):
    if tipo not in catalogo.TIPOS:
        abort(404)

    por_pagina = current_app.config["ITENS_POR_PAGINA"]
    pedida = max(request.args.get("pagina", 1, type=int), 1)
    filtros = catalogo.filtros_da_url(tipo, request.args)

    itens, total = catalogo.listar(current_app, tipo, pedida, por_pagina, filtros)
    total_paginas = max(math.ceil(total / por_pagina), 1)
    pagina = min(pedida, total_paginas)
    if pagina != pedida:
        # Página pedida além do fim: mostra a última em vez de uma grade vazia.
        itens, total = catalogo.listar(current_app, tipo, pagina, por_pagina, filtros)

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
    )


@bp.get("/api/<tipo>/<codigo>")
def api_detalhe(tipo, codigo):
    if tipo not in catalogo.TIPOS:
        abort(404)

    dados = catalogo.detalhe(current_app, tipo, codigo)
    if dados is None:
        abort(404)
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
