




CREATE OR REPLACE VIEW mart.v_receive_monthly AS
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
