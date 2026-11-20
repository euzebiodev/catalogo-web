"""Estruturas dos álbuns oficiais de Copa do Mundo da Panini.

Cada figurinha tem uma sigla e um número, como QAT1 ou FWC19. O banco guarda o número
sequencial (1 até o total da edição) na ordem do álbum; o rótulo (sigla + número) é
derivado daqui.

Edições:
- 2022 (Catar, 670 figurinhas): 00 (logo Panini), FWC1 a FWC7 (introdução), FWC8 a FWC18
  (estádios), oito grupos de quatro seleções com 20 figurinhas cada e FWC19 a FWC29
  (Museu FIFA). Legends e Rookies não têm número e ficam de fora.
- 2026 (EUA, Canadá e México, 994 figurinhas): 00 (logo Panini) e FWC1 a FWC8 (página
  inicial), doze grupos de quatro seleções com 20 figurinhas cada, FWC9 a FWC19
  (FIFA World Cup History) e CC1 a CC14 (figurinhas da Coca-Cola). A numeração FWC é
  contínua: a página inicial termina em FWC8 e o histórico começa em FWC9.

Os dados da edição 2026 vêm da planilha de controle do álbum (994 figurinhas, 48 seleções).
"""

from typing import NamedTuple


class Edicao(NamedTuple):
    """Uma edição do álbum: ano, nome e as seções na ordem do álbum."""

    ano: int
    nome: str
    secoes: tuple  # ((nome da seção, (rótulos em ordem)), ...)

    @property
    def total(self):
        return sum(len(rotulos) for _, rotulos in self.secoes)


def _rotulos(prefixo, inicio, fim):
    return tuple(f"{prefixo}{n}" for n in range(inicio, fim + 1))


# Grupo -> seleções (sigla de três letras, como impressa na figurinha).
GRUPOS_2022 = {
    "A": ("QAT", "ECU", "SEN", "NED"),
    "B": ("ENG", "IRN", "USA", "WAL"),
    "C": ("ARG", "KSA", "MEX", "POL"),
    "D": ("FRA", "AUS", "DEN", "TUN"),
    "E": ("ESP", "CRC", "GER", "JPN"),
    "F": ("BEL", "CAN", "MAR", "CRO"),
    "G": ("BRA", "SRB", "SUI", "CMR"),
    "H": ("POR", "GHA", "URU", "KOR"),
}

# Grupo -> (sigla, nome do país). Os nomes aparecem no título de cada seção.
GRUPOS_2026 = {
    "A": (
        ("MEX", "México"),
        ("RSA", "África do Sul"),
        ("KOR", "Coreia do Sul"),
        ("CZE", "Rep. Tcheca"),
    ),
    "B": (
        ("CAN", "Canadá"),
        ("BIH", "Bósnia"),
        ("QAT", "Catar"),
        ("SUI", "Suíça"),
    ),
    "C": (
        ("BRA", "Brasil"),
        ("MAR", "Marrocos"),
        ("HAI", "Haiti"),
        ("SCO", "Escócia"),
    ),
    "D": (
        ("USA", "Estados Unidos"),
        ("PAR", "Paraguai"),
        ("AUS", "Austrália"),
        ("TUR", "Turquia"),
    ),
    "E": (
        ("GER", "Alemanha"),
        ("CUW", "Curaçao"),
        ("CIV", "Costa do Marfim"),
        ("ECU", "Equador"),
    ),
    "F": (
        ("NED", "Holanda"),
        ("JPN", "Japão"),
        ("SWE", "Suécia"),
        ("TUN", "Tunísia"),
    ),
    "G": (
        ("BEL", "Bélgica"),
        ("EGY", "Egito"),
        ("IRN", "Irã"),
        ("NZL", "Nova Zelândia"),
    ),
    "H": (
        ("ESP", "Espanha"),
        ("CPV", "Cabo Verde"),
        ("KSA", "Arábia Saudita"),
        ("URU", "Uruguai"),
    ),
    "I": (
        ("FRA", "França"),
        ("SEN", "Senegal"),
        ("IRQ", "Iraque"),
        ("NOR", "Noruega"),
    ),
    "J": (
        ("ARG", "Argentina"),
        ("ALG", "Argélia"),
        ("AUT", "Áustria"),
        ("JOR", "Jordânia"),
    ),
    "K": (
        ("POR", "Portugal"),
        ("COD", "Congo"),
        ("UZB", "Uzbequistão"),
        ("COL", "Colômbia"),
    ),
    "L": (
        ("ENG", "Inglaterra"),
        ("CRO", "Croácia"),
        ("GHA", "Gana"),
        ("PAN", "Panamá"),
    ),
}


def _secoes_2022():
    """Seções do álbum de 2022, na ordem: (nome da seção, rótulos)."""
    secoes = [
        ("Introdução", ("00",) + _rotulos("FWC", 1, 7)),
        ("Estádios", _rotulos("FWC", 8, 18)),
    ]
    for grupo, selecoes in GRUPOS_2022.items():
        for sigla in selecoes:
            secoes.append((f"Grupo {grupo} · {sigla}", _rotulos(sigla, 1, 20)))
    secoes.append(("Museu FIFA", _rotulos("FWC", 19, 29)))
    return tuple(secoes)


def _secoes_2026():
    """Seções do álbum de 2026, na ordem: (nome da seção, rótulos)."""
    # A planilha de controle lista nove figurinhas na página inicial: o logo (00, o mesmo
    # padrão do álbum de 2022) e FWC1 a FWC8. Por isso o histórico começa em FWC9.
    secoes = [("Página inicial", ("00",) + _rotulos("FWC", 1, 8))]
    for grupo, selecoes in GRUPOS_2026.items():
        for sigla, nome in selecoes:
            secoes.append((f"Grupo {grupo} · {nome}", _rotulos(sigla, 1, 20)))
    secoes.append(("FIFA World Cup History", _rotulos("FWC", 9, 19)))
    secoes.append(("Figurinhas da Coca-Cola", _rotulos("CC", 1, 14)))
    return tuple(secoes)


EDICOES = {
    2022: Edicao(2022, "Catar 2022", _secoes_2022()),
    2026: Edicao(2026, "EUA, Canadá e México 2026", _secoes_2026()),
}

# Anos que podem ser informados no formulário do álbum.
ANOS = tuple(sorted(EDICOES))


def ano_valido(ano):
    """True se o ano é de uma edição conhecida do álbum de Copa."""
    return ano in EDICOES


def total(ano):
    """Total de figurinhas da edição. Zero se o ano não for de uma edição conhecida."""
    edicao = EDICOES.get(ano)
    return edicao.total if edicao else 0


def secoes_com_numeros(ano):
    """Seções do álbum com o número sequencial (1 até o total) de cada figurinha.

    Devolve [{"nome": str, "figurinhas": [{"numero": int, "rotulo": str}, ...]}, ...].
    Lista vazia se o ano não for de uma edição conhecida.
    """
    edicao = EDICOES.get(ano)
    if edicao is None:
        return []
    numero = 0
    resultado = []
    for nome, rotulos in edicao.secoes:
        figurinhas = []
        for rotulo in rotulos:
            numero += 1
            figurinhas.append({"numero": numero, "rotulo": rotulo})
        resultado.append({"nome": nome, "figurinhas": figurinhas})
    return resultado


def todos_os_rotulos(ano):
    """Rótulos na ordem do álbum: o índice 0 corresponde ao número 1."""
    return [f["rotulo"] for secao in secoes_com_numeros(ano) for f in secao["figurinhas"]]
