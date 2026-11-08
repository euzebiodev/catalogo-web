"""Edição manual dos campos de livros, gibis e vinis.

Só os campos listados em CAMPOS são alterados. Autores, gêneros e faixas não
entram aqui. Editora, estante e gravadora são informadas pelo nome; se o nome
ainda não existir, ele é cadastrado.
"""

import os
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import NamedTuple, Optional

from .db import fetch_one


class Campo(NamedTuple):
    chave: str  # nome do campo no formulário e parâmetro do UPDATE
    coluna: str  # coluna gravada no banco (nas referências, a coluna _id)
    tipo: str  # texto, longo, inteiro, dinheiro, data ou referencia
    rotulo: str
    tabela_ref: Optional[str] = None  # tabela de nomes, nas referências
    obrigatorio: bool = False
    tamanho: int = 200  # tamanho máximo do texto
    faixa: tuple = (0, 100000)  # limites do inteiro


_ANO = Campo("ano_publicacao", "ano_publicacao", "inteiro", "Ano de publicação", faixa=(0, 2100))
_PRECO = Campo("preco", "preco", "dinheiro", "Preço (R$)")
_AQUISICAO = Campo("aquisicao_data", "aquisicao_data", "data", "Data de aquisição")
_CONSERVACAO = Campo("conservacao", "conservacao", "texto", "Conservação")
_FONTE_CAPA = Campo("capa_fonte", "capa_fonte", "texto", "Fonte da capa", tamanho=300)
_ESTANTE = Campo("estante", "estante_id", "referencia", "Estante", tabela_ref="estante")
_EDITORA = Campo("editora", "editora_id", "referencia", "Editora", tabela_ref="editora")
_ENCADERNACAO = Campo("encadernacao", "encadernacao", "texto", "Encadernação")
_ISBN10 = Campo("isbn10", "isbn10", "texto", "ISBN-10", tamanho=20)
_ISBN13 = Campo("isbn13", "isbn13", "texto", "ISBN-13", tamanho=20)
_CLUBE = Campo("clube_do_livro", "clube_do_livro", "texto", "Clube do Livro")
_PAGINAS = Campo("paginas", "paginas", "inteiro", "Páginas", faixa=(0, 100000))

CAMPOS = {
    "livros": {
        "tabela": "livro",
        "campos": [
            Campo("titulo", "titulo", "texto", "Título", obrigatorio=True),
            # Sem coluna própria: os autores ficam na tabela livro_autor (ver _salvar_autores).
            Campo("autores", None, "texto", "Autor(es)", tamanho=500),
            _EDITORA,
            _ESTANTE,
            _PAGINAS,
            _ANO,
            Campo("lingua", "lingua", "texto", "Idioma"),
            Campo("edicao", "edicao", "texto", "Edição"),
            _ENCADERNACAO,
            _ISBN10,
            _ISBN13,
            _CLUBE,
            _CONSERVACAO,
            _AQUISICAO,
            _PRECO,
            _FONTE_CAPA,
            Campo("nota", "nota", "longo", "Observações", tamanho=5000),
            Campo("sinopse", "sinopse", "longo", "Sinopse", tamanho=5000),
        ],
    },
    "gibis": {
        "tabela": "gibi",
        "campos": [
            Campo("titulo", "titulo", "texto", "Título", obrigatorio=True),
            Campo("categoria", "categoria", "texto", "Categoria"),
            _EDITORA,
            _ESTANTE,
            _PAGINAS,
            _ANO,
            _ENCADERNACAO,
            _ISBN10,
            _ISBN13,
            _CLUBE,
            _CONSERVACAO,
            _AQUISICAO,
            _PRECO,
            _FONTE_CAPA,
            Campo("sinopse", "sinopse", "longo", "Sinopse", tamanho=5000),
            Campo("nota", "nota", "longo", "Observações", tamanho=5000),
        ],
    },
    "vinil": {
        "tabela": "lp_vinil",
        "campos": [
            Campo("titulo", "titulo", "texto", "Título", obrigatorio=True),
            Campo("gravadora", "gravadora_id", "referencia", "Gravadora", tabela_ref="gravadora"),
            _ESTANTE,
            Campo("numero_musicas", "numero_musicas", "inteiro", "Número de faixas", faixa=(0, 500)),
            _ANO,
            Campo("numero_catalogo", "numero_catalogo", "texto", "Número de catálogo"),
            _CONSERVACAO,
            _AQUISICAO,
            _PRECO,
            _FONTE_CAPA,
            Campo("notas", "notas", "longo", "Observações", tamanho=5000),
        ],
    },
}


