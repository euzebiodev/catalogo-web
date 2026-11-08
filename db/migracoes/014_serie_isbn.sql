-- ISBN-10 e ISBN-13 de cada número da série do gibi.
--
-- Pode ser reaplicada.

ALTER TABLE gibi_serie_item ADD COLUMN IF NOT EXISTS isbn10 text;
ALTER TABLE gibi_serie_item ADD COLUMN IF NOT EXISTS isbn13 text;
