"""Testes dos filtros da lista. Rodam no banco configurado no .env (use o schema de teste).

Criam itens temporários (T9001...) e os removem no fim.
Execute: .venv\\Scripts\\python.exe -m unittest discover -s tests -t . -v
"""

import os
import unittest

import psycopg
from dotenv import load_dotenv

load_dotenv()

from app import catalogo  # noqa: E402
from app import create_app  # noqa: E402

URL = os.environ["DATABASE_URL"]
CLUBE = "Clube de teste"
OUTRO_CLUBE = "Outro clube de teste"
CLUBE_GIBI = "Clube de teste dos gibis"


def criar_app():
    return create_app({"TESTING": True})


def limpar():
    with psycopg.connect(URL) as conexao:
        conexao.execute("DELETE FROM livro WHERE codigo LIKE 'T900%'")
        conexao.execute("DELETE FROM gibi WHERE codigo LIKE 'T900%'")


class FiltroClubeTest(unittest.TestCase):
    """O filtro "Clube do Livro" vale para livros e gibis."""

    @classmethod
    def setUpClass(cls):
        limpar()
        with psycopg.connect(URL) as conexao:
            conexao.execute(
                """INSERT INTO livro (codigo, titulo, clube_do_livro) VALUES
                   ('T9001', 'Livro de teste do clube', %s),
                   ('T9002', 'Livro de teste de outro clube', %s),
                   ('T9003', 'Livro de teste sem clube', NULL)""",
                (CLUBE, OUTRO_CLUBE),
            )
            conexao.execute(
                "INSERT INTO gibi (codigo, titulo, clube_do_livro)"
                " VALUES ('T9004', 'Gibi de teste do clube', %s)",
                (CLUBE_GIBI,),
            )
        cls.app = criar_app()

    @classmethod
    def tearDownClass(cls):
        limpar()

    def codigos(self, tipo, filtros):
        itens, total = catalogo.listar(self.app, tipo, 1, 100, filtros)
        self.assertEqual(total, len(itens))
        return [item["codigo"] for item in itens]

    def test_filtro_aparece_nos_livros_e_nos_gibis(self):
        for tipo in ("livros", "gibis"):
            campos = {campo["chave"]: campo for campo in catalogo.campos_filtro(self.app, tipo, {})}
            self.assertIn("clube", campos)
            self.assertEqual(campos["clube"]["rotulo"], "Clube do Livro")

    def test_opcoes_trazem_os_clubes_cadastrados(self):
        campos = {campo["chave"]: campo for campo in catalogo.campos_filtro(self.app, "livros", {})}
        self.assertIn(CLUBE, campos["clube"]["opcoes"])
        self.assertIn(OUTRO_CLUBE, campos["clube"]["opcoes"])

    def test_livros_filtrados_pelo_clube(self):
        self.assertEqual(self.codigos("livros", {"clube": CLUBE}), ["T9001"])

    def test_filtro_ignora_maiusculas(self):
        self.assertEqual(self.codigos("livros", {"clube": CLUBE.upper()}), ["T9001"])

    def test_gibis_filtrados_pelo_clube(self):
        self.assertEqual(self.codigos("gibis", {"clube": CLUBE_GIBI}), ["T9004"])

    def test_item_sem_clube_fica_fora_do_filtro(self):
        self.assertNotIn("T9003", self.codigos("livros", {"clube": CLUBE}))
        self.assertNotIn("T9003", self.codigos("livros", {"clube": OUTRO_CLUBE}))

    def test_url_do_filtro(self):
        self.assertEqual(
            catalogo.filtros_da_url("livros", {"clube": f"  {CLUBE}  "}), {"clube": CLUBE}
        )
        # Parâmetro vazio não vira filtro.
        self.assertEqual(catalogo.filtros_da_url("livros", {"clube": ""}), {})
        # Aba sem a coluna clube_do_livro ignora o parâmetro.
        self.assertEqual(catalogo.filtros_da_url("vinil", {"clube": CLUBE}), {})

    def test_pagina_mostra_o_campo_e_filtra(self):
        html = (
            self.app.test_client()
            .get("/livros", query_string={"clube": CLUBE})
            .get_data(as_text=True)
        )
        self.assertIn("Clube do Livro", html)
        self.assertIn(CLUBE, html)
        self.assertIn("T9001", html)
        self.assertNotIn("T9002", html)
