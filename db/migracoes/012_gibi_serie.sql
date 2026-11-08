-- Número da edição/volume dos gibis e controle da série fechada (números marcados e capa de cada número).
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

ALTER TABLE gibi ADD COLUMN IF NOT EXISTS numero_edicao integer;
ALTER TABLE gibi ADD COLUMN IF NOT EXISTS serie_fechada boolean NOT NULL DEFAULT false;
ALTER TABLE gibi ADD COLUMN IF NOT EXISTS serie_total integer;

CREATE TABLE IF NOT EXISTS gibi_serie_item (
    gibi_id      bigint  NOT NULL REFERENCES gibi(id) ON DELETE CASCADE,
    numero       integer NOT NULL,
    marcado      boolean NOT NULL DEFAULT false,
    capa_arquivo text,
    PRIMARY KEY (gibi_id, numero)
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_leitura') THEN
        GRANT SELECT ON gibi_serie_item TO catalogo_leitura;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (numero_edicao, serie_fechada, serie_total) ON gibi TO catalogo_escrita;
        GRANT SELECT, INSERT, UPDATE, DELETE ON gibi_serie_item TO catalogo_escrita;
    END IF;
END
$$;
