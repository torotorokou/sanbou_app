--
-- PostgreSQL database dump
--

\restrict HtICLgrzOMgMqniD703vSJCSvwSiONMAu3i3mWr9Duk78Ok1rIWmaGsbVVtgWTC

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
-- PostgreSQL database dump complete
--

\unrestrict HtICLgrzOMgMqniD703vSJCSvwSiONMAu3i3mWr9Duk78Ok1rIWmaGsbVVtgWTC

