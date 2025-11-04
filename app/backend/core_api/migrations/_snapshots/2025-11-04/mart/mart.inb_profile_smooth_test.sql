--
-- PostgreSQL database dump
--

\restrict zO0pogDTEOpG0oI9PnYt40PyQmdpTe8hAX9DnTCFGVsPHX1pgUw1MfLNkRDAVfH

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
-- Name: inb_profile_smooth_test; Type: TABLE; Schema: mart; Owner: myuser
--

CREATE TABLE mart.inb_profile_smooth_test (
    scope text NOT NULL,
    iso_week integer NOT NULL,
    iso_dow integer NOT NULL,
    day_mean_smooth numeric(14,4) NOT NULL,
    method text NOT NULL,
    params jsonb NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE mart.inb_profile_smooth_test OWNER TO myuser;

--
-- Name: inb_profile_smooth_test inb_profile_smooth_test_pkey; Type: CONSTRAINT; Schema: mart; Owner: myuser
--

ALTER TABLE ONLY mart.inb_profile_smooth_test
    ADD CONSTRAINT inb_profile_smooth_test_pkey PRIMARY KEY (scope, iso_week, iso_dow);


--
-- PostgreSQL database dump complete
--

\unrestrict zO0pogDTEOpG0oI9PnYt40PyQmdpTe8hAX9DnTCFGVsPHX1pgUw1MfLNkRDAVfH

