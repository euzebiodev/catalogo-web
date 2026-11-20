"""Estruturas dos álbuns de Copa do Mundo (2022 e 2026) e regra de total no formulário.

Não usam banco: rodam só com a estrutura em app/copa.py.
"""

import unittest

from app import copa, edicao


class EstruturaAlbumCopa2022(unittest.TestCase):
    def setUp(self):
        self.secoes = copa.secoes_com_numeros(2022)
        self.figurinhas = [f for s in self.secoes for f in s["figurinhas"]]

    def test_total_e_670(self):
        self.assertEqual(len(self.figurinhas), copa.total(2022))
        self.assertEqual(copa.total(2022), 670)

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
        rotulos = {f["rotulo"] for f in self.figurinhas}
        for grupo in copa.GRUPOS_2022.values():
            for sigla in grupo:
                for n in range(1, 21):
                    self.assertIn(f"{sigla}{n}", rotulos)

    def test_trinta_e_duas_selecoes(self):
        self.assertEqual(sum(len(g) for g in copa.GRUPOS_2022.values()), 32)

    def test_todos_os_rotulos_bate_com_as_secoes(self):
        self.assertEqual(copa.todos_os_rotulos(2022), [f["rotulo"] for f in self.figurinhas])


class EstruturaAlbumCopa2026(unittest.TestCase):
    def setUp(self):
        self.secoes = copa.secoes_com_numeros(2026)
        self.figurinhas = [f for s in self.secoes for f in s["figurinhas"]]
        self.por_rotulo = {f["rotulo"]: f["numero"] for f in self.figurinhas}

    def test_total_e_994(self):
        self.assertEqual(copa.total(2026), 994)
        self.assertEqual(len(self.figurinhas), 994)

    def test_numeros_sao_sequenciais_de_1_a_994(self):
        self.assertEqual([f["numero"] for f in self.figurinhas], list(range(1, 995)))

    def test_rotulos_sao_unicos(self):
        rotulos = [f["rotulo"] for f in self.figurinhas]
        self.assertEqual(len(rotulos), len(set(rotulos)))
        self.assertEqual(rotulos, copa.todos_os_rotulos(2026))

    def test_primeira_e_ultima_figurinha(self):
        self.assertEqual(self.figurinhas[0]["rotulo"], "00")
        self.assertEqual(self.figurinhas[-1]["rotulo"], "CC14")

    def test_numeracao_fwc_e_continua(self):
        # Página inicial: 00 e FWC1 a FWC8 (9 figurinhas). Histórico: FWC9 a FWC19.
        self.assertEqual(self.por_rotulo["00"], 1)
        self.assertEqual(self.por_rotulo["FWC8"], 9)
        self.assertEqual(self.por_rotulo["FWC9"], 970)
        self.assertEqual(self.por_rotulo["FWC19"], 980)

    def test_posicoes_das_selecoes_e_da_coca_cola(self):
        # 48 seleções de 20 figurinhas vêm depois da página inicial.
        self.assertEqual(self.por_rotulo["MEX1"], 10)
        self.assertEqual(self.por_rotulo["MEX20"], 29)
        self.assertEqual(self.por_rotulo["PAN20"], 969)
        self.assertEqual(self.por_rotulo["CC1"], 981)
        self.assertEqual(self.por_rotulo["CC14"], 994)

    def test_quarenta_e_oito_selecoes_com_20_figurinhas(self):
        self.assertEqual(sum(len(g) for g in copa.GRUPOS_2026.values()), 48)
        for grupo in copa.GRUPOS_2026.values():
            for sigla, _nome in grupo:
                self.assertIn(f"{sigla}1", self.por_rotulo)
                self.assertIn(f"{sigla}20", self.por_rotulo)
                self.assertNotIn(f"{sigla}21", self.por_rotulo)

    def test_doze_grupos_de_quatro_selecoes(self):
        self.assertEqual(len(copa.GRUPOS_2026), 12)
        for selecoes in copa.GRUPOS_2026.values():
            self.assertEqual(len(selecoes), 4)

    def test_secoes_especiais(self):
        nomes = [s["nome"] for s in self.secoes]
        self.assertEqual(nomes[0], "Página inicial")
        self.assertIn("FIFA World Cup History", nomes)
        self.assertIn("Figurinhas da Coca-Cola", nomes)
        # 12 grupos com 4 seleções cada + 3 seções especiais.
        self.assertEqual(len(nomes), 12 * 4 + 3)
        for nome in ("Página inicial", "FIFA World Cup History", "Figurinhas da Coca-Cola"):
            secao = next(s for s in self.secoes if s["nome"] == nome)
            self.assertGreater(len(secao["figurinhas"]), 0)


class EdicoesConhecidas(unittest.TestCase):
    def test_anos(self):
        self.assertEqual(copa.ANOS, (2022, 2026))
        self.assertTrue(copa.ano_valido(2022))
        self.assertTrue(copa.ano_valido(2026))

    def test_ano_desconhecido_nao_tem_estrutura(self):
        self.assertFalse(copa.ano_valido(2030))
        self.assertEqual(copa.total(2030), 0)
        self.assertEqual(copa.secoes_com_numeros(2030), [])
        self.assertEqual(copa.todos_os_rotulos(2030), [])


class TotalDoAlbum(unittest.TestCase):
    def test_usa_a_edicao_quando_ha_ano(self):
        self.assertEqual(edicao.total_do_album({"copa_ano": 2026, "total": 0}), 994)
        self.assertEqual(edicao.total_do_album({"copa_ano": 2022, "total": 12}), 670)

    def test_usa_o_total_informado_nos_demais_albuns(self):
        self.assertEqual(edicao.total_do_album({"copa_ano": None, "total": 80}), 80)
        self.assertEqual(edicao.total_do_album({"copa_ano": None, "total": 0}), 0)


class RegraDeTotalNoFormulario(unittest.TestCase):
    def test_album_de_copa_2022_forca_670(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Copa 2022", "copa_ano": "2022"})
        self.assertEqual(erros, [])
        self.assertEqual(valores["copa_ano"], 2022)
        self.assertEqual(valores["numero_figurinhas"], 670)

    def test_album_de_copa_2026_forca_994(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Copa 2026", "copa_ano": "2026"})
        self.assertEqual(erros, [])
        self.assertEqual(valores["copa_ano"], 2026)
        self.assertEqual(valores["numero_figurinhas"], 994)

    def test_edicao_desconhecida_da_erro(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Copa", "copa_ano": "2018"})
        self.assertIsNone(valores["numero_figurinhas"])
        self.assertTrue(any("Ano da Copa do Mundo" in erro for erro in erros))

    def test_album_comum_mantem_o_total_digitado(self):
        valores, erros = edicao.ler_formulario("album", {"titulo": "Outro", "numero_figurinhas": "120"})
        self.assertEqual(erros, [])
        self.assertIsNone(valores["copa_ano"])
        self.assertEqual(valores["numero_figurinhas"], 120)


if __name__ == "__main__":
    unittest.main()
