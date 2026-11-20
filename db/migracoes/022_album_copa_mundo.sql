-- Álbum de Copa do Mundo: indica que as figurinhas são identificadas por sigla e número
-- (ex.: QAT1, FWC19), no padrão da Panini, e não por número sequencial.
--
-- O padrão é falso, então os álbuns que já existem continuam com a grade numérica.
-- A lista de figurinhas do álbum de Copa fica no código (app/copa.py).
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS copa_mundo boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (copa_mundo) ON album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
