--
-- PostgreSQL database dump
--

\restrict UmtFt0AtLcandBKoAbTgceoNAipvjhO9Xo4nZOVNNo4lSVdPfSPyhKeF3x29oWz

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

--
-- Name: v_daily_target_with_calendar; Type: VIEW; Schema: mart; Owner: myuser
--

CREATE VIEW mart.v_daily_target_with_calendar AS
 SELECT c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.day_type,
    c.is_business,
    p.target_ton,
    p.scope_used,
    p.created_at
   FROM (ref.v_calendar_classified c
     LEFT JOIN mart.daily_target_plan p ON ((c.ddate = p.ddate)));


ALTER VIEW mart.v_daily_target_with_calendar OWNER TO myuser;

--
-- PostgreSQL database dump complete
--

\unrestrict UmtFt0AtLcandBKoAbTgceoNAipvjhO9Xo4nZOVNNo4lSVdPfSPyhKeF3x29oWz

