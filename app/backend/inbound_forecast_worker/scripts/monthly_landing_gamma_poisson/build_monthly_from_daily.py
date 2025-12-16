from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Tuple

import pandas as pd


@dataclass
class Config:
    daily_csv: str
    out_csv: str
    first_week_days: int = 7
    second_week_days: int = 14


def load_daily(daily_csv: str) -> pd.DataFrame:
    df = pd.read_csv(daily_csv)
    # 日付列を正規化
    date_col = None
    for c in ("date", "日付", "伝票日付"):
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        raise ValueError("daily csv must contain a date-like column (date/日付/伝票日付)")
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["date"]).copy()

    # 重量列検出（kg→t換算）
    value_col = None
    for c in ("actual_weight_ton", "weight_ton", "weight_t"):
        if c in df.columns:
            value_col = c
            break
    if value_col is None:
        raise ValueError("daily csv must contain a weight column (actual_weight_ton/weight_ton/weight_t)")
    vals = df[value_col].astype(float)
    if vals.max() > 50000:
        vals = vals / 1000.0
    df["value_ton"] = vals

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    return df


def build_monthly_features(df: pd.DataFrame, first_week_days: int, second_week_days: int) -> pd.DataFrame:
    # 月次合計 Y_t
    monthly = (
        df.groupby(["year", "month"], as_index=False)["value_ton"]
        .sum()
        .rename(columns={"value_ton": "Y_t"})
    )

    # 第1週実績 A_{t,1}
    mask = df["day"] <= first_week_days
    w1 = (
        df.loc[mask]
        .groupby(["year", "month"], as_index=False)["value_ton"]
        .sum()
        .rename(columns={"value_ton": "A_t1"})
    )
    # 第2週末までの実績 A_{t,1-2}
    mask2 = df["day"] <= second_week_days
    w2 = (
        df.loc[mask2]
        .groupby(["year", "month"], as_index=False)["value_ton"]
        .sum()
        .rename(columns={"value_ton": "A_t1_2"})
    )

    # 第3週末までの実績 A_{t,1-21}
    mask3 = df["day"] <= 21
    w3 = (
        df.loc[mask3]
        .groupby(["year", "month"], as_index=False)["value_ton"]
        .sum()
        .rename(columns={"value_ton": "A_t1_21"})
    )

    out = monthly.merge(w1, on=["year", "month"], how="left")
    out = out.merge(w2, on=["year", "month"], how="left")
    out = out.merge(w3, on=["year", "month"], how="left")
    out["A_t1"].fillna(0.0, inplace=True)
    out["A_t1_2"].fillna(0.0, inplace=True)
    out["A_t1_21"].fillna(0.0, inplace=True)

    # 月番号ダミーは後段で作るのでここでは year_month だけ
    out["year_month"] = out["year"].astype(str) + "-" + out["month"].astype(str).str.zfill(2)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build monthly targets and first-week features from daily actuals")
    ap.add_argument("--daily-csv", default="/works/data/input/01_daily_clean.csv")
    ap.add_argument("--out-csv", default="/works/data/output/gamma_recency_model/monthly_from_daily_firstweek.csv")
    ap.add_argument("--first-week-days", type=int, default=7)
    ap.add_argument("--second-week-days", type=int, default=14)
    args = ap.parse_args(argv)

    cfg = Config(
        daily_csv=args.daily_csv,
        out_csv=args.out_csv,
        first_week_days=args.first_week_days,
        second_week_days=args.second_week_days,
    )

    df_daily = load_daily(cfg.daily_csv)
    df_monthly = build_monthly_features(df_daily, cfg.first_week_days, cfg.second_week_days)
    df_monthly.to_csv(cfg.out_csv, index=False)
    print(f"Wrote monthly features to {cfg.out_csv} (rows={len(df_monthly)})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
