--
-- PostgreSQL database dump
--

\restrict ffIAyBeBlt4xvO5YtVqFvybY7g0knK8pIjXMJSStWIFLIF6UiAXnljtO4bVu0t2

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
-- Name: closure_membership; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.closure_membership (
    ddate date NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL
);


ALTER TABLE ref.closure_membership OWNER TO myuser;

--
-- Name: closure_membership closure_membership_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT closure_membership_pkey PRIMARY KEY (ddate);


--
-- Name: closure_membership fk_cm_day; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);


--
-- Name: closure_membership fk_cm_span; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_span FOREIGN KEY (start_date, end_date) REFERENCES ref.closure_periods(start_date, end_date);


--
-- PostgreSQL database dump complete
--

\unrestrict ffIAyBeBlt4xvO5YtVqFvybY7g0knK8pIjXMJSStWIFLIF6UiAXnljtO4bVu0t2
