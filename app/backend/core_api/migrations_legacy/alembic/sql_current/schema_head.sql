--
-- PostgreSQL database dump
--

\restrict 1tqERPZTUdvMTRz0xpYDWPBycghbcOrKq4vA4CJD2gw0XGcaexVyFsvpWnqzZ1k

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
-- Name: forecast; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA forecast;


--
-- Name: kpi; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA kpi;


--
-- Name: log; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA log;


--
-- Name: mart; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA mart;


--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: raw; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA raw;


--
-- Name: ref; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA ref;


--
-- Name: sandbox; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA sandbox;


--
-- Name: stg; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA stg;


--
-- Name: refresh_inb5y(); Type: FUNCTION; Schema: mart; Owner: -
--

CREATE FUNCTION mart.refresh_inb5y() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz;
  REFRESH MATERIALIZED VIEW mart.mv_inb_avg5y_week_biz;
  REFRESH MATERIALIZED VIEW mart.mv_inb_sunfac5y_week;
  REFRESH MATERIALIZED VIEW mart.mv_inb_holfac5y_mon_dow;
END; $$;


SET default_table_access_method = heap;

--
-- Name: inbound_forecast_daily; Type: TABLE; Schema: forecast; Owner: -
--

CREATE TABLE forecast.inbound_forecast_daily (
    run_id bigint NOT NULL,
    target_date date NOT NULL,
    horizon_days integer,
    p50_ton numeric(18,3) NOT NULL,
    p10_ton numeric(18,3),
    p90_ton numeric(18,3),
    scenario text DEFAULT 'base'::text NOT NULL
);


--
-- Name: inbound_forecast_monthly_raw; Type: TABLE; Schema: forecast; Owner: -
--

CREATE TABLE forecast.inbound_forecast_monthly_raw (
    run_id bigint NOT NULL,
    target_month date NOT NULL,
    p50_ton numeric(18,3) NOT NULL,
    p10_ton numeric(18,3),
    p90_ton numeric(18,3),
    scenario text DEFAULT 'base'::text NOT NULL
);


--
-- Name: inbound_forecast_run; Type: TABLE; Schema: forecast; Owner: -
--

CREATE TABLE forecast.inbound_forecast_run (
    run_id bigint NOT NULL,
    factory_id text NOT NULL,
    target_month date NOT NULL,
    model_name text NOT NULL,
    run_type text NOT NULL,
    run_datetime timestamp with time zone DEFAULT now() NOT NULL,
    horizon_start date,
    horizon_end date,
    allocation_method text,
    train_from date,
    train_to date,
    notes text
);


--
-- Name: inbound_forecast_run_run_id_seq; Type: SEQUENCE; Schema: forecast; Owner: -
--

CREATE SEQUENCE forecast.inbound_forecast_run_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inbound_forecast_run_run_id_seq; Type: SEQUENCE OWNED BY; Schema: forecast; Owner: -
--

ALTER SEQUENCE forecast.inbound_forecast_run_run_id_seq OWNED BY forecast.inbound_forecast_run.run_id;


--
-- Name: inbound_forecast_weekly_raw; Type: TABLE; Schema: forecast; Owner: -
--

CREATE TABLE forecast.inbound_forecast_weekly_raw (
    run_id bigint NOT NULL,
    target_week_start date NOT NULL,
    p50_ton numeric(18,3) NOT NULL,
    p10_ton numeric(18,3),
    p90_ton numeric(18,3),
    scenario text DEFAULT 'base'::text NOT NULL
);


--
-- Name: monthly_targets; Type: TABLE; Schema: kpi; Owner: -
--

CREATE TABLE kpi.monthly_targets (
    month_date date NOT NULL,
    segment text NOT NULL,
    metric text NOT NULL,
    value numeric(20,4) NOT NULL,
    unit text NOT NULL,
    label text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    note text,
    CONSTRAINT chk_month_is_first CHECK ((month_date = (date_trunc('month'::text, (month_date)::timestamp with time zone))::date))
);


--
-- Name: upload_file; Type: TABLE; Schema: log; Owner: -
--

CREATE TABLE log.upload_file (
    id integer NOT NULL,
    file_name text NOT NULL,
    file_hash character varying(64) NOT NULL,
    file_type character varying(20) NOT NULL,
    csv_type character varying(20) NOT NULL,
    file_size_bytes bigint,
    row_count integer,
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    uploaded_by character varying(100),
    processing_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    error_message text,
    metadata jsonb,
    env text DEFAULT 'local_dev'::text NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    deleted_by text
);


--
-- Name: TABLE upload_file; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON TABLE log.upload_file IS 'CSV アップロードファイルのメタ情報';


--
-- Name: COLUMN upload_file.file_name; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.file_name IS '元のファイル名';


--
-- Name: COLUMN upload_file.file_hash; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.file_hash IS 'SHA-256 ハッシュ';


--
-- Name: COLUMN upload_file.file_type; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.file_type IS 'FLASH / FINAL';


--
-- Name: COLUMN upload_file.csv_type; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.csv_type IS 'receive / yard / shipment';


--
-- Name: COLUMN upload_file.file_size_bytes; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.file_size_bytes IS 'ファイルサイズ (bytes)';


--
-- Name: COLUMN upload_file.row_count; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.row_count IS 'データ行数（ヘッダー除く）';


--
-- Name: COLUMN upload_file.uploaded_by; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.uploaded_by IS 'アップロードユーザー';


--
-- Name: COLUMN upload_file.processing_status; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.processing_status IS 'pending / processing / completed / failed';


--
-- Name: COLUMN upload_file.error_message; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.error_message IS 'エラーメッセージ';


--
-- Name: COLUMN upload_file.metadata; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.metadata IS 'その他のメタ情報';


--
-- Name: COLUMN upload_file.is_deleted; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.is_deleted IS '論理削除フラグ (true=削除済み, false=有効)';


--
-- Name: COLUMN upload_file.deleted_at; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.deleted_at IS '削除日時 (is_deleted=true の場合に設定)';


--
-- Name: COLUMN upload_file.deleted_by; Type: COMMENT; Schema: log; Owner: -
--

COMMENT ON COLUMN log.upload_file.deleted_by IS '削除実行者（ユーザー名など）';


--
-- Name: upload_file_id_seq; Type: SEQUENCE; Schema: log; Owner: -
--

CREATE SEQUENCE log.upload_file_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: upload_file_id_seq; Type: SEQUENCE OWNED BY; Schema: log; Owner: -
--

ALTER SEQUENCE log.upload_file_id_seq OWNED BY log.upload_file.id;


--
-- Name: daily_target_plan; Type: TABLE; Schema: mart; Owner: -
--

CREATE TABLE mart.daily_target_plan (
    ddate timestamp without time zone,
    target_ton double precision,
    scope_used text,
    created_at timestamp without time zone
);


--
-- Name: inb_profile_smooth_test; Type: TABLE; Schema: mart; Owner: -
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


--
-- Name: calendar_day; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.calendar_day (
    ddate date NOT NULL,
    y integer GENERATED ALWAYS AS ((EXTRACT(year FROM ddate))::integer) STORED,
    m integer GENERATED ALWAYS AS ((EXTRACT(month FROM ddate))::integer) STORED,
    iso_year integer GENERATED ALWAYS AS ((EXTRACT(isoyear FROM ddate))::integer) STORED,
    iso_week integer GENERATED ALWAYS AS ((EXTRACT(week FROM ddate))::integer) STORED,
    iso_dow integer GENERATED ALWAYS AS ((EXTRACT(isodow FROM ddate))::integer) STORED
);


--
-- Name: calendar_exception; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.calendar_exception (
    ddate date NOT NULL,
    override_type text NOT NULL,
    reason text,
    updated_by text,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT calendar_exception_override_type_check CHECK ((override_type = ANY (ARRAY['FORCE_CLOSED'::text, 'FORCE_OPEN'::text, 'FORCE_RESERVATION'::text])))
);


--
-- Name: closure_periods; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.closure_periods (
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL,
    CONSTRAINT closure_periods_check CHECK ((start_date <= end_date))
);


--
-- Name: holiday_jp; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.holiday_jp (
    hdate date NOT NULL,
    name text NOT NULL
);


--
-- Name: v_closure_days; Type: VIEW; Schema: ref; Owner: -
--

CREATE VIEW ref.v_closure_days AS
 SELECT (g.g)::date AS ddate,
    p.closure_name
   FROM ref.closure_periods p,
    LATERAL generate_series((p.start_date)::timestamp with time zone, (p.end_date)::timestamp with time zone, '1 day'::interval) g(g);


