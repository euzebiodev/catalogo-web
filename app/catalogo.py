"""Consultas do catálogo. Cada tipo tem uma consulta de lista (capas) e uma de detalhe (popup)."""

from decimal import Decimal
from typing import NamedTuple

from .db import fetch_all, fetch_one

TIPOS = {
    "livros": {"nome": "Livros", "tabela": "livro"},
    "gibis": {"nome": "Gibis", "tabela": "gibi"},
    "vinil": {"nome": "Vinil", "tabela": "lp_vinil"},
}


class Filtro(NamedTuple):
    rotulo: str
    # Condição SQL com %(chave)s no lugar do valor.
    condicao: str
    # Consulta que devolve as opções, numa coluna chamada "valor".
    opcoes: str


# Filtros de escolha (select), por tipo. A chave é o nome do parâmetro na URL.
FILTROS = {
    "livros": {
        "genero": Filtro(
            "Gênero",
            "EXISTS (SELECT 1 FROM livro_genero lg JOIN genero g ON g.id = lg.genero_id"
            " WHERE lg.livro_id = l.id AND g.nome = %(genero)s)",
            "SELECT DISTINCT g.nome AS valor FROM genero g"
            " JOIN livro_genero lg ON lg.genero_id = g.id ORDER BY 1",
        ),
        "editora": Filtro(
            "Editora",
            "l.editora_id IN (SELECT id FROM editora WHERE nome = %(editora)s)",
            "SELECT DISTINCT ed.nome AS valor FROM editora ed"
            " JOIN livro l ON l.editora_id = ed.id ORDER BY 1",
        ),
        "encadernacao": Filtro(
            "Encadernação",
            "lower(trim(l.encadernacao)) = lower(%(encadernacao)s)",
            "SELECT DISTINCT initcap(trim(encadernacao)) AS valor FROM livro"
            " WHERE trim(coalesce(encadernacao, '')) <> '' ORDER BY 1",
        ),
    },
    "gibis": {
        "categoria": Filtro(
            "Categoria",
            "lower(g.categoria) = lower(%(categoria)s)",
            "SELECT DISTINCT initcap(trim(categoria)) AS valor FROM gibi"
            " WHERE trim(coalesce(categoria, '')) <> '' ORDER BY 1",
        ),
        "genero": Filtro(
            "Gênero",
            "EXISTS (SELECT 1 FROM gibi_genero gg JOIN genero ge ON ge.id = gg.genero_id"
            " WHERE gg.gibi_id = g.id AND ge.nome = %(genero)s)",
            "SELECT DISTINCT ge.nome AS valor FROM genero ge"
            " JOIN gibi_genero gg ON gg.genero_id = ge.id ORDER BY 1",
        ),
        "editora": Filtro(
            "Editora",
            "g.editora_id IN (SELECT id FROM editora WHERE nome = %(editora)s)",
            "SELECT DISTINCT ed.nome AS valor FROM editora ed"
            " JOIN gibi g ON g.editora_id = ed.id ORDER BY 1",
        ),
    },
    "vinil": {
        "gravadora": Filtro(
            "Gravadora",
            "v.gravadora_id IN (SELECT id FROM gravadora WHERE nome = %(gravadora)s)",
            "SELECT DISTINCT gr.nome AS valor FROM gravadora gr"
            " JOIN lp_vinil v ON v.gravadora_id = gr.id ORDER BY 1",
        ),
        "genero": Filtro(
            "Gênero",
            "EXISTS (SELECT 1 FROM lp_genero lg JOIN genero ge ON ge.id = lg.genero_id"
            " WHERE lg.lp_id = v.id AND ge.nome = %(genero)s)",
            "SELECT DISTINCT ge.nome AS valor FROM genero ge"
            " JOIN lp_genero lg ON lg.genero_id = ge.id ORDER BY 1",
        ),
    },
}

