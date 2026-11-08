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
            "DELETE FROM livro_autor WHERE livro_id IN (SELECT id FROM livro WHERE codigo = 'T9999')"
        )
        conexao.execute("DELETE FROM livro WHERE codigo = 'T9999'")
        conexao.execute(
            """DELETE FROM pessoa p WHERE p.nome LIKE 'Autor de teste%'
               AND NOT EXISTS (SELECT 1 FROM livro_autor la WHERE la.pessoa_id = p.id)"""
        )
        conexao.execute("DELETE FROM editora WHERE nome = 'Editora de teste'")
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


if __name__ == "__main__":
    unittest.main()
