-- Exemplar autografado: campo verdadeiro/falso (Sim/Não) para todos os tipos do acervo.
--
-- O autógrafo é do exemplar, não do título, por isso a coluna fica em cada tabela de
-- item: livro, gibi, lp_vinil e album_figurinha. O padrão é falso, então os itens que
-- já existem continuam "Não" até serem marcados na edição.
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

ALTER TABLE livro           ADD COLUMN IF NOT EXISTS autografado boolean NOT NULL DEFAULT false;
ALTER TABLE gibi            ADD COLUMN IF NOT EXISTS autografado boolean NOT NULL DEFAULT false;
ALTER TABLE lp_vinil        ADD COLUMN IF NOT EXISTS autografado boolean NOT NULL DEFAULT false;
ALTER TABLE album_figurinha ADD COLUMN IF NOT EXISTS autografado boolean NOT NULL DEFAULT false;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (autografado) ON livro, gibi, lp_vinil, album_figurinha TO catalogo_escrita;
    END IF;
END
$$;
