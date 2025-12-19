# -*- coding: utf-8 -*-
"""
serve_predict_model_v4_2_4.py

目的:
- predict_model_v4_2_4_best_repro.py が保存したサービング用バンドル(.joblib)を読み込み、
  未来N日分の予測を生成してCSV出力する推論スクリプト。

入出力:
- 入力: --bundle (必須), （任意）--reserve-csv と列名指定, 予測日数(--future-days)または --start-date/--end-date
- 出力: --out-csv (日付, sum_items_pred, p50, p90, mean_pred, total_pred の表)

注意:
- バンドル内の cfg/target_items/stage1_packs/stage2_models/history_tail を使用
- 予約が無い場合は予約特徴を 0 扱い
- total 系特徴の将来ラグ/MAは「最後の実績値を引き伸ばす」保守的な生成
"""

import os, argparse, json, warnings, re
from typing import Optional, Dict, List, Tuple
import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore", category=UserWarning)


# ===== Utils =====
def _norm_col(s: str) -> str:
    if s is None: return ""
    t = str(s).replace("\u3000"," ").strip()
    t = re.sub(r"[\s\-/＿－―・:：()\[\]（）［］]+","", t)
    try:
        import unicodedata; t = unicodedata.normalize("NFKC", t)
    except Exception: pass
    return t.lower()

def _parse_date_series(sr: pd.Series) -> pd.Series:
    def _clean(x: str) -> str:
        if x is None or (isinstance(x, float) and pd.isna(x)): return ""
        s = str(x)
        s = re.sub(r"[\(（][^\)）]*[\)）]", "", s)
        s = s.replace("年","/").replace("月","/").replace("日","")
        s = s.replace("-", "/").strip()
        return s
    s = sr.astype(str).map(_clean)
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().any(): return dt.dt.normalize()
    s2 = s.str.replace("/", "", regex=False)
    dt2 = pd.to_datetime(s2, format="%Y%m%d", errors="coerce")
    if dt2.notna().any(): return dt2.dt.normalize()
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
        return pd.read_csv(pd.io.common.StringIO(text), dtype=str, low_memory=False)
    except Exception:
        return None

def preprocess_reserve(df: Optional[pd.DataFrame], date_col: str, count_col: str, fixed_col: str) -> pd.DataFrame:
    if df is None or len(df)==0: return pd.DataFrame()
    dd = df.copy()
    # 自動列マッピング（緩やか）
    def _auto(df_, want):
        norm_map = {c: _norm_col(c) for c in df_.columns}
        inv = {}
        for k,v in norm_map.items(): inv.setdefault(v, []).append(k)
        out = {}
        for key, aliases in want.items():
            found = None
            for a in aliases:
                na = _norm_col(a)
                if na in inv: found = inv[na][0]; break
            if found is None:
                for na, cols in inv.items():
                    if any(_norm_col(a) in na for a in aliases): found = cols[0]; break
            if found is None:
                for na, cols in inv.items():
                    if any(na.startswith(_norm_col(a)) for a in aliases): found = cols[0]; break
            out[key] = found
        return out
    cmap = _auto(dd, {
        "date": [date_col, "予約日", "日付", "伝票日付"],
        "count":[count_col, "台数", "予約台数", "件数", "企業数", "total_customer_count"],
        "fixed": [fixed_col, "固定客", "固定", "fixed_customer_count"]
    })
    if cmap["date"] is None:
        raise ValueError("予約データの日付列が見つかりません。")
    dd[cmap["date"]] = _parse_date_series(dd[cmap["date"]])
    if cmap["count"] in dd.columns:
        dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]].astype(str).str.replace(",","", regex=False), errors="coerce")
    if cmap["fixed"] in dd.columns:
        # fixed列（固定客企業数）を数値に変換
        if pd.api.types.is_numeric_dtype(dd[cmap["fixed"]]):
            dd[cmap["fixed"]] = pd.to_numeric(dd[cmap["fixed"]], errors="coerce")
        else:
            # 文字列の場合はboolフラグとして処理
            dd[cmap["fixed"]] = dd[cmap["fixed"]].astype(str).str.lower().isin(["1","true","yes","固定","固定客"]).astype(int)
    grp = dd.groupby(cmap["date"]) if len(dd)>0 else None
    if grp is None or grp.size().sum()==0:
        return pd.DataFrame()
    out = pd.DataFrame({
        "reserve_count": (grp[cmap["count"]].sum() if cmap["count"] in dd.columns else grp.size()).astype(float),
        "reserve_sum": (grp[cmap["count"]].sum() if cmap["count"] in dd.columns else grp.size()).astype(float),
        "fixed_ratio": (
            (grp[cmap["fixed"]].sum() / grp[cmap["count"]].sum()).fillna(0.0) 
            if (cmap["fixed"] in dd.columns and cmap["count"] in dd.columns) 
            else 0.0
        )
    })
    return out

def build_calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    idx = pd.DatetimeIndex(index)
    df = pd.DataFrame(index=idx)
    df["dow"] = idx.weekday
    df["weekofyear"] = idx.isocalendar().week.astype(int)
    df["is_weekend"] = (df["dow"]>=5).astype(int)
    near = set()
    for d in idx[df["is_weekend"]==1]:
        near.add(d); near.add(d + pd.Timedelta(days=1)); near.add(d - pd.Timedelta(days=1))
    df["is_holiday_nearby"] = df.index.isin(list(near)).astype(int)
    ang = 2*np.pi*df["dow"]/7.0
    df["dow_sin"] = np.sin(ang); df["dow_cos"] = np.cos(ang)
    woy = df["weekofyear"].astype(float)
    df["woy_sin"] = np.sin(2*np.pi*woy/52.0)
    df["woy_cos"] = np.cos(2*np.pi*woy/52.0)
    return df

