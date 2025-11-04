






CREATE TABLE ref.calendar_day (
    ddate date NOT NULL,
    y integer GENERATED ALWAYS AS ((EXTRACT(year FROM ddate))::integer) STORED,
    m integer GENERATED ALWAYS AS ((EXTRACT(month FROM ddate))::integer) STORED,
    iso_year integer GENERATED ALWAYS AS ((EXTRACT(isoyear FROM ddate))::integer) STORED,
    iso_week integer GENERATED ALWAYS AS ((EXTRACT(week FROM ddate))::integer) STORED,
    iso_dow integer GENERATED ALWAYS AS ((EXTRACT(isodow FROM ddate))::integer) STORED
);




ALTER TABLE ONLY ref.calendar_day
    ADD CONSTRAINT calendar_day_pkey PRIMARY KEY (ddate);



CREATE INDEX ix_calendar_day_date ON ref.calendar_day USING btree (ddate);



CREATE INDEX ix_calendar_day_ym ON ref.calendar_day USING btree (y, m);




