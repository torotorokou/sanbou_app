"""LightGBM blending on top of Gamma Recency Model predictions.

This script trains a small LightGBM regressor that uses the Gamma model's
point predictions as a feature, along with simple monthly features. It retains
TimeSeriesSplit for CV and evaluates on a hold-out test split aligned with the
Gamma pipeline.

Outputs are written next to the Gamma outputs.
"""
from __future__ import annotations

import os
import sys
import warnings
from typing import Dict, List

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Adjust sys.path so we can import the bundled gamma_recency_model module
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# submission_release_20251027 を基準にする: /works/data/submission_release_20251027
SUBMISSION_ROOT = os.path.dirname(os.path.dirname(HERE))

from gamma_recency_model import (  # type: ignore
    preprocess_daily_to_monthly,
    GammaRecencyModel,
    evaluate_predictions,
    time_series_cross_validation,
    forecast_future,
)

# LightGBM
import lightgbm as lgb
from sklearn.linear_model import RidgeCV
from sklearn.metrics import r2_score

OUTPUT_DIR = os.path.join(SUBMISSION_ROOT, "data", "output", "gamma_recency_model")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _load_monthly() -> pd.DataFrame:
    """submission フォルダ配下の data/input から月次データを作成する。

    - まず submission_release_20251027/data/input/01_daily_clean.csv
    - つぎに submission_release_20251027/data/input/01_daily_clean_with_date.csv
    - 最後の手段として /works/data/input/01_daily_clean.csv
    を順に探す。
    """
    default_path = os.path.join(SUBMISSION_ROOT, "data", "input", "01_daily_clean.csv")
    alt_path = os.path.join(SUBMISSION_ROOT, "data", "input", "01_daily_clean_with_date.csv")
    fallback_root_path = os.path.join(os.path.dirname(os.path.dirname(SUBMISSION_ROOT)), "input", "01_daily_clean.csv")

    if os.path.exists(default_path):
        data_path = default_path
    elif os.path.exists(alt_path):
        data_path = alt_path
    elif os.path.exists(fallback_root_path):
        data_path = fallback_root_path
    else:
        raise FileNotFoundError(
            "日次入力CSVが見つかりません。submission_release_20251027/data/input に "
            "01_daily_clean.csv か 01_daily_clean_with_date.csv を配置してください。"
        )

    return preprocess_daily_to_monthly(data_path)


def build_gamma(monthly: pd.DataFrame, model_kwargs: Dict) -> GammaRecencyModel:
    n = len(monthly)
    train_n = int(np.floor(n * 0.8))
    train_df = monthly.iloc[:train_n].copy()

    model = GammaRecencyModel(**model_kwargs)
    model.fit(train_df)
    return model


def _build_features(df: pd.DataFrame, gamma_pred: np.ndarray | None = None) -> pd.DataFrame:
    """Create a consistent feature matrix for blending.

    Includes:
    - market_size_ton, recency_7, business_ratio
    - month cyclical features (sin, cos)
    - holiday flags if available: is_gw_month, is_obon_month, is_yearend_month
    - optional gamma_pred and interaction gamma_pred * business_ratio
    """
    feats = pd.DataFrame(index=df.index)

    # Base numeric features if present
    for col in ["market_size_ton", "recency_7", "business_ratio"]:
        if col in df.columns:
            feats[col] = df[col].astype(float)

    # Month cyclical encoding
    if "month" in df.columns:
        m = df["month"].astype(float)
        feats["month_sin"] = np.sin(2 * np.pi * m / 12.0)
        feats["month_cos"] = np.cos(2 * np.pi * m / 12.0)

    # Holiday flags
    for hcol in ["is_gw_month", "is_obon_month", "is_yearend_month"]:
        if hcol in df.columns:
            feats[hcol] = df[hcol].astype(float)

    # Gamma prediction and simple interaction
    if gamma_pred is not None:
        feats["gamma_pred"] = gamma_pred
        if "business_ratio" in feats.columns:
            feats["gamma_x_business"] = feats["gamma_pred"] * feats["business_ratio"]

    # Fill any missing columns with zeros to avoid errors
    feats = feats.fillna(0.0)
    return feats


