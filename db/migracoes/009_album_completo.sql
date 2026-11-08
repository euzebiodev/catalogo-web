-- Indica se o álbum de figurinhas está completo.
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS completo boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (completo) ON album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
