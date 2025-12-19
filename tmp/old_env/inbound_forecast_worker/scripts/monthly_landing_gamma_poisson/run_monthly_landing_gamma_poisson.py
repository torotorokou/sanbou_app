from __future__ import annotations

"""Gamma/Poisson-style monthly landing prototype.

目的:
- 月初 1〜2 週までの実績 A_t1, A_t1_2 から、月合計 Y_t を
  ガンマ回帰 (もしくはポワソン回帰) で推定する実験用スクリプト。
- creditable interval（予測区間）として、ガンマ分布を仮定した
  ベイズ風区間 or ログスケール残差の分散から近似区間を出力する。

注意:
- data/submission_release_20251027 フォルダの外で開発するため、
  提出物には含まれません（/works/scripts 配下のみを使用）。
- 現時点では研究用のプロトタイプであり、API は固定されていません。
"""

import argparse
from pathlib import Path
import joblib

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.linear_model import PoissonRegressor
from sklearn.linear_model import TweedieRegressor

# 依存: scikit-learn, pandas, numpy


def load_monthly_from_submission(csv_path: str) -> pd.DataFrame:
    """submission 側で作成済みの monthly_from_daily_firstweek.csv を読み込むヘルパ。

    列想定:
    - year, month, Y_t, A_t1, A_t1_2, ...
    """

    df = pd.read_csv(csv_path)
    needed = {"year", "month", "Y_t", "A_t1", "A_t1_2"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"monthly csv is missing columns: {missing}")
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df


def build_design_poisson(df: pd.DataFrame, use_a21: bool = False, add_growth_features: bool = False) -> pd.DataFrame:
    """単純なポワソン/ガンマ系の設計行列を構成。

    - 基本は log(A_t1_2+eps) + month ダミー。
    - use_a21=True の場合は、A_t1_21 列（第3週末までの累積）がある前提で
      log(A_t1_21+eps) も特徴量に含める。
    """

    out = df.copy()
    eps = 1e-6
    out["log_A_t1_2"] = np.log(out["A_t1_2"].clip(lower=eps))
    if use_a21 and "A_t1_21" in out.columns:
        out["log_A_t1_21"] = np.log(out["A_t1_21"].clip(lower=eps))

    if add_growth_features and "A_t1" in out.columns and "A_t1_2" in out.columns and "A_t1_21" in out.columns:
        # 14日/7日, 21日/14日の伸び率。0割り回避のため eps を加える。
        out["growth_7_14"] = (out["A_t1_2"] + eps) / (out["A_t1"] + eps)
        out["growth_14_21"] = (out["A_t1_21"] + eps) / (out["A_t1_2"] + eps)
    # 簡易な季節性: month の one-hot を追加
    for m in range(1, 13):
        out[f"month_{m:02d}"] = (out["month"] == m).astype(int)
    return out


def fit_poisson_model(
    df: pd.DataFrame,
    min_train_months: int = 12,
    use_a21: bool = False,
    add_growth_features: bool = False,
    use_tweedie: bool = False,
    alpha: float = 1.0,
):
    """Poisson/Tweedie 回帰を用いた簡易モデルを学習。

    - use_a21=True なら log_A_t1_21 も特徴に含める。
    - add_growth_features=True なら伸び率特徴を追加。
    - use_tweedie=True なら TweedieRegressor(power=1.5〜2.0 程度) を使用。
    """

    if len(df) < min_train_months:
        raise ValueError(f"not enough samples: n={len(df)}, need >= {min_train_months}")

    design = build_design_poisson(df, use_a21=use_a21, add_growth_features=add_growth_features)
    # 特徴量列
    feature_cols = ["log_A_t1_2"]
    if use_a21 and "log_A_t1_21" in design.columns:
        feature_cols.append("log_A_t1_21")
    if add_growth_features:
        for c in ("growth_7_14", "growth_14_21"):
            if c in design.columns:
                feature_cols.append(c)
    feature_cols += [c for c in design.columns if c.startswith("month_")]

    X = design[feature_cols].values
    y = design["Y_t"].values

    # PoissonRegressor は y>=0 を想定。小さい値には eps を足す。
    y = np.clip(y, 1e-6, None)

    if use_tweedie:
        # Gamma に近い領域 (1<power<2) を仮定。ここでは 1.5 とする。
        model = TweedieRegressor(power=1.5, alpha=alpha, link="log", max_iter=1000)
    else:
        model = PoissonRegressor(alpha=alpha, max_iter=1000)
    model.fit(X, y)

    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)

    return model, feature_cols, mae, design


