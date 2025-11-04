






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




COMMENT ON MATERIALIZED VIEW mart.mv_inb5y_week_profile_min IS '5y weekly profile (minimal): normal_day_mean (NORMAL), reservation_day_mean (RESERVATION=Sun+Holiday).';



CREATE UNIQUE INDEX mv_inb5y_week_profile_min_pk ON mart.mv_inb5y_week_profile_min USING btree (iso_week);




