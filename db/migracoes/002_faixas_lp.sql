-- Faixas dos LPs, com compositores (ligados à tabela pessoa) e link de clipe.
-- Pode ser aplicado mais de uma vez: só cria o que ainda não existe.
-- Em bancos novos, o db/schema.sql já inclui estas tabelas.

CREATE TABLE IF NOT EXISTS lp_faixa (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lp_id       bigint NOT NULL REFERENCES lp_vinil(id) ON DELETE CASCADE,
    numero      integer NOT NULL,
    titulo      text NOT NULL,
    duracao     text,
    youtube_url text,
    UNIQUE (lp_id, numero)
);

CREATE TABLE IF NOT EXISTS lp_faixa_autor (
    faixa_id  bigint NOT NULL REFERENCES lp_faixa(id) ON DELETE CASCADE,
    pessoa_id bigint NOT NULL REFERENCES pessoa(id),
    PRIMARY KEY (faixa_id, pessoa_id)
);

CREATE INDEX IF NOT EXISTS idx_lp_faixa_autor_p ON lp_faixa_autor (pessoa_id);