def campos_formulario(tipo):
    """Campos para desenhar o formulário, na ordem em que aparecem."""
    return [
        {
            "chave": c.chave,
            "rotulo": c.rotulo,
            "tipo": c.tipo,
            "longo": c.tipo == "longo",
            "obrigatorio": c.obrigatorio,
            "tipo_entrada": "date" if c.tipo == "data" else "text",
            "modo_teclado": {"inteiro": "numeric", "dinheiro": "decimal"}.get(c.tipo, ""),
        }
        for c in CAMPOS[tipo]["campos"]
    ]


def _sql_leitura(tipo):
    tabela = CAMPOS[tipo]["tabela"]
    colunas = ["t.codigo"]
    for c in CAMPOS[tipo]["campos"]:
        if c.coluna is None:
            colunas.append(
                "(SELECT string_agg(p.nome, ', ' ORDER BY p.nome) FROM livro_autor la "
                "JOIN pessoa p ON p.id = la.pessoa_id WHERE la.livro_id = t.id) AS " + c.chave
            )
        elif c.tipo == "referencia":
            colunas.append(
                f"(SELECT r.nome FROM {c.tabela_ref} r WHERE r.id = t.{c.coluna}) AS {c.chave}"
            )
        else:
            colunas.append(f"t.{c.coluna} AS {c.chave}")
    return f"SELECT {', '.join(colunas)} FROM {tabela} t WHERE t.codigo = %s"


def _como_texto(campo, valor):
    if valor is None:
        return ""
    if campo.tipo == "dinheiro":
        return f"{valor:.2f}".replace(".", ",")
    if campo.tipo == "data":
        return valor.isoformat()
    return str(valor)


def ler_para_edicao(app, tipo, codigo):
    """Valores atuais do item, já como texto de formulário. None se o item não existe."""
    linha = fetch_one(app, _sql_leitura(tipo), (codigo,))
    if linha is None:
        return None
    return {c.chave: _como_texto(c, linha[c.chave]) for c in CAMPOS[tipo]["campos"]}


def _converter(campo, bruto):
    if not bruto:
        if campo.obrigatorio:
            raise ValueError("preencha este campo")
        return None

    if campo.tipo in ("texto", "longo", "referencia"):
        if len(bruto) > campo.tamanho:
            raise ValueError(f"use no máximo {campo.tamanho} caracteres")
        return bruto

    if campo.tipo == "inteiro":
        if not bruto.isdigit():
            raise ValueError("use só números")
        numero = int(bruto)
        minimo, maximo = campo.faixa
        if not minimo <= numero <= maximo:
            raise ValueError(f"deve estar entre {minimo} e {maximo}")
        return numero

    if campo.tipo == "dinheiro":
        try:
            valor = Decimal(bruto.replace(",", "."))
        except InvalidOperation:
            raise ValueError("use um valor como 89,90")
        if valor < 0 or valor > 1_000_000:
            raise ValueError("valor fora do intervalo")
        return valor.quantize(Decimal("0.01"))

    if campo.tipo == "data":
        try:
            return date.fromisoformat(bruto)
        except ValueError:
            raise ValueError("use o formato AAAA-MM-DD")

    raise ValueError("tipo de campo desconhecido")


def ler_formulario(tipo, form):
    """Valida o formulário. Devolve os valores convertidos e a lista de erros."""
    valores = {}
    erros = []
    for campo in CAMPOS[tipo]["campos"]:
        bruto = form.get(campo.chave, "").strip()
        try:
            valores[campo.chave] = _converter(campo, bruto)
        except ValueError as erro:
            erros.append(f"{campo.rotulo}: {erro}")
    return valores, erros


def _id_da_referencia(conn, tabela, nome):
    """Id do nome informado; cadastra o nome se ele ainda não existir."""
    if not nome:
        return None
    linha = conn.execute(f"SELECT id FROM {tabela} WHERE nome = %s", (nome,)).fetchone()
    if linha:
        return linha["id"]
    linha = conn.execute(f"INSERT INTO {tabela} (nome) VALUES (%s) RETURNING id", (nome,)).fetchone()
    return linha["id"]


