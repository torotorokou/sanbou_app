






CREATE MATERIALIZED VIEW mart.mv_inb_avg5y_day_scope AS
 WITH base AS (
         SELECT r.ddate,
            r.iso_week,
            r.iso_dow,
            r.is_business,
            r.is_holiday,
            (r.receive_net_ton)::numeric AS y
           FROM mart.mv_receive_daily r
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