# Busca de texto livre: título, código, ISBN/catálogo e nome de autor, artista ou equipe.
BUSCA = {
    "livros": """(l.titulo ILIKE %(q)s OR l.codigo ILIKE %(q)s
                  OR l.isbn10 ILIKE %(q)s OR l.isbn13 ILIKE %(q)s
                  OR EXISTS (SELECT 1 FROM livro_autor la JOIN pessoa p ON p.id = la.pessoa_id
                              WHERE la.livro_id = l.id AND p.nome ILIKE %(q)s))""",
    "gibis": """(g.titulo ILIKE %(q)s OR g.codigo ILIKE %(q)s
                 OR g.isbn10 ILIKE %(q)s OR g.isbn13 ILIKE %(q)s
                 OR EXISTS (SELECT 1 FROM gibi_pessoa gp JOIN pessoa p ON p.id = gp.pessoa_id
                             WHERE gp.gibi_id = g.id AND p.nome ILIKE %(q)s))""",
    "vinil": """(v.titulo ILIKE %(q)s OR v.codigo ILIKE %(q)s OR v.numero_catalogo ILIKE %(q)s
                 OR EXISTS (SELECT 1 FROM lp_artista la JOIN pessoa p ON p.id = la.pessoa_id
                             WHERE la.lp_id = v.id AND p.nome ILIKE %(q)s))""",
}

COLUNA_ANO = {"livros": "l.ano_publicacao", "gibis": "g.ano_publicacao", "vinil": "v.ano_publicacao"}

# Ordenações da lista, por aba. A chave vai na URL (?ordem=); o SQL vem só deste código.
# O desempate é sempre o código. "autor" usa o alias "subtitulo" da consulta de lista.
ORDENACOES = {
    "livros": {
        "codigo": ("Código", "l.codigo"),
        "titulo": ("Título", "l.titulo"),
        "autor": ("Autor", "subtitulo"),
        "editora": ("Editora", "(SELECT ed.nome FROM editora ed WHERE ed.id = l.editora_id)"),
        "ano_asc": ("Ano (mais antigo)", "l.ano_publicacao ASC NULLS LAST"),
        "ano_desc": ("Ano (mais recente)", "l.ano_publicacao DESC NULLS LAST"),
    },
    "gibis": {
        "codigo": ("Código", "g.codigo"),
        "titulo": ("Título", "g.titulo"),
        "autor": ("Autor ou equipe", "subtitulo"),
        "editora": ("Editora", "(SELECT ed.nome FROM editora ed WHERE ed.id = g.editora_id)"),
        "ano_asc": ("Ano (mais antigo)", "g.ano_publicacao ASC NULLS LAST"),
        "ano_desc": ("Ano (mais recente)", "g.ano_publicacao DESC NULLS LAST"),
    },
    "vinil": {
        "codigo": ("Código", "v.codigo"),
        "titulo": ("Título", "v.titulo"),
        "autor": ("Artista", "subtitulo"),
        "gravadora": ("Gravadora", "(SELECT gr.nome FROM gravadora gr WHERE gr.id = v.gravadora_id)"),
        "ano_asc": ("Ano (mais antigo)", "v.ano_publicacao ASC NULLS LAST"),
        "ano_desc": ("Ano (mais recente)", "v.ano_publicacao DESC NULLS LAST"),
    },
}

SQL_LISTA = {
    "livros": """
        SELECT l.codigo, l.titulo, l.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM livro_autor la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.livro_id = l.id) AS subtitulo
        FROM livro l
        {where}
        ORDER BY {ordem}
        LIMIT %(limite)s OFFSET %(deslocamento)s
    """,
    "gibis": """
        SELECT g.codigo, g.titulo, g.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM gibi_pessoa gp JOIN pessoa p ON p.id = gp.pessoa_id
                 WHERE gp.gibi_id = g.id) AS subtitulo
        FROM gibi g
        {where}
        ORDER BY {ordem}
        LIMIT %(limite)s OFFSET %(deslocamento)s
    """,
    "vinil": """
        SELECT v.codigo, v.titulo, v.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM lp_artista la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.lp_id = v.id) AS subtitulo
        FROM lp_vinil v
        {where}
        ORDER BY {ordem}
        LIMIT %(limite)s OFFSET %(deslocamento)s
    """,
}

SQL_TOTAL = {
    "livros": "SELECT count(*) AS total FROM livro l {where}",
    "gibis": "SELECT count(*) AS total FROM gibi g {where}",
    "vinil": "SELECT count(*) AS total FROM lp_vinil v {where}",
}

