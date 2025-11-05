




CREATE OR REPLACE VIEW mart.v_receive_weekly AS
 WITH w AS (
         SELECT d.iso_year,
            d.iso_week,
            min(d.ddate) AS week_start_date,
            max(d.ddate) AS week_end_date,
            (sum(d.receive_net_ton))::numeric(18,3) AS receive_net_ton,
            sum(d.receive_vehicle_count) AS receive_vehicle_count,
            (sum(d.sales_yen))::numeric(18,0) AS sales_yen
           FROM mart.receive_daily d
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





