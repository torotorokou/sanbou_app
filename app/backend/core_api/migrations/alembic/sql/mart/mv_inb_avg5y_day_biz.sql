






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




COMMENT ON MATERIALIZED VIEW mart.mv_inb_avg5y_day_biz IS '5y avg inbound/day (business Mon–Sat, holidays excluded) by (iso_week, iso_dow).';



CREATE UNIQUE INDEX mv_inb_avg5y_day_biz_pk ON mart.mv_inb_avg5y_day_biz USING btree (iso_week, iso_dow);