def run_blend() -> None:
    monthly = _load_monthly().sort_values("year_month").reset_index(drop=True)
    n = len(monthly)
    train_n = int(np.floor(n * 0.8))
    train_df = monthly.iloc[:train_n].copy()
    test_df = monthly.iloc[train_n:].copy()

    # Use best params found previously as defaults
    model_kwargs = dict(
        share_mean_percent=0.1056,
        gamma_shape=4.0,
        gamma_scale=500.0,
        recency_weight=0.48,
        learn_seasonality=False,
        calibr_clip=0.2,
        business_beta=0.2,
        calibr_method="huber",
    )

    gamma_model = build_gamma(monthly, model_kwargs)

    base_cols = ["market_size_ton", "recency_7", "business_ratio", "month"]
    use_cols_all = [c for c in base_cols if c in monthly.columns]

    monthly["gamma_pred"] = gamma_model.predict(monthly[use_cols_all])

    y = monthly["actual_weight_ton"].values

    # Build feature matrices
    X_full = _build_features(monthly, gamma_pred=monthly["gamma_pred"].values)
    X_train = X_full.iloc[:train_n].copy()
    y_train = y[:train_n]
    X_test = X_full.iloc[train_n:].copy()
    y_test = y[train_n:]

    # 1) Linear baseline: RidgeCV (robust for small N)
    ridge = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0], cv=None)
    ridge.fit(X_train, y_train)
    ridge_pred = ridge.predict(X_test)
    r2_ridge = r2_score(y_test, ridge_pred)
    print(f"RidgeCV R²(Test): {r2_ridge:.3f}")
    _ = evaluate_predictions(y_test, ridge_pred, dataset_name="Blend-Ridge(Test)")

    # 2) LGBM with conservative params for tiny datasets
    lgb_params = dict(
        objective="regression",
        learning_rate=0.05,
        num_leaves=3,
        max_depth=2,
        min_data_in_leaf=1,
        n_estimators=500,
        subsample=1.0,
        colsample_bytree=1.0,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
    )
    lgbm = lgb.LGBMRegressor(**lgb_params)
    lgbm.fit(X_train, y_train)
    lgb_pred = lgbm.predict(X_test)
    r2_lgb = r2_score(y_test, lgb_pred)
    print(f"LightGBM R²(Test): {r2_lgb:.3f}")
    _ = evaluate_predictions(y_test, lgb_pred, dataset_name="Blend-LGBM(Test)")

    # Pick best on R^2
    if r2_ridge >= r2_lgb:
        best_name = "ridge"
        best_model = ridge
        y_pred_test = ridge_pred
    else:
        best_name = "lightgbm"
        best_model = lgbm
        y_pred_test = lgb_pred
    print(f"Selected blended model: {best_name}")

    # Save blended predictions
    pred_df = test_df[["year_month", "year", "month", "actual_weight_ton"]].copy()
    pred_df["gamma_pred"] = monthly.loc[train_n:, "gamma_pred"].values
    pred_df["blended_pred"] = y_pred_test
    pred_df["residual"] = pred_df["actual_weight_ton"] - pred_df["blended_pred"]
    pred_df["abs_error"] = pred_df["residual"].abs()
    eps = 1e-8
    pred_df["pct_error"] = (
        (pred_df["abs_error"] / np.maximum(pred_df["actual_weight_ton"].abs(), eps)) * 100.0
    )
    pred_df["year_month"] = pd.to_datetime(pred_df["year_month"]).dt.strftime("%Y-%m")

    # Calculate sigma from test residuals
    sigma = pred_df["residual"].std()
    print(f"Test Residual Sigma: {sigma:.4f}")

    path = os.path.join(OUTPUT_DIR, "blended_prediction_results.csv")
    pred_df[[
        "year_month",
        "actual_weight_ton",
        "gamma_pred",
        "blended_pred",
        "residual",
        "abs_error",
        "pct_error",
    ]].to_csv(path, index=False)

    # Forecast future using gamma as base features, then blend via LGBM
    # 学習データの最終月を取得し、その翌月を予測開始日とする
    last_date = monthly["year_month"].max()
    next_month = last_date + pd.DateOffset(months=1)
    start_date_str = next_month.strftime("%Y-%m-%d")
    print(f"  予測開始月: {start_date_str} (学習データ末月: {last_date.strftime('%Y-%m')})")

    future = forecast_future(
        model=gamma_model,
        last_actual_data=monthly,
        start_date=start_date_str,
        periods=6,
    )
    # Build future features consistently
    fut_base_cols = [c for c in use_cols_all if c in future.columns]
    future_gamma = gamma_model.predict(future[fut_base_cols])
    future_X = _build_features(future, gamma_pred=future_gamma)
    future_blend = best_model.predict(future_X)

    fpath = os.path.join(OUTPUT_DIR, "blended_future_forecast.csv")
    fdf = future[["year_month", "year", "month"]].copy()
    fdf["gamma_pred"] = future_gamma
    fdf["blended_pred"] = future_blend
    fdf["blended_model"] = best_name
    
    # Add sigma intervals
    fdf["sigma"] = sigma
    fdf["blended_pred_plus_sigma"] = fdf["blended_pred"] + sigma
    fdf["blended_pred_minus_sigma"] = fdf["blended_pred"] - sigma

    fdf.to_csv(fpath, index=False)

    print("\n✓ Blending outputs saved:")
    print(f"  - {path}")
    print(f"  - {fpath}")


if __name__ == "__main__":
    run_blend()
