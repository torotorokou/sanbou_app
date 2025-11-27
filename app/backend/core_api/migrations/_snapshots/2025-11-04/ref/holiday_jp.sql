--
-- PostgreSQL database dump
--

\restrict udYCbkZpwfbSpbYNPoNkdtTmYP7oJ5ilp1kUKadarJff1ivqa9Qf2AZGceS7Ft3

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
-- Name: holiday_jp; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.holiday_jp (
    hdate date NOT NULL,
    name text NOT NULL
);


ALTER TABLE ref.holiday_jp OWNER TO myuser;

--
-- Name: holiday_jp holiday_jp_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT holiday_jp_pkey PRIMARY KEY (hdate);


--
-- Name: holiday_jp fk_holiday_day; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT fk_holiday_day FOREIGN KEY (hdate) REFERENCES ref.calendar_day(ddate);


--
-- PostgreSQL database dump complete
--

\unrestrict udYCbkZpwfbSpbYNPoNkdtTmYP7oJ5ilp1kUKadarJff1ivqa9Qf2AZGceS7Ft3

