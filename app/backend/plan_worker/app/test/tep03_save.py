# /backend/app/test/step03_save.py
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import psycopg
from common import _dsn

IN = Path("/backend/app/test/out/smooth_preview.csv")
PARAMS = {"tau_base": 12.0, "lambda": 1.5, "cv_cap": 1.0, "h": 2, "kernel": "tri"}

DDL = """
create table if not exists mart.inb_profile_smooth_test (
  scope text not null,
  iso_week int not null,
  iso_dow  int not null,
  day_mean_smooth numeric(14,4) not null,
  method text not null,
  params jsonb not null,
  updated_at timestamptz not null default now(),
  primary key(scope, iso_week, iso_dow)
);
"""

UPSERT = """
insert into mart.inb_profile_smooth_test
  (scope, iso_week, iso_dow, day_mean_smooth, method, params)
values (%s,%s,%s,%s,%s,%s)
on conflict (scope, iso_week, iso_dow) do update
  set day_mean_smooth = excluded.day_mean_smooth,
      method = excluded.method,
      params = excluded.params,
      updated_at = now();
"""


def main():
    df = pd.read_csv(IN)
    with psycopg.connect(_dsn()) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            cur.executemany(
                UPSERT,
                [
                    (
                        r.scope,
                        int(r.iso_week),
                        int(r.iso_dow),
                        float(r.day_mean_smooth),
                        "shrink+circMA(test)",
                        json.dumps(PARAMS),
                    )
                    for r in df.itertuples(index=False)
                ],
            )
        conn.commit()
    print(f"[save] upsert {len(df)} rows into mart.inb_profile_smooth_test")


if __name__ == "__main__":
    main()
