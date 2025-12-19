# -*- coding: utf-8 -*-
"""
forecast_reservations.py

目的:
- 予約履歴CSVから、日別の reserve_count / reserve_sum / fixed_ratio を短期予測し、
  将来期間の予測CSVを出力するシンプルなユーティリティ。

入出力:
- 入力: --reserve-csv, 列名（柔軟マッチ）, --start-date/--end-date または --future-days
- 出力: --out-csv (date,reserve_count,reserve_sum,fixed_ratio)
- 付加: --emit-manual-string で serve スクリプトに渡せる --manual-reserve 文字列を標準出力に出す

モデル:
- まず LightGBM があれば使用、次に XGBoost/CatBoost を試行。未導入なら scikit-learn の GBR/Ridge にフォールバック。
"""

import os, argparse, warnings, re
from typing import Optional, Dict, List, Tuple
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)


def _norm_col(s: str) -> str:
    if s is None:
        return ""
    t = str(s).replace("\u3000", " ").strip()
    t = re.sub(r"[\s\-/＿－―・:：()\[\]（）［］]+", "", t)
    try:
        import unicodedata
        t = unicodedata.normalize("NFKC", t)
    except Exception:
        pass
    return t.lower()


def _parse_date_series(sr: pd.Series) -> pd.Series:
    def _clean(x: str) -> str:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        s = str(x)
        s = re.sub(r"[\(（][^\)）]*[\)）]", "", s)
        s = s.replace("年", "/").replace("月", "/").replace("日", "")
        s = s.replace("-", "/").strip()
        return s
    s = sr.astype(str).map(_clean)
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().any():
        return dt.dt.normalize()
    s2 = s.str.replace("/", "", regex=False)
    dt2 = pd.to_datetime(s2, format="%Y%m%d", errors="coerce")
    if dt2.notna().any():
        return dt2.dt.normalize()
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def _read_csv_any(path: str) -> Optional[pd.DataFrame]:
    if not path or not os.path.exists(path):
        return None
    for enc in (None, "utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str, low_memory=False)
        except Exception:
            continue
    try:
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="ignore")
        from pandas.io.common import StringIO
        return pd.read_csv(StringIO(text), dtype=str, low_memory=False)
    except Exception:
        return None


def preprocess_reserve(df: Optional[pd.DataFrame], date_col: str, count_col: str, fixed_col: str) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    dd = df.copy()

    def _auto(df_, want):
        norm_map = {c: _norm_col(c) for c in df_.columns}
        inv = {}
        for k, v in norm_map.items():
            inv.setdefault(v, []).append(k)
        out = {}
        for key, aliases in want.items():
            found = None
            for a in aliases:
                na = _norm_col(a)
                if na in inv:
                    found = inv[na][0]
                    break
            if found is None:
                for na, cols in inv.items():
                    if any(_norm_col(a) in na for a in aliases):
                        found = cols[0]
                        break
            if found is None:
                for na, cols in inv.items():
                    if any(na.startswith(_norm_col(a)) for a in aliases):
                        found = cols[0]
                        break
            out[key] = found
        return out

    cmap = _auto(dd, {
        "date": [date_col, "予約日", "日付", "伝票日付"],
        "count": [count_col, "台数", "予約台数", "件数"],
        "fixed": [fixed_col, "固定客", "固定"],
    })
    if cmap["date"] is None:
        raise ValueError("予約データの日付列が見つかりません。")
    dd[cmap["date"]] = _parse_date_series(dd[cmap["date"]])
    if cmap["count"] in dd.columns:
        dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]].astype(str).str.replace(",", "", regex=False), errors="coerce")
    if cmap["fixed"] in dd.columns:
        dd[cmap["fixed"]] = dd[cmap["fixed"]].astype(str).str.lower().isin(["1", "true", "yes", "固定", "固定客"]).astype(int)
    grp = dd.groupby(cmap["date"]) if len(dd) > 0 else None
    if grp is None or grp.size().sum() == 0:
        return pd.DataFrame()
    out = pd.DataFrame({
        "reserve_count": grp.size().astype(float),
        "reserve_sum": (grp[cmap["count"]].sum() if cmap["count"] in dd.columns else grp.size()).astype(float),
        "fixed_ratio": (grp[cmap["fixed"]].mean() if cmap["fixed"] in dd.columns else 0.0),
    })
    return out


