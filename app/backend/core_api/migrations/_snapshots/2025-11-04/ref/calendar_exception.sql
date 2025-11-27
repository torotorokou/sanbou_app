--
-- PostgreSQL database dump
--

\restrict OhG3DufT5aKz2TvbLnhypWHfMqPYF9a9Ucb1QVdB4sP14HZNQlmsCp2XcaeewJH

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
-- Name: calendar_exception; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.calendar_exception (
    ddate date NOT NULL,
    override_type text NOT NULL,
    reason text,
    updated_by text,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT calendar_exception_override_type_check CHECK ((override_type = ANY (ARRAY['FORCE_CLOSED'::text, 'FORCE_OPEN'::text, 'FORCE_RESERVATION'::text])))
);


ALTER TABLE ref.calendar_exception OWNER TO myuser;

--
-- Name: calendar_exception calendar_exception_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT calendar_exception_pkey PRIMARY KEY (ddate);


--
-- Name: calendar_exception fk_cal_exception_day; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT fk_cal_exception_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);


--
-- PostgreSQL database dump complete
--

\unrestrict OhG3DufT5aKz2TvbLnhypWHfMqPYF9a9Ucb1QVdB4sP14HZNQlmsCp2XcaeewJH

