"""Consultas do catálogo. Cada tipo tem uma consulta de lista (capas) e uma de detalhe (popup)."""

from decimal import Decimal

from .db import fetch_all, fetch_one

TIPOS = {
    "livros": {"nome": "Livros", "tabela": "livro"},
    "gibis": {"nome": "Gibis", "tabela": "gibi"},
    "vinil": {"nome": "Vinil", "tabela": "lp_vinil"},
}

SQL_LISTA = {
    "livros": """
        SELECT l.codigo, l.titulo, l.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM livro_autor la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.livro_id = l.id) AS subtitulo
        FROM livro l
        ORDER BY l.codigo
        LIMIT %s OFFSET %s
    """,
    "gibis": """
        SELECT g.codigo, g.titulo, g.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM gibi_pessoa gp JOIN pessoa p ON p.id = gp.pessoa_id
                 WHERE gp.gibi_id = g.id) AS subtitulo
        FROM gibi g
        ORDER BY g.codigo
        LIMIT %s OFFSET %s
    """,
    "vinil": """
        SELECT v.codigo, v.titulo, v.capa_arquivo,
               (SELECT string_agg(p.nome, ', ' ORDER BY p.nome)
                  FROM lp_artista la JOIN pessoa p ON p.id = la.pessoa_id
                 WHERE la.lp_id = v.id) AS subtitulo
        FROM lp_vinil v
        ORDER BY v.codigo
        LIMIT %s OFFSET %s
    """,
}

SQL_TOTAL = {
    "livros": "SELECT count(*) AS total FROM livro",
    "gibis": "SELECT count(*) AS total FROM gibi",
    "vinil": "SELECT count(*) AS total FROM lp_vinil",
}

SQL_DETALHE = {
    "livros": """
        SELECT l.codigo, l.titulo, l.paginas, l.ano_publicacao, l.isbn10, l.isbn13,
               l.encadernacao, l.lingua, l.edicao, l.clube_do_livro, l.conservacao,
               l.aquisicao_data, l.preco, l.nota, l.capa_arquivo, l.capa_fonte,
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


def listar(app, tipo, pagina, por_pagina):
    total = fetch_one(app, SQL_TOTAL[tipo])["total"]
    offset = (pagina - 1) * por_pagina
    itens = fetch_all(app, SQL_LISTA[tipo], (por_pagina, offset))
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

    return {
        "codigo": linha["codigo"],
        "titulo": linha["titulo"],
        "capa_arquivo": linha["capa_arquivo"],
        "capa_fonte": linha["capa_fonte"],
        "campos": campos,
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