def build_calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    idx = pd.DatetimeIndex(index)
    df = pd.DataFrame(index=idx)
    df["dow"] = idx.weekday
    df["weekofyear"] = idx.isocalendar().week.astype(int)
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    try:
        import jpholiday
        df["is_holiday_jp"] = idx.map(lambda d: 1 if jpholiday.is_holiday(d) else 0)
    except Exception:
        df["is_holiday_jp"] = 0
    # Nearby-weekend indicator (index coverage independent): weekend or its ±1 day by weekday rule
    dow = df["dow"].astype(int)
    is_we = (dow >= 5)
    # prev/next weekday values mod 7
    prev_is_we = ((dow - 1) % 7 >= 5)
    next_is_we = ((dow + 1) % 7 >= 5)
    df["is_holiday_nearby"] = (is_we | prev_is_we | next_is_we).astype(int)
    # Weekly seasonality
    ang = 2 * np.pi * df["dow"] / 7.0
    df["dow_sin"] = np.sin(ang)
    df["dow_cos"] = np.cos(ang)
    # Week-of-year seasonality
    woy = df["weekofyear"].astype(float)
    df["woy_sin"] = np.sin(2 * np.pi * woy / 52.0)
    df["woy_cos"] = np.cos(2 * np.pi * woy / 52.0)
    # Month and day-of-month cyclical encodings
    df["month"] = idx.month
    df["day"] = idx.day
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)
    df["dom_sin"] = np.sin(2 * np.pi * df["day"] / 31.0)
    df["dom_cos"] = np.cos(2 * np.pi * df["day"] / 31.0)
    # Yearly seasonality via day-of-year
    try:
        doy = idx.dayofyear
    except Exception:
        doy = pd.Index(np.arange(1, len(idx) + 1))
    df["doy_sin"] = np.sin(2 * np.pi * doy / 366.0)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 366.0)
    # Month boundary features
    df["is_month_start"] = (idx.is_month_start).astype(int)
    df["is_month_end"] = (idx.is_month_end).astype(int)
    # Workday indicator
    df["is_workday"] = ((df["is_weekend"] == 0) & (df["is_holiday_jp"] == 0)).astype(int)
    # Interaction features: holiday × work/weekend
    df["is_workday_and_holiday"] = (df["is_workday"] * df["is_holiday_jp"]).astype(int)
    df["is_weekend_and_holiday"] = (df["is_weekend"] * df["is_holiday_jp"]).astype(int)
    # numeric interaction of dow and holiday (captures which weekday is holiday)
    df["dow_holiday_interaction"] = df["dow"] * df["is_holiday_jp"]
    return df


def _fit_regressor(X: np.ndarray, y: np.ndarray, method: str = "auto",
                   X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None,
                   fast: bool = False):
    # Try LightGBM -> XGBoost -> CatBoost -> fallback to sklearn
    model = None
    method = method or "auto"
    if method == "auto" or method == "lgbm":
        try:
            import lightgbm as lgb
            model = lgb.LGBMRegressor(
                n_estimators=1200, learning_rate=0.03,
                num_leaves=31, max_depth=-1,
                subsample=0.9, colsample_bytree=0.9,
                reg_alpha=0.1, reg_lambda=0.3,
                min_child_samples=20,
                random_state=42
            )
            if X_val is not None and y_val is not None and len(X_val) > 0:
                model.fit(X, y, eval_set=[(X_val, y_val)], eval_metric="l1",
                          callbacks=[lgb.early_stopping(100, verbose=False)])
            else:
                model.fit(X, y)
            return model, "lgbm"
        except Exception:
            model = None
    if method == "auto" or method == "xgb":
        try:
            import xgboost as xgb
            model = xgb.XGBRegressor(
                n_estimators=1200, learning_rate=0.03, max_depth=6,
                subsample=0.9, colsample_bytree=0.9, reg_alpha=0.1, reg_lambda=0.6,
                random_state=42, tree_method="hist"
            )
            if X_val is not None and y_val is not None and len(X_val) > 0:
                model.fit(X, y, eval_set=[(X_val, y_val)], eval_metric="mae", verbose=False,
                          early_stopping_rounds=100)
            else:
                model.fit(X, y)
            return model, "xgb"
        except Exception:
            model = None
    if method == "auto" or method == "cat":
        try:
            from catboost import CatBoostRegressor
            model = CatBoostRegressor(loss_function="MAE", depth=6, iterations=2000, learning_rate=0.03,
                                      l2_leaf_reg=5.0, random_state=42, verbose=False)
            if X_val is not None and y_val is not None and len(X_val) > 0:
                model.fit(X, y, eval_set=(X_val, y_val))
            else:
                model.fit(X, y)
            return model, "cat"
        except Exception:
            model = None
    # sklearn fallback
    from sklearn.ensemble import GradientBoostingRegressor
    # fast flag reduces estimators for quicker training
    n_est = 100 if fast else 300
    model = GradientBoostingRegressor(loss="absolute_error", n_estimators=n_est, learning_rate=0.05, max_depth=2,
                                      subsample=0.8, random_state=42)
    model.fit(X, y)
    return model, "gbr"