def gamma_like_interval(y_pred: np.ndarray, residuals: np.ndarray, alpha: float = 0.32) -> tuple[np.ndarray, np.ndarray]:
    """ガンマ分布を仮定したラフな予測区間。

    - residuals は log(y_true) - log(y_pred) を想定。
    - 正規近似ではなく、実際の分位点 (16%, 84%) を使ったロバストな区間推定。
    """

    eps = 1e-6
    if len(residuals) < 3:
        return y_pred, y_pred

    q_low = float(np.quantile(residuals, 0.16))
    q_high = float(np.quantile(residuals, 0.84))

    lower = np.exp(np.log(y_pred + eps) + q_low)
    upper = np.exp(np.log(y_pred + eps) + q_high)
    return lower, upper


def train_and_save_model(
    monthly_csv: str,
    save_path: str,
    min_train_months: int = 12,
    use_a21: bool = False,
    add_growth_features: bool = False,
    use_tweedie: bool = False,
):
    """全データで学習してモデルを保存する。"""
    df = load_monthly_from_submission(monthly_csv)
    
    # 全データで学習
    model, feature_cols, _mae, design = fit_poisson_model(
        df,
        min_train_months=min_train_months,
        use_a21=use_a21,
        add_growth_features=add_growth_features,
        use_tweedie=use_tweedie,
    )
    
    # 残差を計算して保存（予測区間用）
    X = design[feature_cols].values
    y_pred = model.predict(X)
    log_resid = np.log(np.clip(design["Y_t"].values, 1e-6, None)) - np.log(np.clip(y_pred, 1e-6, None))
    
    artifact = {
        "model": model,
        "feature_cols": feature_cols,
        "residuals": log_resid,
        "config": {
            "use_a21": use_a21,
            "add_growth_features": add_growth_features,
            "use_tweedie": use_tweedie,
        }
    }
    
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, save_path)
    print(f"Model saved to {save_path}")


def load_and_predict(
    monthly_csv: str,
    model_path: str,
    out_csv: str | None = None,
) -> pd.DataFrame:
    """保存済みモデルをロードして推論する。"""
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_cols = artifact["feature_cols"]
    residuals = artifact["residuals"]
    config = artifact["config"]
    
    df = load_monthly_from_submission(monthly_csv)
    
    # 特徴量作成（学習時と同じ設定で）
    design = build_design_poisson(
        df, 
        use_a21=config["use_a21"], 
        add_growth_features=config["add_growth_features"]
    )
    
    # 推論
    X = design[feature_cols].values
    y_pred = model.predict(X)
    
    # 予測区間
    y_low, y_high = gamma_like_interval(y_pred, residuals)
    
    out_df = df.copy()
    out_df["Y_pred"] = y_pred
    out_df["Y_low_68"] = y_low
    out_df["Y_high_68"] = y_high
    
    if out_csv is not None:
        Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_csv, index=False)
        print(f"Predictions saved to {out_csv}")
        
    return out_df


