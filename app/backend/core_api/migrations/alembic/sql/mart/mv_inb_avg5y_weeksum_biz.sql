






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




COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_weeksum_biz IS '5y weekly sum (business Mon–Sat, holidays excluded): AVG/STD across years by iso_week. iso_dow=0 sentinel.';