SQL_DETALHE = {
    "livros": """
        SELECT l.codigo, l.titulo, l.paginas, l.ano_publicacao, l.isbn10, l.isbn13,
               l.encadernacao, l.lingua, l.edicao, l.clube_do_livro, l.conservacao,
               l.aquisicao_data, l.preco, l.sinopse, l.nota, l.capa_arquivo, l.capa_fonte,
               ed.nome AS editora, est.nome AS estante,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM livro_autor la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.livro_id = l.id) AS autores,
               (SELECT string_agg(g.nome, ', ' ORDER BY g.nome)
                  FROM livro_genero lg JOIN genero g ON g.id = lg.genero_id
                 WHERE lg.livro_id = l.id) AS generos
        FROM livro l
        LEFT JOIN editora ed ON ed.id = l.editora_id
        LEFT JOIN estante est ON est.id = l.estante_id
        WHERE l.codigo = %s
    """,
    "gibis": """
        SELECT g.codigo, g.titulo, g.categoria, g.paginas, g.ano_publicacao,
               g.isbn10, g.isbn13, g.encadernacao, g.clube_do_livro, g.conservacao,
               g.aquisicao_data, g.preco, g.sinopse, g.nota, g.capa_arquivo, g.capa_fonte,
               ed.nome AS editora, est.nome AS estante,
               (SELECT string_agg(p.nome || ' (' || gp.papel || ')', ', ' ORDER BY p.nome)
                  FROM gibi_pessoa gp JOIN pessoa p ON p.id = gp.pessoa_id
                 WHERE gp.gibi_id = g.id) AS pessoas,
               (SELECT string_agg(ge.nome, ', ' ORDER BY ge.nome)
                  FROM gibi_genero gg JOIN genero ge ON ge.id = gg.genero_id
                 WHERE gg.gibi_id = g.id) AS generos
        FROM gibi g
        LEFT JOIN editora ed ON ed.id = g.editora_id
        LEFT JOIN estante est ON est.id = g.estante_id
        WHERE g.codigo = %s
    """,
    "vinil": """
        SELECT v.codigo, v.titulo, v.numero_musicas, v.ano_publicacao, v.numero_catalogo,
               v.conservacao, v.aquisicao_data, v.preco, v.notas, v.capa_arquivo, v.capa_fonte,
               gr.nome AS gravadora, est.nome AS estante,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM lp_artista la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.lp_id = v.id) AS artistas,
               (SELECT string_agg(g.nome, ', ' ORDER BY g.nome)
                  FROM lp_genero lg JOIN genero g ON g.id = lg.genero_id
                 WHERE lg.lp_id = v.id) AS generos
        FROM lp_vinil v
        LEFT JOIN gravadora gr ON gr.id = v.gravadora_id
        LEFT JOIN estante est ON est.id = v.estante_id
        WHERE v.codigo = %s
    """,
}

# Faixas com compositores e link de clipe. Só os tipos que têm faixas aparecem aqui.
SQL_FAIXAS = {
    "vinil": """
        SELECT f.numero, f.titulo, f.duracao, f.youtube_url,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM lp_faixa_autor fa JOIN pessoa p ON p.id = fa.pessoa_id
                 WHERE fa.faixa_id = f.id) AS autores
        FROM lp_faixa f
        JOIN lp_vinil v ON v.id = f.lp_id
        WHERE v.codigo = %s
        ORDER BY f.numero
    """,
}

# Rótulos do popup, na ordem em que aparecem. Campos vazios são omitidos.
CAMPOS_POPUP = {
    "livros": [
        ("Autor(es)", "autores"),
        ("Editora", "editora"),
        ("Ano", "ano_publicacao"),
        ("Páginas", "paginas"),
        ("Idioma", "lingua"),
        ("Edição", "edicao"),
        ("Encadernação", "encadernacao"),
        ("ISBN-10", "isbn10"),
        ("ISBN-13", "isbn13"),
        ("Gêneros", "generos"),
        ("Clube do Livro", "clube_do_livro"),
        ("Estante", "estante"),
        ("Conservação", "conservacao"),
        ("Aquisição", "aquisicao_data"),
        ("Preço", "preco"),
        ("Observações", "nota"),
        ("Sinopse", "sinopse"),
    ],
    "gibis": [
        ("Autores e equipe", "pessoas"),
        ("Categoria", "categoria"),
        ("Editora", "editora"),
        ("Ano", "ano_publicacao"),
        ("Páginas", "paginas"),
        ("Encadernação", "encadernacao"),
        ("ISBN-10", "isbn10"),
        ("ISBN-13", "isbn13"),
        ("Gêneros", "generos"),
        ("Clube do Livro", "clube_do_livro"),
        ("Estante", "estante"),
        ("Conservação", "conservacao"),
        ("Aquisição", "aquisicao_data"),
        ("Preço", "preco"),
        ("Sinopse", "sinopse"),
        ("Observações", "nota"),
    ],
    "vinil": [
        ("Artistas", "artistas"),
        ("Gravadora", "gravadora"),
        ("Ano", "ano_publicacao"),
        ("Número de faixas", "numero_musicas"),
        ("Número de catálogo", "numero_catalogo"),
        ("Gêneros", "generos"),
        ("Estante", "estante"),
        ("Conservação", "conservacao"),
        ("Aquisição", "aquisicao_data"),
        ("Preço", "preco"),
        ("Observações", "notas"),
    ],
}


