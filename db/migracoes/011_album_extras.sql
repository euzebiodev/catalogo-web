-- Conteúdo extra dos álbuns (cards e similares): se tem, descrição, quantos itens e quais estão marcados.
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS tem_extra boolean NOT NULL DEFAULT false;
ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS extra_descricao text;
ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS extra_total integer;

CREATE TABLE IF NOT EXISTS album_extra_marcado (
    album_id bigint  NOT NULL REFERENCES album_figurinha(id) ON DELETE CASCADE,
    numero   integer NOT NULL,
    PRIMARY KEY (album_id, numero)
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_leitura') THEN
        GRANT SELECT ON album_extra_marcado TO catalogo_leitura;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (tem_extra, extra_descricao, extra_total) ON album_figurinha TO catalogo_escrita;
        GRANT SELECT, INSERT, DELETE ON album_extra_marcado TO catalogo_escrita;
    END IF;
END
$$;
