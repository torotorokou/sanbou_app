






CREATE TABLE ref.holiday_jp (
    hdate date NOT NULL,
    name text NOT NULL
);




ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT holiday_jp_pkey PRIMARY KEY (hdate);



ALTER TABLE ONLY ref.holiday_jp
    ADD CONSTRAINT fk_holiday_day FOREIGN KEY (hdate) REFERENCES ref.calendar_day(ddate);




