-- Permite ao usuário de escrita editar os autores dos livros (tabelas pessoa e livro_autor).
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT INSERT ON pessoa TO catalogo_escrita;
        GRANT SELECT, INSERT, DELETE ON livro_autor TO catalogo_escrita;
    END IF;
END
$$;
