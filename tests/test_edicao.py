"""Testes da edição manual. Rodam no banco configurado no .env (use o schema de teste).

Criam um livro temporário (T9999) e o removem no fim.
Execute: .venv\\Scripts\\python.exe -m unittest discover -s tests -t . -v
"""

import io
import os
import re
import shutil
import tempfile
import unittest

import psycopg
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

from app import auth  # noqa: E402
from app import catalogo  # noqa: E402
from app import create_app  # noqa: E402
from app import edicao  # noqa: E402

URL = os.environ["DATABASE_URL"]
SENHA = "senha-de-teste-123"
# Capas de teste ficam numa pasta temporária, nunca em dados/capas.
CAPAS_TESTE = tempfile.mkdtemp(prefix="capas-teste-")
PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def criar_app():
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "ADMIN_USUARIO": "admin",
            "ADMIN_SENHA_HASH": generate_password_hash(SENHA),
            "DATABASE_URL_ESCRITA": URL,
            "EDICAO_ATIVA": True,
            "CAPAS_DIR": CAPAS_TESTE,
        }
    )


def limpar_teste():
    with psycopg.connect(URL) as conexao:
        conexao.execute(
            "DELETE FROM livro_extra WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
        )
        conexao.execute(
            "DELETE FROM livro_autor WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
        )
        conexao.execute("DELETE FROM livro WHERE codigo = 'T9999'")
        conexao.execute(
            """DELETE FROM pessoa p WHERE p.nome LIKE 'Autor de teste%'
               AND NOT EXISTS (SELECT 1 FROM livro_autor la WHERE la.pessoa_id = p.id)"""
        )
        conexao.execute("DELETE FROM editora WHERE nome = 'Editora de teste'")
        conexao.execute("DELETE FROM genero WHERE nome LIKE 'Gênero de teste%'")
        # Senha trocada pelo site do usuário de teste (não o login real).
        conexao.execute("DELETE FROM admin_senha WHERE usuario = 'admin'")


class EdicaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        limpar_teste()
        with psycopg.connect(URL) as conexao:
            conexao.execute("INSERT INTO livro (codigo, titulo) VALUES ('T9999', 'Livro de teste')")

    @classmethod
    def tearDownClass(cls):
        limpar_teste()
        shutil.rmtree(CAPAS_TESTE, ignore_errors=True)

    def setUp(self):
        # Volta o registro temporário ao estado inicial, para um teste não afetar o outro.
        with psycopg.connect(URL) as conexao:
            conexao.execute(
                """UPDATE livro SET titulo = 'Livro de teste', paginas = NULL, preco = NULL,
                          aquisicao_data = NULL, nota = NULL, editora_id = NULL, isbn13 = NULL,
                          capa_arquivo = NULL
                    WHERE codigo = 'T9999'"""
            )
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM admin_senha WHERE usuario = 'admin'")
            conexao.execute(
                "DELETE FROM livro_autor WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
            )
            conexao.execute(
                "DELETE FROM livro_genero WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
            )
        self.cliente = criar_app().test_client()

    def token_da_pagina(self, url):
        html = self.cliente.get(url).get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def entrar(self, senha=SENHA):
        return self.cliente.post(
            "/entrar",
            data={
                "csrf": self.token_da_pagina("/entrar"),
                "usuario": "admin",
                "senha": senha,
                "proxima": "/livros",
            },
        )

    def dados_do_formulario(self, **alterados):
        dados = {campo["chave"]: "" for campo in edicao.campos_formulario("livros")}
        dados["titulo"] = "Livro de teste"
        dados.update(alterados)
        return dados

    def ler_no_banco(self):
        with psycopg.connect(URL) as conexao:
            return conexao.execute(
                """SELECT l.titulo, l.paginas, l.preco, l.aquisicao_data, l.nota, ed.nome AS editora
                     FROM livro l LEFT JOIN editora ed ON ed.id = l.editora_id
                    WHERE l.codigo = 'T9999'"""
            ).fetchone()

    def test_sem_login_redireciona_para_entrar(self):
        resposta = self.cliente.get("/livros/T9999/editar")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/entrar", resposta.headers["Location"])

    def test_senha_errada_nao_entra(self):
        resposta = self.entrar("errada")
        self.assertIn("Usuário ou senha inválidos", resposta.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/livros/T9999/editar").status_code, 302)

    def test_post_sem_csrf_e_recusado(self):
        self.entrar()
        resposta = self.cliente.post("/livros/T9999/editar", data={"titulo": "Outro"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.ler_no_banco()[0], "Livro de teste")

    def test_valor_invalido_nao_grava(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        dados = self.dados_do_formulario(paginas="abc", csrf=token)
        resposta = self.cliente.post("/livros/T9999/editar", data=dados)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Páginas: use só números", resposta.get_data(as_text=True))
        self.assertEqual(self.ler_no_banco()[1], None)

    def test_edicao_valida_grava_e_cria_editora(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        dados = self.dados_do_formulario(
            titulo="Livro de teste editado",
            paginas="320",
            preco="89,90",
            aquisicao_data="2024-05-01",
            editora="Editora de teste",
            nota="Observação de teste",
            csrf=token,
        )
        resposta = self.cliente.post("/livros/T9999/editar", data=dados)
        self.assertEqual(resposta.status_code, 302)

        titulo, paginas, preco, aquisicao, nota, editora = self.ler_no_banco()
        self.assertEqual(titulo, "Livro de teste editado")
        self.assertEqual(paginas, 320)
        self.assertEqual(str(preco), "89.90")
        self.assertEqual(aquisicao.isoformat(), "2024-05-01")
        self.assertEqual(nota, "Observação de teste")
        self.assertEqual(editora, "Editora de teste")

    def test_autores_sao_substituidos_pelo_formulario(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        dados = self.dados_do_formulario(autores="Autor de teste A, Autor de teste B", csrf=token)
        resposta = self.cliente.post("/livros/T9999/editar", data=dados)
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            nomes = [
                linha[0]
                for linha in conexao.execute(
                    """SELECT p.nome FROM livro_autor la
                         JOIN pessoa p ON p.id = la.pessoa_id
                         JOIN livro l ON l.id = la.livro_id
                        WHERE l.codigo = 'T9999' ORDER BY p.nome"""
                ).fetchall()
            ]
        self.assertEqual(nomes, ["Autor de teste A", "Autor de teste B"])
        # A página mostra o campo já preenchido.
        html = self.cliente.get("/livros/T9999/editar").get_data(as_text=True)
        self.assertIn("Autor de teste A, Autor de teste B", html)

    def test_generos_sao_substituidos_pelo_formulario(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        dados = self.dados_do_formulario(generos="Gênero de teste A, Gênero de teste B", csrf=token)
        resposta = self.cliente.post("/livros/T9999/editar", data=dados)
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            nomes = [
                linha[0]
                for linha in conexao.execute(
                    """SELECT g.nome FROM livro_genero lg
                         JOIN genero g ON g.id = lg.genero_id
                         JOIN livro l ON l.id = lg.livro_id
                        WHERE l.codigo = 'T9999' ORDER BY g.nome"""
                ).fetchall()
            ]
        self.assertEqual(nomes, ["Gênero de teste A", "Gênero de teste B"])
        html = self.cliente.get("/livros/T9999/editar").get_data(as_text=True)
        self.assertIn("Gênero de teste A, Gênero de teste B", html)

        # Campo vazio remove os gêneros do item.
        dados = self.dados_do_formulario(generos="", csrf=self.token_da_pagina("/livros/T9999/editar"))
        self.cliente.post("/livros/T9999/editar", data=dados)
        with psycopg.connect(URL) as conexao:
            total = conexao.execute(
                "SELECT count(*) FROM livro_genero lg JOIN livro l ON l.id = lg.livro_id WHERE l.codigo = 'T9999'"
            ).fetchone()[0]
        self.assertEqual(total, 0)

    def test_isbn_repetido_mostra_mensagem(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        # ISBN de um livro que já existe no catálogo (L0033).
        dados = self.dados_do_formulario(isbn13="978-8535929881", csrf=token)
        resposta = self.cliente.post("/livros/T9999/editar", data=dados)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Já existe outro item com este ISBN", resposta.get_data(as_text=True))

    def test_popup_mostra_link_so_com_login(self):
        resposta = self.cliente.get("/api/livros/T9999").get_json()
        self.assertFalse(resposta["editavel"])
        self.entrar()
        resposta = self.cliente.get("/api/livros/T9999").get_json()
        self.assertTrue(resposta["editavel"])

    def test_sair_encerra_a_sessao(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        self.cliente.post("/sair", data={"csrf": token})
        self.assertEqual(self.cliente.get("/livros/T9999/editar").status_code, 302)

    def trocar(self, atual, nova, confirmacao):
        token = self.token_da_pagina("/alterar-senha")
        return self.cliente.post(
            "/alterar-senha",
            data={
                "csrf": token,
                "senha_atual": atual,
                "senha_nova": nova,
                "senha_confirmacao": confirmacao,
            },
        )

    def test_troca_de_senha_vale_no_proximo_login(self):
        self.entrar()
        resposta = self.trocar(SENHA, "nova-senha-456", "nova-senha-456")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Senha alterada", resposta.get_data(as_text=True))

        app = criar_app()
        with app.app_context():
            self.assertFalse(auth.conferir_senha(app, "admin", SENHA))
            self.assertTrue(auth.conferir_senha(app, "admin", "nova-senha-456"))

    def test_troca_recusa_senha_atual_errada(self):
        self.entrar()
        resposta = self.trocar("errada", "nova-senha-456", "nova-senha-456")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("A senha atual está errada", resposta.get_data(as_text=True))
        app = criar_app()
        with app.app_context():
            self.assertTrue(auth.conferir_senha(app, "admin", SENHA))

    def test_troca_recusa_senha_curta_ou_confirmacao_diferente(self):
        self.entrar()
        curta = self.trocar(SENHA, "curta", "curta")
        self.assertIn("pelo menos 8 caracteres", curta.get_data(as_text=True))
        diferente = self.trocar(SENHA, "nova-senha-456", "outra-senha-789")
        self.assertIn("confirmação não é igual", diferente.get_data(as_text=True))
        app = criar_app()
        with app.app_context():
            self.assertTrue(auth.conferir_senha(app, "admin", SENHA))

    def test_troca_capa_grava_arquivo_e_aponta_o_item(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        resposta = self.cliente.post(
            "/livros/T9999/capa",
            data={"csrf": token, "capa": (io.BytesIO(PNG_MINIMO), "capa.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            capa = conexao.execute("SELECT capa_arquivo FROM livro WHERE codigo = 'T9999'").fetchone()[0]
        self.assertEqual(capa, "livro/T9999.png")
        self.assertTrue(os.path.exists(os.path.join(CAPAS_TESTE, "livro", "T9999.png")))

    def test_troca_capa_recusa_arquivo_que_nao_e_imagem(self):
        self.entrar()
        token = self.token_da_pagina("/livros/T9999/editar")
        resposta = self.cliente.post(
            "/livros/T9999/capa",
            data={"csrf": token, "capa": (io.BytesIO(b"isto e texto"), "capa.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Use uma imagem JPG, PNG ou WEBP", resposta.get_data(as_text=True))
        with psycopg.connect(URL) as conexao:
            capa = conexao.execute("SELECT capa_arquivo FROM livro WHERE codigo = 'T9999'").fetchone()[0]
        self.assertIsNone(capa)

    def test_edicao_desligada_nao_expoe_rotas(self):
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": None,
                "DATABASE_URL_ESCRITA": None,
                "EDICAO_ATIVA": False,
            }
        )
        cliente = app.test_client()
        self.assertEqual(cliente.get("/livros/T9999/editar").status_code, 404)
        self.assertIn("não está configurada", cliente.get("/entrar").get_data(as_text=True))


class FigurinhasTest(unittest.TestCase):
    """Álbum temporário F9999 com 3 figurinhas: marcar todas deixa o álbum completo."""

    @classmethod
    def setUpClass(cls):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM album_figurinha WHERE codigo = 'F9999'")
            conexao.execute(
                "INSERT INTO album_figurinha (codigo, titulo, numero_figurinhas) VALUES ('F9999', 'Álbum de teste', 3)"
            )

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM album_figurinha WHERE codigo = 'F9999'")

    def setUp(self):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM album_figurinha_marcada WHERE album_id = (SELECT id FROM album_figurinha WHERE codigo = 'F9999')")
            conexao.execute("UPDATE album_figurinha SET numero_figurinhas = 3, completo = false WHERE codigo = 'F9999'")
            conexao.execute("DELETE FROM admin_senha WHERE usuario = 'admin'")
        self.cliente = criar_app().test_client()
        html = self.cliente.get("/entrar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        self.cliente.post("/entrar", data={"csrf": token, "usuario": "admin", "senha": SENHA, "proxima": "/album"})

    def completo_no_banco(self):
        with psycopg.connect(URL) as conexao:
            return conexao.execute("SELECT completo FROM album_figurinha WHERE codigo = 'F9999'").fetchone()[0]

    def marcar(self, numeros):
        html = self.cliente.get("/album/F9999/editar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        return self.cliente.post(
            "/album/F9999/figurinhas",
            data={"csrf": token, "numero": [str(n) for n in numeros]},
        )

    def test_completo_so_quando_todas_estao_marcadas(self):
        self.assertEqual(self.marcar([1, 2]).status_code, 302)
        self.assertFalse(self.completo_no_banco())
        self.assertEqual(self.marcar([1, 2, 3]).status_code, 302)
        self.assertTrue(self.completo_no_banco())
        self.marcar([1])
        self.assertFalse(self.completo_no_banco())

    def test_numero_fora_do_total_e_ignorado(self):
        self.marcar([1, 2, 3, 9])
        with psycopg.connect(URL) as conexao:
            numeros = [r[0] for r in conexao.execute(
                "SELECT m.numero FROM album_figurinha_marcada m JOIN album_figurinha a ON a.id = m.album_id "
                "WHERE a.codigo = 'F9999' ORDER BY m.numero").fetchall()]
        self.assertEqual(numeros, [1, 2, 3])


class ExtrasTest(FigurinhasTest):
    """Itens extras do álbum F9999: marcação com o mesmo limite de 1 até o total."""

    def test_extras_so_aceitam_numeros_ate_o_total(self):
        with psycopg.connect(URL) as conexao:
            conexao.execute(
                "UPDATE album_figurinha SET tem_extra = true, extra_total = 2 WHERE codigo = 'F9999'"
            )
            conexao.execute(
                "DELETE FROM album_extra_marcado WHERE album_id = (SELECT id FROM album_figurinha WHERE codigo = 'F9999')"
            )
        html = self.cliente.get("/album/F9999/editar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        resposta = self.cliente.post(
            "/album/F9999/extras",
            data={"csrf": token, "numero": ["1", "2", "5"]},
        )
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            numeros = [r[0] for r in conexao.execute(
                "SELECT m.numero FROM album_extra_marcado m JOIN album_figurinha a ON a.id = m.album_id "
                "WHERE a.codigo = 'F9999' ORDER BY m.numero").fetchall()]
            conexao.execute("UPDATE album_figurinha SET tem_extra = false, extra_total = NULL WHERE codigo = 'F9999'")
        self.assertEqual(numeros, [1, 2])


class FichasTest(unittest.TestCase):
    """Fichas para impressão: exigem login, têm QR code e mostram o item selecionado."""

    def setUp(self):
        self.cliente = criar_app().test_client()

    def test_fichas_sem_login_redirecionam(self):
        resposta = self.cliente.get("/fichas?i=livros:L0013")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/entrar", resposta.headers["Location"])

    def test_fichas_com_login_trazem_dados_e_qr(self):
        html = self.cliente.get("/entrar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        self.cliente.post("/entrar", data={"csrf": token, "usuario": "admin", "senha": SENHA, "proxima": "/"})
        resposta = self.cliente.get("/fichas?i=livros:L0013&i=gibis:H0007")
        self.assertEqual(resposta.status_code, 200)
        texto = resposta.get_data(as_text=True)
        self.assertIn("Água Viva", texto)
        # Um QR code por ficha (o endereço fica codificado nos pontos, não como texto).
        self.assertEqual(texto.count("<svg"), 2)

    def test_pagina_do_item(self):
        resposta = self.cliente.get("/livros/L0013")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Água Viva", resposta.get_data(as_text=True))
        self.assertEqual(self.cliente.get("/livros/NAOEXISTE").status_code, 404)


class SerieGibiTest(unittest.TestCase):
    """Série fechada de gibi: números marcados e capa por número, num gibi temporário H9999."""

    @classmethod
    def setUpClass(cls):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM gibi WHERE codigo = 'H9999'")
            conexao.execute(
                "INSERT INTO gibi (codigo, titulo, serie_fechada, serie_total) VALUES ('H9999', 'Série de teste', true, 3)"
            )

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM gibi WHERE codigo = 'H9999'")

    def setUp(self):
        with psycopg.connect(URL) as conexao:
            conexao.execute(
                "DELETE FROM gibi_serie_item WHERE gibi_id = (SELECT id FROM gibi WHERE codigo = 'H9999')"
            )
            conexao.execute("DELETE FROM admin_senha WHERE usuario = 'admin'")
        self.cliente = criar_app().test_client()
        html = self.cliente.get("/entrar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        self.cliente.post("/entrar", data={"csrf": token, "usuario": "admin", "senha": SENHA, "proxima": "/"})

    def token(self):
        html = self.cliente.get("/gibis/H9999/editar").get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def test_marca_numeros_e_grava_capa(self):
        resposta = self.cliente.post(
            "/gibis/H9999/serie",
            data={
                "csrf": self.token(),
                "numero": ["1", "2"],
                "capa_2": (io.BytesIO(PNG_MINIMO), "n2.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            linhas = conexao.execute(
                """SELECT s.numero, s.marcado, s.capa_arquivo FROM gibi_serie_item s
                     JOIN gibi g ON g.id = s.gibi_id WHERE g.codigo = 'H9999' ORDER BY s.numero"""
            ).fetchall()
        self.assertEqual([(n, m) for n, m, _ in linhas], [(1, True), (2, True), (3, False)])
        self.assertEqual(linhas[1][2], "gibi/serie/H9999-2.png")
        self.assertTrue(os.path.exists(os.path.join(CAPAS_TESTE, "gibi", "serie", "H9999-2.png")))

    def test_serie_completa_so_com_todos_os_numeros(self):
        def completa():
            with psycopg.connect(URL) as conexao:
                return conexao.execute("SELECT serie_completa FROM gibi WHERE codigo = 'H9999'").fetchone()[0]

        self.cliente.post("/gibis/H9999/serie", data={"csrf": self.token(), "numero": ["1", "2"]})
        self.assertFalse(completa())
        self.cliente.post("/gibis/H9999/serie", data={"csrf": self.token(), "numero": ["1", "2", "3"]})
        self.assertTrue(completa())

    def test_recusa_capa_que_nao_e_imagem(self):
        resposta = self.cliente.post(
            "/gibis/H9999/serie",
            data={"csrf": self.token(), "capa_1": (io.BytesIO(b"texto"), "x.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Use uma imagem JPG, PNG ou WEBP", resposta.get_data(as_text=True))


def limpar_novos():
    """Remove o que os testes de cadastro novo criam (códigos T9997 e F9997)."""
    with psycopg.connect(URL) as conexao:
        conexao.execute(
            "DELETE FROM livro_autor WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9997')"
        )
        conexao.execute("DELETE FROM livro WHERE codigo = 'T9997'")
        conexao.execute("DELETE FROM album_figurinha WHERE codigo = 'F9997'")
        conexao.execute("DELETE FROM pessoa WHERE nome IN ('Autor novo A', 'Autor novo B')")
        conexao.execute("DELETE FROM editora WHERE nome = 'Editora nova de teste'")
        conexao.execute("DELETE FROM estante WHERE nome = 'Estante nova de teste'")
        conexao.execute("DELETE FROM genero WHERE nome LIKE 'Gênero de teste%'")
    for arquivo in ("livro/T9997.png", "album/F9997.png"):
        caminho = os.path.join(CAPAS_TESTE, arquivo)
        if os.path.exists(caminho):
            os.remove(caminho)


DADOS_LIVRO_NOVO = {
    "titulo": "Livro novo de teste",
    "autores": "Autor novo A, Autor novo B",
    "editora": "Editora nova de teste",
    "estante": "Estante nova de teste",
    "paginas": "412",
    "ano_publicacao": "2019",
    "lingua": "Português",
    "edicao": "2ª edição",
    "encadernacao": "Brochura",
    "isbn10": "0306406152",
    "isbn13": "9780306406157",
    "clube_do_livro": "Sim",
    "conservacao": "Bom",
    "aquisicao_data": "2024-03-10",
    "preco": "59,90",
    "capa_fonte": "Editora",
    "nota": "Observação do cadastro novo",
    "sinopse": "Sinopse de teste.",
    "generos": "Gênero de teste A",
}


class NovoItemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        limpar_novos()

    @classmethod
    def tearDownClass(cls):
        limpar_novos()

    def setUp(self):
        # Cada teste começa sem os itens criados pelos anteriores.
        limpar_novos()
        self.cliente = criar_app().test_client()
        self.cliente.post(
            "/entrar",
            data={
                "csrf": self.token_da_pagina("/entrar"),
                "usuario": "admin",
                "senha": SENHA,
                "proxima": "/livros",
            },
        )

    def token_da_pagina(self, url):
        html = self.cliente.get(url).get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def formulario(self, **alterados):
        dados = {campo["chave"]: "" for campo in edicao.campos_formulario("livros")}
        dados["codigo"] = "T9997"
        dados.update(DADOS_LIVRO_NOVO)
        dados["csrf"] = self.token_da_pagina("/livros/novo")
        dados.update(alterados)
        return dados

    def existe(self, tabela, codigo):
        with psycopg.connect(URL) as conexao:
            return conexao.execute(f"SELECT 1 FROM {tabela} WHERE codigo = %s", (codigo,)).fetchone()

    def test_sem_login_redireciona_para_entrar(self):
        resposta = criar_app().test_client().get("/livros/novo")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/entrar", resposta.headers["Location"])

    def test_pagina_sugere_proximo_codigo(self):
        html = self.cliente.get("/livros/novo").get_data(as_text=True)
        self.assertRegex(html, r'name="codigo" value="L\d{4}"')

    def test_cadastra_livro_com_todos_os_campos(self):
        resposta = self.cliente.post("/livros/novo", data=self.formulario(), content_type="multipart/form-data")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/livros/T9997/editar", resposta.headers["Location"])
        self.assertIn("novo=1", resposta.headers["Location"])

        with psycopg.connect(URL) as conexao:
            linha = conexao.execute(
                """SELECT l.titulo, l.paginas, l.ano_publicacao, l.lingua, l.edicao, l.encadernacao,
                          l.isbn10, l.isbn13, l.clube_do_livro, l.conservacao, l.aquisicao_data,
                          l.preco, l.capa_fonte, l.nota, l.sinopse, ed.nome, es.nome
                     FROM livro l
                     LEFT JOIN editora ed ON ed.id = l.editora_id
                     LEFT JOIN estante es ON es.id = l.estante_id
                    WHERE l.codigo = 'T9997'"""
            ).fetchone()
            autores = [
                r[0] for r in conexao.execute(
                    """SELECT p.nome FROM livro_autor la JOIN pessoa p ON p.id = la.pessoa_id
                        JOIN livro l ON l.id = la.livro_id WHERE l.codigo = 'T9997' ORDER BY p.nome"""
                ).fetchall()
            ]
        titulo, paginas, ano, lingua, edicao_, enc, isbn10, isbn13, clube, cons, aquisicao, preco, fonte, nota, sinopse, editora, estante = linha
        self.assertEqual(titulo, "Livro novo de teste")
        self.assertEqual(paginas, 412)
        self.assertEqual(ano, 2019)
        self.assertEqual(lingua, "Português")
        self.assertEqual(edicao_, "2ª edição")
        self.assertEqual(enc, "Brochura")
        self.assertEqual(isbn10, "0306406152")
        self.assertEqual(isbn13, "9780306406157")
        self.assertEqual(clube, "Sim")
        self.assertEqual(cons, "Bom")
        self.assertEqual(aquisicao.isoformat(), "2024-03-10")
        self.assertEqual(str(preco), "59.90")
        self.assertEqual(fonte, "Editora")
        self.assertEqual(nota, "Observação do cadastro novo")
        self.assertEqual(sinopse, "Sinopse de teste.")
        self.assertEqual(editora, "Editora nova de teste")
        self.assertEqual(estante, "Estante nova de teste")
        self.assertEqual(autores, ["Autor novo A", "Autor novo B"])
        with psycopg.connect(URL) as conexao:
            generos = [r[0] for r in conexao.execute(
                """SELECT g.nome FROM livro_genero lg JOIN genero g ON g.id = lg.genero_id
                    JOIN livro l ON l.id = lg.livro_id WHERE l.codigo = 'T9997'"""
            ).fetchall()]
        self.assertEqual(generos, ["Gênero de teste A"])

    def test_codigo_em_minusculas_vira_maiusculas(self):
        resposta = self.cliente.post("/livros/novo", data=self.formulario(codigo="t9997"))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(self.existe("livro", "T9997"))

    def test_codigo_repetido_nao_cria_de_novo(self):
        self.cliente.post("/livros/novo", data=self.formulario())
        resposta = self.cliente.post("/livros/novo", data=self.formulario(isbn10="", isbn13=""))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Já existe um item com este código", resposta.get_data(as_text=True))
        with psycopg.connect(URL) as conexao:
            total = conexao.execute("SELECT count(*) FROM livro WHERE codigo = 'T9997'").fetchone()[0]
        self.assertEqual(total, 1)

    def test_codigo_invalido_nao_cria(self):
        resposta = self.cliente.post("/livros/novo", data=self.formulario(codigo="abc"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Código: use uma letra", resposta.get_data(as_text=True))
        self.assertFalse(self.existe("livro", "ABC"))

    def test_campo_invalido_mantem_digitacao_e_nao_cria(self):
        resposta = self.cliente.post("/livros/novo", data=self.formulario(paginas="muitas"))
        html = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Páginas: use só números", html)
        self.assertIn('value="Livro novo de teste"', html)
        self.assertFalse(self.existe("livro", "T9997"))

    def test_isbn_de_outro_item_nao_cria(self):
        # ISBN já usado por um livro do catálogo (L0033).
        resposta = self.cliente.post("/livros/novo", data=self.formulario(isbn13="978-8535929881"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Já existe um item com este código ou com este ISBN", resposta.get_data(as_text=True))
        self.assertFalse(self.existe("livro", "T9997"))

    def test_capa_invalida_nao_cria_o_item(self):
        dados = self.formulario(capa=(io.BytesIO(b"texto"), "x.png"))
        resposta = self.cliente.post("/livros/novo", data=dados, content_type="multipart/form-data")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Capa: use uma imagem JPG, PNG ou WEBP", resposta.get_data(as_text=True))
        self.assertFalse(self.existe("livro", "T9997"))

    def test_capa_valida_e_gravada_com_o_item(self):
        dados = self.formulario(capa=(io.BytesIO(PNG_MINIMO), "capa.png"))
        resposta = self.cliente.post("/livros/novo", data=dados, content_type="multipart/form-data")
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            capa = conexao.execute("SELECT capa_arquivo FROM livro WHERE codigo = 'T9997'").fetchone()[0]
        self.assertEqual(capa, "livro/T9997.png")
        self.assertTrue(os.path.exists(os.path.join(CAPAS_TESTE, "livro", "T9997.png")))

    def test_cadastra_album_e_calcula_completo(self):
        dados = {
            "csrf": self.token_da_pagina("/album/novo"),
            "codigo": "F9997",
            "titulo": "Álbum novo de teste",
            "numero_figurinhas": "80",
            "tem_extra": "on",
            "extra_descricao": "Cards",
            "extra_total": "5",
            "notas": "Teste",
        }
        resposta = self.cliente.post("/album/novo", data=dados)
        self.assertEqual(resposta.status_code, 302)
        with psycopg.connect(URL) as conexao:
            linha = conexao.execute(
                """SELECT numero_figurinhas, tem_extra, extra_descricao, extra_total, completo
                     FROM album_figurinha WHERE codigo = 'F9997'"""
            ).fetchone()
        self.assertEqual(linha, (80, True, "Cards", 5, False))

    def test_tipo_desconhecido_da_404(self):
        self.assertEqual(self.cliente.get("/revistas/novo").status_code, 404)


class ExcluirItemTest(unittest.TestCase):
    """Exclusão lógica: o item some do site e o registro continua no banco."""

    @classmethod
    def setUpClass(cls):
        limpar_excluido()

    @classmethod
    def tearDownClass(cls):
        limpar_excluido()

    def setUp(self):
        limpar_excluido()
        edicao.criar(criar_app(), "livros", "T9996", {"titulo": "Livro sumido de teste", "autores": ""})
        self.cliente = criar_app().test_client()
        self.cliente.post(
            "/entrar",
            data={
                "csrf": self.token_da_pagina("/entrar"),
                "usuario": "admin",
                "senha": SENHA,
                "proxima": "/livros",
            },
        )

    def token_da_pagina(self, url):
        html = self.cliente.get(url).get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def excluido_no_banco(self):
        with psycopg.connect(URL) as conexao:
            return conexao.execute("SELECT excluido FROM livro WHERE codigo = 'T9996'").fetchone()

    def test_item_aparece_antes_de_excluir(self):
        html = self.cliente.get("/livros?q=Livro+sumido").get_data(as_text=True)
        self.assertIn('data-codigo="T9996"', html)

    def test_excluir_marca_sem_apagar(self):
        token = self.token_da_pagina("/livros/T9996/editar")
        resposta = self.cliente.post("/livros/T9996/excluir", data={"csrf": token})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.excluido_no_banco(), (True,))

    def test_item_excluido_some_da_lista_e_da_busca(self):
        token = self.token_da_pagina("/livros/T9996/editar")
        self.cliente.post("/livros/T9996/excluir", data={"csrf": token})
        html = self.cliente.get("/livros?q=Livro+sumido").get_data(as_text=True)
        self.assertNotIn('data-codigo="T9996"', html)

    def test_item_excluido_nao_tem_pagina_popup_nem_edicao(self):
        token = self.token_da_pagina("/livros/T9996/editar")
        self.cliente.post("/livros/T9996/excluir", data={"csrf": token})
        self.assertEqual(self.cliente.get("/livros/T9996").status_code, 404)
        self.assertEqual(self.cliente.get("/api/livros/T9996").status_code, 404)
        self.assertEqual(self.cliente.get("/livros/T9996/editar").status_code, 404)

    def test_item_excluido_nao_aceita_edicao_nem_troca_de_capa(self):
        token = self.token_da_pagina("/livros/T9996/editar")
        self.cliente.post("/livros/T9996/excluir", data={"csrf": token})
        dados = {"csrf": token, "titulo": "Outro titulo", "autores": ""}
        for chave in edicao.campos_formulario("livros"):
            dados.setdefault(chave["chave"], "")
        self.assertEqual(self.cliente.post("/livros/T9996/editar", data=dados).status_code, 404)
        with psycopg.connect(URL) as conexao:
            titulo = conexao.execute("SELECT titulo FROM livro WHERE codigo = 'T9996'").fetchone()
        self.assertEqual(titulo, ("Livro sumido de teste",))

    def test_excluir_exige_login(self):
        sem_login = criar_app().test_client()
        resposta = sem_login.post("/livros/T9996/excluir", data={"csrf": "x"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.excluido_no_banco(), (False,))

    def test_excluir_exige_csrf(self):
        resposta = self.cliente.post("/livros/T9996/excluir", data={"csrf": "errado"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.excluido_no_banco(), (False,))

    def test_excluir_item_inexistente_da_404(self):
        token = self.token_da_pagina("/livros/T9996/editar")
        self.assertEqual(self.cliente.post("/livros/T0000/excluir", data={"csrf": token}).status_code, 404)

    def test_pagina_de_edicao_mostra_botao_excluir(self):
        html = self.cliente.get("/livros/T9996/editar").get_data(as_text=True)
        self.assertIn("/livros/T9996/excluir", html)
        self.assertIn("Excluir item", html)


class GeneroGibiVinilTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        limpar_generos_gibi_vinil()

    @classmethod
    def tearDownClass(cls):
        limpar_generos_gibi_vinil()

    def generos_do(self, tabela_ligacao, coluna, codigo, tabela_item):
        with psycopg.connect(URL) as conexao:
            return [r[0] for r in conexao.execute(
                f"""SELECT g.nome FROM {tabela_ligacao} lg JOIN genero g ON g.id = lg.genero_id
                      JOIN {tabela_item} i ON i.id = lg.{coluna} WHERE i.codigo = %s ORDER BY g.nome""",
                (codigo,),
            ).fetchall()]

    def test_gibi_grava_generos(self):
        app = criar_app()
        edicao.criar(app, "gibis", "H9996", {"titulo": "Gibi de teste", "serie_fechada": False, "generos": "Gênero de teste A, Gênero de teste B"})
        self.assertEqual(self.generos_do("gibi_genero", "gibi_id", "H9996", "gibi"),
                         ["Gênero de teste A", "Gênero de teste B"])

    def test_vinil_grava_generos(self):
        app = criar_app()
        edicao.criar(app, "vinil", "V996", {"titulo": "Vinil de teste", "generos": "Gênero de teste A"})
        self.assertEqual(self.generos_do("lp_genero", "lp_id", "V996", "lp_vinil"), ["Gênero de teste A"])
        html = criar_app().test_client().get("/vinil/V996").get_data(as_text=True)
        self.assertIn("Gênero de teste A", html)


def limpar_generos_gibi_vinil():
    with psycopg.connect(URL) as conexao:
        conexao.execute("DELETE FROM gibi WHERE codigo = 'H9996'")
        conexao.execute("DELETE FROM lp_vinil WHERE codigo = 'V996'")
        conexao.execute("DELETE FROM genero WHERE nome LIKE 'Gênero de teste%'")


def limpar_excluido():
    with psycopg.connect(URL) as conexao:
        conexao.execute("DELETE FROM livro WHERE codigo = 'T9996'")


def limpar_contagem():
    with psycopg.connect(URL) as conexao:
        conexao.execute("DELETE FROM gibi WHERE codigo IN ('H9998', 'H9997')")


class ContagemItensTest(unittest.TestCase):
    """O resumo da lista conta cada número marcado de uma série fechada como um item."""

    @classmethod
    def setUpClass(cls):
        limpar_contagem()

    @classmethod
    def tearDownClass(cls):
        limpar_contagem()

    def setUp(self):
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM gibi WHERE codigo IN ('H9998', 'H9997')")
            conexao.execute(
                "INSERT INTO gibi (codigo, titulo, serie_fechada, serie_total)"
                " VALUES ('H9998', 'Série de contagem', true, 3)"
            )
            conexao.execute("INSERT INTO gibi (codigo, titulo) VALUES ('H9997', 'Gibi avulso de contagem')")

    def marcar(self, numeros):
        with psycopg.connect(URL) as conexao:
            for numero in range(1, 4):
                conexao.execute(
                    """INSERT INTO gibi_serie_item (gibi_id, numero, marcado)
                       SELECT id, %s, %s FROM gibi WHERE codigo = 'H9998'""",
                    (numero, numero in numeros),
                )

    def test_conta_um_item_por_numero_marcado(self):
        self.marcar({1, 2})
        app = criar_app()
        with app.app_context():
            # Dois números da série mais o gibi avulso; o filtro limita aos itens do teste.
            self.assertEqual(catalogo.contar_itens(app, "gibis", {"q": "contagem"}), 3)

    def test_serie_sem_numero_marcado_nao_conta(self):
        app = criar_app()
        with app.app_context():
            self.assertEqual(catalogo.contar_itens(app, "gibis", {"q": "Série de contagem"}), 0)

    def test_gibi_sem_serie_conta_um(self):
        app = criar_app()
        with app.app_context():
            self.assertEqual(catalogo.contar_itens(app, "gibis", {"q": "Gibi avulso de contagem"}), 1)

    def test_pagina_mostra_o_total_de_itens(self):
        self.marcar({1, 2})
        html = criar_app().test_client().get("/gibis?q=contagem").get_data(as_text=True)
        self.assertIn("3 itens", html)
        self.assertIn("(2 cadastros)", html)


def limpar_extras_livro():
    with psycopg.connect(URL) as conexao:
        conexao.execute(
            "DELETE FROM livro_extra WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
        )
        conexao.execute("UPDATE livro SET tem_conteudo_extra = false WHERE codigo = 'T9999'")


class ConteudoExtraLivroTest(unittest.TestCase):
    """Conteúdo extra do livro T9999: marcador verdadeiro/falso e itens com nome, descrição e foto."""

    @classmethod
    def setUpClass(cls):
        with psycopg.connect(URL) as conexao:
            conexao.execute(
                "INSERT INTO livro (codigo, titulo) VALUES ('T9999', 'Livro de teste')"
                " ON CONFLICT (codigo) DO NOTHING"
            )

    @classmethod
    def tearDownClass(cls):
        limpar_extras_livro()
        shutil.rmtree(os.path.join(CAPAS_TESTE, "extras"), ignore_errors=True)

    def setUp(self):
        limpar_extras_livro()
        shutil.rmtree(os.path.join(CAPAS_TESTE, "extras"), ignore_errors=True)
        with psycopg.connect(URL) as conexao:
            conexao.execute("DELETE FROM admin_senha WHERE usuario = 'admin'")
        self.cliente = criar_app().test_client()
        html = self.cliente.get("/entrar").get_data(as_text=True)
        token = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
        self.cliente.post(
            "/entrar",
            data={"csrf": token, "usuario": "admin", "senha": SENHA, "proxima": "/livros"},
        )

    def token(self, url="/livros/T9999/editar"):
        html = self.cliente.get(url).get_data(as_text=True)
        return re.search(r'name="csrf" value="([^"]+)"', html).group(1)

    def incluir(self, **campos):
        dados = {"csrf": self.token()}
        dados.update(campos)
        return self.cliente.post(
            "/livros/T9999/conteudo-extra", data=dados, content_type="multipart/form-data"
        )

    def itens(self):
        with psycopg.connect(URL) as conexao:
            return conexao.execute(
                """SELECT x.id, x.nome, x.descricao, x.foto_arquivo
                     FROM livro_extra x JOIN livro l ON l.id = x.livro_id
                    WHERE l.codigo = 'T9999' ORDER BY x.ordem, x.id"""
            ).fetchall()

    def arquivo_da_foto(self, item_id, extensao):
        return os.path.join(CAPAS_TESTE, "extras", "livro", f"T9999-{item_id}.{extensao}")

    def test_formulario_tem_o_marcador_e_grava_verdadeiro(self):
        dados = {campo["chave"]: "" for campo in edicao.campos_formulario("livros")}
        dados.update(titulo="Livro de teste", tem_conteudo_extra="on", csrf=self.token())
        self.assertEqual(self.cliente.post("/livros/T9999/editar", data=dados).status_code, 302)
        with psycopg.connect(URL) as conexao:
            marcado = conexao.execute(
                "SELECT tem_conteudo_extra FROM livro WHERE codigo = 'T9999'"
            ).fetchone()[0]
        self.assertTrue(marcado)

        # Sem a caixa marcada, o mesmo formulário volta o marcador para falso.
        dados = {campo["chave"]: "" for campo in edicao.campos_formulario("livros")}
        dados.update(titulo="Livro de teste", csrf=self.token())
        self.cliente.post("/livros/T9999/editar", data=dados)
        with psycopg.connect(URL) as conexao:
            marcado = conexao.execute(
                "SELECT tem_conteudo_extra FROM livro WHERE codigo = 'T9999'"
            ).fetchone()[0]
        self.assertFalse(marcado)

    def test_pagina_de_edicao_mostra_o_gerenciador(self):
        html = self.cliente.get("/livros/T9999/editar").get_data(as_text=True)
        self.assertIn("Gerenciar conteúdo extra", html)
        self.assertIn('name="tem_conteudo_extra"', html)

    def test_item_extra_tem_area_para_arrastar_e_colar_a_foto(self):
        self.incluir(nome="Marcador")
        html = self.cliente.get("/livros/T9999/editar").get_data(as_text=True)
        # Uma área para cada item cadastrado e outra no formulário de inclusão.
        self.assertEqual(html.count('class="zona-foto"'), len(self.itens()) + 1)
        self.assertIn("Arraste a foto aqui", html)
        self.assertIn("Ctrl+V", html)
        self.assertIn("zona-foto-previa", html)
        self.assertIn('name="foto"', html)

    def test_inclui_item_com_foto(self):
        resposta = self.incluir(
            nome="Pôster", descricao="Pôster dobrável", foto=(io.BytesIO(PNG_MINIMO), "poster.png")
        )
        self.assertEqual(resposta.status_code, 302)
        itens = self.itens()
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0][1], "Pôster")
        self.assertEqual(itens[0][2], "Pôster dobrável")
        self.assertEqual(itens[0][3], f"extras/livro/T9999-{itens[0][0]}.png")
        self.assertTrue(os.path.exists(self.arquivo_da_foto(itens[0][0], "png")))

    def test_inclui_item_sem_foto(self):
        self.assertEqual(self.incluir(nome="Marcador", descricao="Dois marcadores").status_code, 302)
        self.assertEqual(
            [(item[1], item[2], item[3]) for item in self.itens()],
            [("Marcador", "Dois marcadores", None)],
        )

    def test_nome_vazio_mostra_erro(self):
        resposta = self.incluir(nome="", descricao="Sem nome")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Nome do item: preencha este campo", resposta.get_data(as_text=True))
        self.assertEqual(self.itens(), [])

    def test_foto_invalida_mostra_erro(self):
        resposta = self.incluir(nome="Agenda", foto=(io.BytesIO(b"isto e texto"), "agenda.png"))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Foto: use uma imagem JPG, PNG ou WEBP", resposta.get_data(as_text=True))
        self.assertEqual(self.itens(), [])

    def test_altera_o_item_sem_perder_a_foto(self):
        self.incluir(nome="Minilivro", foto=(io.BytesIO(PNG_MINIMO), "mini.png"))
        item = self.itens()[0]
        resposta = self.cliente.post(
            "/livros/T9999/conteudo-extra",
            data={
                "csrf": self.token(),
                "extra_id": str(item[0]),
                "nome": "Minilivro de bolso",
                "descricao": "Conto extra",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 302)
        alterado = self.itens()[0]
        self.assertEqual(alterado[1], "Minilivro de bolso")
        self.assertEqual(alterado[2], "Conto extra")
        self.assertEqual(alterado[3], item[3])

    def test_troca_a_foto_e_descarta_a_antiga(self):
        self.incluir(nome="Pôster", foto=(io.BytesIO(PNG_MINIMO), "poster.png"))
        item = self.itens()[0]
        jpg = b"\xff\xd8\xff" + b"\x00" * 64
        resposta = self.incluir(extra_id=str(item[0]), nome="Pôster", foto=(io.BytesIO(jpg), "poster.jpg"))
        self.assertEqual(resposta.status_code, 302)
        trocado = self.itens()[0]
        self.assertEqual(trocado[3], f"extras/livro/T9999-{item[0]}.jpg")
        self.assertTrue(os.path.exists(self.arquivo_da_foto(item[0], "jpg")))
        self.assertFalse(os.path.exists(self.arquivo_da_foto(item[0], "png")))

    def test_exclui_item_e_a_foto(self):
        self.incluir(nome="Agenda", foto=(io.BytesIO(PNG_MINIMO), "agenda.png"))
        item = self.itens()[0]
        resposta = self.cliente.post(
            f"/livros/T9999/conteudo-extra/{item[0]}/excluir", data={"csrf": self.token()}
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.itens(), [])
        self.assertFalse(os.path.exists(self.arquivo_da_foto(item[0], "png")))

    def test_excluir_item_inexistente_da_404(self):
        resposta = self.cliente.post("/livros/T9999/conteudo-extra/999999/excluir", data={"csrf": self.token()})
        self.assertEqual(resposta.status_code, 404)

    def test_pagina_do_livro_mostra_o_botao(self):
        self.incluir(nome="Pôster", descricao="Pôster dobrável")
        html = self.cliente.get("/livros/T9999").get_data(as_text=True)
        self.assertIn("Ver conteúdo extra", html)
        self.assertIn("Pôster dobrável", html)

    def test_livro_sem_extra_nao_mostra_o_botao(self):
        html = self.cliente.get("/livros/T9999").get_data(as_text=True)
        self.assertNotIn("Ver conteúdo extra", html)

    def test_api_do_popup_traz_os_extras_e_o_marcador(self):
        self.incluir(nome="Marcador", foto=(io.BytesIO(PNG_MINIMO), "marcador.png"))
        dados = self.cliente.get("/api/livros/T9999").get_json()
        self.assertEqual([item["nome"] for item in dados["extras_livro"]], ["Marcador"])
        self.assertTrue(dados["extras_livro"][0]["foto"].startswith("extras/livro/T9999-"))
        # O marcador do livro só entra nos campos do popup quando há conteúdo extra.
        with psycopg.connect(URL) as conexao:
            conexao.execute("UPDATE livro SET tem_conteudo_extra = true WHERE codigo = 'T9999'")
        dados = self.cliente.get("/api/livros/T9999").get_json()
        self.assertIn({"rotulo": "Conteúdo extra", "valor": "Sim"}, dados["campos"])

    def test_api_sem_marcador_nao_mostra_conteudo_extra(self):
        dados = self.cliente.get("/api/livros/T9999").get_json()
        self.assertEqual(dados["extras_livro"], [])
        self.assertNotIn("Conteúdo extra", [campo["rotulo"] for campo in dados["campos"]])


if __name__ == "__main__":
    unittest.main()
