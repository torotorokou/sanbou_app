--
-- PostgreSQL database dump
--

\restrict pjdufDjCBmwGKjDekiMxgmwhwVr0ioWaOFl7oTvH2rHvpSjYcGFz9IMpLvobn1r

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
-- Name: receive_shogun_flash; Type: TABLE; Schema: raw; Owner: myuser
--

CREATE TABLE raw.receive_shogun_flash (
    slip_date date,
    sales_date date,
    payment_date date,
    vendor_cd integer,
    vendor_name text,
    slip_type_cd integer,
    slip_type_name text,
    item_cd integer,
    item_name text,
    net_weight numeric(18,3),
    quantity numeric(18,3),
    unit_cd integer,
    unit_name text,
    unit_price numeric(18,2),
    amount numeric(18,0),
    receive_no integer,
    aggregate_item_cd integer,
    aggregate_item_name text,
    category_cd integer,
    category_name text,
    weighing_time_gross time without time zone,
    weighing_time_empty time without time zone,
    site_cd integer,
    site_name text,
    unload_vendor_cd integer,
    unload_vendor_name text,
    unload_site_cd integer,
    unload_site_name text,
    transport_vendor_cd integer,
    transport_vendor_name text,
    client_cd text,
    client_name text,
    manifest_type_cd integer,
    manifest_type_name text,
    manifest_no text,
    sales_staff_cd integer,
    sales_staff_name text,
    column38 character varying(50),
    column39 character varying(50)
);


ALTER TABLE raw.receive_shogun_flash OWNER TO myuser;

--
-- Name: idx_shogun_flash_slip_date; Type: INDEX; Schema: raw; Owner: myuser
--

CREATE INDEX idx_shogun_flash_slip_date ON raw.receive_shogun_flash USING btree (slip_date);


--
-- Name: receive_shogun_flash fk_shogun_flash_ddate; Type: FK CONSTRAINT; Schema: raw; Owner: myuser
--

ALTER TABLE ONLY raw.receive_shogun_flash
    ADD CONSTRAINT fk_shogun_flash_ddate FOREIGN KEY (slip_date) REFERENCES ref.calendar_day(ddate);


--
-- PostgreSQL database dump complete
--

\unrestrict pjdufDjCBmwGKjDekiMxgmwhwVr0ioWaOFl7oTvH2rHvpSjYcGFz9IMpLvobn1r

