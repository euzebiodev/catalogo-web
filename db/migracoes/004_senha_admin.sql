-- Senha do login de edição, guardada no banco para poder ser trocada pelo site.
--
-- Enquanto não houver linha aqui, o login usa CATALOGO_ADMIN_SENHA_HASH do ambiente.
-- Depois que a senha é trocada pelo site, a linha do banco passa a valer.
--
-- Pode ser reaplicada. O GRANT só roda se o papel catalogo_escrita existir.

CREATE TABLE IF NOT EXISTS admin_senha (
    usuario       text PRIMARY KEY,
    senha_hash    text NOT NULL,
    atualizada_em timestamptz NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT SELECT, INSERT, UPDATE ON admin_senha TO catalogo_escrita;
    END IF;
END
$$;
