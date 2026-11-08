-- Exclusão lógica dos itens: o registro fica no banco, marcado como excluido, e não aparece no site.
--
-- Pode ser reaplicada. O GRANT só roda se o papel existir.

ALTER TABLE livro ADD COLUMN IF NOT EXISTS excluido boolean NOT NULL DEFAULT false;
ALTER TABLE gibi ADD COLUMN IF NOT EXISTS excluido boolean NOT NULL DEFAULT false;
ALTER TABLE lp_vinil ADD COLUMN IF NOT EXISTS excluido boolean NOT NULL DEFAULT false;
ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS excluido boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (excluido) ON livro, gibi, lp_vinil, album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
