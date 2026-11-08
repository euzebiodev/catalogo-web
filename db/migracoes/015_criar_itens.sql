-- Cadastro de item novo pela tela "Novo item": o usuário de escrita pode inserir livros, gibis, vinis e álbuns.
--
-- Pode ser reaplicada. Os GRANTs só rodam se o papel existir.
-- Sem esta migração, o cadastro novo falha no servidor com "permission denied".

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT INSERT ON livro, gibi, lp_vinil, album_figurinha TO catalogo_escrita;
        GRANT USAGE ON SEQUENCE livro_id_seq, gibi_id_seq, lp_vinil_id_seq, album_figurinha_id_seq
            TO catalogo_escrita;
    END IF;
END
$$;
