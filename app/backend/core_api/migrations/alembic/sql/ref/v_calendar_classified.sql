




CREATE OR REPLACE VIEW ref.v_calendar_classified AS
 WITH sundays AS (
         SELECT calendar_day.ddate,
            calendar_day.y,
            calendar_day.m,
            row_number() OVER (PARTITION BY calendar_day.y, calendar_day.m ORDER BY calendar_day.ddate) AS sunday_idx
           FROM ref.calendar_day
          WHERE (calendar_day.iso_dow = 7)
        ), second_sunday AS (
         SELECT sundays.ddate,
            true AS is_second_sunday
           FROM sundays
          WHERE (sundays.sunday_idx = 2)
        ), holiday AS (
         SELECT holiday_jp.hdate AS ddate,
            true AS is_holiday
           FROM ref.holiday_jp
        ), closure AS (
         SELECT v_closure_days.ddate,
            true AS is_company_closed
           FROM ref.v_closure_days
        ), ex AS (
         SELECT calendar_exception.ddate,
            calendar_exception.override_type
           FROM ref.calendar_exception
        ), base AS (
         SELECT c.ddate,
            c.y,
            c.m,
            c.iso_year,
            c.iso_week,
            c.iso_dow,
            COALESCE(h.is_holiday, false) AS is_holiday,
            COALESCE(ss.is_second_sunday, false) AS is_second_sunday,
            COALESCE(cl.is_company_closed, false) AS is_company_closed,
                CASE
                    WHEN (COALESCE(cl.is_company_closed, false) OR COALESCE(ss.is_second_sunday, false)) THEN 'CLOSED'::text
                    WHEN ((c.iso_dow = 7) OR COALESCE(h.is_holiday, false)) THEN 'RESERVATION'::text
                    ELSE 'NORMAL'::text
                END AS base_day_type,
                CASE
                    WHEN (COALESCE(cl.is_company_closed, false) OR COALESCE(ss.is_second_sunday, false)) THEN false
                    ELSE true
                END AS base_is_business
           FROM (((ref.calendar_day c
             LEFT JOIN holiday h ON ((h.ddate = c.ddate)))
             LEFT JOIN second_sunday ss ON ((ss.ddate = c.ddate)))
             LEFT JOIN closure cl ON ((cl.ddate = c.ddate)))
        )
 SELECT b.ddate,
    b.y,
    b.m,
    b.iso_year,
    b.iso_week,
    b.iso_dow,
    b.is_holiday,
    b.is_second_sunday,
    b.is_company_closed,
        CASE ex.override_type
            WHEN 'FORCE_CLOSED'::text THEN 'CLOSED'::text
            WHEN 'FORCE_OPEN'::text THEN 'NORMAL'::text
            WHEN 'FORCE_RESERVATION'::text THEN 'RESERVATION'::text
            ELSE b.base_day_type
        END AS day_type,
        CASE ex.override_type
            WHEN 'FORCE_CLOSED'::text THEN false
            WHEN 'FORCE_OPEN'::text THEN true
            WHEN 'FORCE_RESERVATION'::text THEN true
            ELSE b.base_is_business
        END AS is_business
   FROM (base b
     LEFT JOIN ex ON ((ex.ddate = b.ddate)))
  ORDER BY b.ddate;





