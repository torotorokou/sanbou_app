--
-- PostgreSQL database dump
--

\restrict uNyMI7eiZEBPMgRJcQK3QE2Yxx1YrKhFjf89UPhnsYjtd6efrnbDwu1YfbtAkGW

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
-- Name: daily_target_plan; Type: TABLE; Schema: mart; Owner: myuser
--

CREATE TABLE mart.daily_target_plan (
    ddate timestamp without time zone,
    target_ton double precision,
    scope_used text,
    created_at timestamp without time zone
);


ALTER TABLE mart.daily_target_plan OWNER TO myuser;

--
-- PostgreSQL database dump complete
--

\unrestrict uNyMI7eiZEBPMgRJcQK3QE2Yxx1YrKhFjf89UPhnsYjtd6efrnbDwu1YfbtAkGW

