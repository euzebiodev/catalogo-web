-- Permite ao usuário de escrita trocar a capa pela edição (campo capa_arquivo).
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (capa_arquivo) ON livro, gibi, lp_vinil TO catalogo_escrita;
    END IF;
END
$$;
