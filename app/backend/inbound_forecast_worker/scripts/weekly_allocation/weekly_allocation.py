from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np
import datetime as dt


def _detect_value_col(df: pd.DataFrame) -> Optional[str]:
	candidates = ["actual_value", "actual_weight_ton", "weight", "actual"]
	for c in candidates:
		if c in df.columns:
			return c
	# fallback: any numeric column besides date
	for c in df.columns:
		if c != "date" and pd.api.types.is_numeric_dtype(df[c]):
			return c
	return None


def _ensure_date(df: pd.DataFrame, date_col: str = "date") -> pd.Series:
	s = df[date_col]
	if not np.issubdtype(s.dtype, np.datetime64):
		return pd.to_datetime(s)
	return s


def compute_weekly_share_from_history(df_actuals: pd.DataFrame, lookback_years: int = 3) -> pd.DataFrame:
	"""過去実績から「月内週別構成比」を算出する (提出用簡略版)。"""
	if "date" not in df_actuals.columns:
		raise ValueError("df_actuals must contain a 'date' column")

	value_col = _detect_value_col(df_actuals)
	if value_col is None:
		raise ValueError("could not detect numeric value column in df_actuals")

	df = df_actuals.copy()
	df["date"] = _ensure_date(df, "date")

	if lookback_years is not None and lookback_years > 0:
		max_dt = df["date"].max()
		min_dt = max_dt - pd.DateOffset(years=lookback_years)
		df = df[df["date"] >= min_dt]

	df["year"] = df["date"].dt.year
	df["month"] = df["date"].dt.month
	df["day"] = df["date"].dt.day
	df["week_in_month"] = ((df["day"] - 1) // 7) + 1
	df["year_month_str"] = df["date"].dt.strftime("%Y-%m")
	
	# Calculate first weekday of the month (0=Mon, 6=Sun)
	df["month_start_date"] = df["date"].apply(lambda d: d.replace(day=1))
	df["first_weekday"] = df["month_start_date"].dt.dayofweek

	month_sum = df.groupby("year_month_str")[value_col].sum().rename("month_total")
	# Include first_weekday in the grouping (it's constant for each year_month_str)
	week_sum = df.groupby(["year_month_str", "week_in_month", "first_weekday"])[value_col].sum().rename("week_total")

	tmp = week_sum.reset_index().merge(month_sum.reset_index(), on="year_month_str", how="left")
	tmp["share"] = tmp.apply(lambda r: (r["week_total"] / r["month_total"]) if r["month_total"] > 0 else 0.0, axis=1)

	tmp["month_num"] = pd.to_datetime(tmp["year_month_str"] + "-01").dt.month

	df["year"] = df["date"].dt.year
	df["month"] = df["date"].dt.month
	df["day"] = df["date"].dt.day
	df["week_in_month"] = ((df["day"] - 1) // 7) + 1
	df["year_month_str"] = df["date"].dt.strftime("%Y-%m")

	month_sum = df.groupby("year_month_str")[value_col].sum().rename("month_total")
	week_sum = df.groupby(["year_month_str", "week_in_month"])[value_col].sum().rename("week_total")

	tmp = week_sum.reset_index().merge(month_sum.reset_index(), on="year_month_str", how="left")
	tmp["share"] = tmp.apply(lambda r: (r["week_total"] / r["month_total"]) if r["month_total"] > 0 else 0.0, axis=1)

	tmp["month_num"] = pd.to_datetime(tmp["year_month_str"] + "-01").dt.month

	agg = (
		tmp.groupby(["month_num", "week_in_month"])
		.agg(mean_share=("share", "mean"), count_months_used=("share", "count"))
		.reset_index()
	)

	months = np.arange(1, 13)
	weeks = np.arange(1, 6)
	full = pd.MultiIndex.from_product([months, weeks], names=["month_num", "week_in_month"]).to_frame(index=False)
	agg_full = full.merge(agg, on=["month_num", "week_in_month"], how="left")
	agg_full["mean_share"] = agg_full["mean_share"].fillna(0.0)
	agg_full["count_months_used"] = agg_full["count_months_used"].fillna(0).astype(int)

	def _normalize_group(g):
		s = g["mean_share"].sum()
		if s > 0:
			g["mean_share"] = g["mean_share"] / s
		else:
			g["mean_share"] = 1.0 / len(g)
		return g

	agg_norm = agg_full.groupby("month_num", group_keys=False).apply(_normalize_group)
	agg_norm = agg_norm.rename(columns={"month_num": "month"})
	return agg_norm[["month", "week_in_month", "mean_share", "count_months_used"]]


def allocate_monthly_to_weekly(monthly_forecast_df: pd.DataFrame, weekly_share_df: pd.DataFrame) -> pd.DataFrame:
	"""月次予測を週次に按分する (提出用簡略版)。"""
	df = monthly_forecast_df.copy()

	forecast_col = None
	for c in ("blended_pred", "predicted_weight_ton", "forecast_value", "forecast"):
		if c in df.columns:
			forecast_col = c
			break
	if forecast_col is None:
		for c in df.columns:
			if c not in ("year_month", "year", "month") and pd.api.types.is_numeric_dtype(df[c]):
				forecast_col = c
				break
	if forecast_col is None:
		raise ValueError("could not detect forecast value column in monthly_forecast_df")

	if "year_month" in df.columns:
		ym = pd.to_datetime(df["year_month"].astype(str) + "-01")
		df["year"] = ym.dt.year
		df["month"] = ym.dt.month
	elif not ("year" in df.columns and "month" in df.columns):
		raise ValueError("monthly_forecast_df must contain 'year_month' or both 'year' and 'month' columns")

	share = weekly_share_df.copy()
	if "month" not in share.columns:
		raise ValueError("weekly_share_df must contain column 'month' (1-12)")

	out_rows = []
	for _, r in df.iterrows():
		y = int(r["year"])
		m = int(r["month"])
		monthly_val = float(r[forecast_col])
		
		# Check for sigma columns
		monthly_val_plus = r.get("blended_pred_plus_sigma", None)
		monthly_val_minus = r.get("blended_pred_minus_sigma", None)

		s = share[share["month"] == m].sort_values("week_in_month")
		if s["mean_share"].sum() <= 0:
			nweeks = len(s)
			s = s.copy()
			s["mean_share"] = 1.0 / nweeks if nweeks > 0 else 0.0

		total_share = s["mean_share"].sum()
		if total_share <= 0:
			s["mean_share"] = 1.0 / len(s)
			total_share = 1.0
		else:
			s["mean_share"] = s["mean_share"] / total_share

		for _, ss in s.iterrows():
			win = int(ss["week_in_month"])
			share_val = float(ss["mean_share"])
			weekly_fore = monthly_val * share_val
			
			weekly_fore_plus = monthly_val_plus * share_val if monthly_val_plus is not None else None
			weekly_fore_minus = monthly_val_minus * share_val if monthly_val_minus is not None else None

			try:
				candidate_day = 1 + (win - 1) * 7
				last_day = (dt.date(y, m, 28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
				d = min(candidate_day, last_day.day)
				week_start_date = dt.date(y, m, d)
			except Exception:
				week_start_date = None

			out_rows.append(
				{
					"year": y,
					"month": m,
					"week_in_month": win,
					"weekly_forecast_value": weekly_fore,
					"weekly_forecast_value_plus_sigma": weekly_fore_plus,
					"weekly_forecast_value_minus_sigma": weekly_fore_minus,
					"week_start_date": pd.to_datetime(week_start_date) if week_start_date is not None else pd.NaT,
				}
			)

	out = pd.DataFrame(out_rows)

	if not out.empty:
		mm = out.groupby(["year", "month"])["weekly_forecast_value"].sum().rename("sumw").reset_index()
		out = out.merge(mm, on=["year", "month"], how="left")
		orig = df[["year", "month", forecast_col]].rename(columns={forecast_col: "monthly_val"})
		
		# Merge sigma totals if they exist
		if "blended_pred_plus_sigma" in df.columns:
			orig_plus = df[["year", "month", "blended_pred_plus_sigma"]].rename(columns={"blended_pred_plus_sigma": "monthly_val_plus"})
			orig = orig.merge(orig_plus, on=["year", "month"], how="left")
		if "blended_pred_minus_sigma" in df.columns:
			orig_minus = df[["year", "month", "blended_pred_minus_sigma"]].rename(columns={"blended_pred_minus_sigma": "monthly_val_minus"})
			orig = orig.merge(orig_minus, on=["year", "month"], how="left")

		out = out.merge(orig, on=["year", "month"], how="left")
		
		# Normalize main forecast
		out["weekly_forecast_value"] = out.apply(
			lambda r: (r["weekly_forecast_value"] * (r["monthly_val"] / r["sumw"])) if r["sumw"] > 0 else (r["monthly_val"] / len(out[(out.year == r["year"]) & (out.month == r["month"]) ])),
			axis=1,
		)
		
		# Normalize plus sigma
		if "weekly_forecast_value_plus_sigma" in out.columns and "monthly_val_plus" in out.columns:
			# Calculate sum of allocated plus sigma
			mm_plus = out.groupby(["year", "month"])["weekly_forecast_value_plus_sigma"].sum().rename("sumw_plus").reset_index()
			# We can reuse the same logic or just use the same ratio as the main forecast if we assume shares are identical.
			# But let's be precise and re-normalize to match the monthly total exactly.
			out = out.merge(mm_plus, on=["year", "month"], how="left")
			out["weekly_forecast_value_plus_sigma"] = out.apply(
				lambda r: (r["weekly_forecast_value_plus_sigma"] * (r["monthly_val_plus"] / r["sumw_plus"])) if pd.notnull(r["sumw_plus"]) and r["sumw_plus"] > 0 else r["weekly_forecast_value_plus_sigma"],
				axis=1
			)
			out = out.drop(columns=["sumw_plus", "monthly_val_plus"])

		# Normalize minus sigma
		if "weekly_forecast_value_minus_sigma" in out.columns and "monthly_val_minus" in out.columns:
			mm_minus = out.groupby(["year", "month"])["weekly_forecast_value_minus_sigma"].sum().rename("sumw_minus").reset_index()
			out = out.merge(mm_minus, on=["year", "month"], how="left")
			out["weekly_forecast_value_minus_sigma"] = out.apply(
				lambda r: (r["weekly_forecast_value_minus_sigma"] * (r["monthly_val_minus"] / r["sumw_minus"])) if pd.notnull(r["sumw_minus"]) and r["sumw_minus"] > 0 else r["weekly_forecast_value_minus_sigma"],
				axis=1
			)
			out = out.drop(columns=["sumw_minus", "monthly_val_minus"])

		out = out.drop(columns=["sumw", "monthly_val"])

	cols = ["year", "month", "week_in_month", "weekly_forecast_value"]
	if "weekly_forecast_value_plus_sigma" in out.columns:
		cols.append("weekly_forecast_value_plus_sigma")
	if "weekly_forecast_value_minus_sigma" in out.columns:
		cols.append("weekly_forecast_value_minus_sigma")
	cols.append("week_start_date")
	
	return out[cols]

