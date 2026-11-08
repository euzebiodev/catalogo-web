-- Permissões do usuário de escrita usado pela edição manual.
--
-- Pré-requisito (feito uma vez, como superusuário, com senha forte):
--   CREATE ROLE catalogo_escrita LOGIN PASSWORD '...';
-- A senha vai só para DATABASE_URL_ESCRITA no arquivo de configuração do servidor.
--
-- O usuário recebe escrita só nas colunas que a edição altera (ver app/edicao.py).
-- Não tem permissão para apagar nem para criar tabelas.

GRANT SELECT ON ALL TABLES IN SCHEMA public TO catalogo_escrita;

GRANT UPDATE (titulo, editora_id, estante_id, paginas, ano_publicacao, lingua, edicao,
              encadernacao, isbn10, isbn13, clube_do_livro, conservacao, aquisicao_data,
              preco, capa_fonte, nota)
    ON livro TO catalogo_escrita;

GRANT UPDATE (titulo, categoria, editora_id, estante_id, paginas, ano_publicacao,
              encadernacao, isbn10, isbn13, clube_do_livro, conservacao, aquisicao_data,
              preco, capa_fonte, sinopse, nota)
    ON gibi TO catalogo_escrita;

GRANT UPDATE (titulo, gravadora_id, estante_id, numero_musicas, ano_publicacao,
              numero_catalogo, conservacao, aquisicao_data, preco, capa_fonte, notas)
    ON lp_vinil TO catalogo_escrita;

-- Editora, estante e gravadora são cadastradas quando o nome digitado não existe.
GRANT INSERT ON editora, estante, gravadora TO catalogo_escrita;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO catalogo_escrita;
