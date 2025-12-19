
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Add current directory to path to import sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weekly_allocation import compute_weekly_share_from_history, allocate_monthly_to_weekly

def evaluate_weekly_allocation():
    # 1. Load Data
    daily_path = "data/input/01_daily_clean.csv"
    if not os.path.exists(daily_path):
        print(f"Error: {daily_path} not found.")
        return

    df = pd.read_csv(daily_path)
    df["date"] = pd.to_datetime(df["date"])
    
    # Detect value column
    value_col = None
    for c in ["actual_value", "actual_weight_ton", "weight", "actual", "weight_t"]:
        if c in df.columns:
            value_col = c
            break
    if value_col is None:
        print("Error: Value column not found.")
        return

    print(f"Using value column: {value_col}")

    # 2. Prepare Ground Truth (Weekly and Monthly)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["week_in_month"] = ((df["day"] - 1) // 7) + 1
    
    # Filter for evaluation period (e.g., 2024-2025)
    # We will use data BEFORE 2024 for training shares, and 2024-2025 for testing
    split_date = pd.to_datetime("2024-01-01")
    
    train_df = df[df["date"] < split_date].copy()
    test_df = df[df["date"] >= split_date].copy()
    
    print(f"Train samples: {len(train_df)}, Test samples: {len(test_df)}")

    # 3. Compute Shares from Train Data
    print("Computing weekly shares from Train data...")
    shares = compute_weekly_share_from_history(train_df, lookback_years=3)
    
    # 4. Prepare Test Monthly Inputs (Convert to Tons)
    test_monthly = test_df.groupby(["year", "month"])[value_col].sum().reset_index()
    test_monthly[value_col] = test_monthly[value_col] / 1000.0 # Convert to Tons
    test_monthly.rename(columns={value_col: "forecast_value"}, inplace=True)
    
    # 5. Allocate (New Logic: Weekday Aware)
    print("Allocating (Weekday Aware)...")
    allocated_new = allocate_monthly_to_weekly(test_monthly, shares)
    
    # 5b. Allocate (Old Logic: Simple Average Simulation)
    # Re-compute simple monthly shares for baseline
    print("Computing simple monthly shares for baseline...")
    df_train = train_df.copy()
    df_train["year_month_str"] = df_train["date"].dt.strftime("%Y-%m")
    month_sum = df_train.groupby("year_month_str")[value_col].sum().rename("month_total")
    week_sum = df_train.groupby(["year_month_str", "week_in_month"])[value_col].sum().rename("week_total")
    tmp = week_sum.reset_index().merge(month_sum.reset_index(), on="year_month_str", how="left")
    tmp["share"] = tmp.apply(lambda r: (r["week_total"] / r["month_total"]) if r["month_total"] > 0 else 0.0, axis=1)
    tmp["month"] = pd.to_datetime(tmp["year_month_str"] + "-01").dt.month
    
    agg_simple = tmp.groupby(["month", "week_in_month"])["share"].mean().reset_index().rename(columns={"share": "mean_share"})
    
    # Normalize
    def _norm(g):
        s = g["mean_share"].sum()
        if s > 0: g["mean_share"] /= s
        else: g["mean_share"] = 1.0/len(g)
        return g
    agg_simple = agg_simple.groupby("month", group_keys=False).apply(_norm)
    
    # Expand to all weekdays so the new allocator can use it
    agg_simple_expanded = []
    for fw in range(7):
        d = agg_simple.copy()
        d["first_weekday"] = fw
        agg_simple_expanded.append(d)
    shares_old = pd.concat(agg_simple_expanded)
    
    print("Allocating (Simple Average)...")
    allocated_old = allocate_monthly_to_weekly(test_monthly, shares_old)

    # 6. Prepare Test Weekly Ground Truth (Convert to Tons)
    test_weekly_gt = test_df.groupby(["year", "month", "week_in_month"])[value_col].sum().reset_index()
    test_weekly_gt[value_col] = test_weekly_gt[value_col] / 1000.0 # Convert to Tons
    test_weekly_gt.rename(columns={value_col: "actual_weekly_value"}, inplace=True)
    
    # 7. Evaluate Both
    def evaluate(allocated_df, name):
        merged = pd.merge(
            allocated_df, 
            test_weekly_gt, 
            on=["year", "month", "week_in_month"], 
            how="inner"
        )
        mae = mean_absolute_error(merged["actual_weekly_value"], merged["weekly_forecast_value"])
        rmse = np.sqrt(mean_squared_error(merged["actual_weekly_value"], merged["weekly_forecast_value"]))
        r2 = r2_score(merged["actual_weekly_value"], merged["weekly_forecast_value"])
        
        print(f"\n=== {name} Results (2024-2025) ===")
        print(f"MAE:  {mae:.2f} Tons")
        print(f"RMSE: {rmse:.2f} Tons")
        print(f"R2:   {r2:.4f}")
        return mae

    mae_old = evaluate(allocated_old, "Old Logic (Simple Avg)")
    mae_new = evaluate(allocated_new, "New Logic (Weekday Aware)")
    
    print(f"\nImprovement: {mae_old - mae_new:.2f} Tons ({(mae_old - mae_new)/mae_old*100:.1f}%)")


if __name__ == "__main__":
    evaluate_weekly_allocation()
