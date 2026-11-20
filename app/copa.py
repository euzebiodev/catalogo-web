"""Estrutura do álbum oficial da Copa do Mundo Qatar 2022 (Panini, 670 figurinhas).

Cada figurinha tem uma sigla e um número, como QAT1 ou FWC19. O banco guarda o número
sequencial (1 a 670) na ordem do álbum; o rótulo (sigla + número) é derivado daqui.

Ordem do álbum: 00 (logo Panini), FWC1 a FWC7 (introdução), FWC8 a FWC18 (estádios),
oito grupos de quatro seleções com 20 figurinhas cada (1 foto, 2 escudo, 3 a 20 jogadores),
e FWC19 a FWC29 (Museu FIFA). Legends e Rookies não têm número e ficam de fora.
"""

TOTAL_FIGURINHAS = 670

_GRUPOS = {
    "A": ["QAT", "ECU", "SEN", "NED"],
    "B": ["ENG", "IRN", "USA", "WAL"],
    "C": ["ARG", "KSA", "MEX", "POL"],
    "D": ["FRA", "AUS", "DEN", "TUN"],
    "E": ["ESP", "CRC", "GER", "JPN"],
    "F": ["BEL", "CAN", "MAR", "CRO"],
    "G": ["BRA", "SRB", "SUI", "CMR"],
    "H": ["POR", "GHA", "URU", "KOR"],
}


def _rotulos(prefixo, inicio, fim):
    return [f"{prefixo}{n}" for n in range(inicio, fim + 1)]


def _secoes():
    """Lista de (nome da seção, [rótulos em ordem])."""
    secoes = [
        ("Introdução", ["00"] + _rotulos("FWC", 1, 7)),
        ("Estádios", _rotulos("FWC", 8, 18)),
    ]
    for grupo, selecoes in _GRUPOS.items():
        for sigla in selecoes:
            secoes.append((f"Grupo {grupo} · {sigla}", _rotulos(sigla, 1, 20)))
    secoes.append(("Museu FIFA", _rotulos("FWC", 19, 29)))
    return secoes


def secoes_com_numeros():
    """Seções do álbum com o número sequencial (1 a 670) de cada figurinha.

    Devolve [{"nome": str, "figurinhas": [{"numero": int, "rotulo": str}, ...]}, ...].
    """
    numero = 0
    resultado = []
    for nome, rotulos in _secoes():
        figurinhas = []
        for rotulo in rotulos:
            numero += 1
            figurinhas.append({"numero": numero, "rotulo": rotulo})
        resultado.append({"nome": nome, "figurinhas": figurinhas})
    return resultado


def todos_os_rotulos():
    """Rótulos na ordem do álbum: o índice 0 corresponde ao número 1."""
    return [f["rotulo"] for secao in secoes_com_numeros() for f in secao["figurinhas"]]
