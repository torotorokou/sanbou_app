--
-- PostgreSQL database dump
--

\restrict 7YrZS1XZCNGalFbiFSJ5qqAiA1jMMRDoCR6aopThaO9M3fbmCNM0Dsod58WYbSV

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
-- Name: closure_periods; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.closure_periods (
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL,
    CONSTRAINT closure_periods_check CHECK ((start_date <= end_date))
);


ALTER TABLE ref.closure_periods OWNER TO myuser;

--
-- Name: closure_periods closure_periods_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_periods
    ADD CONSTRAINT closure_periods_pkey PRIMARY KEY (start_date, end_date);


--
-- PostgreSQL database dump complete
--

\unrestrict 7YrZS1XZCNGalFbiFSJ5qqAiA1jMMRDoCR6aopThaO9M3fbmCNM0Dsod58WYbSV
