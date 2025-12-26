--
-- PostgreSQL database dump
--

\restrict nSFYhH5rec6EkvCU7oa8wS9UYnn04r1RWFnZk9zg7GNCDhAo6xjSr3ejwSK5AZr

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
-- Name: receive_king_final; Type: TABLE; Schema: raw; Owner: myuser
--

CREATE TABLE raw.receive_king_final (
    invoice_no integer,
    invoice_date character varying(50),
    weighing_location_code integer,
    weighing_location character varying(50),
    sales_purchase_type_code integer,
    sales_purchase_type character varying(50),
    document_type_code integer,
    document_type character varying(50),
    delivery_no bigint,
    vehicle_type_code integer,
    vehicle_type character varying(50),
    customer_code integer,
    customer character varying(50),
    site_code integer,
    site character varying(50),
    discharge_company_code integer,
    discharge_company character varying(50),
    discharge_site_code integer,
    discharge_site character varying(50),
    carrier_code integer,
    carrier character varying(50),
    disposal_company_code integer,
    disposal_contractor character varying(50),
    disposal_site_code integer,
    disposal_site character varying(50),
    gross_weight integer,
    tare_weight integer,
    adjusted_weight integer,
    net_weight integer,
    counterparty_measured_weight integer,
    observed_quantity real,
    weighing_time_gross character varying(50),
    weighing_time_tare character varying(50),
    weighing_location_code1 integer,
    weighing_location1 character varying(50),
    vehicle_no integer,
    vehicle_kind character varying(50),
    driver character varying(50),
    sales_person_code integer,
    sales_person character varying(50),
    admin_person_code integer,
    admin_person character varying(50),
    sales_amount integer,
    sales_tax integer,
    purchase_amount integer,
    purchase_tax integer,
    aggregate_ton real,
    aggregate_kg integer,
    aggregate_m3 real,
    remarks character varying(50),
    item_category_code integer,
    item_category character varying(50),
    item_code integer,
    item_name character varying(50),
    quantity real,
    unit_code integer,
    unit character varying(50),
    unit_price real,
    amount integer,
    aggregation_type_code integer,
    aggregation_type character varying(50),
    unit_price_calc real,
    amount_calc integer,
    tax_amount integer,
    gross_weight_detail integer,
    tare_weight_detail integer,
    net_weight_detail integer,
    scale_ratio integer,
    scale integer,
    remarks_customer character varying(50),
    remarks_internal character varying(50),
    param_start_date character varying(50),
    param_end_date character varying(50),
    param_sales_purchase_type character varying(50),
    param_vehicle_type character varying(50),
    param_document_type character varying(50),
    param_admin_person character varying(50),
    param_company_name character varying(50),
    param_weighing_place_name character varying(50),
    quantity_ton real,
    quantity_kg real,
    quantity_m3 real,
    amount_on_account integer,
    amount_cash integer,
    tax_on_account integer,
    tax_cash integer
);


ALTER TABLE raw.receive_king_final OWNER TO myuser;

--
-- PostgreSQL database dump complete
--

\unrestrict nSFYhH5rec6EkvCU7oa8wS9UYnn04r1RWFnZk9zg7GNCDhAo6xjSr3ejwSK5AZr
