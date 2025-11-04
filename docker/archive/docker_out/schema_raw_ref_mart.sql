--
-- PostgreSQL database dump
--

\restrict rf10zC12U1fpihZDMwxsWKZFpBn8a7ipa14lJgyAupazH3jfJ6nqaobQqHZ3kva

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
-- Name: mart; Type: SCHEMA; Schema: -; Owner: myuser
--

CREATE SCHEMA mart;


ALTER SCHEMA mart OWNER TO myuser;

--
-- Name: raw; Type: SCHEMA; Schema: -; Owner: myuser
--

CREATE SCHEMA raw;


ALTER SCHEMA raw OWNER TO myuser;

--
-- Name: ref; Type: SCHEMA; Schema: -; Owner: myuser
--

CREATE SCHEMA ref;


ALTER SCHEMA ref OWNER TO myuser;

--
-- Name: refresh_inb5y(); Type: FUNCTION; Schema: mart; Owner: myuser
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


ALTER FUNCTION mart.refresh_inb5y() OWNER TO myuser;

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
-- Name: receive_shogun_final; Type: TABLE; Schema: raw; Owner: myuser
--

CREATE TABLE raw.receive_shogun_final (
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


ALTER TABLE raw.receive_shogun_final OWNER TO myuser;

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
-- Name: closure_periods; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.closure_periods (
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL,
    CONSTRAINT closure_periods_check CHECK ((start_date <= end_date))
);


ALTER TABLE ref.closure_periods OWNER TO myuser;

--
-- Name: holiday_jp; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.holiday_jp (
    hdate date NOT NULL,
    name text NOT NULL
);


ALTER TABLE ref.holiday_jp OWNER TO myuser;

--
-- Name: v_closure_days; Type: VIEW; Schema: ref; Owner: myuser
--

CREATE VIEW ref.v_closure_days AS
 SELECT (g.g)::date AS ddate,
    p.closure_name
   FROM ref.closure_periods p,
    LATERAL generate_series((p.start_date)::timestamp with time zone, (p.end_date)::timestamp with time zone, '1 day'::interval) g(g);


ALTER VIEW ref.v_closure_days OWNER TO myuser;

--
-- Name: v_calendar_classified; Type: VIEW; Schema: ref; Owner: myuser
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


ALTER VIEW ref.v_calendar_classified OWNER TO myuser;

--
-- Name: receive_daily; Type: VIEW; Schema: mart; Owner: myuser
--

CREATE VIEW mart.receive_daily AS
 WITH r_shogun_final AS (
         SELECT s.slip_date AS ddate,
            (sum(s.net_weight) / 1000.0) AS receive_ton,
            count(DISTINCT s.receive_no) AS vehicle_count,
            sum(s.amount) AS sales_yen
           FROM raw.receive_shogun_final s
          WHERE (s.slip_date IS NOT NULL)
          GROUP BY s.slip_date
        ), r_shogun_flash AS (
         SELECT f.slip_date AS ddate,
            (sum(f.net_weight) / 1000.0) AS receive_ton,
            count(DISTINCT f.receive_no) AS vehicle_count,
            sum(f.amount) AS sales_yen
           FROM raw.receive_shogun_flash f
          WHERE (f.slip_date IS NOT NULL)
          GROUP BY f.slip_date
        ), r_king AS (
         SELECT (k.invoice_date)::date AS ddate,
            ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
            count(DISTINCT k.invoice_no) AS vehicle_count,
            (sum(k.amount))::numeric AS sales_yen
           FROM raw.receive_king_final k
          WHERE ((k.vehicle_type_code = 1) AND (k.net_weight_detail <> 0))
          GROUP BY (k.invoice_date)::date
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
            'shogun_flash'::text AS text
           FROM r_shogun_flash f
          WHERE (NOT (EXISTS ( SELECT 1
                   FROM r_shogun_final s
                  WHERE (s.ddate = f.ddate))))
        UNION ALL
         SELECT k.ddate,
            k.receive_ton,
            k.vehicle_count,
            k.sales_yen,
            'king'::text AS text
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


ALTER VIEW mart.receive_daily OWNER TO myuser;

--
-- Name: mv_inb5y_week_profile_min; Type: MATERIALIZED VIEW; Schema: mart; Owner: myuser
--

CREATE MATERIALIZED VIEW mart.mv_inb5y_week_profile_min AS
 WITH normal AS (
         SELECT receive_daily.iso_week,
            avg(receive_daily.receive_net_ton) AS normal_day_mean,
            count(*) AS n_normal
           FROM mart.receive_daily
          WHERE ((receive_daily.ddate >= (CURRENT_DATE - '5 years'::interval)) AND (receive_daily.is_business = true) AND (receive_daily.day_type = 'NORMAL'::text) AND (receive_daily.receive_net_ton IS NOT NULL))
          GROUP BY receive_daily.iso_week
        ), resv_samples AS (
         SELECT d.iso_week,
            (d.receive_net_ton / NULLIF(n_1.normal_day_mean, (0)::numeric)) AS r
           FROM (mart.receive_daily d
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


ALTER MATERIALIZED VIEW mart.mv_inb5y_week_profile_min OWNER TO myuser;

--
-- Name: MATERIALIZED VIEW mv_inb5y_week_profile_min; Type: COMMENT; Schema: mart; Owner: myuser
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb5y_week_profile_min IS '5y weekly profile (minimal): normal_day_mean (NORMAL), reservation_day_mean (RESERVATION=Sun+Holiday).';


--
-- Name: mv_inb_avg5y_day_biz; Type: MATERIALIZED VIEW; Schema: mart; Owner: myuser
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz AS
 WITH agg AS (
         SELECT receive_daily.iso_week,
            receive_daily.iso_dow,
            avg(receive_daily.receive_net_ton) AS ave_wd,
            stddev_samp(receive_daily.receive_net_ton) AS sigma_wd,
            count(*) AS n_wd
           FROM mart.receive_daily
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


ALTER MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz OWNER TO myuser;

--
-- Name: MATERIALIZED VIEW mv_inb_avg5y_day_biz; Type: COMMENT; Schema: mart; Owner: myuser
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz IS '5y avg inbound/day (business Mon–Sat, holidays excluded) by (iso_week, iso_dow).';


--
-- Name: mv_inb_avg5y_day_scope; Type: MATERIALIZED VIEW; Schema: mart; Owner: myuser
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope AS
 WITH base AS (
         SELECT r.ddate,
            r.iso_week,
            r.iso_dow,
            r.is_business,
            r.is_holiday,
            (r.receive_net_ton)::numeric AS y
           FROM mart.receive_daily r
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


ALTER MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope OWNER TO myuser;

--
-- Name: mv_inb_avg5y_weeksum_biz; Type: MATERIALIZED VIEW; Schema: mart; Owner: myuser
--

CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz AS
 WITH week_year AS (
         SELECT receive_daily.iso_year,
            receive_daily.iso_week,
            sum(receive_daily.receive_net_ton) AS week_sum_biz
           FROM mart.receive_daily
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


ALTER MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz OWNER TO myuser;

--
-- Name: MATERIALIZED VIEW mv_inb_avg5y_weeksum_biz; Type: COMMENT; Schema: mart; Owner: myuser
--

COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz IS '5y weekly sum (business Mon–Sat, holidays excluded): AVG/STD across years by iso_week. iso_dow=0 sentinel.';


--
-- Name: receive_monthly; Type: VIEW; Schema: mart; Owner: myuser
--

CREATE VIEW mart.receive_monthly AS
 WITH d AS (
         SELECT receive_daily.ddate,
            receive_daily.y,
            receive_daily.m,
            receive_daily.receive_net_ton,
            receive_daily.receive_vehicle_count,
            receive_daily.sales_yen
           FROM mart.receive_daily
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


ALTER VIEW mart.receive_monthly OWNER TO myuser;

--
-- Name: receive_weekly; Type: VIEW; Schema: mart; Owner: myuser
--

CREATE VIEW mart.receive_weekly AS
 WITH w AS (
         SELECT receive_daily.iso_year,
            receive_daily.iso_week,
            min(receive_daily.ddate) AS week_start_date,
            max(receive_daily.ddate) AS week_end_date,
            (sum(receive_daily.receive_net_ton))::numeric(18,3) AS receive_net_ton,
            sum(receive_daily.receive_vehicle_count) AS receive_vehicle_count,
            (sum(receive_daily.sales_yen))::numeric(18,0) AS sales_yen
           FROM mart.receive_daily
          GROUP BY receive_daily.iso_year, receive_daily.iso_week
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


ALTER VIEW mart.receive_weekly OWNER TO myuser;

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
-- Name: v_target_card_per_day; Type: VIEW; Schema: mart; Owner: myuser
--

CREATE VIEW mart.v_target_card_per_day AS
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
           FROM mart.receive_daily r
          GROUP BY r.iso_year, r.iso_week
        ), month_actual AS (
         SELECT (date_trunc('month'::text, (r.ddate)::timestamp with time zone))::date AS month_key,
            sum(COALESCE(r.receive_net_ton, (0)::numeric)) AS month_actual_ton
           FROM mart.receive_daily r
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
     LEFT JOIN mart.receive_daily rprev ON ((rprev.ddate = (b.ddate - '1 day'::interval))))
  ORDER BY b.ddate;


ALTER VIEW mart.v_target_card_per_day OWNER TO myuser;

--
-- Name: calendar_month; Type: TABLE; Schema: ref; Owner: myuser
--

CREATE TABLE ref.calendar_month (
    month_date date NOT NULL
);


ALTER TABLE ref.calendar_month OWNER TO myuser;

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
-- Name: inb_profile_smooth_test inb_profile_smooth_test_pkey; Type: CONSTRAINT; Schema: mart; Owner: myuser
--

ALTER TABLE ONLY mart.inb_profile_smooth_test
    ADD CONSTRAINT inb_profile_smooth_test_pkey PRIMARY KEY (scope, iso_week, iso_dow);


--
-- Name: calendar_day calendar_day_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_day
    ADD CONSTRAINT calendar_day_pkey PRIMARY KEY (ddate);


--
-- Name: calendar_exception calendar_exception_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT calendar_exception_pkey PRIMARY KEY (ddate);


--
-- Name: calendar_month calendar_month_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_month
    ADD CONSTRAINT calendar_month_pkey PRIMARY KEY (month_date);


--
-- Name: closure_membership closure_membership_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT closure_membership_pkey PRIMARY KEY (ddate);


--
-- Name: closure_periods closure_periods_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.closure_periods
    ADD CONSTRAINT closure_periods_pkey PRIMARY KEY (start_date, end_date);


--
-- Name: holiday_jp holiday_jp_pkey; Type: CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT holiday_jp_pkey PRIMARY KEY (hdate);


--
-- Name: mv_inb5y_week_profile_min_pk; Type: INDEX; Schema: mart; Owner: myuser
--

CREATE UNIQUE INDEX mv_inb5y_week_profile_min_pk ON mart.mv_inb5y_week_profile_min USING btree (iso_week);


--
-- Name: mv_inb_avg5y_day_biz_pk; Type: INDEX; Schema: mart; Owner: myuser
--

CREATE UNIQUE INDEX mv_inb_avg5y_day_biz_pk ON mart.mv_inb_avg5y_day_biz USING btree (iso_week, iso_dow);


--
-- Name: mv_inb_avg5y_weeksum_biz_pk; Type: INDEX; Schema: mart; Owner: myuser
--

CREATE UNIQUE INDEX mv_inb_avg5y_weeksum_biz_pk ON mart.mv_inb_avg5y_weeksum_biz USING btree (iso_week);


--
-- Name: ux_mv_inb_avg5y_day_scope; Type: INDEX; Schema: mart; Owner: myuser
--

CREATE UNIQUE INDEX ux_mv_inb_avg5y_day_scope ON mart.mv_inb_avg5y_day_scope USING btree (scope, iso_week, iso_dow);


--
-- Name: idx_shogun_final_slip_date; Type: INDEX; Schema: raw; Owner: myuser
--

CREATE INDEX idx_shogun_final_slip_date ON raw.receive_shogun_final USING btree (slip_date);


--
-- Name: idx_shogun_flash_slip_date; Type: INDEX; Schema: raw; Owner: myuser
--

CREATE INDEX idx_shogun_flash_slip_date ON raw.receive_shogun_flash USING btree (slip_date);


--
-- Name: ix_calendar_day_date; Type: INDEX; Schema: ref; Owner: myuser
--

CREATE INDEX ix_calendar_day_date ON ref.calendar_day USING btree (ddate);


--
-- Name: ix_calendar_day_ym; Type: INDEX; Schema: ref; Owner: myuser
--

CREATE INDEX ix_calendar_day_ym ON ref.calendar_day USING btree (y, m);


--
-- Name: receive_shogun_final fk_shogun_final_ddate; Type: FK CONSTRAINT; Schema: raw; Owner: myuser
--

ALTER TABLE ONLY raw.receive_shogun_final
    ADD CONSTRAINT fk_shogun_final_ddate FOREIGN KEY (slip_date) REFERENCES ref.calendar_day(ddate);


--
-- Name: receive_shogun_flash fk_shogun_flash_ddate; Type: FK CONSTRAINT; Schema: raw; Owner: myuser
--

ALTER TABLE ONLY raw.receive_shogun_flash
    ADD CONSTRAINT fk_shogun_flash_ddate FOREIGN KEY (slip_date) REFERENCES ref.calendar_day(ddate);


--
-- Name: calendar_exception fk_cal_exception_day; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT fk_cal_exception_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);


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
-- Name: holiday_jp fk_holiday_day; Type: FK CONSTRAINT; Schema: ref; Owner: myuser
--

ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT fk_holiday_day FOREIGN KEY (hdate) REFERENCES ref.calendar_day(ddate);


--
-- PostgreSQL database dump complete
--

\unrestrict rf10zC12U1fpihZDMwxsWKZFpBn8a7ipa14lJgyAupazH3jfJ6nqaobQqHZ3kva

