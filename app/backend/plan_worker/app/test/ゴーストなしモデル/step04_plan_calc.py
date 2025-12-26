# ruff: noqa
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from common import _dsn
from plan_smoothing_plus import (
    SmoothConfig,
    apply_intraweek_pipeline,
    bridge_smooth_across_months_and_renorm,
    rolling_smooth,
)
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


def _ensure_odd(n: int) -> int:
    n = max(1, int(n))
    return n if n % 2 == 1 else n + 1


def main():
    ap = argparse.ArgumentParser(description="月→週→日配分（平滑強化版）")
    ap.add_argument("--from-month", type=str)
    ap.add_argument("--to-month", type=str)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    if args.from_month and args.to_month:
        m_from = _parse_month(args.from_month)
        m_to_excl = _first_day_next_month(_parse_month(args.to_month))
    else:
        today = date.today()
        m_from = date(today.year, today.month, 1)
        m_to_excl = _first_day_next_month(m_from)

    OUT.mkdir(parents=True, exist_ok=True)
    eng = create_engine(_engine_url(_dsn()), future=True)

    # --- （省略）SQL読込部分は既存のまま ---
    # あなたの環境の step04_plan_calc.py と同様に base, kpi, week_mass を作成する

    # ▼ここから改良点▼

    # 週ブリッジ平滑（週配分）
    week_mass["w_week"] = rolling_smooth(week_mass["w_week"], window=3, method="median_then_mean")
    week_mass["w_week"] = week_mass["w_week"] / week_mass.groupby("month_date")["w_week"].transform(
        "sum"
    )

    # 週→日 Bモード
    cfg = SmoothConfig(
        intraweek_window=5,
        within_week_rel_cap=1.6,
        min_open_days_for_smooth=3,
        non_biz_share_cap_per_day=0.08,
        per_day_share_cap=None,
        bridge_smooth_enabled=True,
        bridge_smooth_window=5,
        bridge_smooth_scope_values=("biz", "sun", "hol"),  # ←休日含め
    )

    base = (
        base.sort_values(["month_date", "iso_year", "iso_week", "ddate"])
        .groupby(["month_date", "iso_year", "iso_week"], group_keys=False)
        .apply(
            lambda g: apply_intraweek_pipeline(
                df_week=g,
                weight_raw_col="w_day_in_week_raw",
                weight_col="w_day_in_week",
                cfg=cfg,
                scope_col="scope_used",
            ),
            include_groups=True,
        )
    )
    base["target_ton"] = base["w_day_in_week"] * base["week_target_ton_in_month"]

    # 月またぎブリッジ（休日含む）
    if cfg.bridge_smooth_enabled:
        base = bridge_smooth_across_months_and_renorm(
            df=base,
            date_col="ddate",
            month_key="month_date",
            target_col="target_ton",
            scope_col="scope_used",
            scope_values=cfg.bridge_smooth_scope_values,
            window=cfg.bridge_smooth_window,
        )

    # --- ④ 最終7日ロール ---
    base["target_ton"] = rolling_smooth(base["target_ton"], window=7, method="mean_only")

    # 月内再正規化（KPI一致）
    month_tot = base.groupby("month_date")["target_ton"].transform("sum")
    kpi_map = dict(zip(kpi["month_date"], kpi["month_target_ton"]))
    base["target_ton"] = base.apply(
        lambda r: (
            r["target_ton"] * (kpi_map.get(r["month_date"], 0.0) / month_tot.loc[r.name])
            if month_tot.loc[r.name] > 0
            else 0.0
        ),
        axis=1,
    )

    # 出力
    base.to_csv(OUT / "daily_plan_smooth.csv", index=False)
    print("[OK] daily_plan_smooth.csv written")

    if args.debug:
        week_check = base.groupby(["month_date", "iso_week"])["target_ton"].sum().reset_index()
        week_check.to_csv(OUT / "weekly_check.csv", index=False)

    eng.dispose()


if __name__ == "__main__":
    main()