def _lgbm_hpo(X_tr: np.ndarray, y_tr: np.ndarray,
              X_va: Optional[np.ndarray], y_va: Optional[np.ndarray],
              fast: bool = False) -> Optional[object]:
    """Very small LightGBM hyperparameter sweep on a given train/val split.
    Returns best fitted model or None if LightGBM is unavailable.
    """
    try:
        import lightgbm as lgb
        from sklearn.metrics import mean_absolute_error
    except Exception:
        return None
    grid = []
    leaves_list = [31, 63] if fast else [15, 31, 63]
    lr_list = [0.05, 0.03]
    subs_list = [0.9] if fast else [0.8, 0.9]
    col_list = [0.9] if fast else [0.8, 0.9]
    mcs_list = [20] if fast else [10, 20, 30]
    for num_leaves in leaves_list:
        for lr in lr_list:
            for subs in subs_list:
                for col in col_list:
                    for mcs in mcs_list:
                        grid.append(dict(num_leaves=num_leaves, learning_rate=lr, subsample=subs,
                                         colsample_bytree=col, min_child_samples=mcs))
    best = None
    best_mae = float("inf")
    for p in grid:
        m = lgb.LGBMRegressor(n_estimators=1200, random_state=42, max_depth=-1, reg_alpha=0.1, reg_lambda=0.3, **p)
        try:
            if X_va is not None and y_va is not None and len(X_va) > 0:
                m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], eval_metric="l1",
                      callbacks=[lgb.early_stopping(100, verbose=False)])
                yhat = np.ravel(m.predict(X_va))
                mae = mean_absolute_error(y_va, yhat)
            else:
                m.fit(X_tr, y_tr)
                mae = 0.0
            if mae < best_mae:
                best_mae = mae
                best = m
        except Exception:
            continue
    return best


def _fit_base_models(X_tr: np.ndarray, y_tr: np.ndarray,
                     X_va: Optional[np.ndarray], y_va: Optional[np.ndarray],
                     base_hpo: bool = False, fast: bool = False) -> List[Tuple[str, object]]:
    models: List[Tuple[str, object]] = []
    # LightGBM
    try:
        import lightgbm as lgb
        if base_hpo and X_va is not None and y_va is not None and len(X_va) > 0:
            m = _lgbm_hpo(X_tr, y_tr, X_va, y_va, fast=fast)
            if m is None:
                m = lgb.LGBMRegressor(
                    n_estimators=1200, learning_rate=0.03,
                    num_leaves=31, subsample=0.9, colsample_bytree=0.9,
                    reg_alpha=0.1, reg_lambda=0.3, min_child_samples=20,
                    random_state=42
                )
                m.fit(X_tr, y_tr)
        else:
            m = lgb.LGBMRegressor(
                n_estimators=1200, learning_rate=0.03,
                num_leaves=31, subsample=0.9, colsample_bytree=0.9,
                reg_alpha=0.1, reg_lambda=0.3, min_child_samples=20,
                random_state=42
            )
            if X_va is not None and y_va is not None and len(X_va) > 0:
                m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], eval_metric="l1",
                      callbacks=[lgb.early_stopping(100, verbose=False)])
            else:
                m.fit(X_tr, y_tr)
        models.append(("lgbm", m))
    except Exception:
        pass
    # XGBoost
    try:
        import xgboost as xgb
        m = xgb.XGBRegressor(
            n_estimators=1200, learning_rate=0.03, max_depth=6,
            subsample=0.9, colsample_bytree=0.9, reg_alpha=0.1, reg_lambda=0.6,
            random_state=42, tree_method="hist"
        )
        if X_va is not None and y_va is not None and len(X_va) > 0:
            m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], eval_metric="mae", verbose=False,
                  early_stopping_rounds=100)
        else:
            m.fit(X_tr, y_tr)
        models.append(("xgb", m))
    except Exception:
        pass
    # CatBoost
    try:
        from catboost import CatBoostRegressor
        m = CatBoostRegressor(loss_function="MAE", depth=6, iterations=2000, learning_rate=0.03,
                              l2_leaf_reg=5.0, random_state=42, verbose=False)
        if X_va is not None and y_va is not None and len(X_va) > 0:
            m.fit(X_tr, y_tr, eval_set=(X_va, y_va))
        else:
            m.fit(X_tr, y_tr)
        models.append(("cat", m))
    except Exception:
        pass
    # Sklearn GBR
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        m = GradientBoostingRegressor(loss="absolute_error", n_estimators=400, learning_rate=0.05,
                                      max_depth=2, subsample=0.9, random_state=42)
        m.fit(X_tr, y_tr)
        models.append(("gbr", m))
    except Exception:
        pass
    # Sklearn Ridge
    try:
        from sklearn.linear_model import Ridge
        m = Ridge(alpha=1.0)
        m.fit(X_tr, y_tr)
        models.append(("ridge", m))
    except Exception:
        pass
    return models


