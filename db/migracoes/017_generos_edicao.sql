-- Gêneros editáveis pela interface (livros, gibis e vinis): o usuário de escrita pode cadastrar gênero novo
-- e ligá-lo ao item (ou desligar).
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT INSERT ON genero TO catalogo_escrita;
        GRANT USAGE ON SEQUENCE genero_id_seq TO catalogo_escrita;
        GRANT SELECT, INSERT, DELETE ON livro_genero, gibi_genero, lp_genero TO catalogo_escrita;
    END IF;
END
$$;
