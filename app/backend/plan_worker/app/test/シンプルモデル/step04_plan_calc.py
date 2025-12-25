from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from common import _dsn
from plan_smoothing import (
    SmoothConfig,
    apply_intraweek_pipeline,
    bridge_smooth_across_months_and_renorm,
)
from sqlalchemy import create_engine

OUT = Path("/backend/app/test/out/plan")


# ------------------------------------------------------------
# ユーティリティ
# ------------------------------------------------------------
def _parse_month(s: str) -> date:
    y, m = map(int, s.split("-"))
    return date(y, m, 1)


def _first_day_next_month(d: date) -> date:
    return date(
        d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1
    )


def _engine_url(dsn: str) -> str:
    prefix = "postgresql://"
    return (
        ("postgresql+psycopg" + dsn[len("postgresql") :])
        if dsn.startswith(prefix)
        else dsn
    )


def _ensure_odd(n: int) -> int:
    n = max(1, int(n))
    return n if n % 2 == 1 else n + 1


# ------------------------------------------------------------
# メイン
# ------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="月→週→日配分（最終出力は daily_plan.csv 1つ）"
    )
    ap.add_argument("--from-month", type=str, help="例: 2025-03")
    ap.add_argument("--to-month", type=str, help="例: 2026-02（この月まで含む）")

    # 週配分（既存）
    ap.add_argument(
        "--weekly-window", type=int, default=3, help="週の移動平均窓（奇数・中心付き）"
    )
    ap.add_argument(
        "--weekly-alpha",
        type=float,
        default=0.35,
        help="週配分の凸結合：raw(1-α)+MA(α)",
    )
    ap.add_argument(
        "--weekly-cap", type=float, default=1.30, help="週配分の上限（raw の何倍まで）"
    )

    # 週内配分（強化）
    ap.add_argument(
        "--intraweek-window",
        type=int,
        default=3,
        help="週内ロール窓（奇数・中央値→平均）",
    )
    ap.add_argument(
        "--within-week-relcap", type=float, default=1.6, help="週平均×倍率 まで上限"
    )
    ap.add_argument(
        "--min-open-days",
        type=int,
        default=2,
        help="週の営業日がこの数未満なら例外処理",
    )

    # 日タイプ倍率（平日=1.0, 日曜/祝日を抑制したいときに使う）
    ap.add_argument("--sun-mult", type=float, default=1.0, help="日曜倍率（例: 0.6）")
    ap.add_argument("--hol-mult", type=float, default=1.0, help="祝日倍率（例: 0.8）")
    ap.add_argument(
        "--daytype-weight-table",
        type=str,
        default=None,
        help="scope→倍率マスタ（例: ref.daytype_weight）。列: scope(biz/sun/hol), weight_multiplier。渡せば上書きします。",
    )

    # 月またぎブリッジ平滑（既定ON / 平日のみ）
    ap.add_argument(
        "--no-bridge", action="store_true", help="ブリッジ平滑を無効化（既定は有効）"
    )
    ap.add_argument(
        "--bridge-window", type=int, default=5, help="ブリッジのロール窓（奇数）"
    )

    # 検証CSV（週次/整合チェック）
    ap.add_argument("--debug", action="store_true", help="検証用CSVも出力")

    args = ap.parse_args()

    # 期間
    if args.from_month and args.to_month:
        m_from = _parse_month(args.from_month)
        m_to_excl = _first_day_next_month(_parse_month(args.to_month))
    else:
        today = date.today()
        m_from = date(today.year, today.month, 1)
        m_to_excl = _first_day_next_month(m_from)

    # 週配分パラメータ
    W = _ensure_odd(args.weekly_window)
    ALPHA = float(args.weekly_alpha)
    CAP_RATIO = float(args.weekly_cap)

    OUT.mkdir(parents=True, exist_ok=True)
    eng = create_engine(_engine_url(_dsn()), future=True)

    # カレンダー
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

    # プロファイル（平日用 'biz' と 日曜用 'all_sun'）
    prof = pd.read_sql_query(
        """
        select scope, iso_week::int as iso_week, iso_dow::int as iso_dow,
               day_mean_smooth::float8 as day_mean_smooth
        from mart.inb_profile_smooth_test
        """,
        eng,
    )
    if prof.empty:
        raise SystemExit(
            "[error] mart.inb_profile_smooth_test が空です。step03_save を先に実行してください。"
        )
    prof_biz = (
        prof[prof["scope"] == "biz"]
        .copy()
        .rename(columns={"day_mean_smooth": "day_mean_biz"})
    )
    # 日曜・祝日は「all の日曜行」を流用
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
    kpi["month_date"] = (
        pd.to_datetime(kpi["month_date"]).dt.to_period("M").dt.to_timestamp()
    )
    if kpi.empty:
        raise SystemExit(
            f"[error] 対象期間に inbound KPI がありません: {m_from}〜{m_to_excl}（排他）"
        )

    # scope（sun/hol/biz/closed）
    is_closed = (~cal["is_business"]) | (cal["day_type"] == "CLOSED")
    use_sun = (~is_closed) & (cal["iso_dow"] == 7)  # 日曜（営業日のみ）
    use_hol = (~is_closed) & (cal["is_holiday"]) & (~use_sun)  # 祝日（ただし日曜優先）
    use_biz = (~is_closed) & (~use_sun) & (~use_hol)  # 平日

    base = cal.merge(
        prof_biz[["iso_week", "iso_dow", "day_mean_biz"]],
        on=["iso_week", "iso_dow"],
        how="left",
    ).merge(prof_all_sun, on=["iso_week"], how="left")
    base["day_mean_biz"] = base["day_mean_biz"].fillna(0.0)
    base["day_mean_all_sun"] = base["day_mean_all_sun"].fillna(0.0)

    # 日別プロファイル値を決定
    base["day_mean"] = 0.0
    base.loc[use_biz, "day_mean"] = base.loc[use_biz, "day_mean_biz"]
    # ★ 日曜・祝日は all（日曜プロファイル）をそのまま使用
    base.loc[use_sun | use_hol, "day_mean"] = base.loc[
        use_sun | use_hol, "day_mean_all_sun"
    ]

    base["scope_used"] = np.select(
        [is_closed, use_sun, use_hol, use_biz],
        ["closed", "sun", "hol", "biz"],
        default="biz",
    )
    base["month_date"] = base["ddate"].dt.to_period("M").dt.to_timestamp()

    # 倍率（biz/sun/hol を許可）
    scope_mult = {"biz": 1.0, "sun": float(args.sun_mult), "hol": float(args.hol_mult)}
    if args.daytype_weight_table:
        try:
            wtbl = pd.read_sql_query(
                f"select scope, weight_multiplier from {args.daytype_weight_table}", eng
            )
            if not wtbl.empty:
                for k, v in zip(wtbl["scope"], wtbl["weight_multiplier"].astype(float)):
                    if str(k) in scope_mult:
                        scope_mult[str(k)] = float(v)
        except Exception:
            pass

    # ① 月→週（安全平滑 + cap）
    week_mass = (
        base.groupby(["month_date", "iso_year", "iso_week"], as_index=False)["day_mean"]
        .sum()
        .rename(columns={"day_mean": "mu_week"})
    )
    first_dd = (
        base.groupby(["month_date", "iso_year", "iso_week"], as_index=False)["ddate"]
        .min()
        .rename(columns={"ddate": "week_start"})
    )
    open_days = (
        base.assign(is_open=base["day_mean"] > 0)
        .groupby(["month_date", "iso_year", "iso_week"], as_index=False)["is_open"]
        .sum()
        .rename(columns={"is_open": "open_days"})
    )
    week_mass = (
        week_mass.merge(first_dd, on=["month_date", "iso_year", "iso_week"], how="left")
        .merge(open_days, on=["month_date", "iso_year", "iso_week"], how="left")
        .fillna({"open_days": 0})
        .sort_values(["month_date", "week_start"])
    )

    def _blend_smooth_per_month(g: pd.DataFrame) -> pd.DataFrame:
        raw = g["mu_week"].clip(lower=0).astype(float)
        ma = raw.rolling(window=W, center=True, min_periods=1).mean()
        raw_sum = float(raw.sum())
        ma_sum = float(ma.sum())
        w_raw = raw / raw_sum if raw_sum > 0 else 0.0
        w_ma = ma / ma_sum if ma_sum > 0 else 0.0
        w = (1.0 - ALPHA) * w_raw + ALPHA * w_ma
        w_cap = np.where(w_raw > 0, CAP_RATIO * w_raw, 0.0)
        w = np.minimum(w, w_cap)
        w = np.where(g["open_days"] > 0, w, 0.0)
        s = float(np.sum(w))
        g["w_week"] = (w / s) if s > 0 else 0.0
        return g

    week_mass = week_mass.groupby("month_date", group_keys=False).apply(
        _blend_smooth_per_month, include_groups=True
    )
    week_mass = week_mass.merge(
        kpi[["month_date", "month_target_ton"]], on="month_date", how="left"
    )
    week_mass["month_target_ton"] = week_mass["month_target_ton"].astype(float)
    week_mass["week_target_ton_in_month"] = (
        week_mass["w_week"] * week_mass["month_target_ton"]
    )

    # ② 週→日（倍率→平滑→相対キャップ→正規化）
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
        intraweek_window=int(args.intraweek_window),
        intraweek_method="median_then_mean",
        within_week_rel_cap=float(args.within_week_relcap),
        min_open_days_for_smooth=int(args.min_open_days),
        scope_weight_multiplier=scope_mult,  # biz/sun/hol 倍率
        bridge_smooth_enabled=not args.no_bridge,
        bridge_smooth_window=int(args.bridge_window),
        bridge_smooth_scope_values=("biz",),  # 平日のみブリッジ
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

    # 最終DF
    daily = base[
        [
            "ddate",
            "month_date",
            "iso_year",
            "iso_week",
            "iso_dow",
            "scope_used",
            "w_day_in_week_raw",
            "w_day_in_week",
            "target_ton",
        ]
    ].copy()

    # 月またぎブリッジ（有効時）
    if cfg.bridge_smooth_enabled:
        daily = bridge_smooth_across_months_and_renorm(
            df=daily,
            date_col="ddate",
            month_key="month_date",
            target_col="target_ton",
            scope_col="scope_used",
            scope_values=cfg.bridge_smooth_scope_values,
            window=cfg.bridge_smooth_window,
            method="median_then_mean",
        )

    # 出力（最終は常に1つ）
    OUT.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUT / "daily_plan.csv", index=False)

    # 検証CSV（任意）
    if args.debug:
        weekly = (
            daily.groupby(["month_date", "iso_year", "iso_week"], as_index=False)[
                "target_ton"
            ]
            .sum()
            .rename(columns={"target_ton": "week_target_ton_in_month"})
        )
        chk_day_month = (
            daily.groupby("month_date", as_index=False)["target_ton"]
            .sum()
            .rename(columns={"target_ton": "sum_plan"})
            .merge(kpi[["month_date", "month_target_ton"]], on="month_date", how="left")
        )
        chk_day_month["month_target_ton"] = chk_day_month["month_target_ton"].astype(
            float
        )
        chk_day_month["diff"] = (
            chk_day_month["sum_plan"] - chk_day_month["month_target_ton"]
        )

        weekly.to_csv(OUT / "weekly_plan.csv", index=False)
        chk_day_month.to_csv(OUT / "plan_month_check.csv", index=False)

        # 閉所日に配分が乗っていないかチェック
        leak = daily.query("scope_used == 'closed' and target_ton > 1e-9")
        if not leak.empty:
            leak.to_csv(OUT / "leak_closed_days.csv", index=False)
            print(
                f"[warn] closed日の配分リーク {len(leak)} 件 → leak_closed_days.csv を確認してください"
            )

    # ログ
    print(f"[range] months: {m_from} .. (excl) {m_to_excl}")
    print(f"[weekly] window={W} alpha={ALPHA} cap={CAP_RATIO}")
    print(
        f"[intraweek] window={args.intraweek_window} rel_cap={args.within_week_relcap} "
        f"min_open_days={args.min_open_days}"
    )
    print(f"[scope_mult] {scope_mult}")
    print(f"[bridge] enabled={not args.no_bridge} window={args.bridge_window}")
    print("[output] daily_plan.csv written")

    eng.dispose()


if __name__ == "__main__":
    main()