def roll_forward_backtest_gamma_poisson(
    monthly_csv: str,
    min_train_months: int = 12,
    out_csv: str | None = None,
    use_a21: bool = False,
    add_growth_features: bool = False,
    use_tweedie: bool = False,
) -> pd.DataFrame:
    """月次着地の Poisson/Gamma 版ロールフォワード評価。

    - 学習は PoissonRegressor を用いて行い、
      予測区間はログ残差に基づくガンマ風の区間で近似。
    """

    df = load_monthly_from_submission(monthly_csv)
    df = df.copy().reset_index(drop=True)

    preds = []

    for t in range(min_train_months, len(df)):
        train = df.iloc[:t].copy()
        test = df.iloc[t : t + 1].copy()

        model, feature_cols, _mae_train, design_train = fit_poisson_model(
            train,
            min_train_months=min_train_months,
            use_a21=use_a21,
            add_growth_features=add_growth_features,
            use_tweedie=use_tweedie,
        )

        design_test = build_design_poisson(test, use_a21=use_a21, add_growth_features=add_growth_features)
        X_test = design_test[feature_cols].values
        y_pred = model.predict(X_test)

        # log 残差から 1σ 区間を近似
        X_train = design_train[feature_cols].values
        y_train_pred = model.predict(X_train)
        log_resid = np.log(np.clip(train["Y_t"].values, 1e-6, None)) - np.log(np.clip(y_train_pred, 1e-6, None))
        y_low, y_high = gamma_like_interval(y_pred, log_resid)

        preds.append(
            {
                "year": int(test["year"].iloc[0]),
                "month": int(test["month"].iloc[0]),
                "Y_t": float(test["Y_t"].iloc[0]),
                "Y_pred": float(y_pred[0]),
                "Y_low_68": float(y_low[0]),
                "Y_high_68": float(y_high[0]),
            }
        )

    out_df = pd.DataFrame(preds)

    if out_csv is not None:
        Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_csv, index=False)

    return out_df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gamma/Poisson monthly landing prototype")
    parser.add_argument("--monthly-csv", default="/works/data/output/gamma_recency_model/monthly_from_daily_firstweek.csv")
    parser.add_argument("--min-train-months", type=int, default=12)
    parser.add_argument("--out-csv", default="/works/tmp/monthly_landing_gamma_poisson_backtest.csv")
    parser.add_argument("--use-a21", action="store_true", help="Use A_t1_21 (1-21 days cumulative) as additional feature")
    parser.add_argument("--add-growth-features", action="store_true", help="Add growth features (A14/A7, A21/A14)")
    parser.add_argument("--use-tweedie", action="store_true", help="Use TweedieRegressor (gamma-like) instead of PoissonRegressor")
    parser.add_argument("--save-model", type=str, help="Path to save the trained model")
    parser.add_argument("--load-model", type=str, help="Path to load a trained model for inference")
    args = parser.parse_args(argv)

    if args.save_model:
        train_and_save_model(
            monthly_csv=args.monthly_csv,
            save_path=args.save_model,
            min_train_months=args.min_train_months,
            use_a21=args.use_a21,
            add_growth_features=args.add_growth_features,
            use_tweedie=args.use_tweedie,
        )
        return 0

    if args.load_model:
        df = load_and_predict(
            monthly_csv=args.monthly_csv,
            model_path=args.load_model,
            out_csv=args.out_csv,
        )
        # 簡易表示
        print(df[["year", "month", "Y_t", "Y_pred", "Y_low_68", "Y_high_68"]].tail())
        return 0

    df = roll_forward_backtest_gamma_poisson(
        monthly_csv=args.monthly_csv,
        min_train_months=args.min_train_months,
        out_csv=args.out_csv,
        use_a21=args.use_a21,
        add_growth_features=args.add_growth_features,
        use_tweedie=args.use_tweedie,
    )

    mae = mean_absolute_error(df["Y_t"], df["Y_pred"])
    print("=== Gamma/Poisson monthly landing (prototype) ===")
    print(f"samples: {len(df)}")
    print(f"MAE = {mae:.3f}")
    print(f"Saved predictions to {args.out_csv}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
