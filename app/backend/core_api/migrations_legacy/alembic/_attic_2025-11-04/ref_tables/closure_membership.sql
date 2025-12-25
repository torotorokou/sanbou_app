






CREATE TABLE ref.closure_membership (
    ddate date NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    closure_name text NOT NULL
);




ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT closure_membership_pkey PRIMARY KEY (ddate);



ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);



ALTER TABLE ONLY ref.closure_membership
    ADD CONSTRAINT fk_cm_span FOREIGN KEY (start_date, end_date) REFERENCES ref.closure_periods(start_date, end_date);