--
-- Name: v_calendar_classified; Type: VIEW; Schema: ref; Owner: -
--

CREATE VIEW ref.v_calendar_classified AS
 WITH sundays AS (
         SELECT calendar_day.ddate,
            calendar_day.y,
            calendar_day.m,
            row_number() OVER (PARTITION BY calendar_day.y, calendar_day.m ORDER BY calendar_day.ddate) AS sunday_idx
           FROM ref.calendar_day
          WHERE (calendar_day.iso_dow = 7)
        ), second_sunday AS (
         SELECT sundays.ddate,
            true AS is_second_sunday
           FROM sundays
          WHERE (sundays.sunday_idx = 2)
        ), holiday AS (
         SELECT holiday_jp.hdate AS ddate,
            true AS is_holiday
           FROM ref.holiday_jp
        ), closure AS (
         SELECT v_closure_days.ddate,
            true AS is_company_closed
           FROM ref.v_closure_days
        ), ex AS (
         SELECT calendar_exception.ddate,
            calendar_exception.override_type
           FROM ref.calendar_exception
        ), base AS (
         SELECT c.ddate,
            c.y,
            c.m,
            c.iso_year,
            c.iso_week,
            c.iso_dow,
            COALESCE(h.is_holiday, false) AS is_holiday,
            COALESCE(ss.is_second_sunday, false) AS is_second_sunday,
            COALESCE(cl.is_company_closed, false) AS is_company_closed,
                CASE
                    WHEN (COALESCE(cl.is_company_closed, false) OR COALESCE(ss.is_second_sunday, false)) THEN 'CLOSED'::text
                    WHEN ((c.iso_dow = 7) OR COALESCE(h.is_holiday, false)) THEN 'RESERVATION'::text
                    ELSE 'NORMAL'::text
                END AS base_day_type,
                CASE
                    WHEN (COALESCE(cl.is_company_closed, false) OR COALESCE(ss.is_second_sunday, false)) THEN false
                    ELSE true
                END AS base_is_business
           FROM (((ref.calendar_day c
             LEFT JOIN holiday h ON ((h.ddate = c.ddate)))
             LEFT JOIN second_sunday ss ON ((ss.ddate = c.ddate)))
             LEFT JOIN closure cl ON ((cl.ddate = c.ddate)))
        )
 SELECT b.ddate,
    b.y,
    b.m,
    b.iso_year,
    b.iso_week,
    b.iso_dow,
    b.is_holiday,
    b.is_second_sunday,
    b.is_company_closed,
        CASE ex.override_type
            WHEN 'FORCE_CLOSED'::text THEN 'CLOSED'::text
            WHEN 'FORCE_OPEN'::text THEN 'NORMAL'::text
            WHEN 'FORCE_RESERVATION'::text THEN 'RESERVATION'::text
            ELSE b.base_day_type
        END AS day_type,
        CASE ex.override_type
            WHEN 'FORCE_CLOSED'::text THEN false
            WHEN 'FORCE_OPEN'::text THEN true
            WHEN 'FORCE_RESERVATION'::text THEN true
            ELSE b.base_is_business
        END AS is_business
   FROM (base b
     LEFT JOIN ex ON ((ex.ddate = b.ddate)))
  ORDER BY b.ddate;


--
-- Name: receive_king_final; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.receive_king_final (
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


--
-- Name: shogun_flash_receive; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_flash_receive (
    id bigint NOT NULL,
    slip_date date,
    sales_date date,
    payment_date date,
    vendor_cd integer,
    vendor_name text,
    slip_type_cd integer,
    slip_type_name text,
    item_cd integer,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_cd integer,
    unit_name text,
    unit_price numeric,
    amount numeric,
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
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_flash_receive; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_flash_receive IS '受入速報（型変換済み）';


--
-- Name: COLUMN shogun_flash_receive.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_flash_receive.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: shogun_flash_receive_id_seq; Type: SEQUENCE; Schema: stg; Owner: -
--

CREATE SEQUENCE stg.shogun_flash_receive_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shogun_flash_receive_id_seq; Type: SEQUENCE OWNED BY; Schema: stg; Owner: -
--

ALTER SEQUENCE stg.shogun_flash_receive_id_seq OWNED BY stg.shogun_flash_receive.id;


--
-- Name: shogun_final_receive; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_final_receive (
    id bigint DEFAULT nextval('stg.shogun_flash_receive_id_seq'::regclass) NOT NULL,
    slip_date date,
    sales_date date,
    payment_date date,
    vendor_cd integer,
    vendor_name text,
    slip_type_cd integer,
    slip_type_name text,
    item_cd integer,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_cd integer,
    unit_name text,
    unit_price numeric,
    amount numeric,
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
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_final_receive; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_final_receive IS '受入確定（型変換済み）';


--
-- Name: COLUMN shogun_final_receive.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_final_receive.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: v_active_shogun_final_receive; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_final_receive AS
 SELECT id,
    slip_date,
    sales_date,
    payment_date,
    vendor_cd,
    vendor_name,
    slip_type_cd,
    slip_type_name,
    item_cd,
    item_name,
    net_weight,
    quantity,
    unit_cd,
    unit_name,
    unit_price,
    amount,
    receive_no,
    aggregate_item_cd,
    aggregate_item_name,
    category_cd,
    category_name,
    weighing_time_gross,
    weighing_time_empty,
    site_cd,
    site_name,
    unload_vendor_cd,
    unload_vendor_name,
    unload_site_cd,
    unload_site_name,
    transport_vendor_cd,
    transport_vendor_name,
    client_cd,
    client_name,
    manifest_type_cd,
    manifest_type_name,
    manifest_no,
    sales_staff_cd,
    sales_staff_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_receive
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_final_receive; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_final_receive IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: v_active_shogun_flash_receive; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_flash_receive AS
 SELECT id,
    slip_date,
    sales_date,
    payment_date,
    vendor_cd,
    vendor_name,
    slip_type_cd,
    slip_type_name,
    item_cd,
    item_name,
    net_weight,
    quantity,
    unit_cd,
    unit_name,
    unit_price,
    amount,
    receive_no,
    aggregate_item_cd,
    aggregate_item_name,
    category_cd,
    category_name,
    weighing_time_gross,
    weighing_time_empty,
    site_cd,
    site_name,
    unload_vendor_cd,
    unload_vendor_name,
    unload_site_cd,
    unload_site_name,
    transport_vendor_cd,
    transport_vendor_name,
    client_cd,
    client_name,
    manifest_type_cd,
    manifest_type_name,
    manifest_no,
    sales_staff_cd,
    sales_staff_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_receive
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_flash_receive; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_flash_receive IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: v_king_receive_clean; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_king_receive_clean AS
 SELECT make_date((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 1))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer) AS invoice_d,
    invoice_no,
    net_weight_detail,
    amount
   FROM stg.receive_king_final k
  WHERE ((vehicle_type_code = 1) AND (net_weight_detail <> 0) AND ((invoice_date)::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer <= 12)) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer <= 31)));


--
-- Name: VIEW v_king_receive_clean; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_king_receive_clean IS 'KING受入データのクリーンビュー（日付変換済み）';


