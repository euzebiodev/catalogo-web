--
-- PostgreSQL database dump
--


-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--



SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: editora; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE editora (
    id bigint NOT NULL,
    nome text NOT NULL
);


--
-- Name: editora_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE editora ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME editora_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: estante; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE estante (
    id bigint NOT NULL,
    nome text NOT NULL
);


--
-- Name: estante_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE estante ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME estante_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: genero; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE genero (
    id bigint NOT NULL,
    nome text NOT NULL
);


--
-- Name: genero_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE genero ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME genero_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: gibi; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE gibi (
    id bigint NOT NULL,
    codigo character varying(10) NOT NULL,
    titulo text NOT NULL,
    categoria text,
    paginas integer,
    editora_id bigint,
    ano_publicacao integer,
    estante_id bigint,
    conservacao text,
    aquisicao_data date,
    preco numeric(10,2),
    encadernacao text,
    clube_do_livro text,
    isbn10 character varying(10),
    isbn13 character varying(17),
    nota text,
    sinopse text,
    capa_arquivo text,
    capa_fonte text
);


--
-- Name: gibi_genero; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE gibi_genero (
    gibi_id bigint NOT NULL,
    genero_id bigint NOT NULL
);


--
-- Name: gibi_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE gibi ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME gibi_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: gibi_pessoa; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE gibi_pessoa (
    gibi_id bigint NOT NULL,
    pessoa_id bigint NOT NULL,
    papel text NOT NULL,
    CONSTRAINT gibi_pessoa_papel_check CHECK ((papel = ANY (ARRAY['autor'::text, 'roteirista'::text, 'desenhista'::text, 'colorista'::text])))
);


--
-- Name: gravadora; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE gravadora (
    id bigint NOT NULL,
    nome text NOT NULL
);


--
-- Name: gravadora_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE gravadora ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME gravadora_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: livro; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE livro (
    id bigint NOT NULL,
    codigo character varying(10) NOT NULL,
    titulo text NOT NULL,
    paginas integer,
    editora_id bigint,
    ano_publicacao integer,
    estante_id bigint,
    conservacao text,
    aquisicao_data date,
    preco numeric(10,2),
    encadernacao text,
    clube_do_livro text,
    isbn10 character varying(10),
    isbn13 character varying(17),
    lingua text,
    edicao text,
    nota text,
    capa_arquivo text,
    capa_fonte text
);


--
-- Name: livro_autor; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE livro_autor (
    livro_id bigint NOT NULL,
    pessoa_id bigint NOT NULL
);


--
-- Name: livro_genero; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE livro_genero (
    livro_id bigint NOT NULL,
    genero_id bigint NOT NULL
);


--
-- Name: livro_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE livro ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME livro_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: lp_artista; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE lp_artista (
    lp_id bigint NOT NULL,
    pessoa_id bigint NOT NULL
);


--
-- Name: lp_genero; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE lp_genero (
    lp_id bigint NOT NULL,
    genero_id bigint NOT NULL
);


--
-- Name: lp_vinil; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE lp_vinil (
    id bigint NOT NULL,
    codigo character varying(10) NOT NULL,
    titulo text NOT NULL,
    numero_musicas integer,
    gravadora_id bigint,
    ano_publicacao integer,
    estante_id bigint,
    conservacao text,
    aquisicao_data date,
    preco numeric(10,2),
    numero_catalogo text,
    notas text,
    capa_arquivo text,
    capa_fonte text
);


--
-- Name: lp_vinil_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE lp_vinil ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME lp_vinil_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: pessoa; Type: TABLE; Schema: -; Owner: -
--

CREATE TABLE pessoa (
    id bigint NOT NULL,
    nome text NOT NULL
);


--
-- Name: pessoa_id_seq; Type: SEQUENCE; Schema: -; Owner: -
--

ALTER TABLE pessoa ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME pessoa_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: editora editora_nome_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY editora
    ADD CONSTRAINT editora_nome_key UNIQUE (nome);


--
-- Name: editora editora_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY editora
    ADD CONSTRAINT editora_pkey PRIMARY KEY (id);


--
-- Name: estante estante_nome_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY estante
    ADD CONSTRAINT estante_nome_key UNIQUE (nome);


