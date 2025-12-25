"""allow_today_receive_mv

Revision ID: 20251224_006
Revises: 20251224_005
Create Date: 2024-12-24

Include the current date in mart.mv_receive_daily so that same-day receive uploads
are reflected immediately. The previous definition stopped at yesterday, causing
"today" rows to be invisible in dashboards and downstream MVs.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251224_006"
down_revision = "20251224_005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop dependents first to allow recreating mv_receive_daily
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_target_card_per_day;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_weekly;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_monthly;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_daily;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily;")

    # Recreate mv_receive_daily with the inclusive (<= today) date filter
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
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
                 SELECT (k.invoice_date)::date AS ddate,
                    ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
                    count(DISTINCT k.invoice_no) AS vehicle_count,
                    (sum(k.amount))::numeric AS sales_yen
                   FROM stg.receive_king_final k
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
          WHERE (cal.ddate <= ((now() AT TIME ZONE 'Asia/Tokyo'::text))::date)
          ORDER BY cal.ddate
          WITH NO DATA;
        """
    )

    # Populate and index the MV
    op.execute("REFRESH MATERIALIZED VIEW mart.mv_receive_daily;")
    op.execute(
        "CREATE INDEX ix_mv_receive_daily_iso_week ON mart.mv_receive_daily USING btree (iso_year, iso_week);"
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_mv_receive_daily_ddate ON mart.mv_receive_daily USING btree (ddate);"
    )

    # Recreate mv_target_card_per_day (depends on mv_receive_daily)
    op.execute(
        """
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
                   FROM mart.mv_receive_daily r
                  GROUP BY r.iso_year, r.iso_week
                ), month_actual AS (
                 SELECT (date_trunc('month'::text, (r.ddate)::timestamp with time zone))::date AS month_key,
                    sum(COALESCE(r.receive_net_ton, (0)::numeric)) AS month_actual_ton
                   FROM mart.mv_receive_daily r
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
             LEFT JOIN mart.mv_receive_daily rprev ON ((rprev.ddate = (b.ddate - '1 day'::interval))))
          ORDER BY b.ddate
          WITH NO DATA;
        """
    )

    op.execute("REFRESH MATERIALIZED VIEW mart.mv_target_card_per_day;")
    op.execute(
        "CREATE INDEX ix_mv_target_card_per_day_iso_week ON mart.mv_target_card_per_day USING btree (iso_year, iso_week);"
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_mv_target_card_per_day_ddate ON mart.mv_target_card_per_day USING btree (ddate);"
    )

    # Recreate simple views that expose the MV data
    op.execute(
        """
        CREATE VIEW mart.v_receive_daily AS
         SELECT ddate,
            y,
            m,
            iso_year,
            iso_week,
            iso_dow,
            is_business,
            is_holiday,
            day_type,
            receive_net_ton,
            receive_vehicle_count,
            avg_weight_kg_per_vehicle,
            sales_yen,
            unit_price_yen_per_kg,
            source_system
           FROM mart.mv_receive_daily;
        """
    )

    op.execute(
        """
        CREATE VIEW mart.v_receive_monthly AS
         SELECT y,
            m,
            min(ddate) AS month_start,
            max(ddate) AS month_end,
            sum(receive_net_ton) AS receive_net_ton,
            sum(receive_vehicle_count) AS receive_vehicle_count,
            sum(sales_yen) AS sales_yen,
            count(*) FILTER (WHERE (is_business = true)) AS business_days,
            count(*) AS total_days
           FROM mart.mv_receive_daily
          GROUP BY y, m
          ORDER BY y, m;
        """
    )

    op.execute(
        """
        CREATE VIEW mart.v_receive_weekly AS
         SELECT iso_year,
            iso_week,
            min(ddate) AS week_start,
            max(ddate) AS week_end,
            sum(receive_net_ton) AS receive_net_ton,
            sum(receive_vehicle_count) AS receive_vehicle_count,
            sum(sales_yen) AS sales_yen,
            count(*) FILTER (WHERE (is_business = true)) AS business_days,
            count(*) AS total_days
           FROM mart.mv_receive_daily
          GROUP BY iso_year, iso_week
          ORDER BY iso_year, iso_week;
        """
    )

    # Restore minimal grants so the current DB user retains access
    op.execute(
        "GRANT SELECT ON mart.mv_receive_daily, mart.mv_target_card_per_day, "
        "mart.v_receive_daily, mart.v_receive_monthly, mart.v_receive_weekly TO CURRENT_USER;"
    )


