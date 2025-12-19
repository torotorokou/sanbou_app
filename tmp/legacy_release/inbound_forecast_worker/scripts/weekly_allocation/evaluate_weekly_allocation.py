from __future__ import annotations

import os
import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

try:
	# パッケージ実行時（python -m scripts.weekly_allocation.evaluate_weekly_allocation）
	from .weekly_allocation import compute_weekly_share_from_history, allocate_monthly_to_weekly
except ImportError:
	# 直接スクリプト実行時（python scripts/weekly_allocation/evaluate_weekly_allocation.py）
	from weekly_allocation import compute_weekly_share_from_history, allocate_monthly_to_weekly


def aggregate_weekly_actuals(daily_df: pd.DataFrame, value_col: str | None = None) -> pd.DataFrame:
	if "date" not in daily_df.columns:
		raise ValueError("daily_df must contain a 'date' column")
	daily_df = daily_df.copy()
	daily_df["date"] = pd.to_datetime(daily_df["date"])
	if value_col is None:
		for c in ("actual_value", "actual_weight_ton", "weight", "actual", "value"):
			if c in daily_df.columns:
				value_col = c
				break
	if value_col is None:
		for c in daily_df.columns:
			if c != "date" and pd.api.types.is_numeric_dtype(daily_df[c]):
				value_col = c
				break
	if value_col is None:
		raise ValueError("could not detect a numeric value column in daily_df")

	daily_df["year"] = daily_df["date"].dt.year
	daily_df["month"] = daily_df["date"].dt.month
	daily_df["day"] = daily_df["date"].dt.day
	daily_df["week_in_month"] = ((daily_df["day"] - 1) // 7) + 1

	agg = (
		daily_df.groupby(["year", "month", "week_in_month"])[value_col]
		.sum()
		.reset_index()
		.rename(columns={value_col: "weekly_actual"})
	)
	return agg


def compute_metrics(df: pd.DataFrame, actual_col: str = "weekly_actual", pred_col: str = "weekly_forecast_value") -> dict:
	df = df.dropna(subset=[actual_col, pred_col])
	errs = df[pred_col] - df[actual_col]
	mae = float(np.mean(np.abs(errs))) if len(errs) > 0 else float("nan")
	rmse = float(np.sqrt(np.mean(errs ** 2))) if len(errs) > 0 else float("nan")
	with np.errstate(divide="ignore", invalid="ignore"):
		mape = float(np.mean(np.abs(errs / np.where(df[actual_col] == 0, np.nan, df[actual_col]))) * 100.0)
	if len(df) > 0:
		ss_res = float(np.sum((df[pred_col] - df[actual_col]) ** 2))
		ss_tot = float(np.sum((df[actual_col] - df[actual_col].mean()) ** 2))
		r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
	else:
		r2 = float("nan")
	return {"MAE": mae, "RMSE": rmse, "MAPE_pct": mape, "R2": r2, "N": int(len(errs))}


def main(argv: list[str] | None = None) -> int:
	ap = argparse.ArgumentParser(description="Evaluate weekly allocation accuracy (submission bundle)")
	# blended_prediction_results.csv は過去期間の実績付き月次予測を含む
	# blended_future_forecast.csv は将来予測のみで actual が存在しないため、
	# 精度評価では prediction_results 側を使う
	ap.add_argument("--monthly-forecast-csv", type=str, default="./data/output/gamma_recency_model/blended_prediction_results.csv")
	ap.add_argument("--historical-daily-csv", type=str, default="./data/input/01_daily_clean.csv")
	ap.add_argument("--out", type=str, default="./data/output/gamma_recency_model/weekly_allocation_eval.csv")
	ap.add_argument("--min-actual", type=float, default=0.0)
	ap.add_argument("--train-end-date", type=str, default=None)
	ap.add_argument("--lookback-years", type=int, default=3)
	ap.add_argument("--eval-lookback-months", type=int, default=12)
	ap.add_argument("--plot-output", type=str, default="./data/output/gamma_recency_model/weekly_plots")
	args = ap.parse_args(argv)

	if not os.path.exists(args.monthly_forecast_csv):
		print(f"Monthly forecast csv not found: {args.monthly_forecast_csv}")
		return 2
	if not os.path.exists(args.historical_daily_csv):
		print(f"Historical daily csv not found: {args.historical_daily_csv}")
		return 3

	mf = pd.read_csv(args.monthly_forecast_csv)
	hist = pd.read_csv(args.historical_daily_csv)

	# normalize date/value columns
	if "date" not in hist.columns:
		for c in ["伝票日付", "日付", "ds", "date_jp"]:
			if c in hist.columns:
				hist = hist.rename(columns={c: "date"})
				break
	if "date" not in hist.columns:
		hist = hist.rename(columns={hist.columns[0]: "date"})
	hist["date"] = pd.to_datetime(hist["date"])

	value_candidates = ["actual_value", "actual_weight_ton", "weight", "weight_t", "weight_kg", "kg"]
	found_val = None
	for c in value_candidates:
		if c in hist.columns:
			found_val = c
			break
	if found_val is None:
		for c in hist.columns:
			if c != "date" and pd.api.types.is_numeric_dtype(hist[c]):
				found_val = c
				break
	if found_val is None:
		raise ValueError("Could not find a numeric value column in historical daily CSV")
	if found_val != "actual_value":
		hist = hist.rename(columns={found_val: "actual_value"})

	avg = hist["actual_value"].abs().mean()
	if avg > 10000:
		hist["actual_value"] = hist["actual_value"] / 1000.0

	hist_for_share = hist.copy()
	if args.train_end_date is not None:
		cutoff = pd.to_datetime(args.train_end_date)
		hist_for_share = hist_for_share[hist_for_share["date"] < cutoff]
		if hist_for_share.empty:
			print(f"Warning: no records before train_end_date={args.train_end_date}; using full history for shares.")
			hist_for_share = hist.copy()

	shares = compute_weekly_share_from_history(hist_for_share, lookback_years=args.lookback_years)
	# blended_prediction_results.csv には year_month カラムがある想定なので、
	# もし存在すれば実績期間(例: 2025-10 まで)に切り詰めてから按分することで、
	# actual がない将来期間を評価に混ぜないようにする
	if "year_month" in mf.columns:
		# year_month を Period に変換
		mf["year_month"] = pd.PeriodIndex(mf["year_month"], freq="M")
		max_actual_period = mf["year_month"].max()
		# ユーザーから提供された CSV は 2025-10 まで実績ありなので、
		# それ以降を除外（将来予測）
		cutoff_period = pd.Period("2025-10", freq="M")
		mf = mf[mf["year_month"] <= cutoff_period].copy()

	weekly_fore = allocate_monthly_to_weekly(mf, shares)
	weekly_actuals = aggregate_weekly_actuals(hist)

	# 評価期間を直近 N ヶ月に限定（デフォルト: 12ヶ月）
	if args.eval_lookback_months and args.eval_lookback_months > 0:
		# 実績側の最大年月を基準に、N ヶ月前以降を残す
		ym_series = weekly_actuals["year"] * 100 + weekly_actuals["month"]
		max_ym = int(ym_series.max())
		max_year, max_month = divmod(max_ym, 100)
		max_period = pd.Period(f"{max_year}-{max_month}", freq="M")
		cutoff_period = max_period - args.eval_lookback_months + 1
		cutoff_year = cutoff_period.year
		cutoff_month = cutoff_period.month

		weekly_actuals = weekly_actuals[
			(weekly_actuals["year"] > cutoff_year)
			| ((weekly_actuals["year"] == cutoff_year) & (weekly_actuals["month"] >= cutoff_month))
		].copy()

		weekly_fore = weekly_fore[
			(weekly_fore["year"] > cutoff_year)
			| ((weekly_fore["year"] == cutoff_year) & (weekly_fore["month"] >= cutoff_month))
		].copy()

	merged = pd.merge(weekly_fore, weekly_actuals, on=["year", "month", "week_in_month"], how="left")
	merged["error"] = merged["weekly_forecast_value"] - merged["weekly_actual"]
	merged["abs_error"] = merged["error"].abs()
	with np.errstate(divide="ignore", invalid="ignore"):
		merged["pct_error"] = merged["abs_error"] / np.where(merged["weekly_actual"] == 0, np.nan, merged["weekly_actual"]) * 100.0

	metrics = compute_metrics(merged)

	filtered = merged
	filtered_metrics = None
	if args.min_actual and args.min_actual > 0.0:
		filtered = merged[merged["weekly_actual"] >= args.min_actual].copy()
		filtered_metrics = compute_metrics(filtered)

	os.makedirs(os.path.dirname(args.out), exist_ok=True)
	merged.to_csv(args.out, index=False)
	if filtered_metrics is not None:
		fname = args.out.replace(".csv", f".filtered_min{int(args.min_actual)}.csv")
		filtered.to_csv(fname, index=False)
		print("Filtered per-week CSV saved to:", fname)

	print("Weekly allocation evaluation saved to:", args.out)
	print("Summary metrics:")
	for k, v in metrics.items():
		print(f"  {k}: {v}")
	if filtered_metrics is not None:
		print("\nFiltered summary metrics (weekly_actual >= {0}):".format(args.min_actual))
		for k, v in filtered_metrics.items():
			print(f"  {k}: {v}")

	# optional plots
	if args.plot_output:
		plot_dir = args.plot_output
		os.makedirs(plot_dir, exist_ok=True)
		plot_df = filtered if (args.min_actual and args.min_actual > 0.0) else merged
		if "week_start_date" not in plot_df.columns or plot_df["week_start_date"].isna().all():
			def _rep_date(r):
				y = int(r["year"])
				m = int(r["month"])
				win = int(r["week_in_month"])
				day = min(1 + (win - 1) * 7, 29)
				try:
					return pd.to_datetime(pd.Timestamp(year=y, month=m, day=day))
				except Exception:
					return pd.NaT
			plot_df = plot_df.copy()
			plot_df["week_start_date"] = plot_df.apply(_rep_date, axis=1)

		plot_df = plot_df.sort_values("week_start_date")

		plt.figure(figsize=(12, 5))
		plt.plot(plot_df["week_start_date"], plot_df["weekly_actual"], marker="o", label="actual")
		plt.plot(plot_df["week_start_date"], plot_df["weekly_forecast_value"], marker="o", label="forecast")
		plt.xlabel("week_start_date")
		plt.ylabel("weekly value")
		plt.title("Weekly actual vs forecast")
		plt.legend()
		plt.grid(True, linestyle="--", alpha=0.4)
		ts_path = os.path.join(plot_dir, "weekly_actual_vs_forecast.png")
		plt.tight_layout()
		plt.savefig(ts_path)
		plt.close()
		print("Saved time-series plot to:", ts_path)

		plt.figure(figsize=(6, 6))
		plt.scatter(plot_df["weekly_actual"], plot_df["weekly_forecast_value"], alpha=0.7)
		maxv = max(plot_df["weekly_actual"].max(skipna=True) or 0, plot_df["weekly_forecast_value"].max(skipna=True) or 0)
		plt.plot([0, maxv], [0, maxv], color="red", linestyle="--")
		plt.xlabel("weekly_actual")
		plt.ylabel("weekly_forecast_value")
		plt.title("Predicted vs Actual (weekly)")
		plt.grid(True, linestyle="--", alpha=0.4)
		sc_path = os.path.join(plot_dir, "pred_vs_actual_scatter.png")
		plt.tight_layout()
		plt.savefig(sc_path)
		plt.close()
		print("Saved pred vs actual scatter to:", sc_path)

	return 0


if __name__ == "__main__":
	sys.exit(main())

