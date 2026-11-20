"""Estrutura do álbum de Copa do Mundo Qatar 2022 e regra de total no formulário.

Não usam banco: rodam só com a estrutura em app/copa.py.
"""

import unittest

from app import copa, edicao


class EstruturaAlbumCopa(unittest.TestCase):
    def setUp(self):
        self.secoes = copa.secoes_com_numeros()
        self.figurinhas = [f for s in self.secoes for f in s["figurinhas"]]

    def test_total_e_670(self):
        self.assertEqual(len(self.figurinhas), copa.TOTAL_FIGURINHAS)
        self.assertEqual(copa.TOTAL_FIGURINHAS, 670)

    def test_numeros_sao_sequenciais_de_1_a_670(self):
        self.assertEqual([f["numero"] for f in self.figurinhas], list(range(1, 671)))

    def test_rotulos_sao_unicos(self):
        rotulos = [f["rotulo"] for f in self.figurinhas]
        self.assertEqual(len(rotulos), len(set(rotulos)))

    def test_primeira_e_ultima_figurinha(self):
        self.assertEqual(self.figurinhas[0]["rotulo"], "00")
        self.assertEqual(self.figurinhas[-1]["rotulo"], "FWC29")

    def test_posicoes_conhecidas(self):
        por_rotulo = {f["rotulo"]: f["numero"] for f in self.figurinhas}
        # Introdução (00 + FWC1 a FWC7) e estádios (FWC8 a FWC18) vêm antes das seleções.
        self.assertEqual(por_rotulo["FWC7"], 8)
        self.assertEqual(por_rotulo["FWC8"], 9)
        self.assertEqual(por_rotulo["QAT1"], 20)
        self.assertEqual(por_rotulo["QAT20"], 39)
        # Grupo A tem 4 seleções de 20 figurinhas: 80 no total, de 20 a 99.
        self.assertEqual(por_rotulo["ENG1"], 100)
        self.assertEqual(por_rotulo["BRA1"], 20 + 6 * 80)
        self.assertEqual(por_rotulo["FWC19"], 660)

    def test_cada_selecao_tem_20_figurinhas_numeradas(self):
        for grupo in copa._GRUPOS.values():
            for sigla in grupo:
                rotulos = [f"{sigla}{n}" for n in range(1, 21)]
                for rotulo in rotulos:
                    self.assertIn(rotulo, [f["rotulo"] for f in self.figurinhas])

    def test_trinta_e_duas_selecoes(self):
        self.assertEqual(sum(len(g) for g in copa._GRUPOS.values()), 32)

    def test_todos_os_rotulos_bate_com_as_secoes(self):
        self.assertEqual(copa.todos_os_rotulos(), [f["rotulo"] for f in self.figurinhas])


class RegraDeTotalNoFormulario(unittest.TestCase):
    def test_album_de_copa_forca_670(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Copa 2022", "copa_mundo": "on"})
        self.assertEqual(erros, [])
        self.assertTrue(valores["copa_mundo"])
        self.assertEqual(valores["numero_figurinhas"], 670)

    def test_album_comum_mantem_o_total_digitado(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Outro", "numero_figurinhas": "120"})
        self.assertEqual(erros, [])
        self.assertFalse(valores["copa_mundo"])
        self.assertEqual(valores["numero_figurinhas"], 120)


if __name__ == "__main__":
    unittest.main()
