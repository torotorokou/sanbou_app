from __future__ import annotations

import argparse
import os
import sys
import pandas as pd

# Add current directory to sys.path to allow importing sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weekly_allocation import compute_weekly_share_from_history, allocate_monthly_to_weekly


def _detect_monthly_file(provided: str | None) -> str | None:
	candidates = []
	if provided:
		candidates.append(provided)
	candidates += [
		"./data/output/gamma_recency_model/blended_future_forecast.csv",
		"./data/output/gamma_recency_model/blended_prediction_results.csv",
	]
	for p in candidates:
		if p and os.path.exists(p):
			return p
	return None


def main(argv: list[str] | None = None) -> int:
	ap = argparse.ArgumentParser(description="Allocate monthly blended forecasts to weeks using historical daily shares (submission bundle)")
	ap.add_argument("--monthly-forecast-csv", type=str, default=None, help="Monthly forecast CSV (year_month or year+month and forecast column). If not provided, tries defaults in ./data/output/gamma_recency_model.")
	ap.add_argument("--historical-daily-csv", type=str, default="./data/input/01_daily_clean.csv", help="Historical daily actuals CSV with 'date' and value column")
	ap.add_argument("--out", type=str, default="./data/output/gamma_recency_model/weekly_allocated_forecast.parquet", help="Output path (parquet). CSV with same base will also be written.")
	ap.add_argument("--lookback-years", type=int, default=3, help="How many years of history to use when computing weekly shares")
	args = ap.parse_args(argv)

	mfpath = _detect_monthly_file(args.monthly_forecast_csv)
	if mfpath is None:
		print("ERROR: monthly forecast CSV not found. Provide --monthly-forecast-csv or ensure default files exist under ./data/output/gamma_recency_model.")
		return 2

	if not os.path.exists(args.historical_daily_csv):
		print(f"ERROR: historical daily csv not found at {args.historical_daily_csv}")
		return 3

	print(f"Loading monthly forecasts from: {mfpath}")
	mf = pd.read_csv(mfpath)
	print(f"Loaded {len(mf)} monthly rows")

	print(f"Loading historical daily actuals from: {args.historical_daily_csv}")
	hist = pd.read_csv(args.historical_daily_csv)
	print(f"Loaded {len(hist)} daily rows")

	print("Computing weekly shares from history...")
	shares = compute_weekly_share_from_history(hist, lookback_years=args.lookback_years)

	print("Allocating monthly forecasts to weekly forecasts...")
	weekly = allocate_monthly_to_weekly(mf, shares)

	outp = args.out
	os.makedirs(os.path.dirname(outp), exist_ok=True)
	# Parquet は pyarrow / fastparquet が無い環境だと失敗するため、まずはベストエフォートで試し、
	# 失敗しても CSV 出力は必ず行う。
	try:
		print(f"Saving weekly forecast to {outp} (parquet)")
		weekly.to_parquet(outp, index=False)
	except Exception as e:
		print(f"WARNING: failed to write parquet to {outp}: {e}")
		print("Proceeding with CSV output only.")
	csv_out = os.path.splitext(outp)[0] + ".csv"
	print(f"Saving CSV to {csv_out}")
	weekly.to_csv(csv_out, index=False)

	print("Done. Weekly forecast created.")
	return 0


if __name__ == "__main__":
	sys.exit(main())

