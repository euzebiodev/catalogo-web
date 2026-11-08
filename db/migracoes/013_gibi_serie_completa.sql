-- Indica se a série do gibi está completa (todos os números de 1 até o total marcados).
-- O valor é recalculado ao salvar os números e ao salvar o total da série.
--
-- Pode ser reaplicada. O GRANT só roda se o papel existir.

ALTER TABLE gibi ADD COLUMN IF NOT EXISTS serie_completa boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (serie_completa) ON gibi TO catalogo_escrita;
    END IF;
END
$$;
