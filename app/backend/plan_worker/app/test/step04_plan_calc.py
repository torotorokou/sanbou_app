# /backend/app/test/step04_plan_calc.py
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from app.test.plan_smoothing_plus import (
    SmoothConfig,
    apply_intraweek_pipeline,
    bridge_smooth_across_months_and_renorm,
)
from common import _dsn
from sqlalchemy import create_engine

OUT = Path("/backend/app/test/out/plan")


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------
def _parse_month(s: str) -> date:
    y, m = map(int, s.split("-"))
    return date(y, m, 1)


def _first_day_next_month(d: date) -> date:
    return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)


def _engine_url(dsn: str) -> str:
    prefix = "postgresql://"
    return ("postgresql+psycopg" + dsn[len("postgresql") :]) if dsn.startswith(prefix) else dsn


def _ensure_odd(n: int) -> int:
    n = max(1, int(n))
    return n if n % 2 == 1 else n + 1


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="月→週→日配分＋指数平滑（搬入量目標計算）")
    ap.add_argument("--from-month", type=str, required=True)
    ap.add_argument("--to-month", type=str, required=True)

    # smoothing parameters
    ap.add_argument("--intraweek-window", type=int, default=5)
    ap.add_argument("--within-week-relcap", type=float, default=1.4)
    ap.add_argument("--min-open-days", type=int, default=3)
    ap.add_argument("--nonbiz-share-cap", type=float, default=None)
    ap.add_argument("--per-day-share-cap", type=float, default=None)
    ap.add_argument("--bridge-window", type=int, default=7)
    ap.add_argument("--no-bridge", action="store_true")
    ap.add_argument("--ghost-next-prevyear", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------
    m_from = _parse_month(args.from_month)
    m_to_excl = _first_day_next_month(_parse_month(args.to_month))

    # --------------------------------------------------------
    # DB connect
    # --------------------------------------------------------
    eng = create_engine(_engine_url(_dsn()), future=True)

    # Calendar
    cal = pd.read_sql_query(
        """
        select ddate::date as ddate,
               iso_year::int as iso_year,
               iso_week::int as iso_week,
               extract(isodow from ddate)::int as iso_dow,
               is_business,
               coalesce(is_holiday,false) as is_holiday,
               day_type
        from ref.v_calendar_classified
        where ddate >= %(dfrom)s and ddate < %(dto)s
        """,
        eng,
        params={"dfrom": m_from, "dto": m_to_excl},
    )
    cal["ddate"] = pd.to_datetime(cal["ddate"])

    # Profile
    prof = pd.read_sql_query(
        """
        select scope, iso_week::int as iso_week, iso_dow::int as iso_dow,
               day_mean_smooth::float8 as day_mean_smooth
        from mart.inb_profile_smooth_test
        """,
        eng,
    )

    prof_biz = (
        prof[prof["scope"] == "biz"].copy().rename(columns={"day_mean_smooth": "day_mean_biz"})
    )
    prof_all_sun = prof[(prof["scope"] == "all") & (prof["iso_dow"] == 7)][
        ["iso_week", "day_mean_smooth"]
    ].rename(columns={"day_mean_smooth": "day_mean_all_sun"})

    # KPI
    kpi = pd.read_sql_query(
        """
        select date_trunc('month', month_date)::date as month_date,
               segment, metric, value::numeric as month_target_ton
        from kpi.monthly_targets
        where metric='inbound'
          and date_trunc('month', month_date) >= %(mfrom)s
          and date_trunc('month', month_date) <  %(mto)s
        """,
        eng,
        params={"mfrom": m_from, "mto": m_to_excl},
    )
    kpi["month_date"] = pd.to_datetime(kpi["month_date"]).dt.to_period("M").dt.to_timestamp()

    # --------------------------------------------------------
    # Base join
    # --------------------------------------------------------
    is_closed = (~cal["is_business"]) | (cal["day_type"] == "CLOSED")
    use_sun = (~is_closed) & (cal["iso_dow"] == 7)
    use_hol = (~is_closed) & (cal["is_holiday"]) & (~use_sun)
    use_biz = (~is_closed) & (~use_sun) & (~use_hol)

    base = cal.merge(
        prof_biz[["iso_week", "iso_dow", "day_mean_biz"]],
        on=["iso_week", "iso_dow"],
        how="left",
    ).merge(prof_all_sun, on=["iso_week"], how="left")
    base["day_mean_biz"] = base["day_mean_biz"].fillna(0.0)
    base["day_mean_all_sun"] = base["day_mean_all_sun"].fillna(0.0)
    base["day_mean"] = 0.0
    base.loc[use_biz, "day_mean"] = base.loc[use_biz, "day_mean_biz"]
    base.loc[use_sun | use_hol, "day_mean"] = base.loc[use_sun | use_hol, "day_mean_all_sun"]
    base["scope_used"] = np.select(
        [is_closed, use_sun, use_hol, use_biz],
        ["closed", "sun", "hol", "biz"],
        default="biz",
    )
    base["month_date"] = base["ddate"].dt.to_period("M").dt.to_timestamp()

    # --------------------------------------------------------
    # 月→週→日 配分
    # --------------------------------------------------------
    week_sum = (
        base.groupby(["month_date", "iso_year", "iso_week"], as_index=False)["day_mean"]
        .sum()
        .rename(columns={"day_mean": "mu_week_sum"})
    )
    base = base.merge(week_sum, on=["month_date", "iso_year", "iso_week"], how="left")
    base["w_day_in_week_raw"] = np.where(
        base["mu_week_sum"] > 0.0, base["day_mean"] / base["mu_week_sum"], 0.0
    )

    cfg = SmoothConfig(
        intraweek_window=int(args.intraweek_window),
        intraweek_method="median_then_mean",
        within_week_rel_cap=float(args.within_week_relcap),
        min_open_days_for_smooth=int(args.min_open_days),
        nonbiz_share_cap=(
            float(args.nonbiz_share_cap) if args.nonbiz_share_cap is not None else None
        ),
        per_day_share_cap=(
            float(args.per_day_share_cap) if args.per_day_share_cap is not None else None
        ),
        bridge_smooth_enabled=not args.no_bridge,
        bridge_smooth_window=int(args.bridge_window),
        bridge_smooth_scope_values=("biz",),
        ghost_extend=bool(args.ghost_next_prevyear),
    )

    base = (
        base.sort_values(["month_date", "iso_year", "iso_week", "ddate"])
        .groupby(["month_date", "iso_year", "iso_week"], group_keys=True)
        .apply(
            lambda g: apply_intraweek_pipeline(
                df_week=g,
                weight_raw_col="w_day_in_week_raw",
                weight_col="w_day_in_week",
                cfg=cfg,
                scope_col="scope_used",
            ).assign(month_date=g.name[0], iso_year=g.name[1], iso_week=g.name[2]),
            include_groups=False,
        )
        .reset_index(drop=True)
    )

    # 日別の初期目標値
    base = base.merge(kpi[["month_date", "month_target_ton"]], on="month_date", how="left")
    base["target_ton"] = base["w_day_in_week"] * base["month_target_ton"]

    # --------------------------------------------------------
    # (New) 全体スムージング 〜指数移動平均 (EWM)〜
    # --------------------------------------------------------
    smooth_span = 21  # 約3週間の指数平滑
    daily = (
        base[
            [
                "ddate",
                "month_date",
                "iso_year",
                "iso_week",
                "iso_dow",
                "scope_used",
                "target_ton",
            ]
        ]
        .sort_values("ddate")
        .reset_index(drop=True)
    )

    is_biz = daily["scope_used"] == "biz"

    # 平日のみ指数移動平均 (EWM)
    ewm_smoothed = (
        daily.loc[is_biz, "target_ton"].ewm(span=smooth_span, adjust=False, min_periods=1).mean()
    )
    daily.loc[is_biz, "target_ton"] = ewm_smoothed

    # 月単位で再スケール（KPI整合）
    chk = (
        daily.groupby("month_date", as_index=False)["target_ton"]
        .sum()
        .rename(columns={"target_ton": "sum_plan"})
        .merge(kpi[["month_date", "month_target_ton"]], on="month_date", how="left")
    )
    chk["adj_ratio"] = chk["month_target_ton"] / chk["sum_plan"]
    daily = daily.merge(chk[["month_date", "adj_ratio"]], on="month_date", how="left")
    daily["target_ton"] *= daily["adj_ratio"]

    # bridge smooth (optional)
    if cfg.bridge_smooth_enabled:
        daily = bridge_smooth_across_months_and_renorm(
            df=daily,
            date_col="ddate",
            month_key="month_date",
            target_col="target_ton",
            scope_col="scope_used",
            scope_values=cfg.bridge_smooth_scope_values,
            window=cfg.bridge_smooth_window,
            ghost_extend=cfg.ghost_extend,
        )

    # --------------------------------------------------------
    # Export
    # --------------------------------------------------------
    OUT.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUT / "daily_plan.csv", index=False)
    print(f"[smooth] applied Exponential Moving Average span={smooth_span} (biz only)")
    print("[output] daily_plan.csv written")

    eng.dispose()


if __name__ == "__main__":
    main()
