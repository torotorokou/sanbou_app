




CREATE OR REPLACE VIEW ref.v_closure_days AS
 SELECT (g.g)::date AS ddate,
    p.closure_name
   FROM ref.closure_periods p,
    LATERAL generate_series((p.start_date)::timestamp with time zone, (p.end_date)::timestamp with time zone, '1 day'::interval) g(g);





