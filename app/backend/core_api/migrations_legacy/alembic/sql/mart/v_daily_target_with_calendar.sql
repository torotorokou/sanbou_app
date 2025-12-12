




CREATE OR REPLACE VIEW mart.v_daily_target_with_calendar AS
 SELECT c.ddate,
    c.iso_year,
    c.iso_week,
    c.iso_dow,
    c.day_type,
    c.is_business,
    p.target_ton,
    p.scope_used,
    p.created_at
   FROM (ref.v_calendar_classified c
     LEFT JOIN mart.daily_target_plan p ON ((c.ddate = p.ddate)));





