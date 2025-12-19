
import pandas as pd
import numpy as np
import sys
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Add current directory to path to import sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from weekly_allocation import compute_weekly_share_from_history, allocate_monthly_to_weekly

def evaluate_end_to_end():
    print("=== End-to-End Weekly Forecast Evaluation ===")
    
    # 1. Load Data
    daily_path = "data/input/01_daily_clean.csv"
    monthly_pred_path = "data/output/gamma_recency_model/blended_prediction_results.csv"
    
    if not os.path.exists(daily_path) or not os.path.exists(monthly_pred_path):
        print("Error: Input files not found.")
        return

    # Load Daily Actuals
    df_daily = pd.read_csv(daily_path)
    df_daily["date"] = pd.to_datetime(df_daily["date"])
    
    # Detect value column
    value_col = None
    for c in ["weight_t", "actual_value", "actual_weight_ton", "weight", "actual"]:
        if c in df_daily.columns:
            value_col = c
            break
    
    # Prepare Weekly Actuals Ground Truth
    df_daily["year"] = df_daily["date"].dt.year
    df_daily["month"] = df_daily["date"].dt.month
    df_daily["day"] = df_daily["date"].dt.day
    df_daily["week_in_month"] = ((df_daily["day"] - 1) // 7) + 1
    
    # Convert to Tons if needed (assuming daily data might be in kg if value is large, but previous check showed ~80000, likely kg)
    # The monthly model output is usually in Tons.
    # Let's check the scale.
    # If daily sum is ~2000 tons/month, and daily values are ~80000, then daily is kg.
    # 80,000 kg = 80 tons. 25 days * 80 = 2000 tons. Matches.
    # So Daily is KG, Monthly Pred is Tons.
    
    df_daily["weight_ton"] = df_daily[value_col] / 1000.0
    
    weekly_gt = df_daily.groupby(["year", "month", "week_in_month"])["weight_ton"].sum().reset_index()
    weekly_gt.rename(columns={"weight_ton": "actual_weekly_ton"}, inplace=True)

    # Load Monthly Predictions
    df_pred = pd.read_csv(monthly_pred_path)
    # Expected cols: year, month, blended_pred, actual (or similar)
    # Let's identify columns
    pred_col = "blended_pred"
    actual_monthly_col = "actual" # or similar
    
    # Check columns
    print(f"Monthly Pred Columns: {df_pred.columns.tolist()}")
    
    # 2. Compute Shares (using history BEFORE the test period)
    # We need to know the test period.
    # The monthly prediction file contains the test period rows.
    test_years = df_pred["year"].unique()
    min_test_year = min(test_years)
    min_test_month = df_pred[df_pred["year"] == min_test_year]["month"].min()
    
    split_date = pd.Timestamp(f"{min_test_year}-{min_test_month}-01")
    print(f"Test Period Starts: {split_date}")
    
    train_daily = df_daily[df_daily["date"] < split_date].copy()
    shares = compute_weekly_share_from_history(train_daily, lookback_years=3)
    
    # 3. Scenario A: Allocation using ACTUAL Monthly Totals (Baseline)
    # This measures pure allocation error.
    # We need actual monthly totals for the test period.
    # We can get this from df_pred if it has actuals, or aggregate from daily.
    # Aggregating from daily is safer to ensure consistency with weekly GT.
    monthly_actuals = df_daily[df_daily["date"] >= split_date].groupby(["year", "month"])["weight_ton"].sum().reset_index()
    monthly_actuals.rename(columns={"weight_ton": "forecast_value"}, inplace=True) # naming it forecast_value for the allocator
    
    print("Running Scenario A: Allocation of ACTUAL Monthly Totals...")
    alloc_A = allocate_monthly_to_weekly(monthly_actuals, shares)
    
    # 4. Scenario B: Allocation using PREDICTED Monthly Totals (End-to-End)
    # This measures real-world performance.
    monthly_preds = df_pred[["year", "month", pred_col]].copy()
    monthly_preds.rename(columns={pred_col: "forecast_value"}, inplace=True)
    
    print("Running Scenario B: Allocation of PREDICTED Monthly Totals...")
    alloc_B = allocate_monthly_to_weekly(monthly_preds, shares)
    
    # 5. Evaluation
    def calc_metrics(allocated_df, gt_df, label):
        merged = pd.merge(allocated_df, gt_df, on=["year", "month", "week_in_month"], how="inner")
        mae = mean_absolute_error(merged["actual_weekly_ton"], merged["weekly_forecast_value"])
        rmse = np.sqrt(mean_squared_error(merged["actual_weekly_ton"], merged["weekly_forecast_value"]))
        r2 = r2_score(merged["actual_weekly_ton"], merged["weekly_forecast_value"])
        
        print(f"\n--- {label} ---")
        print(f"MAE:  {mae:.2f} Tons")
        print(f"RMSE: {rmse:.2f} Tons")
        print(f"R2:   {r2:.4f}")
        return merged

    res_A = calc_metrics(alloc_A, weekly_gt, "Scenario A (Perfect Monthly Forecast)")
    res_B = calc_metrics(alloc_B, weekly_gt, "Scenario B (End-to-End Prediction)")
    
    # 6. Error Decomposition
    # How much error is added by the monthly forecast?
    mae_A = mean_absolute_error(res_A["actual_weekly_ton"], res_A["weekly_forecast_value"])
    mae_B = mean_absolute_error(res_B["actual_weekly_ton"], res_B["weekly_forecast_value"])
    
    added_error = mae_B - mae_A
    print(f"\nError Contribution:")
    print(f"Weekly Allocation Error (Base): {mae_A:.2f} Tons")
    print(f"Monthly Forecast Error (Added): {added_error:.2f} Tons")
    print(f"Total End-to-End Error:         {mae_B:.2f} Tons")

if __name__ == "__main__":
    evaluate_end_to_end()