def salvar(app, tipo, codigo, valores):
    """Grava os campos do item numa transação. False se o item não existe."""
    cfg = CAMPOS[tipo]
    atribuicoes = []
    params = {"codigo": codigo}

    with app.extensions["db_pool_escrita"].connection() as conn:
        with conn.transaction():
            for campo in cfg["campos"]:
                if campo.coluna is None:
                    continue  # autores: gravados à parte, em livro_autor
                valor = valores.get(campo.chave)
                if campo.tipo == "referencia":
                    valor = _id_da_referencia(conn, campo.tabela_ref, valor)
                params[campo.chave] = valor
                atribuicoes.append(f"{campo.coluna} = %({campo.chave})s")

            cursor = conn.execute(
                f"UPDATE {cfg['tabela']} SET {', '.join(atribuicoes)} WHERE codigo = %(codigo)s RETURNING id",
                params,
            )
            linha = cursor.fetchone()
            if linha is None:
                return False
            if "autores" in valores:
                _salvar_autores(conn, linha["id"], valores["autores"])
            return True


def _salvar_autores(conn, livro_id, texto):
    """Substitui os autores do livro pelos nomes informados, separados por vírgula.

    Nome que ainda não existe é cadastrado em pessoa.
    """
    nomes = []
    for nome in (texto or "").split(","):
        nome = nome.strip()
        if nome and nome not in nomes:
            nomes.append(nome)
    conn.execute("DELETE FROM livro_autor WHERE livro_id = %s", (livro_id,))
    for nome in nomes:
        pessoa = conn.execute("SELECT id FROM pessoa WHERE nome = %s", (nome,)).fetchone()
        if pessoa is None:
            pessoa = conn.execute("INSERT INTO pessoa (nome) VALUES (%s) RETURNING id", (nome,)).fetchone()
        conn.execute(
            "INSERT INTO livro_autor (livro_id, pessoa_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (livro_id, pessoa["id"]),
        )


# Troca de capa: a imagem vai para CAPAS_DIR/<pasta>/<codigo>.<ext> e o banco aponta para ela.

PASTA_CAPA = {"livros": "livro", "gibis": "gibi", "vinil": "lp"}
TAMANHO_MAX_CAPA = 5 * 1024 * 1024  # 5 MB


def tipo_da_imagem(dados):
    """Confere o conteúdo do arquivo, não o nome. Devolve a extensão ou None."""
    if dados[:3] == b"\xff\xd8\xff":
        return "jpg"
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "webp"
    return None


def capa_atual(app, tipo, codigo):
    """Caminho relativo da capa atual do item, ou None."""
    linha = fetch_one(
        app,
        f"SELECT capa_arquivo FROM {CAMPOS[tipo]['tabela']} WHERE codigo = %s",
        (codigo,),
    )
    return linha["capa_arquivo"] if linha else None


def trocar_capa(app, tipo, codigo, dados):
    """Grava a nova capa e aponta o item para ela. False se o item não existe.

    Levanta ValueError se o arquivo for grande demais ou não for JPG, PNG ou WEBP.
    """
    if len(dados) > TAMANHO_MAX_CAPA:
        raise ValueError("A imagem passa de 5 MB.")
    extensao = tipo_da_imagem(dados)
    if extensao is None:
        raise ValueError("Use uma imagem JPG, PNG ou WEBP.")

    pasta = PASTA_CAPA[tipo]
    relativo = f"{pasta}/{codigo}.{extensao}"
    raiz = app.config["CAPAS_DIR"]
    destino = os.path.join(raiz, pasta, f"{codigo}.{extensao}")
    temporario = destino + ".tmp"
    anterior = capa_atual(app, tipo, codigo)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(temporario, "wb") as arquivo:
        arquivo.write(dados)
    try:
        with app.extensions["db_pool_escrita"].connection() as conn:
            cursor = conn.execute(
                f"UPDATE {CAMPOS[tipo]['tabela']} SET capa_arquivo = %s WHERE codigo = %s",
                (relativo, codigo),
            )
            atualizou = cursor.rowcount == 1
        if not atualizou:
            return False
        os.replace(temporario, destino)
    finally:
        if os.path.exists(temporario):
            os.remove(temporario)

    # Se a extensão mudou (ex.: .jpg virou .png), a capa antiga não serve mais.
    if anterior and anterior != relativo:
        antigo = os.path.join(raiz, anterior)
        if os.path.exists(antigo):
            os.remove(antigo)
    return True
