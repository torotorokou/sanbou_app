--
-- PostgreSQL database dump
--

\restrict kr8YJGS5dWl5xkybRfEE7jcP6Kq5ZfLx6vRn3HfeBrCMgjTF0wVJz4raNRoKgKr

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
-- Name: calendar_day; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.calendar_day (
    ddate date NOT NULL,
    y integer GENERATED ALWAYS AS ((EXTRACT(year FROM ddate))::integer) STORED,
    m integer GENERATED ALWAYS AS ((EXTRACT(month FROM ddate))::integer) STORED,
    iso_year integer GENERATED ALWAYS AS ((EXTRACT(isoyear FROM ddate))::integer) STORED,
    iso_week integer GENERATED ALWAYS AS ((EXTRACT(week FROM ddate))::integer) STORED,
    iso_dow integer GENERATED ALWAYS AS ((EXTRACT(isodow FROM ddate))::integer) STORED
);


ALTER TABLE ref.calendar_day OWNER TO myuser;

--
-- Name: calendar_day calendar_day_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_day
    ADD CONSTRAINT calendar_day_pkey PRIMARY KEY (ddate);


--
-- Name: ix_calendar_day_date; Type: INDEX; Schema: ref; Owner: myuser
--

CREATE INDEX ix_calendar_day_date ON ref.calendar_day USING btree (ddate);


--
-- Name: ix_calendar_day_ym; Type: INDEX; Schema: ref; Owner: myuser
--

CREATE INDEX ix_calendar_day_ym ON ref.calendar_day USING btree (y, m);


--
-- PostgreSQL database dump complete
--

\unrestrict kr8YJGS5dWl5xkybRfEE7jcP6Kq5ZfLx6vRn3HfeBrCMgjTF0wVJz4raNRoKgKr

