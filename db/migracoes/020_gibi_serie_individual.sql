-- Cada número de uma série passa a ser um gibi próprio.
--
-- O formulário do gibi ganha Série (caixa de marcar), Nome da série e Número da série.
-- Os números que estavam marcados em uma série fechada viram registros individuais, com
-- a capa e o ISBN de cada número; a equipe e os gêneros do registro antigo são copiados.
-- O primeiro número aproveita o registro que existia, então o código, o QR code e o
-- endereço da página continuam os mesmos. Os demais recebem códigos novos na mesma letra
-- (M0001 -> M0002, M0003...), seguindo a numeração que já existe.
--
-- Saem do sistema a tabela gibi_serie_item e as colunas serie_fechada, serie_total e
-- serie_completa: o controle de números, capas e ISBN por número não existe mais.
-- As capas continuam nos mesmos arquivos (gibi/serie/<codigo>-<numero>.<ext>).
--
-- Pode ser reaplicada: as colunas novas usam IF NOT EXISTS e a conversão só roda enquanto
-- a tabela antiga existir.

ALTER TABLE gibi ADD COLUMN IF NOT EXISTS serie boolean NOT NULL DEFAULT false;
ALTER TABLE gibi ADD COLUMN IF NOT EXISTS nome_serie text;
ALTER TABLE gibi ADD COLUMN IF NOT EXISTS numero_serie integer;

DO $$
DECLARE
    base record;
    numero record;
    codigo_novo text;
    letra text;
    sequencia integer;
    convertido boolean;
    novo_id bigint;
BEGIN
    IF to_regclass('gibi_serie_item') IS NULL THEN
        RETURN;
    END IF;

    FOR base IN
        SELECT g.*
          FROM gibi g
         WHERE g.serie_fechada
           AND EXISTS (SELECT 1 FROM gibi_serie_item s
                        WHERE s.gibi_id = g.id AND s.marcado)
         ORDER BY g.codigo
    LOOP
        -- Próximo número livre na mesma letra do código (M0001 -> sequência 1).
        letra := COALESCE(substring(base.codigo from '^[A-Z]'), 'M');
        SELECT COALESCE(max(substring(g.codigo from 2)::integer), 0) INTO sequencia
          FROM gibi g
         WHERE g.codigo ~ ('^' || letra || '[0-9]+$');

        convertido := false;
        FOR numero IN
            SELECT s.numero, s.capa_arquivo, s.isbn10, s.isbn13
              FROM gibi_serie_item s
             WHERE s.gibi_id = base.id AND s.marcado
             ORDER BY s.numero
        LOOP
            IF NOT convertido THEN
                -- Primeiro número: o registro antigo deixa de ser a série e passa a ser este item.
                UPDATE gibi
                   SET serie = true,
                       nome_serie = base.titulo,
                       numero_serie = numero.numero,
                       capa_arquivo = COALESCE(numero.capa_arquivo, capa_arquivo),
                       isbn10 = COALESCE(numero.isbn10, isbn10),
                       isbn13 = COALESCE(numero.isbn13, isbn13)
                 WHERE id = base.id;
                convertido := true;
            ELSE
                LOOP
                    sequencia := sequencia + 1;
                    codigo_novo := letra || lpad(sequencia::text, length(base.codigo) - 1, '0');
                    EXIT WHEN NOT EXISTS (SELECT 1 FROM gibi WHERE codigo = codigo_novo);
                END LOOP;

                INSERT INTO gibi (codigo, titulo, categoria, editora_id, estante_id, encadernacao,
                                  clube_do_livro, conservacao, isbn10, isbn13, capa_arquivo, capa_fonte,
                                  serie, nome_serie, numero_serie)
                VALUES (codigo_novo, base.titulo, base.categoria, base.editora_id, base.estante_id,
                        base.encadernacao, base.clube_do_livro, base.conservacao,
                        numero.isbn10, numero.isbn13, numero.capa_arquivo, base.capa_fonte,
                        true, base.titulo, numero.numero)
                RETURNING id INTO novo_id;

                -- Gêneros e equipe valem para a série inteira.
                INSERT INTO gibi_genero (gibi_id, genero_id)
                    SELECT novo_id, genero_id FROM gibi_genero WHERE gibi_id = base.id;
                INSERT INTO gibi_pessoa (gibi_id, pessoa_id, papel)
                    SELECT novo_id, pessoa_id, papel FROM gibi_pessoa WHERE gibi_id = base.id;
            END IF;
        END LOOP;
    END LOOP;

    -- Série fechada que ficou sem número marcado continua marcada como série, com o nome
    -- do título (ou o número da edição, quando era o único número anotado).
    UPDATE gibi
       SET serie = true,
           nome_serie = COALESCE(nome_serie, titulo),
           numero_serie = COALESCE(numero_serie, numero_edicao)
     WHERE serie_fechada;
END
$$;

DROP TABLE IF EXISTS gibi_serie_item;
ALTER TABLE gibi DROP COLUMN IF EXISTS serie_fechada;
ALTER TABLE gibi DROP COLUMN IF EXISTS serie_total;
ALTER TABLE gibi DROP COLUMN IF EXISTS serie_completa;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'catalogo_escrita') THEN
        GRANT UPDATE (serie, nome_serie, numero_serie) ON gibi TO catalogo_escrita;
    END IF;
END
$$;
