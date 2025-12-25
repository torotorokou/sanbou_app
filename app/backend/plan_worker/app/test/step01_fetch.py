# /backend/app/test/step01_fetch.py
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd
import psycopg
from common import _dsn  # そのまま

OUT = Path("/backend/app/test/out")  # appuser が書ける場所


def _parse_month(s: str) -> date:
    # "YYYY-MM" -> その月の1日
    y, m = map(int, s.split("-"))
    return date(y, m, 1)


def _first_day_next_month(d: date) -> date:
    return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-month", type=str, default=None, help="例: 2025-03")
    ap.add_argument(
        "--to-month", type=str, default=None, help="例: 2026-02（この月の末日まで含む）"
    )
    args = ap.parse_args()

    # デフォルト（従来挙動）：当年±1年相当
    if args.from_month and args.to_month:
        m_from = _parse_month(args.from_month)  # 包含
        m_to_inclusive = _parse_month(args.to_month)
        m_to_excl = _first_day_next_month(m_to_inclusive)  # 排他（翌月1日）
    else:
        # 既存ロジック相当の広い範囲（当年-1年 ～ 当年+1年）
        # 例：from: 今年の1/1、to_excl: 再来年の1/1
        today = date.today()
        m_from = date(today.year - 1, 1, 1)
        m_to_excl = date(today.year + 2, 1, 1)

    OUT.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(_dsn()) as conn:
        # 1) 5年×週×曜日の基礎プロファイル（MV）…期間非依存のため全件でOK
        mv = pd.read_sql_query(
            """
            select scope, iso_week, iso_dow, ave::float8 as ave,
                   sigma::float8 as sigma, n::int as n, coalesce(cv,0)::float8 as cv
            from mart.mv_inb_avg5y_day_scope
        """,
            conn,
        )

        # 2) カレンダー：日付で絞り込み（[m_from, m_to_excl)）
        cal = pd.read_sql_query(
            """
            select ddate::date,
                   iso_year::int, iso_week::int,
                   extract(isodow from ddate)::int as iso_dow,
                   is_business, coalesce(is_holiday,false) as is_holiday, day_type
            from ref.v_calendar_classified
            where ddate >= %(dfrom)s and ddate < %(dto)s
        """,
            conn,
            params={"dfrom": m_from, "dto": m_to_excl},
        )

        # 3) KPI（月間目標）：月単位で絞り込み（[m_from, m_to_excl)）
        kpi = pd.read_sql_query(
            """
            select date_trunc('month', month_date)::date as month_date,
                   segment, metric, value::numeric as month_target_ton
            from kpi.monthly_targets
            where metric = 'inbound'
              and date_trunc('month', month_date) >= %(mfrom)s
              and date_trunc('month', month_date) <  %(mto)s
        """,
            conn,
            params={"mfrom": m_from, "mto": m_to_excl},
        )

    mv.to_csv(OUT / "mv_scope.csv", index=False)
    cal.to_csv(OUT / "calendar.csv", index=False)
    kpi.to_csv(OUT / "kpi_inbound.csv", index=False)

    print(f"[range] months: {m_from} .. (excl) {m_to_excl}")
    print("[mv] rows:", len(mv), "scopes:", mv["scope"].unique().tolist())
    print("[mv] null ave:", mv["ave"].isna().sum(), "n<=0:", (mv["n"] <= 0).sum())
    print("[cal] range:", cal["ddate"].min(), "…", cal["ddate"].max(), "rows:", len(cal))
    print("[kpi] rows:", len(kpi), "months:", kpi["month_date"].nunique())


if __name__ == "__main__":
    main()
