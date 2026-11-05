"""Aplica o esquema do catálogo no banco definido em DATABASE_URL.

Uso: python setup_db.py

As tabelas são criadas no schema da conexão (search_path). Se a tabela
`livro` já existir ali, nada é feito, então o script pode ser rodado
mais de uma vez sem apagar dados.
"""

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ESQUEMA = Path(__file__).resolve().parent / "db" / "schema.sql"
TABELA_MARCA = "livro"


def main():
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL não definida. Copie .env.example para .env e preencha.")

    with psycopg.connect(url) as conexao:
        ja_existe = conexao.execute("SELECT to_regclass(%s)", (TABELA_MARCA,)).fetchone()[0]
        if ja_existe:
            print("O esquema já existe neste banco. Nada foi alterado.")
            return

        # Tudo roda em uma transação: se algo falhar, nada fica pela metade.
        conexao.execute(ESQUEMA.read_text(encoding="utf-8"))
        print(f"Esquema aplicado a partir de {ESQUEMA.name}.")


if __name__ == "__main__":
    main()
