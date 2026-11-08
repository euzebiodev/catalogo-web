-- Figurinhas marcadas em cada álbum (uma linha por figurinha que o álbum tem).
-- O campo completo do álbum é recalculado a cada gravação: sim quando todas as
-- figurinhas de 1 até numero_figurinhas estão marcadas.
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

CREATE TABLE IF NOT EXISTS album_figurinha_marcada (
    album_id bigint  NOT NULL REFERENCES album_figurinha(id) ON DELETE CASCADE,
    numero   integer NOT NULL,
    PRIMARY KEY (album_id, numero)
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_leitura') THEN
        GRANT SELECT ON album_figurinha_marcada TO catalogo_leitura;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT SELECT, INSERT, DELETE ON album_figurinha_marcada TO catalogo_escrita;
    END IF;
END
$$;