--
-- Name: v_receive_daily; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_receive_daily AS
 WITH r_shogun_final AS (
         SELECT s.slip_date AS ddate,
            (sum(s.net_weight) / 1000.0) AS receive_ton,
            count(DISTINCT s.receive_no) AS vehicle_count,
            sum(s.amount) AS sales_yen
           FROM stg.v_active_shogun_final_receive s
          WHERE (s.slip_date IS NOT NULL)
          GROUP BY s.slip_date
        ), r_shogun_flash AS (
         SELECT f.slip_date AS ddate,
            (sum(f.net_weight) / 1000.0) AS receive_ton,
            count(DISTINCT f.receive_no) AS vehicle_count,
            sum(f.amount) AS sales_yen
           FROM stg.v_active_shogun_flash_receive f
          WHERE (f.slip_date IS NOT NULL)
          GROUP BY f.slip_date
        ), r_king AS (
         SELECT k.invoice_d AS ddate,
            ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
            count(DISTINCT k.invoice_no) AS vehicle_count,
            (sum(k.amount))::numeric AS sales_yen
           FROM stg.v_king_receive_clean k
          GROUP BY k.invoice_d
        ), r_pick AS (
         SELECT r_shogun_final.ddate,
            r_shogun_final.receive_ton,
            r_shogun_final.vehicle_count,
            r_shogun_final.sales_yen,
            'shogun_final'::text AS source
           FROM r_shogun_final
        UNION ALL
         SELECT f.ddate,
            f.receive_ton,
            f.vehicle_count,
            f.sales_yen,
            'shogun_flash'::text AS source
           FROM r_shogun_flash f
          WHERE (NOT (EXISTS ( SELECT 1
                   FROM r_shogun_final s
                  WHERE (s.ddate = f.ddate))))
        UNION ALL
         SELECT k.ddate,
            k.receive_ton,
            k.vehicle_count,
            k.sales_yen,
            'king'::text AS source
           FROM r_king k
          WHERE ((NOT (EXISTS ( SELECT 1
                   FROM r_shogun_final s
                  WHERE (s.ddate = k.ddate)))) AND (NOT (EXISTS ( SELECT 1
                   FROM r_shogun_flash f
                  WHERE (f.ddate = k.ddate)))))
        )
 SELECT cal.ddate,
    cal.y,
    cal.m,
    cal.iso_year,
    cal.iso_week,
    cal.iso_dow,
    cal.is_business,
    cal.is_holiday,
    cal.day_type,
    (COALESCE(p.receive_ton, (0)::numeric))::numeric(18,3) AS receive_net_ton,
    (COALESCE(p.vehicle_count, (0)::bigint))::integer AS receive_vehicle_count,
    (
        CASE
            WHEN (COALESCE(p.vehicle_count, (0)::bigint) > 0) THEN ((COALESCE(p.receive_ton, (0)::numeric) * 1000.0) / (p.vehicle_count)::numeric)
            ELSE NULL::numeric
        END)::numeric(18,3) AS avg_weight_kg_per_vehicle,
    (COALESCE(p.sales_yen, (0)::numeric))::numeric(18,0) AS sales_yen,
    (
        CASE
            WHEN ((COALESCE(p.receive_ton, (0)::numeric) * 1000.0) > (0)::numeric) THEN (p.sales_yen / (p.receive_ton * 1000.0))
            ELSE NULL::numeric
        END)::numeric(18,3) AS unit_price_yen_per_kg,
    p.source AS source_system
   FROM (ref.v_calendar_classified cal
     LEFT JOIN r_pick p ON ((p.ddate = cal.ddate)))
  WHERE (cal.ddate <= (((now() AT TIME ZONE 'Asia/Tokyo'::text))::date - 1))
  ORDER BY cal.ddate;


--
-- Name: VIEW v_receive_daily; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON VIEW mart.v_receive_daily IS '日次受入集計ビュー（将軍・KING統合）';


