-- Aba de álbuns de figurinhas: tabela própria, parecida com lp_vinil.
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

CREATE TABLE IF NOT EXISTS album_figurinha (
    id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo            text NOT NULL UNIQUE,
    titulo            text NOT NULL,
    editora_id        bigint REFERENCES editora(id),
    estante_id        bigint REFERENCES estante(id),
    numero_figurinhas integer,
    ano_publicacao    integer,
    conservacao       text,
    aquisicao_data    date,
    preco             numeric(10, 2),
    capa_arquivo      text,
    capa_fonte        text,
    notas             text
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_leitura') THEN
        GRANT SELECT ON album_figurinha TO catalogo_leitura;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT SELECT ON album_figurinha TO catalogo_escrita;
        GRANT UPDATE (titulo, editora_id, estante_id, numero_figurinhas, ano_publicacao,
                      conservacao, aquisicao_data, preco, capa_arquivo, capa_fonte, notas)
            ON album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
