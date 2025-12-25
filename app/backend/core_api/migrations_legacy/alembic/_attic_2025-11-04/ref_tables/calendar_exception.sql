






CREATE TABLE ref.calendar_exception (
    ddate date NOT NULL,
    override_type text NOT NULL,
    reason text,
    updated_by text,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT calendar_exception_override_type_check CHECK ((override_type = ANY (ARRAY['FORCE_CLOSED'::text, 'FORCE_OPEN'::text, 'FORCE_RESERVATION'::text])))
);




ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT calendar_exception_pkey PRIMARY KEY (ddate);



ALTER TABLE ONLY ref.calendar_exception
    ADD CONSTRAINT fk_cal_exception_day FOREIGN KEY (ddate) REFERENCES ref.calendar_day(ddate);
