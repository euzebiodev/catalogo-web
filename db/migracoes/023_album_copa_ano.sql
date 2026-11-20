-- Edição da Copa do Mundo do álbum: 2022 ou 2026 (ver app/copa.py). Nulo nos álbuns comuns.
--
-- Cada edição tem a sua própria lista de figurinhas (sigla e número), então o total e as
-- seções saem do ano gravado aqui. Os álbuns marcados com copa_mundo (migração 022) passam
-- a apontar para a edição de 2022.
--
-- copa_mundo continua existindo, sincronizada pelo aplicativo, para não quebrar consultas
-- antigas.
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS copa_ano integer;

UPDATE album_figurinha SET copa_ano = 2022 WHERE copa_mundo AND copa_ano IS NULL;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (copa_ano) ON album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
