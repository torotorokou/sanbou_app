




CREATE OR REPLACE VIEW mart.v_target_card_per_day AS
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
  ORDER BY b.ddate;





