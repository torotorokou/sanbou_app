
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_absolute_error

# Add current directory to path to import sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weekly_allocation import compute_weekly_share_from_history

def evaluate_reverse_landing():
    print("=== Reverse Allocation (Landing Prediction) Evaluation ===")
    
    # 1. Load Data
    daily_path = "data/input/01_daily_clean.csv"
    if not os.path.exists(daily_path):
        print("Error: Input file not found.")
        return

    df = pd.read_csv(daily_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Detect value column
    value_col = None
    for c in ["weight_t", "actual_value", "actual_weight_ton", "weight", "actual"]:
        if c in df.columns:
            value_col = c
            break
    
    # Convert to Tons
    df["weight_ton"] = df[value_col] / 1000.0
    
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["week_in_month"] = ((df["day"] - 1) // 7) + 1
    
    # 2. Split Train/Test
    split_date = pd.Timestamp("2024-01-01")
    train_df = df[df["date"] < split_date].copy()
    test_df = df[df["date"] >= split_date].copy()
    
    print(f"Train: ~{train_df['date'].max().date()}, Test: {test_df['date'].min().date()}~")

    # 3. Compute Weekly Shares (The "Ratios")
    print("Computing weekly shares from history...")
    shares = compute_weekly_share_from_history(train_df, lookback_years=3)
    
    # Transform shares into a lookup: (month, week) -> cumulative_share
    # We want to know: "At the end of Week N, what % of the month is usually done?"
    shares_lookup = {}
    for m in range(1, 13):
        month_shares = shares[shares["month"] == m].sort_values("week_in_month")
        cumulative = 0.0
        for _, row in month_shares.iterrows():
            w = int(row["week_in_month"])
            s = row["mean_share"]
            cumulative += s
            shares_lookup[(m, w)] = cumulative
            
    # 4. Simulate Landing Prediction on Test Data
    results = []
    
    # Group test data by month
    test_months = test_df.groupby(["year", "month"])
    
    for (year, month), group in test_months:
        actual_monthly_total = group["weight_ton"].sum()
        
        # Calculate cumulative actuals by week
        weekly_sums = group.groupby("week_in_month")["weight_ton"].sum()
        
        current_cumulative_actual = 0.0
        
        for w in range(1, 5): # Evaluate at end of Week 1, 2, 3, 4
            if w in weekly_sums.index:
                current_cumulative_actual += weekly_sums[w]
                
                # Get expected progress ratio
                expected_ratio = shares_lookup.get((month, w), None)
                
                if expected_ratio and expected_ratio > 0:
                    # PREDICT: Monthly Total = Current / Ratio
                    predicted_total = current_cumulative_actual / expected_ratio
                    
                    error = predicted_total - actual_monthly_total
                    abs_error = abs(error)
                    ape = abs_error / actual_monthly_total
                    
                    results.append({
                        "year": year,
                        "month": month,
                        "at_end_of_week": w,
                        "actual_total": actual_monthly_total,
                        "predicted_total": predicted_total,
                        "expected_ratio": expected_ratio,
                        "current_actual": current_cumulative_actual,
                        "abs_error": abs_error,
                        "ape": ape
                    })

    res_df = pd.DataFrame(results)
    
    # 5. Report Metrics
    print("\n=== Accuracy by Timing (When prediction is made) ===")
    summary = res_df.groupby("at_end_of_week").agg(
        MAE=("abs_error", "mean"),
        MAPE=("ape", "mean"),
        Count=("ape", "count")
    )
    summary["MAPE"] = summary["MAPE"] * 100
    print(summary)
    
    print("\n=== Example Predictions (End of Week 2) ===")
    week2_res = res_df[res_df["at_end_of_week"] == 2].head(5)
    print(week2_res[["year", "month", "actual_total", "predicted_total", "ape"]])

if __name__ == "__main__":
    evaluate_reverse_landing()
