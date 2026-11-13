-- Conteúdo extra dos livros (pôster, marcadores, agendas, minilivros e similares).
--
-- tem_conteudo_extra é o marcador verdadeiro/falso do livro: "Sim" quando a edição
-- veio com algum item extra, mesmo que ele ainda não tenha sido cadastrado.
-- Cada item cadastrado fica em livro_extra, com nome, descrição e (opcional) foto.
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

ALTER TABLE livro ADD COLUMN IF NOT EXISTS tem_conteudo_extra boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS livro_extra (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    livro_id     bigint  NOT NULL REFERENCES livro(id) ON DELETE CASCADE,
    nome         text    NOT NULL,
    descricao    text,
    foto_arquivo text,
    ordem        integer NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_livro_extra_livro ON livro_extra USING btree (livro_id);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_leitura') THEN
        GRANT SELECT ON livro_extra TO catalogo_leitura;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (tem_conteudo_extra) ON livro TO catalogo_escrita;
        GRANT SELECT, INSERT, UPDATE, DELETE ON livro_extra TO catalogo_escrita;
        GRANT USAGE ON SEQUENCE livro_extra_id_seq TO catalogo_escrita;
    END IF;
END
$$;
