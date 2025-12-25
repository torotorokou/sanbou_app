--
-- PostgreSQL database dump
--

\restrict ZZpEdgMzA1O71hGL7QJBgZwxpndNZxnaq5uaXvSht5BpmeEi6rRAR2Aah05EU7B

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: calendar_month; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.calendar_month (
    month_date date NOT NULL
);


ALTER TABLE ref.calendar_month OWNER TO myuser;

--
-- Name: calendar_month calendar_month_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_month
    ADD CONSTRAINT calendar_month_pkey PRIMARY KEY (month_date);


--
-- PostgreSQL database dump complete
--

\unrestrict ZZpEdgMzA1O71hGL7QJBgZwxpndNZxnaq5uaXvSht5BpmeEi6rRAR2Aah05EU7B
