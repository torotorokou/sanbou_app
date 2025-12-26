from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from common import _dsn
from plan_smoothing_plus import (
    SmoothConfig,
    apply_intraweek_pipeline,
    bridge_smooth_across_months_and_renorm,
)
from scipy.ndimage import gaussian_filter1d
from sqlalchemy import create_engine

OUT = Path("/backend/app/test/out/plan")


def _parse_month(s: str) -> date:
    y, m = map(int, s.split("-"))
    return date(y, m, 1)


def _first_day_next_month(d: date) -> date:
    return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)


def _engine_url(dsn: str) -> str:
    prefix = "postgresql://"
    return ("postgresql+psycopg" + dsn[len("postgresql") :]) if dsn.startswith(prefix) else dsn


def main():
    ap = argparse.ArgumentParser(description="月→週→日配分＋ガウス平滑（日曜祝日固定）")
    ap.add_argument("--from-month", type=str, required=True)
    ap.add_argument("--to-month", type=str, required=True)
    ap.add_argument("--sigma", type=float, default=2.0)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    m_from = _parse_month(args.from_month)
    m_to_excl = _first_day_next_month(_parse_month(args.to_month))
    OUT.mkdir(parents=True, exist_ok=True)
    eng = create_engine(_engine_url(_dsn()), future=True)

    # カレンダー・KPI・プロファイル
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

    prof = pd.read_sql_query(
        """
        select scope, iso_week::int as iso_week, iso_dow::int as iso_dow,
               day_mean_smooth::float8 as day_mean_smooth
        from mart.inb_profile_smooth_test
        """,
        eng,
    )
    prof_biz = prof[prof["scope"] == "biz"].rename(columns={"day_mean_smooth": "day_mean_biz"})
    prof_all_sun = prof[(prof["scope"] == "all") & (prof["iso_dow"] == 7)][
        ["iso_week", "day_mean_smooth"]
    ].rename(columns={"day_mean_smooth": "day_mean_all_sun"})

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

    # 区分
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

    # 月→週→日配分
    week_mass = (
        base.groupby(["month_date", "iso_year", "iso_week"], as_index=False)["day_mean"]
        .sum()
        .rename(columns={"day_mean": "mu_week"})
    )
    total = week_mass.groupby("month_date")["mu_week"].transform("sum")
    week_mass["w_week"] = week_mass["mu_week"] / total
    week_mass = week_mass.merge(
        kpi[["month_date", "month_target_ton"]], on="month_date", how="left"
    )
    week_mass["week_target_ton_in_month"] = week_mass["w_week"] * week_mass["month_target_ton"]

    base = base.merge(
        week_mass[["month_date", "iso_year", "iso_week", "week_target_ton_in_month"]],
        on=["month_date", "iso_year", "iso_week"],
        how="left",
    )
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
        intraweek_window=3,
        intraweek_method="median_then_mean",
        within_week_rel_cap=1.6,
        min_open_days_for_smooth=2,
        scope_weight_multiplier={"biz": 1.0, "sun": 1.0, "hol": 1.0},
        bridge_smooth_enabled=True,
        bridge_smooth_window=5,
        bridge_smooth_scope_values=("biz",),
    )

    base = (
        base.sort_values(["month_date", "iso_year", "iso_week", "ddate"])
        .groupby(["month_date", "iso_year", "iso_week"], group_keys=False)
        .apply(
            lambda g: apply_intraweek_pipeline(
                g, "w_day_in_week_raw", "w_day_in_week", cfg, scope_col="scope_used"
            ),
            include_groups=True,
        )
    )

    base["target_ton"] = base["w_day_in_week"] * base["week_target_ton_in_month"]

    # 月またぎブリッジ
    daily = bridge_smooth_across_months_and_renorm(
        df=base,
        date_col="ddate",
        month_key="month_date",
        target_col="target_ton",
        scope_col="scope_used",
        scope_values=("biz",),
        window=7,
        method="gaussian",
    )

    # 平日のみ全体ガウス平滑
    biz_mask = daily["scope_used"] == "biz"
    x = daily.loc[biz_mask, "target_ton"].to_numpy(dtype=float)
    if len(x) > 10:
        smoothed = gaussian_filter1d(x, sigma=args.sigma)
        daily.loc[biz_mask, "target_ton"] = smoothed

    # KPI再整合
    def _renorm_month(g: pd.DataFrame) -> pd.DataFrame:
        m = g["month_date"].iloc[0]
        target = float(kpi.loc[kpi["month_date"] == m, "month_target_ton"].iloc[0])
        cur = float(g["target_ton"].sum())
        if cur > 0:
            g["target_ton"] *= target / cur
        return g

    daily = daily.groupby("month_date", group_keys=False).apply(_renorm_month, include_groups=True)

    # 出力
    daily.to_csv(OUT / "daily_plan_smooth_final.csv", index=False)
    print("[OK] daily_plan_smooth_final.csv written")

    if args.debug:
        weekly = (
            daily.groupby(["iso_year", "iso_week"], as_index=False)
            .agg({"target_ton": "sum"})
            .rename(columns={"target_ton": "week_target_ton"})
        )
        weekly.to_csv(OUT / "weekly_plan_smooth_final.csv", index=False)
        print("[debug] weekly_plan_smooth_final.csv written")

    eng.dispose()

    # === DB保存処理 ===
    cols_keep = ["ddate", "target_ton", "scope_used"]
    daily_out = daily[cols_keep].copy()
    daily_out["created_at"] = pd.Timestamp.now()

    print(f"[info] saving {len(daily_out)} rows to mart.daily_target_plan ...")
    daily_out.to_sql(
        "daily_target_plan",
        eng,
        schema="mart",
        if_exists="replace",  # or "append"
        index=False,
    )
    print("[OK] mart.daily_target_plan updated.")


if __name__ == "__main__":
    main()