def downgrade() -> None:
    # Drop dependents before reverting the MV definition
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_target_card_per_day;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_weekly;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_monthly;")
    op.execute("DROP VIEW IF EXISTS mart.v_receive_daily;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mart.mv_receive_daily;")

    # Recreate the previous (<= yesterday) mv_receive_daily definition
    op.execute(
        """
        CREATE MATERIALIZED VIEW mart.mv_receive_daily AS
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
                 SELECT (k.invoice_date)::date AS ddate,
                    ((sum(k.net_weight_detail))::numeric / 1000.0) AS receive_ton,
                    count(DISTINCT k.invoice_no) AS vehicle_count,
                    (sum(k.amount))::numeric AS sales_yen
                   FROM stg.receive_king_final k
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
          ORDER BY cal.ddate
          WITH NO DATA;
        """
    )

    op.execute("REFRESH MATERIALIZED VIEW mart.mv_receive_daily;")
    op.execute(
        "CREATE INDEX ix_mv_receive_daily_iso_week ON mart.mv_receive_daily USING btree (iso_year, iso_week);"
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_mv_receive_daily_ddate ON mart.mv_receive_daily USING btree (ddate);"
    )

    # Recreate mv_target_card_per_day in its original form
    op.execute(
        """
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
                   FROM mart.mv_receive_daily r
                  GROUP BY r.iso_year, r.iso_week
                ), month_actual AS (
                 SELECT (date_trunc('month'::text, (r.ddate)::timestamp with time zone))::date AS month_key,
                    sum(COALESCE(r.receive_net_ton, (0)::numeric)) AS month_actual_ton
                   FROM mart.mv_receive_daily r
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
             LEFT JOIN mart.mv_receive_daily rprev ON ((rprev.ddate = (b.ddate - '1 day'::interval))))
          ORDER BY b.ddate
          WITH NO DATA;
        """
    )

    op.execute("REFRESH MATERIALIZED VIEW mart.mv_target_card_per_day;")
    op.execute(
        "CREATE INDEX ix_mv_target_card_per_day_iso_week ON mart.mv_target_card_per_day USING btree (iso_year, iso_week);"
    )
    op.execute(
        "CREATE UNIQUE INDEX ux_mv_target_card_per_day_ddate ON mart.mv_target_card_per_day USING btree (ddate);"
    )

    # Recreate the dependent views
    op.execute(
        """
        CREATE VIEW mart.v_receive_daily AS
         SELECT ddate,
            y,
            m,
            iso_year,
            iso_week,
            iso_dow,
            is_business,
            is_holiday,
            day_type,
            receive_net_ton,
            receive_vehicle_count,
            avg_weight_kg_per_vehicle,
            sales_yen,
            unit_price_yen_per_kg,
            source_system
           FROM mart.mv_receive_daily;
        """
    )

    op.execute(
        """
        CREATE VIEW mart.v_receive_monthly AS
         SELECT y,
            m,
            min(ddate) AS month_start,
            max(ddate) AS month_end,
            sum(receive_net_ton) AS receive_net_ton,
            sum(receive_vehicle_count) AS receive_vehicle_count,
            sum(sales_yen) AS sales_yen,
            count(*) FILTER (WHERE (is_business = true)) AS business_days,
            count(*) AS total_days
           FROM mart.mv_receive_daily
          GROUP BY y, m
          ORDER BY y, m;
        """
    )

    op.execute(
        """
        CREATE VIEW mart.v_receive_weekly AS
         SELECT iso_year,
            iso_week,
            min(ddate) AS week_start,
            max(ddate) AS week_end,
            sum(receive_net_ton) AS receive_net_ton,
            sum(receive_vehicle_count) AS receive_vehicle_count,
            sum(sales_yen) AS sales_yen,
            count(*) FILTER (WHERE (is_business = true)) AS business_days,
            count(*) AS total_days
           FROM mart.mv_receive_daily
          GROUP BY iso_year, iso_week
          ORDER BY iso_year, iso_week;
        """
    )

    op.execute(
        "GRANT SELECT ON mart.mv_receive_daily, mart.mv_target_card_per_day, "
        "mart.v_receive_daily, mart.v_receive_monthly, mart.v_receive_weekly TO CURRENT_USER;"
    )
