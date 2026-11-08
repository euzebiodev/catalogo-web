-- Sinopse dos livros (os gibis já têm a coluna sinopse).
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

ALTER TABLE livro ADD COLUMN IF NOT EXISTS sinopse text;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (sinopse) ON livro TO catalogo_escrita;
    END IF;
END
$$;
