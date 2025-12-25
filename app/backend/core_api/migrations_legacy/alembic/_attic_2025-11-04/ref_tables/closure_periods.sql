






CREATE TABLE ref.closure_periods (
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL,
    CONSTRAINT closure_periods_check CHECK ((start_date <= end_date))
);




ALTER TABLE ONLY ref.closure_periods
    ADD CONSTRAINT closure_periods_pkey PRIMARY KEY (start_date, end_date);