def build_exog(index: pd.DatetimeIndex, total: pd.Series,
               reserve_daily: Optional[pd.DataFrame], use_same_day_info: bool,
               shift_reserve_until: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    cal = build_calendar_features(index)
    ex = cal.copy()
    if isinstance(reserve_daily, pd.DataFrame) and len(reserve_daily)>0:
        r = reserve_daily.reindex(index).fillna(0.0)
        if not use_same_day_info:
            # 同日情報を使わない: 指定境界日までは1日シフト、それ以降（未来予測分）はシフトしない
            r_shift = r.shift(1)
            if shift_reserve_until is None:
                # 全期間シフト（後方一致）
                r = r_shift
            else:
                idx = pd.DatetimeIndex(index)
                past_mask = idx <= pd.Timestamp(shift_reserve_until)
                r = r.copy()
                # マスクで過去部分のみシフト値に置換
                if past_mask.any():
                    r.loc[past_mask, :] = r_shift.loc[past_mask, :]
            r = r.fillna(0.0)
        # 予約の移動平均（過去のみ）
        r_ma3 = r.rolling(3, min_periods=1).mean().shift(1).fillna(0.0)
        r_ma7 = r.rolling(7, min_periods=1).mean().shift(1).fillna(0.0)
        r_ma14 = r.rolling(14, min_periods=1).mean().shift(1).fillna(0.0)
        r_ma3.columns = [f"{c}_ma3" for c in r_ma3.columns]
        r_ma7.columns = [f"{c}_ma7" for c in r_ma7.columns]
        r_ma14.columns = [f"{c}_ma14" for c in r_ma14.columns]
        ex = ex.join(r).join(r_ma3).join(r_ma7).join(r_ma14)
    else:
        ex[["reserve_count","reserve_sum","fixed_ratio"]] = 0.0
    total = total.reindex(index).astype(float)
    ex["total_lag1"] = total.shift(1)
    ex["total_ma3"]  = total.rolling(3,  min_periods=1).mean().shift(1)
    ex["total_ma7"]  = total.rolling(7,  min_periods=1).mean().shift(1)
    ex["total_ma14"] = total.rolling(14, min_periods=1).mean().shift(1)
    return ex.fillna(0.0)

def predict_from_pack(X_today: pd.DataFrame, pack: Dict) -> float:
    preds = []
    cols = pack.get("cols", list(X_today.columns))
    X_today2 = X_today.reindex(columns=cols, fill_value=0.0)
    for name, model, scaler, selector in pack["base"]:
        Xt = selector.transform(scaler.transform(X_today2.values))
        preds.append(np.ravel(model.predict(Xt))[0])
    if not preds:
        return float("nan")
    M = np.array(preds).reshape(1,-1)
    meta = pack["meta"][1]
    return float(np.ravel(meta.predict(M))[0])

def make_stage2_matrix(df_in: pd.DataFrame, target_items: List[str], add_dow_item_interactions: bool) -> Tuple[pd.DataFrame, List[str]]:
    cols_pred = [f"{it}_pred" for it in target_items if f"{it}_pred" in df_in.columns]
    X = df_in.drop(columns=[c for c in ["合計"] if c in df_in.columns]).copy()
    if add_dow_item_interactions and "dow" in X.columns:
        d = pd.get_dummies(X["dow"].astype(int), prefix="dow", drop_first=False)
        X = X.join(d)
        for c in cols_pred:
            if c not in X.columns: continue
            for k in d.columns:
                X[f"{c}__{k}"] = X[c] * d[k]
    dt_cols = list(X.select_dtypes(include=["datetime","datetimetz","datetime64[ns]"]).columns)
    if dt_cols:
        X = X.drop(columns=dt_cols)
    feature_names = list(X.columns)
    return X.astype(float), feature_names

def _get_feat_names(models: Dict, default_cols: List[str]) -> List[str]:
    for k in ("_feature_names", "feature_names", "features"):
        v = models.get(k)
        if isinstance(v, (list, tuple)) and len(v)>0:
            return list(v)
    return list(default_cols)

def predict_total(models: Dict, x_today_raw: pd.DataFrame) -> Tuple[float,float,float]:
    # Handle flexible stored structures
    feat = _get_feat_names(models, list(x_today_raw.columns))
    x_aligned = x_today_raw.reindex(columns=feat, fill_value=0.0).fillna(0.0)

    scaler = models.get("scaler")
    selector = models.get("selector")
    Xt = x_aligned.values
    try:
        if scaler is not None:
            Xt = scaler.transform(Xt)
        if selector is not None:
            Xt = selector.transform(Xt)
    except Exception:
        # If transform fails, fall back to raw
        Xt = x_aligned.values

    # Models: try known keys, else fallbacks
    m_ls = models.get("ls") or models.get("mean") or models.get("gbdt_ls") or models.get("model")
    m_p50 = models.get("p50") or models.get("gbdt_p50")
    m_p90 = models.get("p90") or models.get("gbdt_p90")

    # Predict with available models
    mean = float(m_ls.predict(Xt)[0]) if m_ls is not None else float("nan")
    p50 = float(m_p50.predict(Xt)[0]) if m_p50 is not None else mean
    p90 = float(m_p90.predict(Xt)[0]) if m_p90 is not None else mean
    return p50, p90, mean

def _mae(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    m = np.isfinite(y) & np.isfinite(yhat)
    return float(np.mean(np.abs(y[m] - yhat[m]))) if m.sum() else float("nan")

def _blend_weight(y_true: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    # Guard: shape mismatch or empty → fallback to using b only (w=0.0)
    if not isinstance(a, np.ndarray): a = np.asarray(a)
    if not isinstance(b, np.ndarray): b = np.asarray(b)
    if not isinstance(y_true, np.ndarray): y_true = np.asarray(y_true)
    if len(y_true)==0 or len(a)==0 or len(b)==0:
        return 0.0
    n = min(len(y_true), len(a), len(b))
    if n <= 2:
        return 0.0
    # align last n elements
    yt, at, bt = y_true[-n:], a[-n:], b[-n:]
    k = min(28, max(8, n//4)) if n>8 else n
    yt, at, bt = yt[-k:], at[-k:], bt[-k:]
    best_w, best_mae = 0.0, 1e18
    for w in np.linspace(0,1,41):
        try:
            m = w*at + (1-w)*bt
        except Exception:
            continue
        v = _mae(yt, m)
        if np.isfinite(v) and v < best_mae:
            best_mae, best_w = v, float(w)
    return best_w

def _resid_bias_adjustment(pred_day: pd.Timestamp,
                           hist_df: pd.DataFrame,
                           target_items: List[str],
                           models_total: Dict,
                           w: float,
                           cfg: Dict) -> float:
    if hist_df is None or len(hist_df)==0: return 0.0
    try:
        idx_hist = pd.DatetimeIndex(hist_df.index)
        recent_mask = idx_hist >= (pd.Timestamp(pred_day) - pd.Timedelta(days=int(cfg.get("resid_bias_window_days", 42))))
        # 残差: 実測 - ブレンド
        feat_df, _ = make_stage2_matrix(hist_df, target_items, bool(cfg.get("add_dow_item_interactions", True)))
        Xt_hist = models_total["selector"].transform(
            models_total["scaler"].transform(
                feat_df.reindex(columns=models_total.get("_feature_names", feat_df.columns), fill_value=0.0).values
            )
        )
        direct_hist = np.ravel(models_total["ls"].predict(Xt_hist))
        sum_hist = hist_df[[c for c in hist_df.columns if c.endswith("_pred")]].sum(axis=1).values.astype(float)
        base_pred_hist = w * direct_hist + (1 - w) * sum_hist
        y_hist = hist_df["合計"].values.astype(float)
        resid = y_hist - base_pred_hist
        wd = idx_hist.weekday
        dow = int(pd.Timestamp(pred_day).weekday())
        mask = (wd == dow) & recent_mask
        r = resid[mask]
        r = r[np.isfinite(r)]
        if r.size == 0: return 0.0
        q = float(cfg.get("resid_bias_quantile", 0.5))
        adj = float(np.median(r)) if abs(q-0.5) < 1e-9 else float(np.quantile(r, q))
        r_all = resid[recent_mask]; r_all = r_all[np.isfinite(r_all)]
        if r_all.size >= 5:
            cap = float(np.quantile(np.abs(r_all), float(cfg.get("resid_bias_cap_pct", 0.85))))
            adj = float(np.clip(adj, -cap, cap))
        return adj
    except Exception:
        return 0.0

def _robust_std(x: np.ndarray) -> float:
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    if x.size < 3:
        return float("nan")
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    if mad > 0:
        return float(1.4826 * mad)
    # fallback to standard deviation
    return float(np.std(x, ddof=1)) if x.size > 1 else 0.0

def _time_decay_weights(n: int, mode: str = "linear") -> Optional[np.ndarray]:
    if n <= 0 or mode is None or mode == "none":
        return None
    t = np.linspace(0, 1, n)
    if mode == "linear":
        w = t
    elif mode == "exponential":
        w = np.exp(3 * t)
    else:
        return None
    s = w.sum()
    return w / s if s > 0 else None


# ===== Inference main =====
def run_inference(bundle_path: str,
                  res_walk_csv: Optional[str],
                  reserve_csv: Optional[str], reserve_date_col: str, reserve_count_col: str, reserve_fixed_col: str,
                  future_days: Optional[int], start_date: Optional[str], end_date: Optional[str], out_csv: str,
                  reserve_forecast_csv: Optional[str] = None,
                  weekly_bundle: Optional[str] = None,
                  weekly_meta_bundle: Optional[str] = None,
                  weekly_meta_alpha: float = 1.0,
                  weekly_meta_cap_low: Optional[float] = None,
                  weekly_meta_cap_high: Optional[float] = None,
                  mode: str = "base",
                  prompt_reserve: bool = False,
                  manual_reserve: Optional[str] = None,
                  reserve_default_count: Optional[float] = None,
                  reserve_default_sum: Optional[float] = None,
                  reserve_default_fixed: Optional[float] = None,
                  residual_refit: bool = False,
                  residual_refit_window: int = 90,
                  residual_model: str = "gbr",
                  disable_calibration: bool = False,
                  no_same_day_info: bool = False,
                  eval_sequential: bool = False,
                  auto_reserve: bool = False,
                  auto_reserve_window: int = 84,
                  auto_reserve_method: str = "dow_median",
                  # overrides for calibration/guardrails
                  calib_a_low: Optional[float] = None,
                  calib_a_high: Optional[float] = None,
                  calib_b_cap: Optional[float] = None,
                  calib_window_days: Optional[int] = None,
                  calib_window_days_tuesday: Optional[int] = None,
                  apply_zero_cap_in_base: bool = False,
                  zero_cap_quantile_override: Optional[float] = None):

    # Debug trace: begin
    try:
        print(f"[TRACE] run_inference: start bundle={bundle_path} out={out_csv}")
    except Exception:
        pass
    # Accept either a path to joblib file or an already-loaded bundle dict
    bundle_dir = None
    if isinstance(bundle_path, dict):
        bundle = bundle_path
    else:
        bundle = joblib.load(bundle_path)
        try:
            bundle_dir = os.path.dirname(bundle_path)
        except Exception:
            bundle_dir = None
    # 週次バンドル（任意）
    weekly_cfg = None; weekly_stage2 = None; weekly_w = None; weekly_calib = None
    if weekly_bundle:
        try:
            wb = joblib.load(weekly_bundle) if isinstance(weekly_bundle, str) else weekly_bundle
            if isinstance(wb, dict):
                weekly_cfg = wb.get('cfg', {})
                weekly_stage2 = wb.get('weekly_stage2')
                weekly_w = wb.get('w')
                weekly_calib = wb.get('calib')
                weekly_stack = wb.get('weekly_stack')
        except Exception:
            weekly_cfg = None; weekly_stage2 = None; weekly_w = None; weekly_calib = None
            weekly_stack = None

    # バンドル内のキー差異に対応（旧/新トレーナー両対応）
    cfg: Dict = bundle.get("cfg") or bundle.get("config") or {}
    target_items: List[str] = bundle.get("target_items", [])
    stage1_packs: Dict = bundle.get("stage1_packs") or bundle.get("item_packs") or {}
    models_total: Dict = bundle.get("stage2_models") or bundle.get("models_total") or {}
    hist_tail: pd.DataFrame = bundle.get("history_tail")
    # --- Safety: ensure history_tail does not contain future dates or accidental leakage ---
    try:
        if isinstance(hist_tail, pd.DataFrame) and len(hist_tail) > 0:
            # normalize/parse index to datetime if needed
            try:
                hist_tail_index = pd.DatetimeIndex(hist_tail.index)
            except Exception:
                # if index is a column-like, try to find a date-like column
                if "date" in hist_tail.columns:
                    hist_tail = hist_tail.set_index(pd.to_datetime(hist_tail["date"], errors="coerce"))
                else:
                    hist_tail.index = pd.to_datetime(pd.Series(hist_tail.index), errors="coerce")
            # drop rows with NaT index
            hist_tail = hist_tail[~pd.isna(pd.DatetimeIndex(hist_tail.index))]
            # If history contains any dates in the future (relative to now), trim them and warn
            now_dt = pd.Timestamp.utcnow().normalize()
            if len(hist_tail) > 0:
                max_hist = pd.DatetimeIndex(hist_tail.index).max()
                if max_hist > now_dt:
                    print(f"[WARN] history_tail contains future dates (max={max_hist.date()}); trimming to today ({now_dt.date()}).")
                    hist_tail = hist_tail.loc[pd.DatetimeIndex(hist_tail.index) <= now_dt]
    except Exception:
        # best-effort safety: if anything fails, ensure hist_tail is either a DataFrame or None
        try:
            if isinstance(hist_tail, pd.DataFrame) and len(hist_tail) == 0:
                hist_tail = pd.DataFrame()
        except Exception:
            hist_tail = pd.DataFrame()

    if not isinstance(hist_tail, pd.DataFrame) or len(hist_tail)==0:
        # Fallback: load res_walkforward.csv to derive total history
        # Prefer user-provided path; else try sibling file next to bundle
        if not res_walk_csv and bundle_dir:
            cand = os.path.join(bundle_dir, "res_walkforward.csv")
            if os.path.exists(cand):
                res_walk_csv = cand
        dfw = _read_csv_any(res_walk_csv) if res_walk_csv else None
        if dfw is None or len(dfw)==0:
            raise RuntimeError("bundle に history_tail が無く、res_walkforward.csv も見つかりません。--res-walk-csv を指定してください。")
        # Identify date index
        date_col = None
        for cand in ["date","日付","伝票日付"]:
            if cand in dfw.columns: date_col = cand; break
        if date_col is not None:
            dfw[date_col] = _parse_date_series(dfw[date_col]); dfw = dfw.set_index(date_col)
        else:
            dfw.index = _parse_date_series(pd.Series(dfw.index))
        # pick y_true
        def pick_col(df: pd.DataFrame, cands: List[str]) -> Optional[str]:
            for c in cands:
                if c in df.columns: return c
            low = {c: _norm_col(c) for c in df.columns}
            for c, n in low.items():
                if any(k in n for k in cands): return c
            return None
        y_col = pick_col(dfw, ["y_true","actual","y","truth"]) or "y_true"
        yy = pd.to_numeric(dfw[y_col].astype(str).str.replace(",","", regex=False), errors="coerce")
        hist_tail = pd.DataFrame({"合計": yy}).dropna()
        # Keep reasonable tail length if huge
        K = int(cfg.get("serving_history_days", 60)) if isinstance(cfg, dict) else 60
        if len(hist_tail) > max(90, K):
            hist_tail = hist_tail.tail(max(90, K))

    # 予測期間の決定（last_date が無いバンドルにも対応）
    ld_raw = bundle.get("last_date")
    if ld_raw is not None:
        try:
            last_date = pd.to_datetime(ld_raw).normalize()
        except Exception:
            last_date = pd.to_datetime(pd.DatetimeIndex(hist_tail.index).max()).normalize()
    else:
        last_date = pd.to_datetime(pd.DatetimeIndex(hist_tail.index).max()).normalize()

    if start_date and end_date:
        idx_future = pd.date_range(pd.to_datetime(start_date), pd.to_datetime(end_date), freq="D")
    else:
        n = int(future_days or 7)
        idx_future = pd.date_range(last_date + pd.Timedelta(days=1), periods=n, freq="D")
    try:
        print(f"[TRACE] future days: {len(idx_future)} from {idx_future.min().date() if len(idx_future)>0 else 'NA'} to {idx_future.max().date() if len(idx_future)>0 else 'NA'}")
    except Exception:
        pass

    # 予約読み込み
    reserve_daily = pd.DataFrame()
    if reserve_csv:
        try:
            for enc in (None, "utf-8-sig", "cp932"):
                try:
                    df_r = pd.read_csv(reserve_csv, encoding=enc, dtype=str, low_memory=False)
                    reserve_daily = preprocess_reserve(df_r, reserve_date_col, reserve_count_col, reserve_fixed_col)
                    break
                except Exception:
                    continue
        except Exception:
            reserve_daily = pd.DataFrame()

    # 予約予測CSVの取り込み（ある場合は未来日の予約を優先的に上書き）
    reserve_forecast = pd.DataFrame()
    if reserve_forecast_csv and os.path.exists(reserve_forecast_csv):
        try:
            df_rf = pd.read_csv(reserve_forecast_csv, dtype=str)
            # Safety check: ensure reserve forecast does not accidentally contain actuals/target columns
            lower_cols = [c.lower() for c in df_rf.columns]
            for banned in ("y_true", "actual", "合計", "total", "y"):
                if any(banned == c or banned in c for c in lower_cols):
                    raise RuntimeError(f"reserve_forecast_csv appears to contain target/actual column '{banned}' — aborting to avoid leakage.")
            # date パース
            if "date" in df_rf.columns:
                df_rf["date"] = pd.to_datetime(df_rf["date"], errors="coerce").dt.normalize()
                df_rf = df_rf.set_index("date")
            else:
                df_rf.index = pd.to_datetime(df_rf.index, errors="coerce").to_series().dt.normalize()
            # 重複日付を集約
            if not df_rf.index.is_unique:
                agg_map = {"reserve_count":"sum","reserve_sum":"sum","fixed_ratio":"mean"}
                cols_present = [c for c in ["reserve_count","reserve_sum","fixed_ratio"] if c in df_rf.columns]
                df_rf = df_rf.groupby(level=0)[cols_present].agg({c: agg_map[c] for c in cols_present})
            # 型変換とクリップ
            for c in ["reserve_count", "reserve_sum", "fixed_ratio"]:
                if c in df_rf.columns:
                    if c == "fixed_ratio":
                        df_rf[c] = pd.to_numeric(df_rf[c], errors="coerce").clip(0.0, 1.0)
                    else:
                        df_rf[c] = pd.to_numeric(df_rf[c], errors="coerce").clip(lower=0.0)
            reserve_forecast = df_rf[[c for c in ["reserve_count","reserve_sum","fixed_ratio"] if c in df_rf.columns]].dropna(how="all").sort_index()
        except Exception:
            reserve_forecast = pd.DataFrame()

    # manual_reserve のパース（形式: "YYYY-MM-DD=count,sum[,fixed];YYYY-MM-DD=count,sum"）
    manual_map = {}
    if manual_reserve:
        try:
            for token in str(manual_reserve).split(";"):
                token = token.strip()
                if not token:
                    continue
                if "=" in token:
                    day, vals = token.split("=", 1)
                elif ":" in token:
                    day, vals = token.split(":", 1)
                else:
                    continue
                d = pd.to_datetime(day.strip(), errors="coerce")
                if pd.isna(d):
                    continue
                parts = [v.strip() for v in vals.split(",")]
                c = float(parts[0]) if len(parts) > 0 and parts[0] != "" else (reserve_default_count if reserve_default_count is not None else 0.0)
                s = float(parts[1]) if len(parts) > 1 and parts[1] != "" else (reserve_default_sum if reserve_default_sum is not None else 0.0)
                f = float(parts[2]) if len(parts) > 2 and parts[2] != "" else (reserve_default_fixed if reserve_default_fixed is not None else 0.0)
                manual_map[pd.Timestamp(d).normalize()] = (c, s, f)
        except Exception:
            pass

    # total系列（合計）の将来拡張（最後の値を固定延長）
    total_hist = hist_tail["合計"].astype(float).copy()
    if len(total_hist)==0:
        raise RuntimeError("history_tail に '合計' 列がありません。")
    # 将来拡張: 履歴と重複しない日だけに限定し、重複があれば末尾を優先
    add_idx = pd.DatetimeIndex(idx_future)
    add_idx = add_idx[~add_idx.isin(total_hist.index)]
    ext = pd.Series([total_hist.iloc[-1]]*len(add_idx), index=add_idx)
    if len(ext) > 0:
        total_ext = pd.concat([total_hist, ext])
    else:
        total_ext = total_hist.copy()
    if not total_ext.index.is_unique:
        total_ext = total_ext[~total_ext.index.duplicated(keep="last")]

    # 過去（hist_tail.index）用の exog と per-item 予測を作り、w を推定
    idx_hist = pd.DatetimeIndex(hist_tail.index)
    use_same_day = bool(cfg.get("use_same_day_info", True))
    if no_same_day_info:
        use_same_day = False
    exog_hist = build_exog(idx_hist, total_hist, reserve_daily, use_same_day, shift_reserve_until=idx_hist.max())
    per_item_hist = {}
    for it in target_items:
        pack = stage1_packs.get(it)
        if pack is None: continue
        vals = []
        for d in idx_hist:
            today_feats = exog_hist.loc[[d]]
            vals.append(predict_from_pack(today_feats, pack))
        per_item_hist[it] = pd.Series(vals, index=idx_hist, dtype=float)
    # per_item_hist が空でも後段で安全に扱えるよう、sum_hist は hist_df から再計算する（ここではダミー）
    sum_hist = pd.Series(dtype=float)

    # Stage2 入力を組み立てて direct_hist を算出
    rows = []
    for d in idx_hist:
        row = {f"{it}_pred": per_item_hist.get(it, pd.Series(index=idx_hist)).reindex([d]).iloc[0] if it in per_item_hist else np.nan
               for it in target_items}
        for c in exog_hist.columns:
            row[c] = float(exog_hist.loc[d, c])
        row["合計"] = float(total_hist.loc[d])
        rows.append((d, row))
    hist_df = pd.DataFrame([r for _, r in rows], index=[t for t,_ in rows])
    hist_feat, feat_names = make_stage2_matrix(hist_df, target_items, bool(cfg.get("add_dow_item_interactions", True)))
    hist_feat = hist_feat.fillna(0.0)
    # Align features and apply available preprocessing
    feat = _get_feat_names(models_total, feat_names)
    Xh = hist_feat.reindex(columns=feat, fill_value=0.0).fillna(0.0)
    Xt = Xh.values
    try:
        sc = models_total.get("scaler"); sel = models_total.get("selector")
        if sc is not None:
            Xt = sc.transform(Xt)
        if sel is not None:
            Xt = sel.transform(Xt)
    except Exception:
        Xt = Xh.values
    m_ls = models_total.get("ls") or models_total.get("mean") or models_total.get("gbdt_ls") or models_total.get("model")
    direct_hist = pd.Series(np.ravel(m_ls.predict(Xt)) if m_ls is not None else np.nan, index=hist_df.index)

    # sum_hist を hist_df 上の *_pred から再計算（列が無い場合はゼロ）
    pred_cols = [c for c in hist_df.columns if c.endswith("_pred")]
    if pred_cols:
        sum_hist_series = hist_df[pred_cols].sum(axis=1).fillna(0.0).astype(float)
    else:
        sum_hist_series = pd.Series(0.0, index=hist_df.index, dtype=float)

    y_hist = hist_df["合計"].values.astype(float)
    w = _blend_weight(y_hist, direct_hist.values, sum_hist_series.values)

    # 残差の頑健な標準偏差（同曜日/全体）を事前計算し、シグマ推定のフォールバックに使用
    base_pred_hist_full = (w * direct_hist.values + (1.0 - w) * sum_hist_series.values)
    resid_hist_full = y_hist - base_pred_hist_full
    idx_hist_weekday = pd.DatetimeIndex(hist_df.index).weekday
    W_sigma = int(cfg.get("sigma_window_days", cfg.get("calibration_window_days_tuesday", 56))) if isinstance(cfg, dict) else 56
    resid_std_by_dow = {}
    for dwd in range(7):
        mask = (idx_hist_weekday == dwd)
        r = resid_hist_full[-W_sigma:][mask[-W_sigma:]] if len(resid_hist_full) >= 1 else np.array([])
        resid_std_by_dow[dwd] = _robust_std(r) if r.size > 0 else float("nan")
    resid_std_all = _robust_std(resid_hist_full[-max(28, W_sigma):])

    # 未来推論ベース
    # 予測開始日（horizon算出/アンカー決定用）
    pred_start = pd.DatetimeIndex(idx_future).min()
    anchor_dt = pd.Timestamp(pred_start) - pd.Timedelta(days=1)

    # 週次評価（weekly_bundle 指定）では、評価ウィンドウ内の実績『合計』をラグ/移動平均に絶対に使わない。
    # よって特徴量用の total 系列は anchor までの実績のみを残し、以降は直近実績の定数延長に固定する。
    total_for_exog = total_ext.copy()
    try:
        if weekly_bundle:
            hist_until_anchor = total_hist.loc[pd.DatetimeIndex(total_hist.index) <= anchor_dt]
            if len(hist_until_anchor) == 0:
                # フォールバック: 何も無ければ total_hist の末尾を1点だけ採用
                hist_until_anchor = total_hist.tail(1)
            last_val = float(hist_until_anchor.iloc[-1]) if len(hist_until_anchor) > 0 else float(total_hist.iloc[-1])
            # anchor より後の全インデックス（評価対象を含む）を定数延長で再構成
            future_idx_for_feat = pd.DatetimeIndex([d for d in total_ext.index if d > anchor_dt])
            const_ext = pd.Series([last_val]*len(future_idx_for_feat), index=future_idx_for_feat)
            total_for_exog = pd.concat([hist_until_anchor, const_ext])
            # 重複を除去（末尾を優先）
            if not total_for_exog.index.is_unique:
                total_for_exog = total_for_exog[~total_for_exog.index.duplicated(keep="last")]
    except Exception:
        total_for_exog = total_ext.copy()

    # 予測開始日より後は予約の同日情報をシフトしない（no_same_day_infoの適用は過去部分のみ）
    if no_same_day_info:
        shift_until = min(pd.Timestamp(pred_start) - pd.Timedelta(days=1), pd.Timestamp(idx_hist.max()))
    else:
        shift_until = None
    exog_all = build_exog(total_for_exog.index, total_for_exog, reserve_daily, use_same_day, shift_reserve_until=shift_until)
    if not exog_all.index.is_unique:
        exog_all = exog_all[~exog_all.index.duplicated(keep="last")]
    # 予測開始日（horizon算出用）
    pred_start_dt = pd.DatetimeIndex(idx_future).min()

    # 実績(y_true)の読み込み（評価/順次再学習用）
    actuals = pd.Series(dtype=float)
    if res_walk_csv:
        dfw_any = _read_csv_any(res_walk_csv)
        if dfw_any is not None and len(dfw_any)>0:
            # date列とy_trueの推定
            dcol = None
            for cand in ["date","日付","伝票日付"]:
                if cand in dfw_any.columns:
                    dcol = cand; break
            if dcol is not None:
                dfw_any[dcol] = _parse_date_series(dfw_any[dcol]); dfw_any = dfw_any.set_index(dcol)
            else:
                dfw_any.index = _parse_date_series(pd.Series(dfw_any.index))
            ycol = None
            for cand in ["y_true","actual","y","truth"]:
                if cand in dfw_any.columns:
                    ycol = cand; break
            if ycol is not None:
                actuals = pd.to_numeric(dfw_any[ycol].astype(str).str.replace(",","", regex=False), errors="coerce").dropna()
                actuals.index = pd.DatetimeIndex(actuals.index)

    # 順次再学習に使う可変な履歴と統計
    total_hist_cur = total_hist.copy()
    hist_df_cur = hist_df.copy()
    direct_hist_cur = direct_hist.copy()
    sum_hist_series_cur = sum_hist_series.copy()
    y_hist_cur = y_hist.copy()
    resid_std_by_dow_cur = dict(resid_std_by_dow)
    resid_std_all_cur = float(resid_std_all)
    w_cur = float(w)
    # 未来日の予約が欠落している場合の補完（manual -> prompt -> defaults -> 0）
    # reserve_daily を未来日インデックスで拡張
    if not isinstance(reserve_daily, pd.DataFrame) or reserve_daily.empty:
        reserve_daily = pd.DataFrame(columns=["reserve_count","reserve_sum","fixed_ratio"], dtype=float)
    reserve_daily = reserve_daily.copy()

    # 自動補完のためのDOW統計（履歴W日）を作成
    typical_by_dow = {}
    if auto_reserve and isinstance(reserve_daily, pd.DataFrame) and len(reserve_daily) > 0:
        try:
            # 学習に使う履歴: last_date 以前のデータから末尾W日
            res_hist = reserve_daily.copy()
            res_hist = res_hist.loc[res_hist.index <= last_date]
            if len(res_hist) > auto_reserve_window:
                res_hist = res_hist.tail(auto_reserve_window)
            if len(res_hist) > 0:
                dow = pd.DatetimeIndex(res_hist.index).weekday
                tmp = res_hist.copy(); tmp["dow"] = dow
                if auto_reserve_method == "dow_median":
                    stat = tmp.groupby("dow")[ ["reserve_count","reserve_sum","fixed_ratio"] ].median()
                else:
                    stat = tmp.groupby("dow")[ ["reserve_count","reserve_sum","fixed_ratio"] ].median()
                for dwd, row in stat.iterrows():
                    typical_by_dow[int(dwd)] = (float(row.get("reserve_count", 0.0) or 0.0),
                                                float(row.get("reserve_sum", 0.0) or 0.0),
                                                float(row.get("fixed_ratio", 0.0) or 0.0))
        except Exception:
            typical_by_dow = {}
    for d in idx_future:
        if d in manual_map:
            c, s, f = manual_map[d]
            reserve_daily.loc[d, ["reserve_count","reserve_sum","fixed_ratio"]] = [c, s, f]
        # 予約予測CSVがある場合は、未来日は常に予測で上書き（実予約の混入を防止）
        elif d in reserve_forecast.index:
            rr = reserve_forecast.reindex([d])
            c = float(rr["reserve_count"].iloc[0]) if "reserve_count" in rr.columns and pd.notna(rr["reserve_count"].iloc[0]) else 0.0
            s = float(rr["reserve_sum"].iloc[0]) if "reserve_sum" in rr.columns and pd.notna(rr["reserve_sum"].iloc[0]) else 0.0
            f = float(rr["fixed_ratio"].iloc[0]) if "fixed_ratio" in rr.columns and pd.notna(rr["fixed_ratio"].iloc[0]) else 0.0
            reserve_daily.loc[d, ["reserve_count","reserve_sum","fixed_ratio"]] = [c, s, f]
        elif (
            d not in reserve_daily.index or
            reserve_daily.reindex([d])[ ["reserve_count","reserve_sum"] ].isna().any().any()
        ):
            if prompt_reserve:
                # 対話プロンプト
                while True:
                    try:
                        raw = input(f"[INPUT] {d.date()} の予約 'count,sum[,fixed]' を入力してください（空でデフォルト）: ").strip()
                    except EOFError:
                        raw = ""
                    if raw == "":
                        # 自動補完 or デフォルト or 0
                        dwd = int(pd.Timestamp(d).weekday())
                        if auto_reserve and dwd in typical_by_dow:
                            c, s, f = typical_by_dow[dwd]
                        elif reserve_default_count is not None and reserve_default_sum is not None:
                            c = float(reserve_default_count); s = float(reserve_default_sum); f = float(reserve_default_fixed or 0.0)
                        else:
                            print("  デフォルト未指定のため、0で補完します。")
                            c = 0.0; s = 0.0; f = 0.0 if reserve_default_fixed is None else float(reserve_default_fixed)
                        break
                    parts = [p.strip() for p in raw.split(",")]
                    try:
                        c = float(parts[0]) if len(parts)>0 else 0.0
                        s = float(parts[1]) if len(parts)>1 else 0.0
                        f = float(parts[2]) if len(parts)>2 else float(reserve_default_fixed or 0.0)
                        break
                    except Exception:
                        print("  パースに失敗しました。例: 12,48 または 12,48,0")
                        continue
                reserve_daily.loc[d, ["reserve_count","reserve_sum","fixed_ratio"]] = [c, s, f]
            else:
                # 非対話: 自動補完 -> デフォルト -> 0
                dwd = int(pd.Timestamp(d).weekday())
                if auto_reserve and dwd in typical_by_dow:
                    c, s, f = typical_by_dow[dwd]
                else:
                    c = float(reserve_default_count) if reserve_default_count is not None else 0.0
                    s = float(reserve_default_sum) if reserve_default_sum is not None else 0.0
                    f = float(reserve_default_fixed) if reserve_default_fixed is not None else 0.0
                reserve_daily.loc[d, ["reserve_count","reserve_sum","fixed_ratio"]] = [c, s, f]
    # exog_all を予約で更新（インデックスを共通部分に揃える）
    _cols_res = ["reserve_count","reserve_sum","fixed_ratio"]
    common_idx = reserve_daily.index.intersection(exog_all.index)
    if len(common_idx) > 0:
        exog_all.loc[common_idx, _cols_res] = reserve_daily.reindex(common_idx)[_cols_res].fillna(0.0).values
    # 残差再学習（任意）: base_blend に対し (y - base_blend) を学習
    # mode=tuned のときのみ「曜日別の軽量モデル」も併用（h は曜日に対応）。
    resid_model = None
    resid_models_by_dow: Dict[int, object] = {}
    resid_feat_names: List[str] = []
    if residual_refit:
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.linear_model import Ridge
            # 学習データ（直近 W 日）
            W = int(max(30, residual_refit_window))
            # hist_df（上で作成済み）の特徴とターゲット
            hist_feat_for_resid = hist_feat.fillna(0.0)
            # base_blend（full）
            base_pred_hist_full = (w * direct_hist.values + (1.0 - w) * sum_hist_series.values)
            y_hist_full = y_hist
            # 末尾 W に制限
            if len(hist_feat_for_resid) > W:
                hist_feat_for_resid = hist_feat_for_resid.tail(W)
                base_pred_hist_full = base_pred_hist_full[-W:]
                y_hist_full = y_hist_full[-W:]
            resid_target = y_hist_full - base_pred_hist_full
            X_resid = hist_feat_for_resid.values
            resid_feat_names = list(hist_feat_for_resid.columns)
            # サンプル重み（線形時系列減衰）
            # base: 緩やか（linear）、tuned: 強め（exponential）
            sw = _time_decay_weights(len(X_resid), mode=("exponential" if mode=="tuned" else "linear"))
            if residual_model.lower() == "ridge":
                m = Ridge(alpha=2.0)
            else:
                m = GradientBoostingRegressor(
                    loss="absolute_error", n_estimators=200, learning_rate=0.04,
                    max_depth=2, subsample=0.8, random_state=42
                )
            try:
                m.fit(X_resid, resid_target, sample_weight=sw)
            except TypeError:
                m.fit(X_resid, resid_target)
            resid_model = m
            # mode=tuned の場合のみ曜日別モデルを作成
            if mode == "tuned":
                try:
                    if "dow" in hist_feat_for_resid.columns:
                        for dwd in range(7):
                            mask = (hist_feat_for_resid["dow"].astype(int) == dwd)
                            Xd = hist_feat_for_resid.loc[mask]
                            yd = resid_target[mask.values]
                            if len(Xd) >= max(18, W // 7):
                                if residual_model.lower() == "ridge":
                                    md = Ridge(alpha=3.0)
                                    try:
                                        md.fit(Xd.values, yd)
                                    except TypeError:
                                        md.fit(Xd.values, yd)
                                else:
                                    md = GradientBoostingRegressor(
                                        loss="absolute_error", n_estimators=160, learning_rate=0.045,
                                        max_depth=2, subsample=0.85, random_state=42
                                    )
                                    try:
                                        md.fit(Xd.values, yd)
                                    except TypeError:
                                        md.fit(Xd.values, yd)
                                resid_models_by_dow[int(dwd)] = md
                except Exception:
                    resid_models_by_dow = {}
            print(f"[INFO] residual-refit enabled: model={residual_model} window={W} rows={len(X_resid)} mode={mode} per-dow={len(resid_models_by_dow)}")
        except Exception as e:
            print(f"[WARN] residual-refit failed: {e}")

    results = []
    for d in idx_future:
        # eval_sequential: 直前に実績を取り込んだ場合、統計類を再構築
        if eval_sequential:
            try:
                # exog_hist_cur 再構築
                idx_hist_cur = pd.DatetimeIndex(total_hist_cur.index)
                exog_hist_cur = build_exog(idx_hist_cur, total_hist_cur, reserve_daily, use_same_day, shift_reserve_until=idx_hist_cur.max())
                # per-item 予測
                per_item_hist_cur = {}
                for it in target_items:
                    pack = stage1_packs.get(it)
                    if pack is None: continue
                    vals = []
                    for dd in idx_hist_cur:
                        vals.append(predict_from_pack(exog_hist_cur.loc[[dd]], pack))
                    per_item_hist_cur[it] = pd.Series(vals, index=idx_hist_cur, dtype=float)
                # hist_df_cur
                rows_cur = []
                for dd in idx_hist_cur:
                    row = {f"{it}_pred": per_item_hist_cur.get(it, pd.Series(index=idx_hist_cur)).reindex([dd]).iloc[0] if it in per_item_hist_cur else np.nan for it in target_items}
                    for c in exog_hist_cur.columns: row[c] = float(exog_hist_cur.loc[dd, c])
                    row["合計"] = float(total_hist_cur.loc[dd])
                    rows_cur.append((dd, row))
                hist_df_cur = pd.DataFrame([r for _, r in rows_cur], index=[t for t,_ in rows_cur])
                hist_feat_cur, feat_names_cur = make_stage2_matrix(hist_df_cur, target_items, bool(cfg.get("add_dow_item_interactions", True)))
                hist_feat_cur = hist_feat_cur.fillna(0.0)
                feat_cur = _get_feat_names(models_total, feat_names_cur)
                Xh_cur = hist_feat_cur.reindex(columns=feat_cur, fill_value=0.0).fillna(0.0)
                Xt_cur = Xh_cur.values
                try:
                    sc = models_total.get("scaler"); sel = models_total.get("selector")
                    if sc is not None: Xt_cur = sc.transform(Xt_cur)
                    if sel is not None: Xt_cur = sel.transform(Xt_cur)
                except Exception:
                    Xt_cur = Xh_cur.values
                m_ls = models_total.get("ls") or models_total.get("mean") or models_total.get("gbdt_ls") or models_total.get("model")
                direct_hist_cur = pd.Series(np.ravel(m_ls.predict(Xt_cur)) if m_ls is not None else np.nan, index=hist_df_cur.index)
                pred_cols_cur = [c for c in hist_df_cur.columns if c.endswith("_pred")]
                if pred_cols_cur:
                    sum_hist_series_cur = hist_df_cur[pred_cols_cur].sum(axis=1).fillna(0.0).astype(float)
                else:
                    sum_hist_series_cur = pd.Series(0.0, index=hist_df_cur.index, dtype=float)
                y_hist_cur = hist_df_cur["合計"].values.astype(float)
                w_cur = _blend_weight(y_hist_cur, direct_hist_cur.values, sum_hist_series_cur.values)
                # 残差統計
                base_pred_hist_full_cur = (w_cur * direct_hist_cur.values + (1.0 - w_cur) * sum_hist_series_cur.values)
                resid_hist_full_cur = y_hist_cur - base_pred_hist_full_cur
                idx_hist_weekday_cur = pd.DatetimeIndex(hist_df_cur.index).weekday
                W_sigma_cur = int(cfg.get("sigma_window_days", cfg.get("calibration_window_days_tuesday", 56))) if isinstance(cfg, dict) else 56
                resid_std_by_dow_cur = {}
                for dwd in range(7):
                    mask = (idx_hist_weekday_cur == dwd)
                    r = resid_hist_full_cur[-W_sigma_cur:][mask[-W_sigma_cur:]] if len(resid_hist_full_cur) >= 1 else np.array([])
                    resid_std_by_dow_cur[dwd] = _robust_std(r) if r.size > 0 else float("nan")
                resid_std_all_cur = _robust_std(resid_hist_full_cur[-max(28, W_sigma_cur):])
                # exog_all_cur
                add_idx2 = pd.DatetimeIndex([dd for dd in idx_future if dd not in total_hist_cur.index])
                ext2 = pd.Series([total_hist_cur.iloc[-1]]*len(add_idx2), index=add_idx2)
                if len(ext2) > 0:
                    total_ext_cur = pd.concat([total_hist_cur, ext2])
                else:
                    total_ext_cur = total_hist_cur.copy()
                if not total_ext_cur.index.is_unique:
                    total_ext_cur = total_ext_cur[~total_ext_cur.index.duplicated(keep="last")]
                # 予測開始日以降はシフトしない
                if no_same_day_info:
                    pred_start_cur = pd.DatetimeIndex(idx_future).min()
                    shift_until_cur = min(pd.Timestamp(pred_start_cur) - pd.Timedelta(days=1), pd.Timestamp(idx_hist_cur.max()))
                else:
                    shift_until_cur = None
                exog_all = build_exog(total_ext_cur.index, total_ext_cur, reserve_daily, use_same_day, shift_reserve_until=shift_until_cur)
            except Exception:
                pass

        today_feats = exog_all.loc[[d]]
        per_item_pred = {}
        for it in target_items:
            pack = stage1_packs.get(it)
            if pack is None: continue
            per_item_pred[it] = predict_from_pack(today_feats, pack)
        sum_items_today = float(np.nansum(list(per_item_pred.values())))

        x_total = {f"{it}_pred":[per_item_pred.get(it, np.nan)] for it in target_items}
        for c in today_feats.columns: x_total[c] = [float(today_feats.iloc[0][c])]
        x_total = pd.DataFrame(x_total, index=[d])
        x_total_proc, _ = make_stage2_matrix(x_total, target_items, bool(cfg.get("add_dow_item_interactions", True)))
        p50, p90, mean_pred = predict_total(models_total, x_total_proc)

        # Weekly override: prefer weekly_stack, else use weekly_stage2 or weekly w+calib when provided
        weekly_applied = False
        # stacking: if present, construct base preds and run meta
        if (not weekly_applied) and ('weekly_stack' in locals() and weekly_stack is not None):
            try:
                base_models = weekly_stack.get('base_models', [])
                meta = weekly_stack.get('meta_model') or weekly_stack.get('meta')
                # build base predictions vector
                base_preds = []
                # Build a robust feature row aligned to weekly_stack feature_names
                expected_fn = list(weekly_stack.get('feature_names', [])) if isinstance(weekly_stack, dict) else []
                dow_int = int(pd.to_datetime(d).weekday())
                # helper to safely get value from today_feats
                def _tf(name, default=0.0):
                    try:
                        if name in today_feats.columns:
                            return float(today_feats.iloc[0][name])
                    except Exception:
                        pass
                    return float(default)

                feat_row = {}
                # core preds
                feat_row['mean_pred'] = float(mean_pred) if np.isfinite(mean_pred) else 0.0
                feat_row['sum_items_pred'] = float(sum_items_today) if np.isfinite(sum_items_today) else 0.0
                try:
                    wwk_tmp = float(weekly_w) if weekly_w is not None else 0.5
                except Exception:
                    wwk_tmp = 0.5
                feat_row['base_blend'] = float(max(0.0, wwk_tmp * feat_row['mean_pred'] + (1.0 - wwk_tmp) * feat_row['sum_items_pred']))
                feat_row['direct_minus_sum'] = float(feat_row['mean_pred'] - feat_row['sum_items_pred'])
                # calendar / dow one-hot
                for k in range(7):
                    feat_row[f'dow_{k}'] = 1.0 if dow_int == k else 0.0
                # reserve-related and total-related features
                for name in expected_fn:
                    if name in feat_row:
                        continue
                    if name.startswith('reserve_') or name.startswith('fixed_ratio'):
                        feat_row[name] = _tf(name, 0.0)
                    elif name.startswith('total_') or name == 'total_lag1':
                        feat_row[name] = _tf(name, 0.0)
                    elif name == 'is_weekend' or name == 'is_holiday_nearby':
                        feat_row[name] = int(_tf(name, 0.0))
                    elif name == 'h':
                        try:
                            feat_row['h'] = int((pd.Timestamp(d) - pd.Timestamp(pred_start_dt)).days) + 1
                        except Exception:
                            feat_row['h'] = 1
                    elif name == 'mean_pred' or name == 'sum_items_pred' or name == 'base_blend' or name == 'direct_minus_sum':
                        # already set
                        pass
                    elif name.startswith('dow_'):
                        # already set by dow loop
                        pass
                    else:
                        # fallback: try today_feats, else 0
                        feat_row[name] = _tf(name, 0.0)

                Xw_df = pd.DataFrame([feat_row], index=[d])

                for mdl in base_models:
                    if mdl is None:
                        base_preds.append(0.0)
                        continue
                    try:
                        expected_cols = None
                        if hasattr(mdl, 'feature_name_'):
                            expected_cols = list(mdl.feature_name_)
                        elif hasattr(mdl, 'get_booster'):
                            try:
                                expected_cols = list(mdl.get_booster().feature_names)
                            except Exception:
                                expected_cols = None
                        if expected_cols is None:
                            Xw_vals = Xw_df.values
                        else:
                            Xw_vals = Xw_df.reindex(columns=expected_cols, fill_value=0.0).values
                        p = float(np.ravel(mdl.predict(Xw_vals))[0])
                    except Exception:
                        try:
                            p = float(np.ravel(mdl.predict(np.array([[feat_row.get('mean_pred',0.0), feat_row.get('sum_items_pred',0.0)]])))[0])
                        except Exception:
                            p = 0.0
                    base_preds.append(p)
                M = np.array(base_preds).reshape(1, -1)
                try:
                    # if meta scaler present, apply it first
                    scaler_meta = weekly_stack.get('meta_scaler') if isinstance(weekly_stack, dict) else None
                    if scaler_meta is not None:
                        M_proc = scaler_meta.transform(M)
                    else:
                        M_proc = M
                    meta_pred = float(np.ravel(meta.predict(M_proc))[0])
                except Exception:
                    try:
                        meta_pred = float(np.ravel(meta.predict(M))[0]) if hasattr(meta, 'predict') else 0.0
                    except Exception:
                        meta_pred = 0.0
                total_pred_today = float(max(0.0, meta_pred))
                weekly_applied = True
            except Exception:
                weekly_applied = False
        if weekly_stage2 is not None:
            try:
                fn = list(weekly_stage2.get('feature_names', []))
                featurizer = weekly_stage2.get('featurizer', 'mean_sum_dow')
                dow_int = int(pd.to_datetime(d).weekday())
                feat = {
                    'mean_pred': float(mean_pred) if np.isfinite(mean_pred) else 0.0,
                    'sum_items_pred': float(sum_items_today) if np.isfinite(sum_items_today) else 0.0,
                }
                # base_blend/diff は学習時の表現力を補助（w は weekly バンドルが持つ値を使用）
                try:
                    wwk_tmp = float(weekly_w) if weekly_w is not None else 0.5
                except Exception:
                    wwk_tmp = 0.5
                feat['base_blend'] = float(max(0.0, wwk_tmp*feat['mean_pred'] + (1.0-wwk_tmp)*feat['sum_items_pred']))
                feat['direct_minus_sum'] = float(feat['mean_pred'] - feat['sum_items_pred'])
                # DOW one-hot は常に追加
                for k in range(7):
                    feat[f'dow_{k}'] = 1.0 if dow_int == k else 0.0
                if featurizer == 'mean_sum_reserve_cal_h':
                    # exog から予約/カレンダー/horizon
                    def _getf(name, default=0.0):
                        try:
                            return float(today_feats.get(name, pd.Series([default], index=[d])).iloc[0])
                        except Exception:
                            return float(default)
                    feat.update({
                        'reserve_count': _getf('reserve_count', 0.0),
                        'reserve_sum': _getf('reserve_sum', 0.0),
                        'fixed_ratio': _getf('fixed_ratio', 0.0),
                        'reserve_count_ma3': _getf('reserve_count_ma3', 0.0),
                        'reserve_count_ma7': _getf('reserve_count_ma7', 0.0),
                        'reserve_count_ma14': _getf('reserve_count_ma14', 0.0),
                        'reserve_sum_ma3': _getf('reserve_sum_ma3', 0.0),
                        'reserve_sum_ma7': _getf('reserve_sum_ma7', 0.0),
                        'reserve_sum_ma14': _getf('reserve_sum_ma14', 0.0),
                        'fixed_ratio_ma3': _getf('fixed_ratio_ma3', 0.0),
                        'fixed_ratio_ma7': _getf('fixed_ratio_ma7', 0.0),
                        'fixed_ratio_ma14': _getf('fixed_ratio_ma14', 0.0),
                        # total 系履歴特徴（学習と整合）
                        'total_lag1': _getf('total_lag1', 0.0),
                        'total_ma3': _getf('total_ma3', 0.0),
                        'total_ma7': _getf('total_ma7', 0.0),
                        'total_ma14': _getf('total_ma14', 0.0),
                        'is_weekend': int(_getf('is_weekend', 0.0)),
                        'is_holiday_nearby': int(_getf('is_holiday_nearby', 0.0)),
                        'h': int((pd.Timestamp(d) - pd.Timestamp(pred_start_dt)).days) + 1 if 'pred_start_dt' in locals() else 1,
                    })
                dfX = pd.DataFrame([feat], index=[d])
                Xw = dfX.reindex(columns=fn, fill_value=0.0).values
                total_pred_today = float(np.ravel(weekly_stage2['model'].predict(Xw))[0])
                total_pred_today = float(max(0.0, total_pred_today))
                weekly_applied = True
            except Exception:
                weekly_applied = False
        if (not weekly_applied) and (weekly_w is not None or weekly_calib is not None):
            try:
                wwk = float(0.5 if weekly_w is None else weekly_w)
                base = float(max(0.0, wwk*mean_pred + (1.0-wwk)*sum_items_today))
                a, b = (1.0, 0.0)
                if isinstance(weekly_calib, dict):
                    a, b = weekly_calib.get(int(pd.to_datetime(d).weekday()), (1.0, 0.0))
                total_pred_today = float(max(0.0, float(a)*base + float(b)))
                weekly_applied = True
            except Exception:
                weekly_applied = False
        if not weekly_applied:
            total_pred_today = max(0.0, w_cur*mean_pred + (1.0-w_cur)*sum_items_today)

    # ゼロ予約×週末近傍の上限キャップ（tunedのみ）
        is_weekend = bool(today_feats.get("is_weekend", pd.Series([0], index=[d])).iloc[0])
        is_hnear   = bool(today_feats.get("is_holiday_nearby", pd.Series([0], index=[d])).iloc[0])
        if mode == "tuned" or apply_zero_cap_in_base:
            reserve_zero = (float(today_feats.get("reserve_count", pd.Series([0.0], index=[d])).iloc[0]) == 0.0) and \
                           (float(today_feats.get("reserve_sum",   pd.Series([0.0], index=[d])).iloc[0]) == 0.0)
            if reserve_zero and (is_weekend or is_hnear):
                hist_vals = hist_df["合計"].tail(180).values
                if len(hist_vals) >= 20:
                    zcq = float(zero_cap_quantile_override) if (zero_cap_quantile_override is not None) else float(cfg.get("zero_cap_quantile", 0.15))
                    cap = float(np.nanpercentile(hist_vals, 100*zcq))
                    sum_items_today = min(sum_items_today, cap)
                    total_pred_today = min(total_pred_today, cap)
                    p50 = min(p50, cap); p90 = min(p90, cap)

        # 曜日キャリブ（直近窓で a,b を推定）
        dow = int(pd.to_datetime(d).weekday())
        # 現在horizon（予測開始日からの経過日数+1）
        try:
            h_cur = int((pd.Timestamp(d) - pd.Timestamp(pred_start_dt)).days) + 1
        except Exception:
            h_cur = 1
        if not (disable_calibration or weekly_applied) and h_cur >= 2:
            # window overrides
            cw = int(cfg.get("calibration_window_days", 28))
            cwt = int(cfg.get("calibration_window_days_tuesday", 56))
            if calib_window_days is not None:
                cw = int(calib_window_days)
            if calib_window_days_tuesday is not None:
                cwt = int(calib_window_days_tuesday)
            Wc = int(cwt if dow==2 else cw)
            # tuned: 週末・祝日近傍では窓を延長
            is_weekend = bool(today_feats.get("is_weekend", pd.Series([0], index=[d])).iloc[0])
            is_hnear   = bool(today_feats.get("is_holiday_nearby", pd.Series([0], index=[d])).iloc[0])
            if mode == "tuned" and (is_weekend or is_hnear):
                Wc = int(min(90, max(Wc, int(Wc * 1.25))))
            if len(hist_df_cur) >= Wc:
                wd = pd.DatetimeIndex(hist_df_cur.index).weekday
                mask = (wd == dow)
                if mask.sum() >= 6:
                    # 配列長の整合を取りながらキャリブ
                    base_pred_hist = (w_cur * direct_hist_cur.values + (1.0-w_cur) * sum_hist_series_cur.values)
                    y_sub = y_hist_cur[-Wc:][mask[-Wc:]]
                    p_sub = base_pred_hist[-Wc:][mask[-Wc:]]
                    A = np.vstack([p_sub, np.ones_like(p_sub)]).T
                    try:
                        a, b = np.linalg.lstsq(A, y_sub, rcond=None)[0]
                        # guard against unstable scaling
                        if not np.isfinite(a) or not np.isfinite(b):
                            raise ValueError("non-finite calibration")
                        # base: 固定クリップ、tuned: h依存+週末近傍タイト
                        if mode == "tuned":
                            if h_cur <= 1:
                                a_low, a_high, b_cap = 0.5, 1.6, 60000.0
                            elif h_cur <= 3:
                                a_low, a_high, b_cap = 0.56, 1.48, 48000.0
                            elif h_cur <= 5:
                                a_low, a_high, b_cap = 0.59, 1.44, 38000.0
                            else:
                                a_low, a_high, b_cap = 0.61, 1.38, 29000.0
                            if is_weekend or is_hnear:
                                a_low = max(a_low, 0.62 if h_cur >= 6 else 0.60)
                                a_high = min(a_high, 1.36 if h_cur >= 6 else 1.40)
                                b_cap = min(b_cap, 26000.0 if h_cur >= 6 else 32000.0)
                        else:
                            a_low, a_high, b_cap = 0.60, 1.40, 50000.0
                        # apply explicit CLI overrides if provided
                        if calib_a_low is not None:
                            a_low = float(calib_a_low)
                        if calib_a_high is not None:
                            a_high = float(calib_a_high)
                        if calib_b_cap is not None:
                            b_cap = float(calib_b_cap)
                        a = float(np.clip(a, a_low, a_high))
                        b = float(np.clip(b, -b_cap, b_cap))
                        total_pred_today = float(max(0.0, a * total_pred_today + b))
                    except Exception:
                        pass

        # 残差再学習の適用（有効時）
        if (resid_model is not None and resid_feat_names) and (not weekly_applied):
            try:
                x_resid_today = x_total_proc.reindex(columns=resid_feat_names, fill_value=0.0).values
                # mode=tuned: 曜日（=horizon）別モデルがあれば優先使用、base: 単一モデル
                use_model = resid_models_by_dow.get(dow, resid_model) if mode=="tuned" else resid_model
                adj_hat = float(np.ravel(use_model.predict(x_resid_today))[0])
                total_pred_today = float(max(0.0, total_pred_today + adj_hat))
            except Exception:
                pass
        elif not weekly_applied:
            # フォールバック: 残差バイアス補正（曜日×直近W日）
            adj = _resid_bias_adjustment(d, hist_df_cur, target_items, models_total, w_cur, cfg)
            total_pred_today = float(max(0.0, total_pred_today + adj))

        # 1シグマ推定（優先: 分位点 -> 代替: 残差の頑健標準偏差）
        z90 = 1.2815515655446004
        sigma_q = (p90 - p50) / z90 if (np.isfinite(p90) and np.isfinite(p50) and (p90 > p50)) else float("nan")
        sigma_hist_dow = resid_std_by_dow_cur.get(dow, float("nan"))
        sigma = sigma_q if np.isfinite(sigma_q) else (sigma_hist_dow if np.isfinite(sigma_hist_dow) else (resid_std_all_cur if np.isfinite(resid_std_all_cur) else 0.0))
        sigma = float(max(0.0, sigma))
        low_1s = max(0.0, total_pred_today - sigma)
        high_1s = max(low_1s, total_pred_today + sigma)

        # 追加: 学習で使えるように主要な外生特徴を保存
        def _getf(name, default=0.0):
            try:
                return float(today_feats.get(name, pd.Series([default], index=[d])).iloc[0])
            except Exception:
                return float(default)
        results.append({
            "date": d,
            "sum_items_pred": sum_items_today,
            "p50": p50,
            "p90": p90,
            "mean_pred": mean_pred,
            "total_pred": total_pred_today,
            "sigma_1": sigma,
            "total_pred_low_1sigma": low_1s,
            "total_pred_high_1sigma": high_1s,
            # exog snapshot
            "reserve_count": _getf("reserve_count", 0.0),
            "reserve_sum": _getf("reserve_sum", 0.0),
            "fixed_ratio": _getf("fixed_ratio", 0.0),
            "reserve_count_ma3": _getf("reserve_count_ma3", 0.0),
            "reserve_count_ma7": _getf("reserve_count_ma7", 0.0),
            "reserve_count_ma14": _getf("reserve_count_ma14", 0.0),
            "reserve_sum_ma3": _getf("reserve_sum_ma3", 0.0),
            "reserve_sum_ma7": _getf("reserve_sum_ma7", 0.0),
            "reserve_sum_ma14": _getf("reserve_sum_ma14", 0.0),
            "fixed_ratio_ma3": _getf("fixed_ratio_ma3", 0.0),
            "fixed_ratio_ma7": _getf("fixed_ratio_ma7", 0.0),
            "fixed_ratio_ma14": _getf("fixed_ratio_ma14", 0.0),
            "dow": int(dow),
            "is_weekend": int(_getf("is_weekend", 0.0)),
            "is_holiday_nearby": int(_getf("is_holiday_nearby", 0.0)),
            "weekofyear": int(_getf("weekofyear", float(pd.Timestamp(d).isocalendar().week))),
            "woy_sin": _getf("woy_sin", 0.0),
            "woy_cos": _getf("woy_cos", 0.0),
            "dow_sin": _getf("dow_sin", 0.0),
            "dow_cos": _getf("dow_cos", 0.0),
            "total_lag1": _getf("total_lag1", 0.0),
            "total_ma3": _getf("total_ma3", 0.0),
            "total_ma7": _getf("total_ma7", 0.0),
            "total_ma14": _getf("total_ma14", 0.0),
            "h": int(h_cur),
        })

        # 順次: 実績があれば履歴に取り込み、次日から反映
        if eval_sequential and d in actuals.index:
            try:
                total_hist_cur.loc[d] = float(actuals.loc[d])
                total_hist_cur = total_hist_cur.sort_index()
            except Exception:
                pass

    try:
        print(f"[TRACE] results rows: {len(results)}")
    except Exception:
        pass
    out = pd.DataFrame(results).set_index("date").sort_index()
    # Optional: apply weekly_meta bundle adjustment (weekly total -> daily redistribution)
    if weekly_meta_bundle:
        try:
            wm = joblib.load(weekly_meta_bundle) if isinstance(weekly_meta_bundle, str) else weekly_meta_bundle
            wm_features = list(wm.get('feature_names', [])) if isinstance(wm, dict) else []
            wm_model = wm.get('model') if isinstance(wm, dict) else None
            cfg_wm = wm.get('cfg') if isinstance(wm, dict) else {}
            week_start_dow = int(cfg_wm.get('week_start_dow', 0))
            # determine week frequency
            freq_map = {0:'W-MON',1:'W-TUE',2:'W-WED',3:'W-THU',4:'W-FRI',5:'W-SAT',6:'W-SUN'}
            week_freq = freq_map.get(week_start_dow, 'W-MON')
            dfw = out.copy()
            # assign week id and group
            dfw['week_id'] = pd.DatetimeIndex(dfw.index).to_period(week_freq).astype(str)
            g = dfw.groupby('week_id', sort=False)
            for wk, grp in g:
                try:
                    # consider only full 7-day groups
                    dates = pd.DatetimeIndex(grp.index)
                    if len(dates) != 7:
                        continue
                    # safety: contiguous and aligned to desired DOW
                    if (dates.max() - dates.min()).days != 6:
                        continue
                    if int(dates.min().weekday()) != week_start_dow:
                        continue
                    prw = grp.copy()
                    def _sumcol(c: str) -> float:
                        return float(pd.to_numeric(prw.get(c), errors='coerce').sum()) if c in prw.columns else float('nan')
                    def _meancol(c: str) -> float:
                        return float(pd.to_numeric(prw.get(c), errors='coerce').mean()) if c in prw.columns else float('nan')
                    def _stdcol(c: str) -> float:
                        return float(pd.to_numeric(prw.get(c), errors='coerce').std()) if c in prw.columns else float('nan')
                    feats = {
                        'tp_sum': _sumcol('total_pred'),
                        'sp_sum': _sumcol('sum_items_pred'),
                        'tp_mean': _meancol('total_pred'),
                        'sp_mean': _meancol('sum_items_pred'),
                        'tp_std': _stdcol('total_pred'),
                        'sp_std': _stdcol('sum_items_pred'),
                    }
                    feats['tp_minus_sp_sum'] = feats.get('tp_sum', 0.0) - feats.get('sp_sum', 0.0)
                    feats['tp_div_sp_sum'] = (feats.get('tp_sum', float('nan')) / feats.get('sp_sum', float('nan')))
                    if not np.isfinite(feats['tp_div_sp_sum']) or abs(feats.get('sp_sum', 0.0)) <= 1e-6:
                        feats['tp_div_sp_sum'] = float('nan')
                    # Build X in model's feature order; unknowns (e.g., lag features) are filled with 0.0
                    Xw = pd.DataFrame([feats]).reindex(columns=wm_features, fill_value=0.0).values
                    if wm_model is None:
                        continue
                    y_hat = float(np.ravel(wm_model.predict(Xw))[0])
                    # optional blend and cap relative to base tp_sum
                    tp_sum = float(feats.get('tp_sum', 0.0))
                    y_blend = float((weekly_meta_alpha * y_hat) + ((1.0 - weekly_meta_alpha) * tp_sum))
                    if weekly_meta_cap_low is not None:
                        y_blend = max(y_blend, float(weekly_meta_cap_low) * tp_sum)
                    if weekly_meta_cap_high is not None:
                        y_blend = min(y_blend, float(weekly_meta_cap_high) * tp_sum)
                    # redistribute to days by base shares
                    base = pd.to_numeric(prw['total_pred'], errors='coerce').fillna(0.0).values
                    ssum = float(np.sum(base))
                    if ssum <= 0.0:
                        shares = np.ones_like(base, dtype=float) / max(1, len(base))
                    else:
                        shares = base / ssum
                    adj = y_blend * shares
                    out.loc[dates, 'total_pred'] = adj
                except Exception:
                    continue
        except Exception:
            pass
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    out.to_csv(out_csv, encoding="utf-8-sig")
    print(f"[SAVED] predictions -> {out_csv}")


def main():
    ap = argparse.ArgumentParser(description="Serve inference for v4_2_4 bundle (future forecast)")
    ap.add_argument("--bundle", type=str, required=True, help="predict_model_v4_2_4_best_repro.py で保存した .joblib")
    ap.add_argument("--out-csv", type=str, required=True, help="予測を書き出すCSVパス")
    ap.add_argument("--future-days", type=int, default=7, help="予測日数（start/end 未指定時）")
    ap.add_argument("--start-date", type=str, default=None)
    ap.add_argument("--end-date", type=str, default=None)
    ap.add_argument("--reserve-csv", type=str, default=None)
    ap.add_argument("--reserve-forecast-csv", type=str, default=None, help="予約の予測CSV (date,reserve_count,reserve_sum,fixed_ratio)")
    ap.add_argument("--res-walk-csv", type=str, default=None, help="history_tail が無いバンドル用の履歴（res_walkforward.csv）")
    ap.add_argument("--reserve-date-col", type=str, default="予約日")
    ap.add_argument("--reserve-count-col", type=str, default="台数")
    ap.add_argument("--reserve-fixed-col", type=str, default="固定客")
    
    # DB直接取得モード（CSV廃止）
    ap.add_argument("--use-db", action="store_true",
                    help="DBから予約データを直接取得（--reserve-csvの代わり）")
    ap.add_argument("--db-connection-string", type=str, default=None,
                    help="PostgreSQL接続文字列（--use-db時に指定、未指定時は環境変数DATABASE_URL）")
    ap.add_argument("--reserve-start-date", type=str, default=None,
                    help="予約データ開始日（YYYY-MM-DD形式、--use-db時に使用）")
    ap.add_argument("--reserve-end-date", type=str, default=None,
                    help="予約データ終了日（YYYY-MM-DD形式、--use-db時に使用）")
    ap.add_argument("--mode", type=str, default="base", choices=["base","tuned"], help="推論ロジックの構成（base: 従来, tuned: 追加調整を有効化）")
    ap.add_argument("--weekly-bundle", type=str, default=None, help="週次用バンドル（weekly_stage2 または w+calib を含む joblib）")
    ap.add_argument("--weekly-meta-bundle", type=str, default=None, help="週合計を直接予測する weekly_meta バンドル(joblib) 週内に比例配分して置換")
    ap.add_argument("--weekly-meta-alpha", type=float, default=1.0, help="週合計のblend率: y=alpha*meta+(1-alpha)*tp_sum")
    ap.add_argument("--weekly-meta-cap-low", type=float, default=None, help="週合計の下限比率（tp_sumに対する倍率）")
    ap.add_argument("--weekly-meta-cap-high", type=float, default=None, help="週合計の上限比率（tp_sumに対する倍率）")
    # 予約未指定時の補完仕様
    ap.add_argument("--prompt-reserve", action="store_true", help="未来日の予約が無い場合、対話入力を促す")
    ap.add_argument("--manual-reserve", type=str, default=None,
                    help="手動予約の指定。'YYYY-MM-DD=count,sum[,fixed];YYYY-MM-DD=count,sum' 形式")
    ap.add_argument("--reserve-default-count", type=float, default=None, help="予約countのデフォルト値（非対話補完）")
    ap.add_argument("--reserve-default-sum", type=float, default=None, help="予約sumのデフォルト値（非対話補完）")
    ap.add_argument("--reserve-default-fixed", type=float, default=None, help="固定客比率のデフォルト（0〜1）")
    # 予約の自動予測（DOW中央値）
    ap.add_argument("--auto-reserve", action="store_true", help="履歴からDOW中央値で未来日の予約(count/sum/fixed)を自動補完")
    ap.add_argument("--auto-reserve-window", type=int, default=84, help="自動補完に使う直近期の履歴日数")
    ap.add_argument("--auto-reserve-method", type=str, default="dow_median", choices=["dow_median"], help="自動補完手法")
    # 残差再学習（任意）
    ap.add_argument("--residual-refit", action="store_true", help="直近期の残差を軽量モデルで再学習して将来に加算")
    ap.add_argument("--residual-refit-window", type=int, default=90, help="残差再学習に使う直近期の日数")
    ap.add_argument("--residual-model", type=str, default="gbr", choices=["gbr","ridge"], help="残差モデルの種類")
    # 評価・運用向け制御
    ap.add_argument("--disable-calibration", action="store_true", help="曜日キャリブレーション(a,b)の適用を無効化")
    ap.add_argument("--no-same-day-info", action="store_true", help="当日予約情報を使わずに(1日シフトして)特徴量を作る")
    ap.add_argument("--eval-sequential", action="store_true", help="t～t+7の各日で実績を逐次取り込み、残差統計の再学習を反映して推論")
    # calibration/guardrail overrides
    ap.add_argument("--calib-a-low", type=float, default=None, help="曜日キャリブのa下限を上書き")
    ap.add_argument("--calib-a-high", type=float, default=None, help="曜日キャリブのa上限を上書き")
    ap.add_argument("--calib-b-cap", type=float, default=None, help="曜日キャリブのbの絶対値上限を上書き")
    ap.add_argument("--calib-window-days", type=int, default=None, help="曜日キャリブの窓長（火曜以外）上書き")
    ap.add_argument("--calib-window-days-tuesday", type=int, default=None, help="曜日キャリブの窓長（火曜）上書き")
    ap.add_argument("--apply-zero-cap-in-base", action="store_true", help="baseモードでもゼロ予約×週末近傍キャップを適用")
    ap.add_argument("--zero-cap-quantile", type=float, default=None, help="ゼロ予約キャップの分位（0-1）を上書き")

    args = ap.parse_args()
    
    # DB直接取得モード
    reserve_csv_arg = args.reserve_csv
    if args.use_db:
        from datetime import datetime
        from db_loader import load_reserve_from_db
        import tempfile
        
        # 日付範囲の決定（start-date/end-date または future-daysから）
        if args.start_date and args.end_date:
            reserve_start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            reserve_end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        elif args.reserve_start_date and args.reserve_end_date:
            reserve_start = datetime.strptime(args.reserve_start_date, "%Y-%m-%d").date()
            reserve_end = datetime.strptime(args.reserve_end_date, "%Y-%m-%d").date()
        else:
            # バンドルの history_tail から last_date を推定（簡易版）
            import joblib
            bundle = joblib.load(args.bundle)
            from datetime import timedelta
            if bundle.get("history_tail") is not None and len(bundle["history_tail"]) > 0:
                last_date_str = bundle["history_tail"]["date"].max()
                last_date = datetime.strptime(str(last_date_str)[:10], "%Y-%m-%d").date()
                reserve_start = last_date - timedelta(days=args.future_days + 60)
                reserve_end = last_date + timedelta(days=args.future_days)
            else:
                raise ValueError(
                    "--use-db requires --start-date/--end-date or --reserve-start-date/--reserve-end-date"
                )
        
        print(f"[DB MODE] Loading reserve from DB: {reserve_start} to {reserve_end}")
        reserve_df = load_reserve_from_db(
            start_date=reserve_start,
            end_date=reserve_end,
            date_col=args.reserve_date_col,
            count_col=args.reserve_count_col,
            fixed_col=args.reserve_fixed_col,
            connection_string=args.db_connection_string,
        )
        print(f"[DB MODE] Loaded {len(reserve_df)} reserve records from DB")
        
        # 一時CSVに保存（run_inference が reserve_csv を要求するため）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            reserve_df.to_csv(f, index=False)
            reserve_csv_arg = f.name
            print(f"[DB MODE] Saved reserve to temporary CSV: {reserve_csv_arg}")
    
    run_inference(bundle_path=args.bundle,
                  res_walk_csv=args.res_walk_csv,
                  reserve_csv=reserve_csv_arg,
                  reserve_date_col=args.reserve_date_col,
                  reserve_count_col=args.reserve_count_col,
                  reserve_fixed_col=args.reserve_fixed_col,
                  reserve_forecast_csv=args.reserve_forecast_csv,
                  weekly_bundle=args.weekly_bundle,
                  weekly_meta_bundle=args.weekly_meta_bundle,
                  weekly_meta_alpha=args.weekly_meta_alpha,
                  weekly_meta_cap_low=args.weekly_meta_cap_low,
                  weekly_meta_cap_high=args.weekly_meta_cap_high,
                  future_days=args.future_days,
                  start_date=args.start_date, end_date=args.end_date,
                  out_csv=args.out_csv,
                  mode=args.mode,
                  prompt_reserve=bool(args.prompt_reserve),
                  manual_reserve=args.manual_reserve,
                  reserve_default_count=args.reserve_default_count,
                  reserve_default_sum=args.reserve_default_sum,
                  reserve_default_fixed=args.reserve_default_fixed,
                  residual_refit=bool(args.residual_refit),
                  residual_refit_window=args.residual_refit_window,
                  residual_model=args.residual_model,
                  disable_calibration=bool(args.disable_calibration),
                  no_same_day_info=bool(args.no_same_day_info),
                  eval_sequential=bool(args.eval_sequential),
                  auto_reserve=bool(args.auto_reserve),
                  auto_reserve_window=args.auto_reserve_window,
                  auto_reserve_method=args.auto_reserve_method,
                  calib_a_low=args.calib_a_low,
                  calib_a_high=args.calib_a_high,
                  calib_b_cap=args.calib_b_cap,
                  calib_window_days=args.calib_window_days,
                  calib_window_days_tuesday=args.calib_window_days_tuesday,
                  apply_zero_cap_in_base=bool(args.apply_zero_cap_in_base),
                  zero_cap_quantile_override=args.zero_cap_quantile)
if __name__ == "__main__":
    main()