--
-- Name: estante estante_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY estante
    ADD CONSTRAINT estante_pkey PRIMARY KEY (id);


--
-- Name: genero genero_nome_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY genero
    ADD CONSTRAINT genero_nome_key UNIQUE (nome);


--
-- Name: genero genero_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY genero
    ADD CONSTRAINT genero_pkey PRIMARY KEY (id);


--
-- Name: gibi gibi_codigo_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_codigo_key UNIQUE (codigo);


--
-- Name: gibi_genero gibi_genero_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_genero
    ADD CONSTRAINT gibi_genero_pkey PRIMARY KEY (gibi_id, genero_id);


--
-- Name: gibi gibi_isbn10_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_isbn10_key UNIQUE (isbn10);


--
-- Name: gibi gibi_isbn13_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_isbn13_key UNIQUE (isbn13);


--
-- Name: gibi_pessoa gibi_pessoa_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_pessoa
    ADD CONSTRAINT gibi_pessoa_pkey PRIMARY KEY (gibi_id, pessoa_id, papel);


--
-- Name: gibi gibi_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_pkey PRIMARY KEY (id);


--
-- Name: gravadora gravadora_nome_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gravadora
    ADD CONSTRAINT gravadora_nome_key UNIQUE (nome);


--
-- Name: gravadora gravadora_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gravadora
    ADD CONSTRAINT gravadora_pkey PRIMARY KEY (id);


--
-- Name: livro_autor livro_autor_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_autor
    ADD CONSTRAINT livro_autor_pkey PRIMARY KEY (livro_id, pessoa_id);


--
-- Name: livro livro_codigo_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_codigo_key UNIQUE (codigo);


--
-- Name: livro_genero livro_genero_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_genero
    ADD CONSTRAINT livro_genero_pkey PRIMARY KEY (livro_id, genero_id);


--
-- Name: livro livro_isbn10_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_isbn10_key UNIQUE (isbn10);


--
-- Name: livro livro_isbn13_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_isbn13_key UNIQUE (isbn13);


--
-- Name: livro livro_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_pkey PRIMARY KEY (id);


--
-- Name: lp_artista lp_artista_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_artista
    ADD CONSTRAINT lp_artista_pkey PRIMARY KEY (lp_id, pessoa_id);


--
-- Name: lp_genero lp_genero_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_genero
    ADD CONSTRAINT lp_genero_pkey PRIMARY KEY (lp_id, genero_id);


--
-- Name: lp_vinil lp_vinil_codigo_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_vinil
    ADD CONSTRAINT lp_vinil_codigo_key UNIQUE (codigo);


--
-- Name: lp_vinil lp_vinil_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_vinil
    ADD CONSTRAINT lp_vinil_pkey PRIMARY KEY (id);


--
-- Name: pessoa pessoa_nome_key; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY pessoa
    ADD CONSTRAINT pessoa_nome_key UNIQUE (nome);


--
-- Name: pessoa pessoa_pkey; Type: CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY pessoa
    ADD CONSTRAINT pessoa_pkey PRIMARY KEY (id);


--
-- Name: idx_gibi_editora; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_gibi_editora ON gibi USING btree (editora_id);


--
-- Name: idx_gibi_estante; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_gibi_estante ON gibi USING btree (estante_id);


--
-- Name: idx_gibi_genero_g; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_gibi_genero_g ON gibi_genero USING btree (genero_id);


--
-- Name: idx_gibi_pessoa_p; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_gibi_pessoa_p ON gibi_pessoa USING btree (pessoa_id);


--
-- Name: idx_livro_autor_p; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_livro_autor_p ON livro_autor USING btree (pessoa_id);


--
-- Name: idx_livro_editora; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_livro_editora ON livro USING btree (editora_id);


--
-- Name: idx_livro_estante; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_livro_estante ON livro USING btree (estante_id);


--
-- Name: idx_livro_genero_g; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_livro_genero_g ON livro_genero USING btree (genero_id);


--
-- Name: idx_lp_artista_p; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_lp_artista_p ON lp_artista USING btree (pessoa_id);


--
-- Name: idx_lp_estante; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_lp_estante ON lp_vinil USING btree (estante_id);


