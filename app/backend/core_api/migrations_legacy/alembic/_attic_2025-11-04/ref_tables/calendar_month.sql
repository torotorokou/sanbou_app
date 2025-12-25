






CREATE TABLE ref.calendar_month (
    month_date date NOT NULL
);




ALTER TABLE ONLY ref.calendar_month
    ADD CONSTRAINT calendar_month_pkey PRIMARY KEY (month_date);