def filtros_da_url(tipo, args):
    """Lê só os parâmetros de filtro conhecidos e descarta os vazios."""
    chaves = ["q", "ano_de", "ano_ate", *FILTROS[tipo]]
    valores = {chave: args.get(chave, "").strip() for chave in chaves}
    return {chave: valor for chave, valor in valores.items() if valor}


def ordem_da_url(tipo, args):
    """Chave de ordenação pedida; valor desconhecido cai no padrão (código)."""
    pedida = args.get("ordem", "").strip()
    return pedida if pedida in ORDENACOES[tipo] else "codigo"


def opcoes_ordem(tipo):
    """Opções do seletor "Ordenar por", na ordem em que aparecem."""
    return [{"chave": chave, "rotulo": rotulo} for chave, (rotulo, _) in ORDENACOES[tipo].items()]


def ordenar_sql(tipo, ordem):
    """Cláusula ORDER BY. Vem só de ORDENACOES; o código é o desempate."""
    alias = {"livros": "l", "gibis": "g", "vinil": "v"}[tipo]
    _, expressao = ORDENACOES[tipo][ordem]
    return f"{expressao}, {alias}.codigo"


def campos_filtro(app, tipo, filtros):
    """Campos de escolha do formulário, com as opções vindas do banco."""
    campos = []
    for chave, filtro in FILTROS[tipo].items():
        opcoes = [linha["valor"] for linha in fetch_all(app, filtro.opcoes)]
        campos.append({"chave": chave, "rotulo": filtro.rotulo, "opcoes": opcoes})
    return campos


def montar_filtro(tipo, filtros):
    """Monta o WHERE e os parâmetros. Os nomes de coluna vêm só do código; os valores vão como parâmetros."""
    condicoes = []
    params = {}

    if "q" in filtros:
        condicoes.append(BUSCA[tipo])
        params["q"] = f"%{_escapar_like(filtros['q'])}%"

    for chave, filtro in FILTROS[tipo].items():
        if chave in filtros:
            condicoes.append(filtro.condicao)
            params[chave] = filtros[chave]

    for chave, operador in (("ano_de", ">="), ("ano_ate", "<=")):
        if chave in filtros and filtros[chave].isdigit():
            condicoes.append(f"{COLUNA_ANO[tipo]} {operador} %({chave})s")
            params[chave] = int(filtros[chave])

    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    return where, params


def listar(app, tipo, pagina, por_pagina, filtros=None, ordem="codigo"):
    where, params = montar_filtro(tipo, filtros or {})
    total = fetch_one(app, SQL_TOTAL[tipo].format(where=where), params)["total"]
    params_lista = {
        **params,
        "limite": por_pagina,
        "deslocamento": (pagina - 1) * por_pagina,
    }
    consulta = SQL_LISTA[tipo].format(where=where, ordem=ordenar_sql(tipo, ordem))
    itens = fetch_all(app, consulta, params_lista)
    return itens, total


def detalhe(app, tipo, codigo):
    linha = fetch_one(app, SQL_DETALHE[tipo], (codigo,))
    if linha is None:
        return None

    campos = []
    for rotulo, chave in CAMPOS_POPUP[tipo]:
        valor = formatar(linha.get(chave))
        if valor:
            campos.append({"rotulo": rotulo, "valor": valor})

    faixas = fetch_all(app, SQL_FAIXAS[tipo], (codigo,)) if tipo in SQL_FAIXAS else []

    return {
        "codigo": linha["codigo"],
        "titulo": linha["titulo"],
        "capa_arquivo": linha["capa_arquivo"],
        "capa_fonte": linha["capa_fonte"],
        "campos": campos,
        "faixas": faixas,
    }


def formatar(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return f"R$ {valor:.2f}".replace(".", ",")
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    texto = str(valor).strip()
    return texto or None


def _escapar_like(texto):
    """Escapa os curingas do ILIKE para que % e _ digitados sejam buscados como texto."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