--
-- Name: mv_inb5y_week_profile_min; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_inb5y_week_profile_min AS
 WITH normal AS (
         SELECT receive_daily.iso_week,
            avg(receive_daily.receive_net_ton) AS normal_day_mean,
            count(*) AS n_normal
           FROM mart.v_receive_daily receive_daily
          WHERE ((receive_daily.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (receive_daily.is_business = true) AND (receive_daily.day_type = 'NORMAL'::text) AND (receive_daily.receive_net_ton IS NOT NULL))
          GROUP BY receive_daily.iso_week
        ), resv_samples AS (
         SELECT d.iso_week,
            (d.receive_net_ton / NULLIF(n_1.normal_day_mean, (0)::numeric)) AS r
           FROM (mart.v_receive_daily d
             JOIN normal n_1 USING (iso_week))
          WHERE ((d.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (d.is_business = true) AND (d.day_type = 'RESERVATION'::text) AND (d.receive_net_ton IS NOT NULL))
        ), agg AS (
         SELECT resv_samples.iso_week,
            avg(resv_samples.r) AS off_fac_raw,
            count(*) AS n_off
           FROM resv_samples
          GROUP BY resv_samples.iso_week
        ), g AS (
         SELECT avg(resv_samples.r) AS g_off_fac
           FROM resv_samples
        )
 SELECT n.iso_week,
    (n.normal_day_mean)::numeric(14,4) AS normal_day_mean,
    ((n.normal_day_mean * COALESCE(
        CASE
            WHEN (a.n_off >= 3) THEN a.off_fac_raw
            ELSE NULL::numeric
        END, ( SELECT g.g_off_fac
           FROM g), 0.50)))::numeric(14,4) AS reservation_day_mean,
    CURRENT_TIMESTAMP AS updated_at
   FROM (normal n
     LEFT JOIN agg a USING (iso_week))
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_inb5y_week_profile_min; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb5y_week_profile_min IS '5y weekly profile (minimal): normal_day_mean (NORMAL), reservation_day_mean (RESERVATION=Sun+Holiday).';


--
-- Name: mv_inb_avg5y_day_biz; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz AS
 WITH agg AS (
         SELECT receive_daily.iso_week,
            receive_daily.iso_dow,
            avg(receive_daily.receive_net_ton) AS ave_wd,
            stddev_samp(receive_daily.receive_net_ton) AS sigma_wd,
            count(*) AS n_wd
           FROM mart.v_receive_daily receive_daily
          WHERE ((receive_daily.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (receive_daily.is_business = true) AND (receive_daily.is_holiday = false) AND ((receive_daily.iso_dow >= 1) AND (receive_daily.iso_dow <= 6)) AND (receive_daily.receive_net_ton IS NOT NULL))
          GROUP BY receive_daily.iso_week, receive_daily.iso_dow
        )
 SELECT iso_week,
    iso_dow,
    (ave_wd)::numeric(14,4) AS ave,
    (sigma_wd)::numeric(14,4) AS sigma,
    n_wd AS n,
        CASE
            WHEN (ave_wd > (0)::numeric) THEN ((sigma_wd / ave_wd))::numeric(14,4)
            ELSE NULL::numeric
        END AS cv,
        CASE
            WHEN (n_wd < 3) THEN 'LOW_SAMPLE'::text
            WHEN (ave_wd <= (1)::numeric) THEN 'LOW_MEAN'::text
            WHEN ((sigma_wd / NULLIF(ave_wd, (0)::numeric)) > 0.60) THEN 'HIGH_VARIANCE'::text
            ELSE 'OK'::text
        END AS quality,
    CURRENT_TIMESTAMP AS updated_at
   FROM agg
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_inb_avg5y_day_biz; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz IS '5y avg inbound/day (business Mon–Sat, holidays excluded) by (iso_week, iso_dow).';


--
-- Name: mv_inb_avg5y_day_scope; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope AS
 WITH base AS (
         SELECT r.ddate,
            r.iso_week,
            r.iso_dow,
            r.is_business,
            r.is_holiday,
            (r.receive_net_ton)::numeric AS y
           FROM mart.v_receive_daily r
          WHERE ((r.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (r.receive_net_ton IS NOT NULL))
        ), scoped AS (
         SELECT 'all'::text AS scope,
            base.iso_week,
            base.iso_dow,
            base.y
           FROM base
        UNION ALL
         SELECT 'biz'::text AS scope,
            base.iso_week,
            base.iso_dow,
            base.y
           FROM base
          WHERE ((base.is_business = true) AND (COALESCE(base.is_holiday, false) = false) AND ((base.iso_dow >= 1) AND (base.iso_dow <= 6)))
        ), agg AS (
         SELECT scoped.scope,
            scoped.iso_week,
            scoped.iso_dow,
            avg(scoped.y) AS ave,
            stddev_samp(scoped.y) AS sigma,
            count(*) AS n
           FROM scoped
          GROUP BY scoped.scope, scoped.iso_week, scoped.iso_dow
        )
 SELECT scope,
    iso_week,
    iso_dow,
    (ave)::numeric(14,4) AS ave,
    (sigma)::numeric(14,4) AS sigma,
    n,
        CASE
            WHEN (ave <> (0)::numeric) THEN ((sigma / NULLIF(ave, (0)::numeric)))::numeric(14,4)
            ELSE NULL::numeric
        END AS cv,
    jsonb_build_object('window_years', 5, 'include_holiday', (scope = 'all'::text), 'include_sunday', (scope = 'all'::text), 'y_filter', 'is not null') AS criteria,
    CURRENT_TIMESTAMP AS updated_at
   FROM agg
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_inb_avg5y_day_scope; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope IS '5y average inbound per day by (scope, iso_week, iso_dow). scope=all: all days, scope=biz: business Mon-Sat only.';


--
-- Name: mv_inb_avg5y_weeksum_biz; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz AS
 WITH week_year AS (
         SELECT receive_daily.iso_year,
            receive_daily.iso_week,
            sum(receive_daily.receive_net_ton) AS week_sum_biz
           FROM mart.v_receive_daily receive_daily
          WHERE ((receive_daily.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (receive_daily.is_business = true) AND (receive_daily.is_holiday = false) AND ((receive_daily.iso_dow >= 1) AND (receive_daily.iso_dow <= 6)) AND (receive_daily.receive_net_ton IS NOT NULL))
          GROUP BY receive_daily.iso_year, receive_daily.iso_week
        ), agg AS (
         SELECT week_year.iso_week,
            avg(week_year.week_sum_biz) AS ave,
            stddev_samp(week_year.week_sum_biz) AS sigma,
            count(*) AS n
           FROM week_year
          GROUP BY week_year.iso_week
        )
 SELECT iso_week,
    0 AS iso_dow,
    (ave)::numeric(14,2) AS ave,
    (sigma)::numeric(14,2) AS sigma,
    n,
        CASE
            WHEN (ave > (0)::numeric) THEN ((sigma / ave))::numeric(14,4)
            ELSE NULL::numeric
        END AS cv,
        CASE
            WHEN (n < 3) THEN 'LOW_SAMPLE'::text
            WHEN (ave <= (1)::numeric) THEN 'LOW_MEAN'::text
            WHEN ((sigma / NULLIF(ave, (0)::numeric)) > 0.60) THEN 'HIGH_VARIANCE'::text
            ELSE 'OK'::text
        END AS quality,
    CURRENT_TIMESTAMP AS updated_at
   FROM agg
  ORDER BY iso_week
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_inb_avg5y_weeksum_biz; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz IS '5y weekly sum (business Mon–Sat, holidays excluded): AVG/STD across years by iso_week. iso_dow=0 sentinel.';


--
-- Name: mv_sales_tree_daily; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_sales_tree_daily AS
 SELECT COALESCE(sales_date, slip_date) AS sales_date,
    sales_staff_cd AS rep_id,
    sales_staff_name AS rep_name,
    client_cd AS customer_id,
    client_name AS customer_name,
    item_cd AS item_id,
    item_name,
    amount AS amount_yen,
    net_weight AS qty_kg,
    receive_no AS slip_no,
    1 AS slip_count
   FROM stg.shogun_flash_receive
  WHERE ((category_cd = 1) AND (COALESCE(sales_date, slip_date) IS NOT NULL) AND (COALESCE(is_deleted, false) = false))
  WITH NO DATA;


--
-- Name: v_daily_target_with_calendar; Type: VIEW; Schema: mart; Owner: -
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


--
-- Name: mv_target_card_per_day; Type: MATERIALIZED VIEW; Schema: mart; Owner: -
--

CREATE MATERIALIZED VIEW mart.mv_target_card_per_day AS
 WITH base AS (
         SELECT v.ddate,
            v.iso_year,
            v.iso_week,
            v.iso_dow,
            v.day_type,
            v.is_business,
            (COALESCE(v.target_ton, (0)::double precision))::numeric AS day_target_ton
           FROM mart.v_daily_target_with_calendar v
        ), week_target AS (
         SELECT v_daily_target_with_calendar.iso_year,
            v_daily_target_with_calendar.iso_week,
            (sum(COALESCE(v_daily_target_with_calendar.target_ton, (0)::double precision)))::numeric AS week_target_ton
           FROM mart.v_daily_target_with_calendar
          GROUP BY v_daily_target_with_calendar.iso_year, v_daily_target_with_calendar.iso_week
        ), month_target AS (
         SELECT DISTINCT ON (((date_trunc('month'::text, (mt_1.month_date)::timestamp with time zone))::date)) (date_trunc('month'::text, (mt_1.month_date)::timestamp with time zone))::date AS month_key,
            (mt_1.value)::numeric AS month_target_ton
           FROM kpi.monthly_targets mt_1
          WHERE ((mt_1.metric = 'inbound'::text) AND (mt_1.segment = 'factory'::text))
          ORDER BY ((date_trunc('month'::text, (mt_1.month_date)::timestamp with time zone))::date), mt_1.updated_at DESC
        ), week_actual AS (
         SELECT r.iso_year,
            r.iso_week,
            sum(COALESCE(r.receive_net_ton, (0)::numeric)) AS week_actual_ton
           FROM mart.v_receive_daily r
          GROUP BY r.iso_year, r.iso_week
        ), month_actual AS (
         SELECT (date_trunc('month'::text, (r.ddate)::timestamp with time zone))::date AS month_key,
            sum(COALESCE(r.receive_net_ton, (0)::numeric)) AS month_actual_ton
           FROM mart.v_receive_daily r
          GROUP BY ((date_trunc('month'::text, (r.ddate)::timestamp with time zone))::date)
        )
 SELECT b.ddate,
    b.day_target_ton,
    wt.week_target_ton,
    mt.month_target_ton,
    COALESCE(rprev.receive_net_ton, (0)::numeric) AS day_actual_ton_prev,
    COALESCE(wa.week_actual_ton, (0)::numeric) AS week_actual_ton,
    COALESCE(ma.month_actual_ton, (0)::numeric) AS month_actual_ton,
    b.iso_year,
    b.iso_week,
    b.iso_dow,
    b.day_type,
    b.is_business
   FROM (((((base b
     LEFT JOIN week_target wt ON (((wt.iso_year = b.iso_year) AND (wt.iso_week = b.iso_week))))
     LEFT JOIN month_target mt ON ((mt.month_key = (date_trunc('month'::text, (b.ddate)::timestamp with time zone))::date)))
     LEFT JOIN week_actual wa ON (((wa.iso_year = b.iso_year) AND (wa.iso_week = b.iso_week))))
     LEFT JOIN month_actual ma ON ((ma.month_key = (date_trunc('month'::text, (b.ddate)::timestamp with time zone))::date)))
     LEFT JOIN mart.v_receive_daily rprev ON ((rprev.ddate = (b.ddate - '1 day'::interval))))
  ORDER BY b.ddate
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_target_card_per_day; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON MATERIALIZED VIEW mart.mv_target_card_per_day IS 'Materialized version of v_target_card_per_day for fast query. Refreshed daily after ETL completion.';


--
-- Name: v_sales_tree_daily; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_sales_tree_daily AS
 SELECT sales_date,
    rep_id,
    rep_name,
    customer_id,
    customer_name,
    item_id,
    item_name,
    amount_yen,
    qty_kg,
    slip_no,
    slip_count
   FROM mart.mv_sales_tree_daily;


--
-- Name: v_customer_sales_daily; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_customer_sales_daily AS
 SELECT sales_date,
    customer_id,
    max(customer_name) AS customer_name,
    max(rep_id) AS sales_rep_id,
    max(rep_name) AS sales_rep_name,
    count(DISTINCT slip_no) AS visit_count,
    sum(amount_yen) AS total_amount_yen,
    sum(qty_kg) AS total_qty_kg
   FROM mart.v_sales_tree_daily v
  GROUP BY sales_date, customer_id;


--
-- Name: v_receive_monthly; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_receive_monthly AS
 WITH d AS (
         SELECT r.ddate,
            r.y,
            r.m,
            r.receive_net_ton,
            r.receive_vehicle_count,
            r.sales_yen
           FROM mart.v_receive_daily r
        )
 SELECT make_date(y, m, 1) AS month_date,
    to_char((make_date(y, m, 1))::timestamp with time zone, 'YYYY-MM'::text) AS month,
    y,
    m,
    (sum(receive_net_ton))::numeric(18,3) AS receive_net_ton,
    sum(receive_vehicle_count) AS receive_vehicle_count,
    (sum(sales_yen))::numeric(18,0) AS sales_yen,
    (
        CASE
            WHEN (sum(receive_vehicle_count) > 0) THEN ((sum(receive_net_ton) * 1000.0) / (sum(receive_vehicle_count))::numeric)
            ELSE NULL::numeric
        END)::numeric(18,3) AS avg_weight_kg_per_vehicle,
    (
        CASE
            WHEN ((sum(receive_net_ton) * 1000.0) > (0)::numeric) THEN (sum(sales_yen) / (sum(receive_net_ton) * 1000.0))
            ELSE NULL::numeric
        END)::numeric(18,3) AS unit_price_yen_per_kg
   FROM d
  GROUP BY y, m
  ORDER BY y, m;


--
-- Name: VIEW v_receive_monthly; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON VIEW mart.v_receive_monthly IS '月次受入集計ビュー（将軍・KING統合）';


--
-- Name: v_receive_weekly; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_receive_weekly AS
 WITH w AS (
         SELECT d.iso_year,
            d.iso_week,
            min(d.ddate) AS week_start_date,
            max(d.ddate) AS week_end_date,
            (sum(d.receive_net_ton))::numeric(18,3) AS receive_net_ton,
            sum(d.receive_vehicle_count) AS receive_vehicle_count,
            (sum(d.sales_yen))::numeric(18,0) AS sales_yen
           FROM mart.v_receive_daily d
          GROUP BY d.iso_year, d.iso_week
        )
 SELECT iso_year,
    iso_week,
    ((iso_year * 100) + iso_week) AS iso_yearweek_key,
    week_start_date,
    week_end_date,
    to_char(((make_date(iso_year, 1, 4) + (((iso_week - 1))::double precision * '7 days'::interval)) - ((((EXTRACT(isodow FROM make_date(iso_year, 1, 4)))::integer - 1))::double precision * '1 day'::interval)), '"W"IW'::text) AS week_label_simple,
    to_char((week_start_date)::timestamp with time zone, 'YYYY-"W"IW'::text) AS week_label_i18n,
    receive_net_ton,
    receive_vehicle_count,
    sales_yen,
    (
        CASE
            WHEN (receive_vehicle_count > 0) THEN ((receive_net_ton * 1000.0) / (receive_vehicle_count)::numeric)
            ELSE NULL::numeric
        END)::numeric(18,3) AS avg_weight_kg_per_vehicle,
    (
        CASE
            WHEN ((receive_net_ton * 1000.0) > (0)::numeric) THEN (sales_yen / (receive_net_ton * 1000.0))
            ELSE NULL::numeric
        END)::numeric(18,3) AS unit_price_yen_per_kg
   FROM w
  ORDER BY iso_year, iso_week;


--
-- Name: VIEW v_receive_weekly; Type: COMMENT; Schema: mart; Owner: -
--

COMMENT ON VIEW mart.v_receive_weekly IS '週次受入集計ビュー（将軍・KING統合）';


--
-- Name: v_sales_tree_detail_base; Type: VIEW; Schema: mart; Owner: -
--

CREATE VIEW mart.v_sales_tree_detail_base AS
 SELECT COALESCE(sales_date, slip_date) AS sales_date,
    sales_staff_cd AS rep_id,
    sales_staff_name AS rep_name,
    client_cd AS customer_id,
    client_name AS customer_name,
    item_cd AS item_id,
    item_name,
    amount AS amount_yen,
    net_weight AS qty_kg,
    receive_no AS slip_no,
    category_cd,
    category_name,
        CASE
            WHEN (category_cd = 1) THEN 'waste'::text
            WHEN (category_cd = 3) THEN 'valuable'::text
            ELSE 'other'::text
        END AS category_kind,
    aggregate_item_cd,
    aggregate_item_name,
    id AS source_id,
    upload_file_id,
    source_row_no
   FROM stg.shogun_flash_receive s
  WHERE ((COALESCE(sales_date, slip_date) IS NOT NULL) AND (COALESCE(is_deleted, false) = false) AND (category_cd = ANY (ARRAY[1, 3])));


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: shogun_final_receive; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_final_receive (
    slip_date text,
    sales_date text,
    payment_date text,
    vendor_cd text,
    vendor_name text,
    slip_type_cd text,
    slip_type_name text,
    item_cd text,
    item_name text,
    net_weight text,
    quantity text,
    unit_cd text,
    unit_name text,
    unit_price text,
    amount text,
    receive_no text,
    aggregate_item_cd text,
    aggregate_item_name text,
    category_cd text,
    category_name text,
    weighing_time_gross text,
    weighing_time_empty text,
    site_cd text,
    site_name text,
    unload_vendor_cd text,
    unload_vendor_name text,
    unload_site_cd text,
    unload_site_name text,
    transport_vendor_cd text,
    transport_vendor_name text,
    client_cd text,
    client_name text,
    manifest_type_cd text,
    manifest_type_name text,
    sales_staff_cd text,
    sales_staff_name text,
    manifest_no text,
    column38 text,
    column39 text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: shogun_final_shipment; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_final_shipment (
    slip_date text,
    client_name text,
    item_name text,
    net_weight text,
    quantity text,
    unit_name text,
    unit_price text,
    amount text,
    transport_vendor_name text,
    vendor_cd text,
    vendor_name text,
    site_cd text,
    site_name text,
    slip_type_name text,
    shipment_no text,
    detail_note text,
    id text,
    created_at text,
    category_cd text,
    category_name text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: shogun_final_yard; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_final_yard (
    slip_date text,
    client_name text,
    item_name text,
    net_weight text,
    quantity text,
    unit_name text,
    unit_price text,
    amount text,
    sales_staff_name text,
    vendor_cd text,
    vendor_name text,
    category_cd text,
    category_name text,
    item_cd text,
    slip_no text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: shogun_flash_receive; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_flash_receive (
    slip_date text,
    sales_date text,
    payment_date text,
    vendor_cd text,
    vendor_name text,
    slip_type_cd text,
    slip_type_name text,
    item_cd text,
    item_name text,
    net_weight text,
    quantity text,
    unit_cd text,
    unit_name text,
    unit_price text,
    amount text,
    receive_no text,
    aggregate_item_cd text,
    aggregate_item_name text,
    category_cd text,
    category_name text,
    weighing_time_gross text,
    weighing_time_empty text,
    site_cd text,
    site_name text,
    unload_vendor_cd text,
    unload_vendor_name text,
    unload_site_cd text,
    unload_site_name text,
    transport_vendor_cd text,
    transport_vendor_name text,
    client_cd text,
    client_name text,
    manifest_type_cd text,
    manifest_type_name text,
    sales_staff_cd text,
    sales_staff_name text,
    manifest_no text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: shogun_flash_shipment; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_flash_shipment (
    slip_date text,
    client_name text,
    item_name text,
    net_weight text,
    quantity text,
    unit_name text,
    unit_price text,
    amount text,
    transport_vendor_name text,
    vendor_cd text,
    vendor_name text,
    site_cd text,
    site_name text,
    slip_type_name text,
    shipment_no text,
    detail_note text,
    id text,
    created_at text,
    category_cd text,
    category_name text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: shogun_flash_yard; Type: TABLE; Schema: raw; Owner: -
--

CREATE TABLE raw.shogun_flash_yard (
    slip_date text,
    client_name text,
    item_name text,
    net_weight text,
    quantity text,
    unit_name text,
    unit_price text,
    amount text,
    sales_staff_name text,
    vendor_cd text,
    vendor_name text,
    category_cd text,
    category_name text,
    item_cd text,
    slip_no text,
    upload_file_id integer,
    source_row_no integer
);


--
-- Name: calendar_month; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.calendar_month (
    month_date date NOT NULL
);


--
-- Name: closure_membership; Type: TABLE; Schema: ref; Owner: -
--

CREATE TABLE ref.closure_membership (
    ddate date NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL
);


--
-- Name: v_customer; Type: VIEW; Schema: ref; Owner: -
--

CREATE VIEW ref.v_customer AS
 SELECT client_cd AS customer_id,
    max(client_name) AS customer_name,
    max(sales_staff_cd) AS sales_rep_id,
    max(sales_staff_name) AS sales_rep_name
   FROM stg.shogun_flash_receive s
  WHERE (is_deleted = false)
  GROUP BY client_cd;


--
-- Name: v_item; Type: VIEW; Schema: ref; Owner: -
--

CREATE VIEW ref.v_item AS
 SELECT item_cd AS item_id,
    max(item_name) AS item_name,
    max(unit_cd) AS unit_cd,
    max(unit_name) AS unit_name,
    max(category_cd) AS category_cd,
    max(category_name) AS category_name
   FROM stg.shogun_flash_receive s
  WHERE (is_deleted = false)
  GROUP BY item_cd;


--
-- Name: v_sales_rep; Type: VIEW; Schema: ref; Owner: -
--

CREATE VIEW ref.v_sales_rep AS
 SELECT sales_staff_cd AS sales_rep_id,
    max(sales_staff_name) AS sales_rep_name
   FROM stg.shogun_flash_receive s
  WHERE (is_deleted = false)
  GROUP BY sales_staff_cd;


--
-- Name: receive_flash; Type: TABLE; Schema: sandbox; Owner: -
--

CREATE TABLE sandbox.receive_flash (
    id integer NOT NULL,
    slip_date timestamp without time zone NOT NULL,
    sales_date timestamp without time zone,
    payment_date timestamp without time zone,
    vendor_cd integer NOT NULL,
    vendor_name text NOT NULL,
    slip_type_cd integer,
    slip_type_name text,
    item_cd integer NOT NULL,
    item_name text NOT NULL,
    net_weight double precision NOT NULL,
    quantity double precision NOT NULL,
    unit_cd integer,
    unit_name text,
    unit_price double precision,
    amount double precision,
    receive_no integer NOT NULL,
    aggregate_item_cd integer,
    aggregate_item_name text,
    category_cd integer,
    category_name text,
    weighing_time_gross text,
    weighing_time_empty text,
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
    raw_data_json jsonb,
    validation_errors jsonb,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: receive_flash_id_seq; Type: SEQUENCE; Schema: sandbox; Owner: -
--

CREATE SEQUENCE sandbox.receive_flash_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: receive_flash_id_seq; Type: SEQUENCE OWNED BY; Schema: sandbox; Owner: -
--

ALTER SEQUENCE sandbox.receive_flash_id_seq OWNED BY sandbox.receive_flash.id;


--
-- Name: shipment_flash; Type: TABLE; Schema: sandbox; Owner: -
--

CREATE TABLE sandbox.shipment_flash (
    slip_date date NOT NULL,
    shipment_no text NOT NULL,
    client_en_name text NOT NULL,
    vendor_cd integer NOT NULL,
    vendor_en_name text NOT NULL,
    site_cd integer,
    site_en_name text,
    item_en_name text NOT NULL,
    net_weight double precision NOT NULL,
    quantity double precision NOT NULL,
    unit_en_name text,
    unit_price double precision,
    amount double precision,
    transport_vendor_en_name text,
    slip_type_en_name text,
    detail_note text
);


--
-- Name: v_sales_tree_detail_base; Type: VIEW; Schema: sandbox; Owner: -
--

CREATE VIEW sandbox.v_sales_tree_detail_base AS
 SELECT COALESCE(sales_date, slip_date) AS sales_date,
    sales_staff_cd AS rep_id,
    sales_staff_name AS rep_name,
    client_cd AS customer_id,
    client_name AS customer_name,
    item_cd AS item_id,
    item_name,
    amount AS amount_yen,
    net_weight AS qty_kg,
    receive_no AS slip_no,
    category_cd,
    category_name,
        CASE
            WHEN (category_cd = 1) THEN 'waste'::text
            WHEN (category_cd = 3) THEN 'valuable'::text
            ELSE 'other'::text
        END AS category_kind,
    aggregate_item_cd,
    aggregate_item_name,
    id AS source_id,
    upload_file_id,
    source_row_no
   FROM stg.shogun_flash_receive s
  WHERE ((COALESCE(sales_date, slip_date) IS NOT NULL) AND (COALESCE(is_deleted, false) = false));


--
-- Name: yard_flash; Type: TABLE; Schema: sandbox; Owner: -
--

CREATE TABLE sandbox.yard_flash (
    slip_date date NOT NULL,
    client_en_name text NOT NULL,
    item_en_name text NOT NULL,
    net_weight double precision NOT NULL,
    quantity double precision NOT NULL,
    unit_en_name text,
    unit_price double precision,
    amount double precision,
    sales_staff_en_name text,
    vendor_cd integer NOT NULL,
    vendor_en_name text NOT NULL,
    category_cd integer,
    category_en_name text,
    item_cd integer NOT NULL,
    slip_no text
);


--
-- Name: shogun_flash_shipment; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_flash_shipment (
    id bigint NOT NULL,
    slip_date date,
    client_name text,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_name text,
    unit_price numeric,
    amount numeric,
    transport_vendor_name text,
    vendor_cd integer,
    vendor_name text,
    site_cd integer,
    site_name text,
    slip_type_name text,
    shipment_no text,
    detail_note text,
    category_cd integer,
    category_name text,
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_flash_shipment; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_flash_shipment IS '出荷速報（型変換済み）';


--
-- Name: COLUMN shogun_flash_shipment.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_flash_shipment.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: shogun_flash_shipment_id_seq; Type: SEQUENCE; Schema: stg; Owner: -
--

CREATE SEQUENCE stg.shogun_flash_shipment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shogun_flash_shipment_id_seq; Type: SEQUENCE OWNED BY; Schema: stg; Owner: -
--

ALTER SEQUENCE stg.shogun_flash_shipment_id_seq OWNED BY stg.shogun_flash_shipment.id;


--
-- Name: shogun_final_shipment; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_final_shipment (
    id bigint DEFAULT nextval('stg.shogun_flash_shipment_id_seq'::regclass) NOT NULL,
    slip_date date,
    client_name text,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_name text,
    unit_price numeric,
    amount numeric,
    transport_vendor_name text,
    vendor_cd integer,
    vendor_name text,
    site_cd integer,
    site_name text,
    slip_type_name text,
    shipment_no text,
    detail_note text,
    category_cd integer,
    category_name text,
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_final_shipment; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_final_shipment IS '出荷確定（型変換済み）';


--
-- Name: COLUMN shogun_final_shipment.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_final_shipment.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: shogun_flash_yard; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_flash_yard (
    id bigint NOT NULL,
    slip_date date,
    client_name text,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_name text,
    unit_price numeric,
    amount numeric,
    sales_staff_name text,
    vendor_cd integer,
    vendor_name text,
    category_cd integer,
    category_name text,
    item_cd integer,
    slip_no text,
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_flash_yard; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_flash_yard IS 'ヤード速報（型変換済み）';


--
-- Name: COLUMN shogun_flash_yard.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_flash_yard.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: shogun_flash_yard_id_seq; Type: SEQUENCE; Schema: stg; Owner: -
--

CREATE SEQUENCE stg.shogun_flash_yard_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shogun_flash_yard_id_seq; Type: SEQUENCE OWNED BY; Schema: stg; Owner: -
--

ALTER SEQUENCE stg.shogun_flash_yard_id_seq OWNED BY stg.shogun_flash_yard.id;


--
-- Name: shogun_final_yard; Type: TABLE; Schema: stg; Owner: -
--

CREATE TABLE stg.shogun_final_yard (
    id bigint DEFAULT nextval('stg.shogun_flash_yard_id_seq'::regclass) NOT NULL,
    slip_date date,
    client_name text,
    item_name text,
    net_weight numeric,
    quantity numeric,
    unit_name text,
    unit_price numeric,
    amount numeric,
    sales_staff_name text,
    vendor_cd integer,
    vendor_name text,
    category_cd integer,
    category_name text,
    item_cd integer,
    slip_no text,
    upload_file_id integer,
    source_row_no integer,
    is_deleted boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_by text
);


--
-- Name: TABLE shogun_final_yard; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON TABLE stg.shogun_final_yard IS 'ヤード確定（型変換済み）';


--
-- Name: COLUMN shogun_final_yard.deleted_by; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON COLUMN stg.shogun_final_yard.deleted_by IS '削除実行者 (ユーザー名またはシステム識別子)';


--
-- Name: v_active_shogun_final_shipment; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_final_shipment AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    transport_vendor_name,
    vendor_cd,
    vendor_name,
    site_cd,
    site_name,
    slip_type_name,
    shipment_no,
    detail_note,
    category_cd,
    category_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_shipment
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_final_shipment; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_final_shipment IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: v_active_shogun_final_yard; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_final_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_final_yard
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_final_yard; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_final_yard IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: v_active_shogun_flash_shipment; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_flash_shipment AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    transport_vendor_name,
    vendor_cd,
    vendor_name,
    site_cd,
    site_name,
    slip_type_name,
    shipment_no,
    detail_note,
    category_cd,
    category_name,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_shipment
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_flash_shipment; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_flash_shipment IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: v_active_shogun_flash_yard; Type: VIEW; Schema: stg; Owner: -
--

CREATE VIEW stg.v_active_shogun_flash_yard AS
 SELECT id,
    slip_date,
    client_name,
    item_name,
    net_weight,
    quantity,
    unit_name,
    unit_price,
    amount,
    sales_staff_name,
    vendor_cd,
    vendor_name,
    category_cd,
    category_name,
    item_cd,
    slip_no,
    upload_file_id,
    source_row_no,
    is_deleted,
    deleted_at,
    created_at
   FROM stg.shogun_flash_yard
  WHERE (is_deleted = false);


--
-- Name: VIEW v_active_shogun_flash_yard; Type: COMMENT; Schema: stg; Owner: -
--

COMMENT ON VIEW stg.v_active_shogun_flash_yard IS 'Active rows view: filters out soft-deleted rows (is_deleted = false only)';


--
-- Name: inbound_forecast_run run_id; Type: DEFAULT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_run ALTER COLUMN run_id SET DEFAULT nextval('forecast.inbound_forecast_run_run_id_seq'::regclass);


--
-- Name: upload_file id; Type: DEFAULT; Schema: log; Owner: -
--

ALTER TABLE ONLY log.upload_file ALTER COLUMN id SET DEFAULT nextval('log.upload_file_id_seq'::regclass);


--
-- Name: receive_flash id; Type: DEFAULT; Schema: sandbox; Owner: -
--

ALTER TABLE ONLY sandbox.receive_flash ALTER COLUMN id SET DEFAULT nextval('sandbox.receive_flash_id_seq'::regclass);


--
-- Name: shogun_flash_receive id; Type: DEFAULT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_receive ALTER COLUMN id SET DEFAULT nextval('stg.shogun_flash_receive_id_seq'::regclass);


--
-- Name: shogun_flash_shipment id; Type: DEFAULT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_shipment ALTER COLUMN id SET DEFAULT nextval('stg.shogun_flash_shipment_id_seq'::regclass);


--
-- Name: shogun_flash_yard id; Type: DEFAULT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_yard ALTER COLUMN id SET DEFAULT nextval('stg.shogun_flash_yard_id_seq'::regclass);


--
-- Name: inbound_forecast_daily inbound_forecast_daily_pkey; Type: CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_daily
    ADD CONSTRAINT inbound_forecast_daily_pkey PRIMARY KEY (run_id, target_date, scenario);


--
-- Name: inbound_forecast_monthly_raw inbound_forecast_monthly_raw_pkey; Type: CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_monthly_raw
    ADD CONSTRAINT inbound_forecast_monthly_raw_pkey PRIMARY KEY (run_id, target_month, scenario);


--
-- Name: inbound_forecast_run inbound_forecast_run_pkey; Type: CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_run
    ADD CONSTRAINT inbound_forecast_run_pkey PRIMARY KEY (run_id);


--
-- Name: inbound_forecast_weekly_raw inbound_forecast_weekly_raw_pkey; Type: CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_weekly_raw
    ADD CONSTRAINT inbound_forecast_weekly_raw_pkey PRIMARY KEY (run_id, target_week_start, scenario);


--
-- Name: monthly_targets uq_monthly_targets; Type: CONSTRAINT; Schema: kpi; Owner: -
--

ALTER TABLE ONLY kpi.monthly_targets
    ADD CONSTRAINT uq_monthly_targets UNIQUE (month_date, segment, metric);


--
-- Name: upload_file upload_file_pkey; Type: CONSTRAINT; Schema: log; Owner: -
--

ALTER TABLE ONLY log.upload_file
    ADD CONSTRAINT upload_file_pkey PRIMARY KEY (id);


--
-- Name: inb_profile_smooth_test inb_profile_smooth_test_pkey; Type: CONSTRAINT; Schema: mart; Owner: -
--

ALTER TABLE ONLY mart.inb_profile_smooth_test
    ADD CONSTRAINT inb_profile_smooth_test_pkey PRIMARY KEY (scope, iso_week, iso_dow);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: calendar_day calendar_day_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.calendar_day
    ADD CONSTRAINT calendar_day_pkey PRIMARY KEY (ddate);


--
-- Name: calendar_exception calendar_exception_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT calendar_exception_pkey PRIMARY KEY (ddate);


--
-- Name: calendar_month calendar_month_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.calendar_month
    ADD CONSTRAINT calendar_month_pkey PRIMARY KEY (month_date);


--
-- Name: closure_membership closure_membership_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT closure_membership_pkey PRIMARY KEY (ddate);


--
-- Name: closure_periods closure_periods_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.closure_periods
    ADD CONSTRAINT closure_periods_pkey PRIMARY KEY (start_date, end_date);


--
-- Name: holiday_jp holiday_jp_pkey; Type: CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT holiday_jp_pkey PRIMARY KEY (hdate);


--
-- Name: receive_flash receive_flash_pkey; Type: CONSTRAINT; Schema: sandbox; Owner: -
--

ALTER TABLE ONLY sandbox.receive_flash
    ADD CONSTRAINT receive_flash_pkey PRIMARY KEY (id);


--
-- Name: shogun_final_receive shogun_final_receive_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_final_receive
    ADD CONSTRAINT shogun_final_receive_pkey PRIMARY KEY (id);


--
-- Name: shogun_final_shipment shogun_final_shipment_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_final_shipment
    ADD CONSTRAINT shogun_final_shipment_pkey PRIMARY KEY (id);


--
-- Name: shogun_final_yard shogun_final_yard_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_final_yard
    ADD CONSTRAINT shogun_final_yard_pkey PRIMARY KEY (id);


--
-- Name: shogun_flash_receive shogun_flash_receive_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_receive
    ADD CONSTRAINT shogun_flash_receive_pkey PRIMARY KEY (id);


--
-- Name: shogun_flash_shipment shogun_flash_shipment_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_shipment
    ADD CONSTRAINT shogun_flash_shipment_pkey PRIMARY KEY (id);


--
-- Name: shogun_flash_yard shogun_flash_yard_pkey; Type: CONSTRAINT; Schema: stg; Owner: -
--

ALTER TABLE ONLY stg.shogun_flash_yard
    ADD CONSTRAINT shogun_flash_yard_pkey PRIMARY KEY (id);


--
-- Name: idx_kpi_month_date; Type: INDEX; Schema: kpi; Owner: -
--

CREATE INDEX idx_kpi_month_date ON kpi.monthly_targets USING btree (month_date);


--
-- Name: idx_upload_file_duplicate_fallback; Type: INDEX; Schema: log; Owner: -
--

CREATE INDEX idx_upload_file_duplicate_fallback ON log.upload_file USING btree (csv_type, file_name, file_size_bytes, row_count, processing_status);


--
-- Name: idx_upload_file_status; Type: INDEX; Schema: log; Owner: -
--

CREATE INDEX idx_upload_file_status ON log.upload_file USING btree (processing_status);


--
-- Name: idx_upload_file_uploaded_at; Type: INDEX; Schema: log; Owner: -
--

CREATE INDEX idx_upload_file_uploaded_at ON log.upload_file USING btree (uploaded_at);


--
-- Name: ix_upload_file_hash_csv_time; Type: INDEX; Schema: log; Owner: -
--

CREATE INDEX ix_upload_file_hash_csv_time ON log.upload_file USING btree (file_hash, csv_type, uploaded_by, uploaded_at);


--
-- Name: idx_mv_sales_tree_daily_composite; Type: INDEX; Schema: mart; Owner: -
--

CREATE INDEX idx_mv_sales_tree_daily_composite ON mart.mv_sales_tree_daily USING btree (sales_date, rep_id, customer_id, item_id);


--
-- Name: idx_mv_sales_tree_daily_slip; Type: INDEX; Schema: mart; Owner: -
--

CREATE INDEX idx_mv_sales_tree_daily_slip ON mart.mv_sales_tree_daily USING btree (sales_date, customer_id, slip_no);


--
-- Name: ix_mv_target_card_per_day_iso_week; Type: INDEX; Schema: mart; Owner: -
--

CREATE INDEX ix_mv_target_card_per_day_iso_week ON mart.mv_target_card_per_day USING btree (iso_year, iso_week);


--
-- Name: mv_inb5y_week_profile_min_pk; Type: INDEX; Schema: mart; Owner: -
--

CREATE UNIQUE INDEX mv_inb5y_week_profile_min_pk ON mart.mv_inb5y_week_profile_min USING btree (iso_week);


--
-- Name: mv_inb_avg5y_day_biz_pk; Type: INDEX; Schema: mart; Owner: -
--

CREATE UNIQUE INDEX mv_inb_avg5y_day_biz_pk ON mart.mv_inb_avg5y_day_biz USING btree (iso_week, iso_dow);


--
-- Name: mv_inb_avg5y_weeksum_biz_pk; Type: INDEX; Schema: mart; Owner: -
--

CREATE UNIQUE INDEX mv_inb_avg5y_weeksum_biz_pk ON mart.mv_inb_avg5y_weeksum_biz USING btree (iso_week);


--
-- Name: ux_mv_inb_avg5y_day_scope; Type: INDEX; Schema: mart; Owner: -
--

CREATE UNIQUE INDEX ux_mv_inb_avg5y_day_scope ON mart.mv_inb_avg5y_day_scope USING btree (scope, iso_week, iso_dow);


--
-- Name: ux_mv_target_card_per_day_ddate; Type: INDEX; Schema: mart; Owner: -
--

CREATE UNIQUE INDEX ux_mv_target_card_per_day_ddate ON mart.mv_target_card_per_day USING btree (ddate);


--
-- Name: idx_shogun_final_receive_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_final_receive_upload_file_id ON raw.shogun_final_receive USING btree (upload_file_id);


--
-- Name: idx_shogun_final_shipment_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_final_shipment_upload_file_id ON raw.shogun_final_shipment USING btree (upload_file_id);


--
-- Name: idx_shogun_final_yard_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_final_yard_upload_file_id ON raw.shogun_final_yard USING btree (upload_file_id);


--
-- Name: idx_shogun_flash_receive_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_flash_receive_upload_file_id ON raw.shogun_flash_receive USING btree (upload_file_id);


--
-- Name: idx_shogun_flash_shipment_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_flash_shipment_upload_file_id ON raw.shogun_flash_shipment USING btree (upload_file_id);


--
-- Name: idx_shogun_flash_yard_upload_file_id; Type: INDEX; Schema: raw; Owner: -
--

CREATE INDEX idx_shogun_flash_yard_upload_file_id ON raw.shogun_flash_yard USING btree (upload_file_id);


--
-- Name: ix_calendar_day_date; Type: INDEX; Schema: ref; Owner: -
--

CREATE INDEX ix_calendar_day_date ON ref.calendar_day USING btree (ddate);


--
-- Name: ix_calendar_day_ym; Type: INDEX; Schema: ref; Owner: -
--

CREATE INDEX ix_calendar_day_ym ON ref.calendar_day USING btree (y, m);


--
-- Name: idx_king_invdate_func_no_filtered; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_king_invdate_func_no_filtered ON stg.receive_king_final USING btree (make_date((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 1))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer), invoice_no) WHERE ((vehicle_type_code = 1) AND (net_weight_detail <> 0) AND ((invoice_date)::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer <= 12)) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer <= 31)));


--
-- Name: idx_king_invdate_receiveno_cover; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_king_invdate_receiveno_cover ON stg.receive_king_final USING btree (make_date((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 1))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer, (split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer), invoice_no) INCLUDE (net_weight_detail, amount) WHERE ((vehicle_type_code = 1) AND (net_weight_detail <> 0) AND ((invoice_date)::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 2))::integer <= 12)) AND (((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer >= 1) AND ((split_part(replace((invoice_date)::text, '/'::text, '-'::text), '-'::text, 3))::integer <= 31)));


--
-- Name: idx_shogun_flash_receive_is_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_receive_is_deleted ON stg.shogun_flash_receive USING btree (is_deleted);


--
-- Name: idx_shogun_flash_receive_slip_date; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_receive_slip_date ON stg.shogun_flash_receive USING btree (slip_date);


--
-- Name: idx_shogun_flash_receive_upload; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_receive_upload ON stg.shogun_flash_receive USING btree (upload_file_id, source_row_no);


--
-- Name: idx_shogun_flash_receive_upload_file_id; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_receive_upload_file_id ON stg.shogun_flash_receive USING btree (upload_file_id);


--
-- Name: idx_shogun_flash_shipment_is_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_shipment_is_deleted ON stg.shogun_flash_shipment USING btree (is_deleted);


--
-- Name: idx_shogun_flash_shipment_slip_date; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_shipment_slip_date ON stg.shogun_flash_shipment USING btree (slip_date);


--
-- Name: idx_shogun_flash_shipment_upload; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_shipment_upload ON stg.shogun_flash_shipment USING btree (upload_file_id, source_row_no);


--
-- Name: idx_shogun_flash_shipment_upload_file_id; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_shipment_upload_file_id ON stg.shogun_flash_shipment USING btree (upload_file_id);


--
-- Name: idx_shogun_flash_yard_is_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_yard_is_deleted ON stg.shogun_flash_yard USING btree (is_deleted);


--
-- Name: idx_shogun_flash_yard_slip_date; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_yard_slip_date ON stg.shogun_flash_yard USING btree (slip_date);


--
-- Name: idx_shogun_flash_yard_upload; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_yard_upload ON stg.shogun_flash_yard USING btree (upload_file_id, source_row_no);


--
-- Name: idx_shogun_flash_yard_upload_file_id; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX idx_shogun_flash_yard_upload_file_id ON stg.shogun_flash_yard USING btree (upload_file_id);


--
-- Name: ix_shogun_flash_receive_upload_slip_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX ix_shogun_flash_receive_upload_slip_deleted ON stg.shogun_flash_receive USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: ix_shogun_flash_shipment_upload_slip_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX ix_shogun_flash_shipment_upload_slip_deleted ON stg.shogun_flash_shipment USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: ix_shogun_flash_yard_upload_slip_deleted; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX ix_shogun_flash_yard_upload_slip_deleted ON stg.shogun_flash_yard USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: shogun_final_receive_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_receive_is_deleted_idx ON stg.shogun_final_receive USING btree (is_deleted);


--
-- Name: shogun_final_receive_slip_date_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_receive_slip_date_idx ON stg.shogun_final_receive USING btree (slip_date);


--
-- Name: shogun_final_receive_upload_file_id_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_receive_upload_file_id_idx ON stg.shogun_final_receive USING btree (upload_file_id);


--
-- Name: shogun_final_receive_upload_file_id_slip_date_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_receive_upload_file_id_slip_date_is_deleted_idx ON stg.shogun_final_receive USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: shogun_final_receive_upload_file_id_source_row_no_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_receive_upload_file_id_source_row_no_idx ON stg.shogun_final_receive USING btree (upload_file_id, source_row_no);


--
-- Name: shogun_final_shipment_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_shipment_is_deleted_idx ON stg.shogun_final_shipment USING btree (is_deleted);


--
-- Name: shogun_final_shipment_slip_date_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_shipment_slip_date_idx ON stg.shogun_final_shipment USING btree (slip_date);


--
-- Name: shogun_final_shipment_upload_file_id_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_shipment_upload_file_id_idx ON stg.shogun_final_shipment USING btree (upload_file_id);


--
-- Name: shogun_final_shipment_upload_file_id_slip_date_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_shipment_upload_file_id_slip_date_is_deleted_idx ON stg.shogun_final_shipment USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: shogun_final_shipment_upload_file_id_source_row_no_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_shipment_upload_file_id_source_row_no_idx ON stg.shogun_final_shipment USING btree (upload_file_id, source_row_no);


--
-- Name: shogun_final_yard_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_yard_is_deleted_idx ON stg.shogun_final_yard USING btree (is_deleted);


--
-- Name: shogun_final_yard_slip_date_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_yard_slip_date_idx ON stg.shogun_final_yard USING btree (slip_date);


--
-- Name: shogun_final_yard_upload_file_id_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_yard_upload_file_id_idx ON stg.shogun_final_yard USING btree (upload_file_id);


--
-- Name: shogun_final_yard_upload_file_id_slip_date_is_deleted_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_yard_upload_file_id_slip_date_is_deleted_idx ON stg.shogun_final_yard USING btree (upload_file_id, slip_date, is_deleted);


--
-- Name: shogun_final_yard_upload_file_id_source_row_no_idx; Type: INDEX; Schema: stg; Owner: -
--

CREATE INDEX shogun_final_yard_upload_file_id_source_row_no_idx ON stg.shogun_final_yard USING btree (upload_file_id, source_row_no);


--
-- Name: inbound_forecast_daily inbound_forecast_daily_run_id_fkey; Type: FK CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_daily
    ADD CONSTRAINT inbound_forecast_daily_run_id_fkey FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id);


--
-- Name: inbound_forecast_monthly_raw inbound_forecast_monthly_raw_run_id_fkey; Type: FK CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_monthly_raw
    ADD CONSTRAINT inbound_forecast_monthly_raw_run_id_fkey FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id);


--
-- Name: inbound_forecast_weekly_raw inbound_forecast_weekly_raw_run_id_fkey; Type: FK CONSTRAINT; Schema: forecast; Owner: -
--

ALTER TABLE ONLY forecast.inbound_forecast_weekly_raw
    ADD CONSTRAINT inbound_forecast_weekly_raw_run_id_fkey FOREIGN KEY (run_id) REFERENCES forecast.inbound_forecast_run(run_id);


--
-- Name: monthly_targets fk_kpi_month; Type: FK CONSTRAINT; Schema: kpi; Owner: -
--

ALTER TABLE ONLY kpi.monthly_targets
    ADD CONSTRAINT fk_kpi_month FOREIGN KEY (month_date) REFERENCES ref.calendar_month(month_date);


--
-- Name: calendar_exception fk_cal_exception_day; Type: FK CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT fk_cal_exception_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);


--
-- Name: closure_membership fk_cm_day; Type: FK CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);


--
-- Name: closure_membership fk_cm_span; Type: FK CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_span FOREIGN KEY (start_date, end_date) REFERENCES ref.closure_periods(start_date, end_date);


--
-- Name: holiday_jp fk_holiday_day; Type: FK CONSTRAINT; Schema: ref; Owner: -
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT fk_holiday_day FOREIGN KEY (hdate) REFERENCES ref.calendar_day(ddate);


--
-- PostgreSQL database dump complete
--

\unrestrict 1tqERPZTUdvMTRz0xpYDWPBycghbcOrKq4vA4CJD2gw0XGcaexVyFsvpWnqzZ1k