--
-- Name: idx_lp_genero_g; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_lp_genero_g ON lp_genero USING btree (genero_id);


--
-- Name: idx_lp_gravadora; Type: INDEX; Schema: -; Owner: -
--

CREATE INDEX idx_lp_gravadora ON lp_vinil USING btree (gravadora_id);


--
-- Name: gibi gibi_editora_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_editora_id_fkey FOREIGN KEY (editora_id) REFERENCES editora(id);


--
-- Name: gibi gibi_estante_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi
    ADD CONSTRAINT gibi_estante_id_fkey FOREIGN KEY (estante_id) REFERENCES estante(id);


--
-- Name: gibi_genero gibi_genero_genero_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_genero
    ADD CONSTRAINT gibi_genero_genero_id_fkey FOREIGN KEY (genero_id) REFERENCES genero(id);


--
-- Name: gibi_genero gibi_genero_gibi_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_genero
    ADD CONSTRAINT gibi_genero_gibi_id_fkey FOREIGN KEY (gibi_id) REFERENCES gibi(id) ON DELETE CASCADE;


--
-- Name: gibi_pessoa gibi_pessoa_gibi_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_pessoa
    ADD CONSTRAINT gibi_pessoa_gibi_id_fkey FOREIGN KEY (gibi_id) REFERENCES gibi(id) ON DELETE CASCADE;


--
-- Name: gibi_pessoa gibi_pessoa_pessoa_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY gibi_pessoa
    ADD CONSTRAINT gibi_pessoa_pessoa_id_fkey FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);


--
-- Name: livro_autor livro_autor_livro_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_autor
    ADD CONSTRAINT livro_autor_livro_id_fkey FOREIGN KEY (livro_id) REFERENCES livro(id) ON DELETE CASCADE;


--
-- Name: livro_autor livro_autor_pessoa_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_autor
    ADD CONSTRAINT livro_autor_pessoa_id_fkey FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);


--
-- Name: livro livro_editora_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_editora_id_fkey FOREIGN KEY (editora_id) REFERENCES editora(id);


--
-- Name: livro livro_estante_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro
    ADD CONSTRAINT livro_estante_id_fkey FOREIGN KEY (estante_id) REFERENCES estante(id);


--
-- Name: livro_genero livro_genero_genero_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_genero
    ADD CONSTRAINT livro_genero_genero_id_fkey FOREIGN KEY (genero_id) REFERENCES genero(id);


--
-- Name: livro_genero livro_genero_livro_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY livro_genero
    ADD CONSTRAINT livro_genero_livro_id_fkey FOREIGN KEY (livro_id) REFERENCES livro(id) ON DELETE CASCADE;


--
-- Name: lp_artista lp_artista_lp_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_artista
    ADD CONSTRAINT lp_artista_lp_id_fkey FOREIGN KEY (lp_id) REFERENCES lp_vinil(id) ON DELETE CASCADE;


--
-- Name: lp_artista lp_artista_pessoa_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_artista
    ADD CONSTRAINT lp_artista_pessoa_id_fkey FOREIGN KEY (pessoa_id) REFERENCES pessoa(id);


--
-- Name: lp_genero lp_genero_genero_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_genero
    ADD CONSTRAINT lp_genero_genero_id_fkey FOREIGN KEY (genero_id) REFERENCES genero(id);


--
-- Name: lp_genero lp_genero_lp_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_genero
    ADD CONSTRAINT lp_genero_lp_id_fkey FOREIGN KEY (lp_id) REFERENCES lp_vinil(id) ON DELETE CASCADE;


--
-- Name: lp_vinil lp_vinil_estante_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_vinil
    ADD CONSTRAINT lp_vinil_estante_id_fkey FOREIGN KEY (estante_id) REFERENCES estante(id);


--
-- Name: lp_vinil lp_vinil_gravadora_id_fkey; Type: FK CONSTRAINT; Schema: -; Owner: -
--

ALTER TABLE ONLY lp_vinil
    ADD CONSTRAINT lp_vinil_gravadora_id_fkey FOREIGN KEY (gravadora_id) REFERENCES gravadora(id);


--
-- PostgreSQL database dump complete
--