def _time_series_oof_splits(n: int, k: int, min_train: int = 28) -> List[Tuple[slice, slice]]:
    """Create forward-chaining time series splits producing (train, valid) index slices.
    Ensures each train fold has at least min_train samples and valid fold is non-empty.
    """
    k = max(2, int(k))
    splits: List[Tuple[slice, slice]] = []
    # simple equal-sized folds on index order
    fold_sizes = np.full(k, n // k, dtype=int)
    fold_sizes[: n % k] += 1
    boundaries = np.cumsum(fold_sizes)
    start = 0
    for b in boundaries:
        # train: [0, start), valid: [start, b)
        tr = slice(0, start)
        va = slice(start, b)
        if (va.stop - va.start) <= 0 or (tr.stop - tr.start) < min_train:
            start = b
            continue
        splits.append((tr, va))
        start = b
    if not splits and n > min_train:
        splits.append((slice(0, n - min_train), slice(n - min_train, n)))
    return splits


def _make_features(df_hist: pd.DataFrame) -> pd.DataFrame:
    # df_hist: index=date, columns [reserve_count,reserve_sum,fixed_ratio]
    # Ensure unique, sorted index to avoid reindex duplicate errors
    if not df_hist.index.is_unique:
        df_hist = df_hist.groupby(level=0).agg({
            "reserve_count": "sum",
            "reserve_sum": "sum",
            "fixed_ratio": "mean",
        })
    df_hist = df_hist.sort_index()
    idx = pd.DatetimeIndex(df_hist.index)
    cal = build_calendar_features(idx)
    x = cal.copy()
    # Lags and rolling windows of past reservations
    # Derived series: average ticket (sum per count), robust to zero count
    if all(c in df_hist.columns for c in ["reserve_sum", "reserve_count"]):
        avg_ticket = (df_hist["reserve_sum"].astype(float) / (df_hist["reserve_count"].astype(float).replace(0.0, np.nan))).fillna(0.0)
        df_hist = df_hist.copy()
        df_hist["avg_ticket"] = avg_ticket
    else:
        df_hist = df_hist.copy()
        df_hist["avg_ticket"] = 0.0

    for col in ["reserve_count", "reserve_sum", "fixed_ratio", "avg_ticket"]:
        if col not in df_hist.columns:
            x[col] = 0.0
            continue
        s = df_hist[col].astype(float).reindex(idx).fillna(0.0)
        # lags
        x[f"{col}_lag1"] = s.shift(1)
        x[f"{col}_lag2"] = s.shift(2)
        x[f"{col}_lag3"] = s.shift(3)
        x[f"{col}_lag7"] = s.shift(7)
        x[f"{col}_lag14"] = s.shift(14)
        x[f"{col}_lag21"] = s.shift(21)
        x[f"{col}_lag28"] = s.shift(28)
        # moving averages
        x[f"{col}_ma3"] = s.rolling(3, min_periods=1).mean().shift(1)
        x[f"{col}_ma7"] = s.rolling(7, min_periods=1).mean().shift(1)
        x[f"{col}_ma14"] = s.rolling(14, min_periods=1).mean().shift(1)
        x[f"{col}_ma28"] = s.rolling(28, min_periods=7).mean().shift(1)
        # differences
        # IMPORTANT: shift(1) to avoid using current target value as a feature (leakage)
        x[f"{col}_diff1"] = s.diff(1).shift(1)
        x[f"{col}_diff7"] = s.diff(7).shift(1)
        # Same-DOW naive averages for use as features (not direct predictions)
        x[f"{col}_dow_last1"] = s.shift(7)
        x[f"{col}_dow_last2"] = s.shift(14)
        x[f"{col}_dow_ma4"] = (
            pd.concat([s.shift(7), s.shift(14), s.shift(21), s.shift(28)], axis=1)
            .mean(axis=1)
        )
        # Exponentially-weighted same-DOW mean (recent same-weekdays weighted more)
        try:
            window_same = 8
            weights = np.exp(-0.5 * np.arange(1, window_same + 1))  # decay per week
            weights = weights / (weights.sum() + 1e-12)
            cols = []
            for k in range(1, window_same + 1):
                cols.append(s.shift(7 * k).fillna(0.0).values.reshape(-1, 1))
            if cols:
                P = np.hstack(cols)
                wmean = (P * weights.reshape(1, -1)).sum(axis=1)
                x[f"{col}_dow_wexp"] = pd.Series(wmean, index=idx)
            else:
                x[f"{col}_dow_wexp"] = 0.0
        except Exception:
            x[f"{col}_dow_wexp"] = 0.0
        # lag ratio features (lag1 / lag7), stable with tiny eps
        eps = 1e-6
        x[f"{col}_lag1_div_lag7"] = (s.shift(1) / (s.shift(7) + eps)).fillna(0.0)
        x[f"{col}_lag1_minus_lag7"] = (s.shift(1) - s.shift(7)).fillna(0.0)
    x = x.fillna(0.0)
    return x


def _dow_baseline_series(hist_train: pd.DataFrame, target_col: str, dates: pd.DatetimeIndex,
                         window_same_dow: int = 8, agg: str = "median") -> np.ndarray:
    """Compute leak-free same-DOW baseline for the given future dates using ONLY past data.
    For each date d in dates, take last N occurrences of the same weekday before d and aggregate.
    """
    s = hist_train[target_col].astype(float).copy()
    res = []
    for d in dates:
        dow = d.weekday()
        past = s.loc[(s.index < d) & (s.index.weekday == dow)]
        if len(past) == 0:
            res.append(float(past.mean()) if len(s) else 0.0)
            continue
        vals = past.tail(window_same_dow).values
        if agg == "median":
            res.append(float(np.median(vals)))
        else:
            res.append(float(np.mean(vals)))
    return np.asarray(res, dtype=float)


def _predict_for_col(Xmat: pd.DataFrame, m_entry, meta_entry, use_stack: bool) -> np.ndarray:
    # m_entry can be:
    # - ("stack", base_models) where base_models is a list of (name, model, cols)
    # - (model, name, cols) for simple models
    # - (model, name) older format (kept for compatibility)
    if use_stack and isinstance(m_entry, tuple) and len(m_entry) >= 1 and m_entry[0] == "stack":
        base_models = m_entry[1]
        # base_models: list of tuples (name, model, cols)
        if len(base_models) >= 1:
            try:
                meta, names_keep = meta_entry if isinstance(meta_entry, tuple) else (meta_entry, [n for n, *_ in base_models])
            except Exception:
                meta, names_keep = meta_entry, [n for n, *_ in base_models]
            # Keep the full training column list per model (not just the first element!)
            name_to_model = {}
            for bm in base_models:
                # Expected formats: (name, model, cols) or (name, model)
                if len(bm) >= 3:
                    n, m, cols = bm[0], bm[1], bm[2]
                else:
                    n, m, cols = bm[0], bm[1], None
                # cols should be a list of feature names; keep as-is
                name_to_model[n] = (m, cols)
            cols_list = []
            for n in names_keep:
                info = name_to_model.get(n)
                if info is None:
                    continue
                m, cols = info
                # align features to model's training columns if available
                if cols is not None:
                    X_in = Xmat.reindex(columns=cols, fill_value=0.0)
                else:
                    X_in = Xmat
                try:
                    cols_list.append(np.ravel(m.predict(X_in.values)).reshape(-1, 1))
                except Exception:
                    # fallback: try passing full matrix
                    cols_list.append(np.ravel(m.predict(Xmat.values)).reshape(-1, 1))
            if cols_list and meta is not None:
                P_pred = np.hstack(cols_list)
                return np.ravel(meta.predict(P_pred))
            # fallback to first base model
            first = base_models[0]
            fm = first[1]
            fcols = first[2] if len(first) > 2 else None
            X_in = Xmat.reindex(columns=fcols, fill_value=0.0) if fcols is not None else Xmat
            try:
                return np.ravel(fm.predict(X_in.values))
            except Exception:
                return np.zeros(len(Xmat))
        else:
            return np.zeros(len(Xmat))
    else:
        # simple model entry: (model, name, cols) or (model, name)
        if isinstance(m_entry, tuple) and len(m_entry) >= 1:
            m = m_entry[0]
            cols = m_entry[2] if len(m_entry) > 2 else None
            if cols is not None:
                X_in = Xmat.reindex(columns=cols, fill_value=0.0)
            else:
                X_in = Xmat
            return np.ravel(m.predict(X_in.values))
        else:
            # unexpected format
            return np.zeros(len(Xmat))


def run_forecast(reserve_csv: str,
                 reserve_date_col: str, reserve_count_col: str, reserve_fixed_col: str,
                 start_date: Optional[str], end_date: Optional[str], future_days: Optional[int],
                 out_csv: str, method: str = "auto",
                 emit_manual_string: bool = False,
                 train_end_date: Optional[str] = None,
                 blend_naive: bool = True,
                 blend_default_alpha: float = 0.8,
                 blend_alpha_steps: int = 11,
                 drop_const_threshold: float = 0.0,
                 fast: bool = False,
                 lgbm_hpo: bool = False,
                 lgbm_hpo_sum_only: bool = False,
                 leak_audit: bool = False) -> str:
    df_r = _read_csv_any(reserve_csv)
    if df_r is None:
        raise FileNotFoundError(f"予約CSVが見つかりません: {reserve_csv}")
    hist = preprocess_reserve(df_r, reserve_date_col, reserve_count_col, reserve_fixed_col)
    if len(hist) == 0:
        raise RuntimeError("予約の履歴が空です。")
    # De-duplicate and sort
    if not hist.index.is_unique:
        hist = hist.groupby(level=0).agg({
            "reserve_count": "sum",
            "reserve_sum": "sum",
            "fixed_ratio": "mean",
        })
    hist = hist.sort_index()

    # Define prediction window
    ld = pd.to_datetime(hist.index.max()).normalize()
    if start_date and end_date:
        idx_pred = pd.date_range(pd.to_datetime(start_date), pd.to_datetime(end_date), freq="D")
    else:
        n = int(future_days or 7)
        idx_pred = pd.date_range(ld + pd.Timedelta(days=1), periods=n, freq="D")

    # Optional training cutoff (leak-free evaluation): restrict training history to <= train_end_date
    hist_train = hist.copy()
    if train_end_date:
        try:
            cutoff = pd.to_datetime(train_end_date).normalize()
            hist_train = hist.loc[hist.index <= cutoff]
            if len(hist_train) < 30:
                # Ensure we have a minimal amount of training data; if too short, fallback to full hist
                hist_train = hist.copy()
        except Exception:
            pass

    # Train one model per target or a multi-target simple loop
    X_hist = _make_features(hist_train)
    # drop near-constant features for speed if requested
    if drop_const_threshold and drop_const_threshold > 0.0:
        var = X_hist.var(axis=0)
        keep = var[var >= float(drop_const_threshold)].index.tolist()
        if len(keep) == 0:
            keep = X_hist.columns.tolist()
        X_hist = X_hist[keep]
    y_cols = ["reserve_count", "reserve_sum", "fixed_ratio"]
    models: Dict[str, object] = {}
    meta_models: Dict[str, Optional[object]] = {}
    blend_alpha: Dict[str, float] = {c: float(blend_default_alpha) for c in y_cols}
    use_stack = (method in ("stack", "stackoof"))
    use_oof = (method == "stackoof")
    # 時系列の末尾を検証にする時間分割
    val_tail = 28 if len(X_hist) > 200 else (14 if len(X_hist) > 60 else 7)
    # keep DataFrame form to allow per-target column dropping (e.g., remove fixed_ratio features)
    X_all_hist_df = X_hist.copy()
    for col in y_cols:
        y_all = hist[col].reindex(X_hist.index).fillna(0.0).values.astype(float)
        # prepare feature matrix per-target: drop fixed_ratio-derived features for other targets
        if col != "fixed_ratio":
            feats_df_for_col = X_all_hist_df.drop(columns=[c for c in X_all_hist_df.columns if c.startswith("fixed_ratio")], errors='ignore')
        else:
            feats_df_for_col = X_all_hist_df
        X_all_hist = feats_df_for_col.values
        train_cols_for_col = feats_df_for_col.columns.tolist()
        if use_stack and use_oof:
            # OOFスタッキング
            splits = _time_series_oof_splits(len(X_all_hist), k=5)
            P_list: List[np.ndarray] = []
            y_list: List[np.ndarray] = []
            names_list: List[List[str]] = []
            for tr, va in splits:
                X_tr, y_tr = X_all_hist[tr], y_all[tr]
                X_va, y_va = X_all_hist[va], y_all[va]
                base_models = _fit_base_models(X_tr, y_tr, X_va, y_va, base_hpo=False)
                if len(base_models) >= 2 and len(X_va) > 0:
                    names = [name for name, _ in base_models]
                    P = np.column_stack([np.ravel(m.predict(X_va)) for _, m in base_models])
                    P_list.append(P)
                    y_list.append(y_va)
                    names_list.append(names)
            if P_list:
                # 列（ベースモデル）の不一致対策: すべてのfoldに共通するモデル名に揃える
                common = None
                for names in names_list:
                    s = set(names)
                    common = (s if common is None else (common & s))
                common_names = sorted(list(common)) if common else []
                # 安全策: 共通が少なすぎる場合は、最も頻出の名前の並びを採用
                if len(common_names) < 1:
                    from collections import Counter
                    cnt = Counter([n for names in names_list for n in names])
                    common_names = [n for n, _ in cnt.most_common(3)]
                # 各foldのPを共通並びに再構成
                P_use_list: List[np.ndarray] = []
                for P, names in zip(P_list, names_list):
                    name_to_idx = {n: i for i, n in enumerate(names)}
                    cols = []
                    for n in common_names:
                        if n in name_to_idx:
                            cols.append(P[:, name_to_idx[n]].reshape(-1, 1))
                    if cols:
                        P_use_list.append(np.hstack(cols))
                P_oof = np.vstack(P_use_list) if P_use_list else np.vstack(P_list)
                y_oof = np.concatenate(y_list)
                from sklearn.linear_model import Ridge
                meta = Ridge(alpha=0.5)
                meta.fit(P_oof, y_oof)
            else:
                meta = None
            # 全履歴でベースを再学習
            base_full = _fit_base_models(X_all_hist, y_all, None, None, base_hpo=False)
            # attach training columns to each base model for alignment at prediction
            base_with_cols = []
            for name, m in base_full:
                base_with_cols.append((name, m, train_cols_for_col))
            models[col] = ("stack", base_with_cols)
            # 予測時に列合わせするため、メタモデルと使用モデル名をセットで保存
            try:
                meta_models[col] = (meta, common_names)
            except Exception:
                meta_models[col] = (meta, [name for name, _ in base_full])
        elif use_stack:
            # 単純スタッキング（末尾val） + 軽HPO
            if len(X_all_hist) > val_tail + 28:
                X_tr, y_tr = X_all_hist[:-val_tail], y_all[:-val_tail]
                X_va, y_va = X_all_hist[-val_tail:], y_all[-val_tail:]
            else:
                X_tr, y_tr = X_all_hist, y_all
                X_va, y_va = None, None
            base_models = _fit_base_models(X_tr, y_tr, X_va, y_va, base_hpo=True, fast=fast)
            if X_va is not None and y_va is not None and len(base_models) >= 2 and len(X_va) > 0:
                P_va = np.column_stack([np.ravel(m.predict(X_va)) for _, m in base_models])
                from sklearn.linear_model import Ridge
                meta = Ridge(alpha=0.5)
                meta.fit(P_va, y_va)
            else:
                meta = None
            # ベースを全履歴でリフィット
            base_refit: List[Tuple[str, object, list]] = []
            for name, m in base_models:
                try:
                    m.fit(X_all_hist, y_all)
                except Exception:
                    pass
                base_refit.append((name, m, train_cols_for_col))
            models[col] = ("stack", base_refit)
            meta_models[col] = meta
        else:
            if len(X_all_hist) > val_tail + 28:
                X_tr, y_tr = X_all_hist[:-val_tail], y_all[:-val_tail]
                X_va, y_va = X_all_hist[-val_tail:], y_all[-val_tail:]
            else:
                X_tr, y_tr = X_all_hist, y_all
                X_va, y_va = None, None
            # If method=lgbm and HPO enabled, run a tiny HPO (optionally only for reserve_sum)
            if (method == "lgbm") and (lgbm_hpo) and (not lgbm_hpo_sum_only or col == "reserve_sum") and (X_va is not None) and (y_va is not None) and (len(X_va) > 0):
                try:
                    import lightgbm as lgb
                    m = _lgbm_hpo(X_tr, y_tr, X_va, y_va, fast=fast)
                    if m is None:
                        raise ImportError
                    name = "lgbm"
                except Exception:
                    m, name = _fit_regressor(X_tr, y_tr, method=method, X_val=X_va, y_val=y_va, fast=fast)
            else:
                m, name = _fit_regressor(X_tr, y_tr, method=method, X_val=X_va, y_val=y_va, fast=fast)
            # save the exact training columns for this target for alignment
            models[col] = (m, name, train_cols_for_col)
            meta_models[col] = None

    # Learn blend weight alpha on validation tail using training history only
    if blend_naive:
        val_tail = 28 if len(X_hist) > 200 else (14 if len(X_hist) > 60 else 7)
        if len(X_hist) >= val_tail + 10:  # ensure minimal samples
            X_val_full = X_hist.tail(val_tail)
            dates_val = X_val_full.index
            for col in y_cols:
                y_true = hist[col].reindex(dates_val).values.astype(float)
                # Per-target feature alignment (drop fixed_ratio-derived features for non-fixed targets)
                if col != "fixed_ratio":
                    X_val = X_val_full.drop(columns=[c for c in X_val_full.columns if c.startswith("fixed_ratio")], errors='ignore')
                else:
                    X_val = X_val_full
                # model predictions on validation window with aligned features
                y_model = _predict_for_col(X_val, models[col], meta_models.get(col), use_stack)
                # same-DOW naive baseline using only past up to each date
                y_naive = _dow_baseline_series(hist_train, col, dates_val, window_same_dow=8, agg="median")
                m = np.isfinite(y_true) & np.isfinite(y_model) & np.isfinite(y_naive)
                if m.sum() < max(5, val_tail // 2):
                    continue
                y_t = y_true[m]; p_m = y_model[m]; p_n = y_naive[m]
                # Grid search alpha in [0,1]
                best_a, best_mae = blend_default_alpha, float("inf")
                steps = max(3, int(blend_alpha_steps))
                for a in np.linspace(0.0, 1.0, steps):
                    pred = a * p_m + (1 - a) * p_n
                    mae = float(np.mean(np.abs(y_t - pred)))
                    if mae < best_mae:
                        best_mae, best_a = mae, a
                blend_alpha[col] = float(best_a)

    # Predict
    # Build features for prediction using ONLY training history to avoid leakage
    X_all = _make_features(pd.concat([hist_train, pd.DataFrame(index=idx_pred)], axis=0))
    # Safety: drop any duplicate index that may appear due to upstream data
    if not X_all.index.is_unique:
        X_all = X_all[~X_all.index.duplicated(keep="last")]
    X_pred = X_all.reindex(idx_pred).fillna(0.0)
    # apply same drop_const to prediction features
    if drop_const_threshold and drop_const_threshold > 0.0:
        X_pred = X_pred[X_hist.columns.intersection(X_pred.columns)]
    pred = pd.DataFrame(index=idx_pred)

    # Optional: Leakage audit — ensure that feature vectors at recent training dates do not change
    # when recomputed using only past data (exclude current-day target). This helps detect
    # accidental use of unshifted target values in features.
    if leak_audit:
        try:
            tail_check = min(14, len(X_hist))
            if tail_check > 0:
                dates_check = list(X_hist.tail(tail_check).index)
                for d in dates_check:
                    past = hist_train.loc[hist_train.index < d]
                    # recompute features using only past plus placeholder row at d
                    X_chk_all = _make_features(pd.concat([past, pd.DataFrame(index=pd.DatetimeIndex([d]))], axis=0))
                    if d not in X_chk_all.index:
                        continue
                    # Align columns
                    cols_common = X_hist.columns.intersection(X_chk_all.columns)
                    v1 = X_hist.loc[d, cols_common].astype(float).values
                    v2 = X_chk_all.loc[d, cols_common].astype(float).values
                    if not np.allclose(v1, v2, atol=1e-8, rtol=1e-6):
                        dif = np.abs(v1 - v2)
                        bad_idx = np.where(dif > 1e-6)[0][:5]
                        bad_cols = [cols_common[i] for i in bad_idx]
                        raise AssertionError(f"Leak audit failed at {d.date()}: features differ when excluding current day. Example cols: {bad_cols}")
        except Exception as e:
            raise
    for col in y_cols:
        # For prediction, drop fixed_ratio-derived features for other targets to match training
        if col != "fixed_ratio":
            X_pred_col = X_pred.drop(columns=[c for c in X_pred.columns if c.startswith("fixed_ratio")], errors='ignore')
        else:
            X_pred_col = X_pred
        yhat_model = _predict_for_col(X_pred_col, models[col], meta_models.get(col), use_stack)
        if blend_naive:
            naive = _dow_baseline_series(hist_train, col, idx_pred, window_same_dow=8, agg="median")
            a = blend_alpha.get(col, blend_default_alpha)
            yhat = a * yhat_model + (1 - a) * naive
        else:
            yhat = yhat_model
        # Clamp/fix bounds
        if col in ("reserve_count", "reserve_sum"):
            yhat = np.clip(yhat, 0.0, None)
        if col == "fixed_ratio":
            yhat = np.clip(yhat, 0.0, 1.0)
        pred[col] = yhat

    # Output CSV
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    out = pred.copy()
    out.index.name = "date"
    out.to_csv(out_csv, encoding="utf-8-sig")

    # Optional: emit manual-reserve string for serve
    manual_str = ""  # YYYY-MM-DD=count,sum,fixed;...
    if emit_manual_string:
        toks = []
        for d, row in out.iterrows():
            toks.append(f"{d.date()}={row['reserve_count']:.0f},{row['reserve_sum']:.0f},{row['fixed_ratio']:.3f}")
        manual_str = ";".join(toks)
        print(manual_str)

    print(f"[SAVED] reserve forecast -> {out_csv}")
    return manual_str


def main():
    ap = argparse.ArgumentParser(description="Forecast daily reservations (count/sum/fixed_ratio)")
    ap.add_argument("--reserve-csv", type=str, required=True)
    ap.add_argument("--reserve-date-col", type=str, default="予約日")
    ap.add_argument("--reserve-count-col", type=str, default="台数")
    ap.add_argument("--reserve-fixed-col", type=str, default="固定客")
    ap.add_argument("--start-date", type=str, default=None)
    ap.add_argument("--end-date", type=str, default=None)
    ap.add_argument("--future-days", type=int, default=7)
    ap.add_argument("--out-csv", type=str, required=True)
    ap.add_argument("--method", type=str, default="auto", choices=["auto", "lgbm", "xgb", "cat", "gbr", "stack", "stackoof"])
    ap.add_argument("--emit-manual-string", action="store_true")
    ap.add_argument("--train-end-date", type=str, default=None, help="学習に使う履歴の最終日（これ以降のデータは学習に使わない）")
    ap.add_argument("--blend-naive", action="store_true", help="同曜日ナイーブとのブレンドを有効化（デフォルト有効）")
    ap.add_argument("--no-blend-naive", action="store_true", help="同曜日ナイーブブレンドを無効化するフラグ")
    ap.add_argument("--blend-default-alpha", type=float, default=0.8, help="検証で重みが学習できない場合のデフォルトα（モデル側の重み）")
    ap.add_argument("--blend-alpha-steps", type=int, default=11, help="α探索の分割数（デフォルト11=0.0..1.0を0.1刻み）")
    ap.add_argument("--lgbm-hpo", action="store_true", help="method=lgbm のとき軽量HPOを有効化")
    ap.add_argument("--lgbm-hpo-sum-only", action="store_true", help="reserve_sum にのみHPOを適用")

    args = ap.parse_args()
    # resolve blend flag
    blend_flag = True
    if getattr(args, "no_blend_naive", False):
        blend_flag = False
    elif getattr(args, "blend_naive", False):
        blend_flag = True

    run_forecast(reserve_csv=args.reserve_csv,
                 reserve_date_col=args.reserve_date_col,
                 reserve_count_col=args.reserve_count_col,
                 reserve_fixed_col=args.reserve_fixed_col,
                 start_date=args.start_date, end_date=args.end_date,
                 future_days=args.future_days,
                 out_csv=args.out_csv, method=args.method,
                 emit_manual_string=bool(args.emit_manual_string),
                 train_end_date=args.train_end_date,
                 blend_naive=blend_flag,
                 blend_default_alpha=float(args.blend_default_alpha),
                 blend_alpha_steps=int(getattr(args, "blend_alpha_steps", 11)),
                 lgbm_hpo=bool(getattr(args, "lgbm_hpo", False)),
                 lgbm_hpo_sum_only=bool(getattr(args, "lgbm_hpo_sum_only", False)))


if __name__ == "__main__":
    main()
