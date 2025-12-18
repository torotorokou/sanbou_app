# -*- coding: utf-8 -*-
"""
predict_model_v4_2_4_best_repro.py  —  高速化・安定化 完全修正版（コピペ可）

目的：
- 既存「日次実数」ベストモデルを“精度維持のまま高速化”し、運用に耐える形に整備
- retrain間引き・前計算キャッシュ・並列化・軽量学習器パラメータのスイッチを追加
- 学習→保存（bundle.joblib）→将来のAPI化にそのまま活用できるようメタ情報を同梱

主な追加・変更点（既定は従来互換）：
- --retrain-interval K        : Walk-forward中の再学習をK日おきに実施（デフォルト=1=毎日）
- --n-splits N                : TimeSeriesSplitの分割数（高速化には3推奨、既定=5）
- --rf-n-estimators / --gbr-n-estimators : 木本数を制御（高速化用）
- --n-jobs                    : Stage1（品目別）を並列実行（-1=全コア）
- --disable-elastic           : Stage1のElasticNetをスキップ（OOFで劣位なら高速化）
- --no-plots                  : 実行後のPNG出力をスキップ（CI等で高速化）
- キャッシュ                  : 各品目の(X_all, y_all)を1度だけ構築→学習時はスライスだけ
- 再利用                      : retrainしない日はStage1 pack＆Stage2モデルを再利用
- バンドル保存（--save-bundle PATH）: 予測に必要な最終パック・メタを joblib で保存
"""

import os
import sys
import re
import json
import time
import argparse
import warnings
import platform
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Any

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import r2_score, mean_absolute_error

warnings.filterwarnings("ignore", category=UserWarning)

# =========================
# Config
# =========================

@dataclass
class Config:
    top_n: int = 6
    min_stage1_days: int = 120
    min_stage2_rows: int = 28
    use_same_day_info: bool = True
    max_history_days: int = 600
    time_decay: str = "linear"            # none | linear | exponential
    calibration_window_days: int = 28
    calibration_window_days_tuesday: int = 56
    zero_cap_quantile: float = 0.15
    share_oof_models: int = 2
    random_state: int = 42

# =========================
# Timer
# =========================

class Timer:
    def __init__(self):
        self._stack = []
        self.marks: Dict[str, float] = {}

    def start(self, key: str):
        self._stack.append((key, time.time()))

    def stop(self):
        if not self._stack:
            return 0.0
        key, t0 = self._stack.pop()
        dt = time.time() - t0
        self.marks[key] = self.marks.get(key, 0.0) + dt
        return dt

    def get(self):
        return {k: float(v) for k, v in self.marks.items()}

# =========================
# Utils
# =========================

def _mae(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    m = np.isfinite(y) & np.isfinite(yhat)
    return float(np.mean(np.abs(y[m] - yhat[m]))) if m.sum() else float("nan")

def _time_decay_weights(n: int, mode: str) -> Optional[np.ndarray]:
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

def _blend_weight(y_true: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    """histベースで direct(a) と sum(b) をブレンドする重み w を探索（MAE最小）"""
    n = len(y_true)
    k = min(28, max(8, n // 4)) if n > 8 else n
    yt, at, bt = y_true[-k:], a[-k:], b[-k:]
    best_w, best_mae = 0.5, 1e18
    for w in np.linspace(0, 1, 41):
        m = w * at + (1 - w) * bt
        v = _mae(yt, m)
        if np.isfinite(v) and v < best_mae:
            best_mae, best_w = v, float(w)
    return best_w

def _norm_col(s: str) -> str:
    if s is None:
        return ""
    t = str(s).replace("\u3000"," ").strip()
    t = re.sub(r"[\s\-/＿－―・:：()\[\]（）［］]+", "", t)
    try:
        import unicodedata
        t = unicodedata.normalize("NFKC", t)
    except Exception:
        pass
    return t.lower()

def _read_csv(path: Optional[str]) -> Optional[pd.DataFrame]:
    if not path:
        return None
    for enc in (None, "utf-8-sig", "cp932"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str, low_memory=False)
        except Exception:
            continue
    return None

def _clean_date_string(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = str(x)
    s = re.sub(r"[\(（][^\)）]*[\)）]", "", s)
    s = s.replace("年","/").replace("月","/").replace("日","")
    s = s.replace("-", "/")
    return s.strip()

def _parse_date_series(sr: pd.Series) -> pd.Series:
    s = sr.astype(str).map(_clean_date_string)
    dt = pd.to_datetime(s, errors="coerce")
    if dt.notna().any():
        return dt.dt.normalize()
    s2 = s.str.replace("/", "", regex=False)
    dt2 = pd.to_datetime(s2, format="%Y%m%d", errors="coerce")
    if dt2.notna().any():
        return dt2.dt.normalize()
    return pd.to_datetime(s, errors="coerce").dt.normalize()

def _auto_map_columns(df: pd.DataFrame, want: Dict[str, List[str]]) -> Dict[str, str]:
    norm_map = {c: _norm_col(c) for c in df.columns}
    inv: Dict[str, List[str]] = {}
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
                    found = cols[0]; break
        if found is None:
            for na, cols in inv.items():
                if any(na.startswith(_norm_col(a)) for a in aliases):
                    found = cols[0]; break
        out[key] = found
    return out

# =========================
# Preprocess
# =========================

def preprocess_raw(df: pd.DataFrame, date_col: str, item_col: str, weight_col: str,
                   out_dir: Optional[str] = None) -> pd.DataFrame:
    want = {
        "date":   [date_col, "伝票日付", "日付", "受入日", "搬入日", "計上日"],
        "item":   [item_col, "品名", "商品", "銘柄", "品目", "カテゴリ"],
        "weight": [weight_col, "正味重量", "重量", "数量", "重量kg", "正味量"]
    }
    cmap = _auto_map_columns(df, want)
    miss = [k for k,v in cmap.items() if v is None]
    if miss:
        msg = f"[ERROR] 必須列の自動特定に失敗: {miss}\n実列={list(df.columns)[:30]}"
        raise ValueError(msg)
    dd = df[[cmap["date"], cmap["item"], cmap["weight"]]].copy()
    dd.columns = ["__date__", "__item__", "__weight__"]
    dd["__date__"] = _parse_date_series(dd["__date__"])
    # 重量列の型チェック：文字列なら","除去、数値ならそのまま
    if pd.api.types.is_numeric_dtype(dd["__weight__"]):
        dd["__weight__"] = pd.to_numeric(dd["__weight__"], errors="coerce")
    else:
        dd["__weight__"] = pd.to_numeric(dd["__weight__"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    dd = dd.dropna(subset=["__date__", "__weight__"])
    if len(dd) == 0:
        _emit_preprocess_diagnostics(df, date_col, item_col, weight_col, out_dir, stage="raw->clean")
        raise ValueError("preprocess後のdf_rawが空です。日付/品目/重量の列名と値の形式を確認してください。")
    dd = dd.rename(columns={"__date__": date_col, "__item__": item_col, "__weight__": weight_col})
    dd[date_col] = pd.to_datetime(dd[date_col]).dt.normalize()
    return dd

def _emit_preprocess_diagnostics(df: pd.DataFrame, date_col: str, item_col: str, weight_col: str,
                                 out_dir: Optional[str], stage: str):
    try:
        os.makedirs(out_dir or ".", exist_ok=True)
        path = os.path.join(out_dir or ".", "preprocess_diagnostics.json")
        diag = {
            "input_columns_head": list(df.columns)[:50],
            "n_rows": int(len(df)),
            "date_sample": df.get(date_col, df.iloc[:,0]).head(20).tolist(),
            "stage": stage
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(diag, f, ensure_ascii=False, indent=2)
        print(f"[DIAG] 前処理診断を書き出しました: {path}")
    except Exception as e:
        print(f"[WARN] 診断書き出しに失敗: {e}")

def preprocess_reserve(df: Optional[pd.DataFrame], date_col: str, count_col: str, fixed_col: str) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    dd = df.copy()

    def _auto_map_columns2(df_, want):
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
                    found = inv[na][0]; break
            if found is None:
                for na, cols in inv.items():
                    if any(_norm_col(a) in na for a in aliases): found = cols[0]; break
            if found is None:
                for na, cols in inv.items():
                    if any(na.startswith(_norm_col(a)) for a in aliases): found = cols[0]; break
            out[key] = found
        return out

    cmap = _auto_map_columns2(dd, {
        "date":[date_col, "予約日", "日付"],
        "count":[count_col, "台数", "予約台数", "件数"],
        "fixed":[fixed_col, "固定客", "固定"]
    })
    if cmap["date"] is None:
        raise ValueError("予約データの日付列が見つかりません。")
    dd[cmap["date"]] = _parse_date_series(dd[cmap["date"]])
    if cmap["count"] in dd.columns:
        # 台数列の型チェック：文字列なら","除去、数値ならそのまま
        if pd.api.types.is_numeric_dtype(dd[cmap["count"]]):
            dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]], errors="coerce")
        else:
            dd[cmap["count"]] = pd.to_numeric(dd[cmap["count"]].astype(str).str.replace(",","",regex=False), errors="coerce")
    if cmap["fixed"] in dd.columns:
        dd[cmap["fixed"]] = dd[cmap["fixed"]].astype(str).str.lower().isin(["1","true","yes","固定","固定客"]).astype(int)
    grp = dd.groupby(cmap["date"])
    out = pd.DataFrame({
        "reserve_count": grp.size().astype(float),
        "reserve_sum": (grp[cmap["count"]].sum() if cmap["count"] in dd.columns else grp.size()).astype(float),
        "fixed_ratio": (grp[cmap["fixed"]].mean() if cmap["fixed"] in dd.columns else 0.0)
    })
    return out

# =========================
# Feature construction
# =========================

def build_pivot(df_raw: pd.DataFrame, date_col: str, item_col: str, weight_col: str):
    if len(df_raw) == 0:
        raise ValueError("preprocess後のdf_rawが空です。")
    g = df_raw.groupby([date_col, item_col])[weight_col].sum()
    if len(g) == 0:
        raise ValueError("groupby結果が空です。列名と値を確認してください。")
    pvt = g.unstack(fill_value=0.0).sort_index()

    i_min, i_max = pvt.index.min(), pvt.index.max()
    if pd.isna(i_min) or pd.isna(i_max):
        raise ValueError("日付indexにNaTが含まれています。日付の形式を確認してください。")
    full_idx = pd.date_range(i_min, i_max, freq="D")
    pvt = pvt.reindex(full_idx, fill_value=0.0)
    total = pvt.sum(axis=1).astype(float)
    return pvt, total

def get_target_items(df_raw: pd.DataFrame, date_col: str, item_col: str,
                     weight_col: str, top_n: int, lookback_days: int = 365) -> List[str]:
    # 強制的に指定された品目リストを返す
    forced_items = [
        "混合廃棄物A",
        "混合廃棄物B",
        "GC 軽鉄･ｽﾁｰﾙ類",
        "選別",
        "木くず",
        "混合廃棄物C"
    ]
    # データに含まれているものだけフィルタリング（念のため）
    available_items = set(df_raw[item_col].unique())
    valid_items = [item for item in forced_items if item in available_items]
    
    if not valid_items:
        # もし強制リストの品目が一つもなければ、従来のロジックでトップNを選択
        print("[WARN] 指定された品目が見つかりません。自動選択に切り替えます。")
        dt = pd.to_datetime(df_raw[date_col], errors="coerce")
        cutoff = dt.max() - pd.Timedelta(days=lookback_days)
        sub = df_raw[dt >= cutoff]
        if len(sub) == 0: sub = df_raw
        g = sub.groupby(item_col)[weight_col].sum().sort_values(ascending=False)
        return list(g.head(top_n).index)
        
    return valid_items

def build_calendar_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    idx = pd.DatetimeIndex(index)
    df = pd.DataFrame(index=idx)
    df["dow"] = idx.weekday
    df["weekofyear"] = idx.isocalendar().week.astype(int)
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    near = set()
    for d in idx[df["is_weekend"] == 1]:
        near.add(d); near.add(d + pd.Timedelta(days=1)); near.add(d - pd.Timedelta(days=1))
    df["is_holiday_nearby"] = df.index.isin(list(near)).astype(int)
    ang = 2 * np.pi * df["dow"] / 7.0
    df["dow_sin"] = np.sin(ang); df["dow_cos"] = np.cos(ang)
    return df

def build_exog(index: pd.DatetimeIndex, total: pd.Series,
               reserve_daily: Optional[pd.DataFrame], use_same_day_info: bool) -> pd.DataFrame:
    cal = build_calendar_features(index)
    ex = cal.copy()
    if isinstance(reserve_daily, pd.DataFrame) and len(reserve_daily) > 0:
        r = reserve_daily.reindex(index).fillna(0.0)
        if not use_same_day_info:
            r = r.shift(1).fillna(0.0)
        ex = ex.join(r)
    else:
        ex[["reserve_count", "reserve_sum", "fixed_ratio"]] = 0.0
    # 合計のラグ/移動平均
    ex["total_lag1"] = total.shift(1)
    ex["total_ma3"]  = total.rolling(3, min_periods=1).mean().shift(1)
    ex["total_ma7"]  = total.rolling(7, min_periods=1).mean().shift(1)
    ex["total_ma14"] = total.rolling(14, min_periods=1).mean().shift(1)
    return ex.fillna(0.0).astype("float32")

def build_item_design(item: str, pvt: pd.DataFrame, exog: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    s = pvt[item].astype(float)
    df = exog.copy()
    df[f"{item}_lag1"] = s.shift(1)
    df[f"{item}_ma7"]  = s.rolling(7, min_periods=1).mean().shift(1)
    df[f"{item}_ma28"] = s.rolling(28, min_periods=1).mean().shift(1)
    df = df.fillna(0.0)
    return df.astype("float32"), s.astype("float32")

# =========================
# Stage1 (per-item stacking)
# =========================

def _make_base_specs(args) -> List[Tuple[str, Any]]:
    specs: List[Tuple[str, Any]] = []
    if not args.disable_elastic:
        specs.append(("elastic", ElasticNet(alpha=0.08, l1_ratio=0.4, max_iter=20000)))
    specs.append(("rf", RandomForestRegressor(
        n_estimators=args.rf_n_estimators, min_samples_leaf=3,
        random_state=42, n_jobs=1)))
    specs.append(("gbr", GradientBoostingRegressor(
        n_estimators=args.gbr_n_estimators, learning_rate=0.07,
        max_depth=3, subsample=0.9, random_state=42)))
    return specs

def oof_stack_for_item(X: pd.DataFrame, y: pd.Series, cfg: Config,
                       n_splits: int, base_specs: List[Tuple[str, Any]]) -> Tuple[pd.Series, Dict]:
    X = X.astype(float); y = y.astype(float)
    n = len(X)
    if n < 40 or y.nunique() <= 1:
        naive = y.rolling(7, min_periods=1).mean().shift(1).bfill()
        model = Ridge(alpha=0.5).fit(naive.values.reshape(-1,1), y.values)
        meta_oof = pd.Series(model.predict(naive.values.reshape(-1,1)), index=X.index, dtype=float)
        return meta_oof, {"base": [], "meta": ("ridge", model), "cols": ["naive"], "kept_models": []}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    oof = pd.DataFrame(index=X.index, columns=[n for n,_ in base_specs], dtype=float)

    scalers: Dict[str, StandardScaler] = {}
    selectors: Dict[str, VarianceThreshold] = {}
    fitted: Dict[str, Any] = {}

    for name, est in base_specs:
        fold_mae = []
        for tr, va in tscv.split(np.arange(n)):
            Xtr, Xva = X.iloc[tr], X.iloc[va]
            ytr, yva = y.iloc[tr], y.iloc[va]
            scaler = StandardScaler()
            selector = VarianceThreshold(1e-4)
            Xt_tr = selector.fit_transform(scaler.fit_transform(Xtr.values))
            Xt_va = selector.transform(scaler.transform(Xva.values))
            sw = _time_decay_weights(len(Xt_tr), cfg.time_decay)
            m = clone(est)
            try:
                m.fit(Xt_tr, ytr.values, sample_weight=sw)
            except TypeError:
                m.fit(Xt_tr, ytr.values)
            pv = np.ravel(m.predict(Xt_va))
            oof.loc[Xva.index, name] = pv
            fold_mae.append(_mae(yva.values, pv))
        scaler = StandardScaler(); selector = VarianceThreshold(1e-4)
        Xt_full = selector.fit_transform(scaler.fit_transform(X.values))
        sw_full = _time_decay_weights(len(Xt_full), cfg.time_decay)
        m = clone(est)
        try:
            m.fit(Xt_full, y.values, sample_weight=sw_full)
        except TypeError:
            m.fit(Xt_full, y.values)
        scalers[name], selectors[name], fitted[name] = scaler, selector, m
        print(f"[OOF] {name} mean_valMAE={np.mean(fold_mae):.3f}")

    naive = y.shift(1)
    base_mae = {c: _mae(y.values, oof[c].values) for c in oof.columns}
    naive_mae = _mae(y.values, naive.values)
    keep = [k for k,v in sorted(base_mae.items(), key=lambda kv: kv[1])
            if (v+1e-12) <= 0.99*naive_mae][:cfg.share_oof_models]
    if not keep:
        keep = [min(base_mae, key=base_mae.get)]

    oof_used = oof[keep].ffill().bfill()
    meta = Ridge(alpha=0.5); meta.fit(oof_used.values, y.values)

    cols = list(X.columns)
    kept_models = list(keep)
    pack = {
        "base":[(k, fitted[k], scalers[k], selectors[k]) for k in keep],
        "meta":("ridge", meta),
        "cols": cols,
        "kept_models": kept_models,
    }
    meta_oof = pd.Series(meta.predict(oof_used.values), index=X.index, dtype=float)
    return meta_oof, pack

def predict_from_pack(X_today: pd.DataFrame, pack: Dict) -> float:
    preds = []
    cols = pack.get("cols", list(X_today.columns))
    X_today2 = X_today.reindex(columns=cols, fill_value=0.0)
    for name, model, scaler, selector in pack["base"]:
        Xt = selector.transform(scaler.transform(X_today2.values))
        preds.append(np.ravel(model.predict(Xt))[0])
    M = np.array(preds).reshape(1,-1)
    meta = pack["meta"][1]
    return float(np.ravel(meta.predict(M))[0])

# =========================
# Stage2 (Total)
# =========================

def fit_total_models(df_hist: pd.DataFrame, cfg: Config, args) -> Dict:
    """df_hist: columns = *_pred + exog + '合計'"""
    num_df = df_hist.drop(columns=[c for c in ["合計"] if c in df_hist.columns]).copy()
    # 非数値を除去（安全対策）
    num_df = num_df.select_dtypes(include=[np.number]).astype(float)
    y = df_hist["合計"].astype(float).values

    scaler = StandardScaler(); selector = VarianceThreshold(1e-4)
    Xt = selector.fit_transform(scaler.fit_transform(num_df.values))
    sw = _time_decay_weights(len(Xt), cfg.time_decay)

    gbdt_p50 = GradientBoostingRegressor(
        loss="quantile", alpha=0.5,
        n_estimators=args.gbr_n_estimators, learning_rate=0.05,
        max_depth=3, subsample=0.9, random_state=cfg.random_state)
    gbdt_p90 = GradientBoostingRegressor(
        loss="quantile", alpha=0.9,
        n_estimators=max(args.gbr_n_estimators, 200), learning_rate=0.05,
        max_depth=3, subsample=0.9, random_state=cfg.random_state)
    gbdt_ls  = GradientBoostingRegressor(
        loss="squared_error",
        n_estimators=max(args.gbr_n_estimators, 200), learning_rate=0.06,
        max_depth=3, subsample=0.9, random_state=cfg.random_state)
    for m in (gbdt_p50, gbdt_p90, gbdt_ls):
        try:
            m.fit(Xt, y, sample_weight=sw)
        except TypeError:
            m.fit(Xt, y)
    models = {
        "scaler":scaler, "selector":selector,
        "p50":gbdt_p50, "p90":gbdt_p90, "ls":gbdt_ls,
        "_feature_names": list(num_df.columns)
    }
    return models

def predict_total(models: Dict, x_today_raw: pd.DataFrame) -> Tuple[float, float, float]:
    feat = models.get("_feature_names", list(x_today_raw.columns))
    x_aligned = x_today_raw.reindex(columns=feat, fill_value=0.0)
    Xt = models["selector"].transform(models["scaler"].transform(x_aligned.values))
    p50 = float(models["p50"].predict(Xt)[0])
    p90 = float(models["p90"].predict(Xt)[0])
    mean = float(models["ls"].predict(Xt)[0])
    return p50, p90, mean

# =========================
# Main Walk-forward
# =========================

def run_walkforward(df_raw: pd.DataFrame,
                    df_reserve: Optional[pd.DataFrame],
                    date_col: str, item_col: str, weight_col: str,
                    reserve_date_col: str, reserve_count_col: str, reserve_fixed_col: str,
                    out_dir: str, cfg: Config, args):

    from joblib import Parallel, delayed  # 並列はここでimport

    os.makedirs(out_dir, exist_ok=True)
    timer = Timer()
    timer.start("total_runtime")

    # --- Safety: ensure input data do not contain future dates (basic leakage guard) ---
    try:
        # Use tz-naive timestamp for comparison
        now_dt = pd.Timestamp.utcnow().tz_localize(None).normalize()
        # raw data
        if len(df_raw) > 0:
            # Convert to tz-naive for comparison
            df_raw_dates = pd.to_datetime(df_raw[date_col], errors="coerce")
            if pd.api.types.is_datetime64tz_dtype(df_raw_dates):
                df_raw_dates = df_raw_dates.dt.tz_localize(None)
            dmax = df_raw_dates.max()
            if pd.notna(dmax):
                try:
                    # compare dates (avoid tz-aware vs tz-naive issues)
                    if pd.to_datetime(dmax).normalize().date() > now_dt.date():
                        if getattr(args, "enforce_no_leak", False):
                            raise RuntimeError(f"[LEAK] raw data contains future dates (max={pd.to_datetime(dmax).date()}); --enforce-no-leak aborting.")
                        msg = f"[WARN] raw data contains future dates (max={pd.to_datetime(dmax).date()}); trimming to today ({now_dt.date()})."
                        print(msg)
                        df_raw = df_raw[df_raw_dates.dt.normalize() <= now_dt]
                except Exception:
                    # fallback: if any unexpected issue, re-raise to surface
                    raise
        # reserve data
        if isinstance(df_reserve, pd.DataFrame) and len(df_reserve) > 0:
            # Convert to tz-naive for comparison
            df_reserve_dates = pd.to_datetime(df_reserve[reserve_date_col], errors="coerce")
            if pd.api.types.is_datetime64tz_dtype(df_reserve_dates):
                df_reserve_dates = df_reserve_dates.dt.tz_localize(None)
            rmax = df_reserve_dates.max()
            if pd.notna(rmax):
                try:
                    if pd.to_datetime(rmax).normalize().date() > now_dt.date():
                        if getattr(args, "enforce_no_leak", False):
                            raise RuntimeError(f"[LEAK] reserve data contains future dates (max={pd.to_datetime(rmax).date()}); --enforce-no-leak aborting.")
                        msg = f"[WARN] reserve data contains future dates (max={pd.to_datetime(rmax).date()}); trimming to today ({now_dt.date()})."
                        print(msg)
                        df_reserve = df_reserve[df_reserve_dates.dt.normalize() <= now_dt]
                except Exception:
                    raise
    except Exception:
        # allow outer logic to handle exceptions but surface message
        raise

    # ---- Preprocess ----
    timer.start("preprocess")
    df_raw = preprocess_raw(df_raw, date_col, item_col, weight_col, out_dir=out_dir)
    timer.stop()

    print(f"[DEBUG] rows_after_preprocess={len(df_raw)} "
          f"date_min={pd.to_datetime(df_raw[date_col]).min()} "
          f"date_max={pd.to_datetime(df_raw[date_col]).max()} "
          f"unique_items={df_raw[item_col].nunique()}")

    target_items = get_target_items(df_raw, date_col, item_col, weight_col, top_n=cfg.top_n)
    print(f"[INFO] target_items={target_items}")
    if not target_items:
        fallback = list(df_raw[item_col].value_counts().head(max(5, cfg.top_n)).index)
        target_items = fallback
        print(f"[WARN] fallback target_items={target_items}")

    pvt, total = build_pivot(df_raw, date_col, item_col, weight_col)
    idx = pvt.index
    # 履歴窓の上限を物理的に確保（最終評価期間に影響しないよう全期間exogを先に構築）
    reserve_daily = preprocess_reserve(df_reserve, reserve_date_col, reserve_count_col, reserve_fixed_col)
    # --- Safety: ensure reserve_daily does not contain dates beyond available raw history (prevent future-leak)
    try:
        max_pvt = pd.to_datetime(pd.DatetimeIndex(pvt.index).max()).normalize()
        if isinstance(reserve_daily, pd.DataFrame) and len(reserve_daily) > 0:
            rmax = pd.to_datetime(pd.DatetimeIndex(reserve_daily.index).max()).normalize()
            if pd.notna(rmax) and rmax > max_pvt:
                if getattr(args, "enforce_no_leak", False):
                    raise RuntimeError(f"[LEAK] reserve data contains dates beyond raw history (reserve_max={rmax.date()} > raw_max={max_pvt.date()}); --enforce-no-leak aborting.")
                print(f"[WARN] reserve data contains dates beyond raw history (reserve_max={rmax.date()} > raw_max={max_pvt.date()}); trimming reserve to raw_max.")
                reserve_daily = reserve_daily[pd.to_datetime(reserve_daily.index).normalize() <= max_pvt]
    except Exception:
        # surface unexpected errors
        raise

    exog = build_exog(idx, total, reserve_daily, cfg.use_same_day_info)

    # 前計算（高速化）
    item_design_cache: Dict[str, Tuple[pd.DataFrame, pd.Series]] = {}
    for it in target_items:
        X_all, y_all = build_item_design(it, pvt, exog)
        item_design_cache[it] = (X_all, y_all)

    results = []
    stage2_rows: List[Dict] = []
    item_model_log: Dict[str, Dict] = {}
    models_total_cache: Optional[Dict] = None

    # ---- Walk-forward ----
    for i, pred_day in enumerate(idx):
        if i < cfg.min_stage1_days:
            if i % 20 == 0:
                print(f"[SKIP] {pred_day.date()}  i={i} < min_stage1_days={cfg.min_stage1_days}")
            continue

        # 訓練インデックス（max_history_days でスライス）
        train_idx = idx[(idx < pred_day)]
        train_idx = train_idx[-cfg.max_history_days:] if cfg.max_history_days else train_idx

        # 今日の特徴量（exog）
        today_feats = exog.loc[[pred_day]].copy()

        # 学習間引き
        need_retrain = (len(stage2_rows) <= cfg.min_stage2_rows) or ((i % max(1, args.retrain_interval)) == 0)

        # ---- Stage1 per item ----
        def _fit_and_predict_one(it: str) -> Tuple[str, float]:
            X_all, y_all = item_design_cache[it]
            X_tr, y_tr = X_all.loc[train_idx], y_all.loc[train_idx]
            if need_retrain or ("last_pack" not in item_model_log.get(it, {})):
                timer.start("stage1_per_item_fit")
                meta_oof, pack = oof_stack_for_item(
                    X_tr, y_tr, cfg,
                    n_splits=max(2, args.n_splits),
                    base_specs=_make_base_specs(args)
                )
                timer.stop()
                item_model_log.setdefault(it, {})["last_pack"] = pack
                item_model_log[it]["kept_models"] = pack.get("kept_models", [])
                item_model_log[it]["n_features"] = len(pack.get("cols", []))
                item_model_log[it]["feature_columns"] = pack.get("cols", [])
            pack = item_model_log[it]["last_pack"]
            timer.start("stage1_per_item_predict")
            pred = predict_from_pack(today_feats, pack)
            timer.stop()
            return it, float(pred)

        if args.n_jobs != 1:
            # NOTE: Use threads to ensure in-place mutations to item_model_log are visible
            # across parallel workers. Process-based backends would not reflect child updates.
            outs = Parallel(n_jobs=args.n_jobs, prefer="threads")(
                delayed(_fit_and_predict_one)(it) for it in target_items
            )
        else:
            outs = [_fit_and_predict_one(it) for it in target_items]

        per_item_pred = {it: p for it, p in outs}
        sum_items_today = float(np.sum(list(per_item_pred.values())))

        # ---- Stage2 用の当日行を準備（学習ラグの整合のために真値も保持） ----
        row = {f"{it}_pred": per_item_pred[it] for it in target_items}
        for c in today_feats.columns:
            row[c] = float(today_feats.iloc[0][c])
        row["合計"] = float(total.loc[pred_day])
        stage2_rows.append(row)

        # Warm-up（一定行はsumのみ出力）
        if len(stage2_rows) <= cfg.min_stage2_rows:
            print(f"[DEBUG] Stage2 warmup rows={len(stage2_rows)}/{cfg.min_stage2_rows+1}")
            y_true = float(total.loc[pred_day])
            results.append({
                "date": pred_day, "y_true": y_true,
                "sum_items_pred": sum_items_today, "total_pred": sum_items_today
            })
            continue

        # ---- Stage2 学習（間引き対応）----
        hist_df = pd.DataFrame(stage2_rows[:-1]).set_index(
            pd.DatetimeIndex(idx[(idx < pred_day)][-len(stage2_rows[:-1]):])
        )
        if need_retrain or (models_total_cache is None):
            timer.start("stage2_fit")
            models_total_cache = fit_total_models(hist_df, cfg, args)
            timer.stop()

        # ---- Stage2 予測 ----
        timer.start("stage2_predict")
        x_total = {f"{it}_pred":[per_item_pred[it]] for it in target_items}
        for c in today_feats.columns:
            x_total[c] = [float(today_feats.iloc[0][c])]
        x_total_df = pd.DataFrame(x_total, index=[pred_day])
        # 非数値除外（保険）
        x_total_df = x_total_df.select_dtypes(include=[np.number]).astype(float)

        p50, p90, mean_pred = predict_total(models_total_cache, x_total_df)
        timer.stop()

        # ---- ブレンド（direct vs sum）----
        y_hist = hist_df["合計"].values.astype(float)
        # 学習に使った数値列に限定して direct を算出
        hist_num = hist_df.drop(columns=["合計"]).select_dtypes(include=[np.number]).astype(float)
        direct_hist = models_total_cache["ls"].predict(
            models_total_cache["selector"].transform(
                models_total_cache["scaler"].transform(
                    hist_num.reindex(columns=models_total_cache["_feature_names"], fill_value=0.0).values
                )
            )
        )
        sum_hist = hist_df[[c for c in hist_df.columns if c.endswith("_pred")]].sum(axis=1).values.astype(float)
        w = _blend_weight(y_hist, np.array(direct_hist), np.array(sum_hist))
        total_pred_today = float(w * mean_pred + (1 - w) * sum_items_today)

        # ---- 曜日別キャリブレーション ----
        dow = int(pd.to_datetime(pred_day).weekday())
        W = cfg.calibration_window_days_tuesday if dow == 2 else cfg.calibration_window_days
        if len(hist_df) >= W:
            wd = pd.to_datetime(hist_df.index).weekday
            mask = (wd == dow)
            if mask.sum() >= 6:
                base_pred_hist = (w * np.array(direct_hist) + (1 - w) * sum_hist)
                y_sub = y_hist[-W:][mask[-W:]]
                p_sub = base_pred_hist[-W:][mask[-W:]]
                A = np.vstack([p_sub, np.ones_like(p_sub)]).T
                try:
                    a, b = np.linalg.lstsq(A, y_sub, rcond=None)[0]
                    total_pred_today = float(max(0.0, a * total_pred_today + b))
                except Exception:
                    pass

        # ---- ガード（予約ゼロ×休日近辺の上限キャップ）----
        is_weekend = bool(x_total_df.get("is_weekend", pd.Series([0])).iloc[0])
        is_hnear   = bool(x_total_df.get("is_holiday_nearby", pd.Series([0])).iloc[0])
        reserve_zero = (float(x_total_df.get("reserve_count", pd.Series([0])).iloc[0]) == 0.0) and \
                       (float(x_total_df.get("reserve_sum", pd.Series([0])).iloc[0]) == 0.0)
        if reserve_zero and (is_weekend or is_hnear):
            hist_vals = pd.Series([r["合計"] for r in stage2_rows[:-1]]).tail(180).values
            if len(hist_vals) >= 20:
                cap = float(np.nanpercentile(hist_vals, 100 * cfg.zero_cap_quantile))
                total_pred_today = min(total_pred_today, cap)

        y_true = float(total.loc[pred_day])
        results.append({
            "date": pred_day, "y_true": y_true,
            "sum_items_pred": sum_items_today, "total_pred": total_pred_today
        })

        if len(results) % 10 == 0:
            ys = np.array([r["y_true"] for r in results]); ps = np.array([r["total_pred"] for r in results])
            print(f"[PROGRESS] {len(results)} days -> R²={r2_score(ys, ps):.3f}  MAE={mean_absolute_error(ys, ps):,.0f}")

    if not results:
        raise RuntimeError("有効な評価期間がありません（min_stage1_days が大きすぎる等）")

    df_res = pd.DataFrame(results).set_index("date").sort_index()
    ys = df_res["y_true"].values; ps = df_res["total_pred"].values; ss = df_res["sum_items_pred"].values
    scores = {
        "R2_total": float(r2_score(ys, ps)), "MAE_total": float(mean_absolute_error(ys, ps)),
        "R2_sum_only": float(r2_score(ys, ss)), "MAE_sum_only": float(mean_absolute_error(ys, ss)),
        "n_days": int(len(df_res)),
        "config": asdict(cfg)
    }

    # ---- Save results ----
    df_res.to_csv(os.path.join(out_dir, "res_walkforward.csv"), encoding="utf-8-sig")
    with open(os.path.join(out_dir, "scores_walkforward.json"), "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

    # ---- Plots ----
    if not args.no_plots:
        try:
            import matplotlib.pyplot as plt
            plt.style.use('seaborn-v0_8-whitegrid')

            fig, ax = plt.subplots(figsize=(12,5))
            ax.plot(df_res.index, df_res["y_true"], label="Actual")
            ax.plot(df_res.index, df_res["total_pred"], "--", label="Predicted")
            ax.set_title("Walk-forward Prediction vs Actual"); ax.legend()
            fig.tight_layout(); plt.savefig(os.path.join(out_dir, "pred_vs_actual.png")); plt.close()

            err = (df_res["total_pred"] - df_res["y_true"]).values
            fig, ax = plt.subplots(figsize=(8,4))
            ax.hist(err, bins=30); ax.set_title("Error Histogram (Pred - Actual)"); ax.set_xlabel("Error")
            fig.tight_layout(); plt.savefig(os.path.join(out_dir, "error_hist.png")); plt.close()

            tmp = df_res.copy(); tmp["dow"] = pd.to_datetime(tmp.index).weekday
            by = tmp.groupby("dow").apply(lambda g: mean_absolute_error(g["y_true"].values, g["total_pred"].values))
            fig, ax = plt.subplots(figsize=(8,4))
            ax.bar(range(7), [by.get(d, np.nan) for d in range(7)])
            ax.set_title("MAE by Day-of-Week"); ax.set_xlabel("DOW (Mon=0)"); ax.set_ylabel("MAE")
            fig.tight_layout(); plt.savefig(os.path.join(out_dir, "mae_by_dow.png")); plt.close()
        except Exception as e:
            print(f"[WARN] plot failed: {e}")

    # ---- Metadata / History ----
    timings = timer.get()
    timer.stop()  # total_runtime
    timings = timer.get()

    # Stage2 feature importance（最終モデル）
    try:
        feat_names = models_total_cache.get("_feature_names", []) if models_total_cache else []
        if models_total_cache and hasattr(models_total_cache["ls"], "feature_importances_"):
            importances = models_total_cache["ls"].feature_importances_
            pd.Series(importances, index=feat_names).sort_values(ascending=False)\
              .to_csv(os.path.join(out_dir, "stage2_feature_importance.csv"), encoding="utf-8-sig")
            with open(os.path.join(out_dir, "stage2_feature_names.txt"), "w", encoding="utf-8") as f:
                for c in feat_names:
                    f.write(str(c) + "\n")
    except Exception as e:
        print(f"[WARN] feature importance dump failed: {e}")

    meta = {
        "scores": scores,
        "timings_seconds": timings,
        "n_target_items": len(target_items),
        "target_items": target_items,
        "per_item_model_summary": {k: {
            "kept_models": v.get("kept_models", []),
            "n_features": v.get("n_features", np.nan),
            "feature_columns": v.get("feature_columns", []),
        } for k,v in item_model_log.items()},
        "env": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": __import__("numpy").__version__,
            "pandas": __import__("pandas").__version__,
            "sklearn": __import__("sklearn").__version__,
        }
    }
    with open(os.path.join(out_dir, "run_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # run_history.csv に1行追記
    try:
        hist_path = os.path.join(out_dir, "run_history.csv")
        row = {
            "ts": pd.Timestamp.utcnow().isoformat(),
            "R2_total": scores["R2_total"],
            "MAE_total": scores["MAE_total"],
            "n_days": scores["n_days"],
            "top_n": cfg.top_n,
            "min_stage1_days": cfg.min_stage1_days,
            "min_stage2_rows": cfg.min_stage2_rows,
            "use_same_day_info": cfg.use_same_day_info,
            "max_history_days": cfg.max_history_days,
            "time_decay": cfg.time_decay,
            "calibration_window_days": cfg.calibration_window_days,
            "calibration_window_days_tuesday": cfg.calibration_window_days_tuesday,
            "zero_cap_quantile": cfg.zero_cap_quantile,
            "share_oof_models": cfg.share_oof_models,
            "total_runtime_sec": timings.get("total_runtime", np.nan),
            "stage1_fit_sec": timings.get("stage1_per_item_fit", np.nan),
            "stage2_fit_sec": timings.get("stage2_fit", np.nan),
            "retrain_interval": args.retrain_interval,
            "n_splits": args.n_splits,
            "rf_n_estimators": args.rf_n_estimators,
            "gbr_n_estimators": args.gbr_n_estimators,
            "n_jobs": args.n_jobs,
            "disable_elastic": bool(args.disable_elastic),
        }
        df_hist = pd.DataFrame([row])
        if os.path.exists(hist_path):
            df_hist_existing = pd.read_csv(hist_path)
            df_hist = pd.concat([df_hist_existing, df_hist], ignore_index=True)
        df_hist.to_csv(hist_path, index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"[WARN] history append failed: {e}")

    # ---- Save bundle for API use ----
    if args.save_bundle:
        try:
            import joblib
            last_date_val = None
            try:
                last_date_val = pd.to_datetime(pd.DatetimeIndex(pvt.index).max()).normalize().isoformat()
            except Exception:
                last_date_val = None

            bundle = {
                "target_items": target_items,
                "stage2_feature_names": (models_total_cache.get("_feature_names", []) if models_total_cache else []),
                "models_total": models_total_cache,
                "item_packs": {k: v.get("last_pack") for k,v in item_model_log.items()},
                "stage1_packs": {k: v.get("last_pack") for k,v in item_model_log.items()},
                "config": asdict(cfg),
                "args": {
                    "retrain_interval": args.retrain_interval,
                    "n_splits": args.n_splits,
                    "rf_n_estimators": args.rf_n_estimators,
                    "gbr_n_estimators": args.gbr_n_estimators,
                    "disable_elastic": bool(args.disable_elastic),
                },
                "saved_at": pd.Timestamp.utcnow().isoformat(),
                "last_date": last_date_val,
                "enforce_no_leak": bool(getattr(args, "enforce_no_leak", False)),
            }
            os.makedirs(os.path.dirname(args.save_bundle), exist_ok=True)
            joblib.dump(bundle, args.save_bundle)
            print(f"[BUNDLE] saved -> {args.save_bundle}")
        except Exception as e:
            print(f"[WARN] bundle save failed: {e}")

    # ---- Summary ----
    print("\n=== Summary ===")
    print(json.dumps(scores, indent=2, ensure_ascii=False))
    print(f"[SAVED] {out_dir}/res_walkforward.csv, scores_walkforward.json, run_metadata.json, run_history.csv (+ plots)")
    return df_res, scores

# =========================
# CLI
# =========================

def _hybrid_parse_res_walk(res_walk_csv: str) -> pd.Series:
    df = _read_csv(res_walk_csv)
    if df is None or len(df) == 0:
        raise FileNotFoundError(f"res-walk csv 読み込み失敗: {res_walk_csv}")
    dcol = None
    for c in ["date", "日付", "伝票日付"]:
        if c in df.columns:
            dcol = c; break
    if dcol is None:
        df.index = _parse_date_series(df.iloc[:,0])
    else:
        df[dcol] = _parse_date_series(df[dcol]); df = df.set_index(dcol)
    ycol = None
    for c in ["y_true", "actual", "y", "truth", "合計"]:
        if c in df.columns:
            ycol = c; break
    if ycol is None:
        raise RuntimeError("res_walk_csv に y_true/actual 列が見つかりません。")
    y = pd.to_numeric(df[ycol].astype(str).str.replace(",","", regex=False), errors="coerce").dropna()
    y.index = pd.DatetimeIndex(y.index).sort_values()
    return y


def _hybrid_make_basic_feats(y: pd.Series, asof_date: pd.Timestamp, horizon: int) -> Dict[str, float]:
    hist = y.loc[y.index <= asof_date]
    if len(hist) == 0:
        return {"lag1": np.nan, "lag7": np.nan, "lag14": np.nan, "lag28": np.nan,
                "ma3": np.nan, "ma7": np.nan, "ma14": np.nan, "ma28": np.nan,
                "dow": float((asof_date + pd.Timedelta(days=horizon)).weekday()),
                "h": float(horizon)}
    def _lag(k):
        idx = asof_date - pd.Timedelta(days=k)
        return float(hist.loc[idx]) if idx in hist.index else float("nan")
    def _ma(k):
        sub = hist.tail(k).astype(float)
        return float(sub.mean()) if len(sub) > 0 else float("nan")
    d_target = asof_date + pd.Timedelta(days=horizon)
    return {
        "lag1": _lag(1), "lag7": _lag(7), "lag14": _lag(14), "lag28": _lag(28),
        "ma3": _ma(3), "ma7": _ma(7), "ma14": _ma(14), "ma28": _ma(28),
        "dow": float(pd.Timestamp(d_target).weekday()),
        "dow_sin": float(np.sin(2*np.pi*(pd.Timestamp(d_target).weekday())/7.0)),
        "dow_cos": float(np.cos(2*np.pi*(pd.Timestamp(d_target).weekday())/7.0)),
        "h": float(horizon),
    }


def _hybrid_morioka_base(y: pd.Series, asof_date: pd.Timestamp, horizon: int,
                         w_recent: int = 84, trend_window: int = 90) -> float:
    hist = y.loc[y.index <= asof_date]
    if len(hist) < 8:
        return float(hist.iloc[-1]) if len(hist) else 0.0
    target_dt = asof_date + pd.Timedelta(days=horizon)
    dwd = int(pd.Timestamp(target_dt).weekday())
    sub = hist.tail(w_recent)
    mask = (pd.DatetimeIndex(sub.index).weekday == dwd)
    base = float(np.median(sub[mask])) if mask.any() else float(sub.median())
    tw = min(len(hist), int(trend_window))
    sub2 = hist.tail(tw).astype(float)
    if len(sub2) >= 10:
        x = np.arange(len(sub2), dtype=float)
        A = np.vstack([x, np.ones_like(x)]).T
        try:
            a, b = np.linalg.lstsq(A, sub2.values, rcond=None)[0]
            base = float(base + a * horizon)
        except Exception:
            pass
    return float(max(0.0, base))


def _hybrid_fit_shortterm_ensemble(X: pd.DataFrame, y: pd.Series,
                                   val_ratio: float = 0.2) -> Tuple[List, np.ndarray]:
    from sklearn.linear_model import Ridge
    n = len(X)
    if n < 40:
        models = [Ridge(alpha=50.0).fit(X, y)]
        weights = np.array([1.0])
        return models, weights
    split = int(n * (1.0 - val_ratio))
    X_tr, y_tr = X.iloc[:split], y.iloc[:split]
    X_va, y_va = X.iloc[split:], y.iloc[split:]
    models = [
        ("ridge", Ridge(alpha=50.0)),
        ("rf1", RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
        ("rf2", RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42, n_jobs=-1)),
        ("et", ExtraTreesRegressor(n_estimators=200, random_state=42, n_jobs=-1)),
        ("gbr", GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42)),
    ]
    maes = []
    fitted = []
    from sklearn.metrics import mean_absolute_error
    for name, mdl in models:
        try:
            mdl.fit(X_tr, y_tr)
            pred = mdl.predict(X_va)
            mae = float(mean_absolute_error(y_va, pred)) if len(X_va) else 1e6
        except Exception:
            mae = 1e6
        maes.append(mae)
        fitted.append(mdl)
    maes = np.array(maes, dtype=float)
    inv = 1.0 / np.clip(maes, 1e-6, None)
    w = inv / inv.sum() if np.isfinite(inv).any() else np.ones_like(inv)/len(inv)
    return fitted, w


def _hybrid_predict_shortterm(models: List, weights: np.ndarray, X: pd.DataFrame) -> float:
    preds = []
    for mdl in models:
        try:
            preds.append(np.ravel(mdl.predict(X))[0])
        except Exception:
            preds.append(0.0)
    preds = np.array(preds, dtype=float)
    return float(max(0.0, float(np.dot(weights, preds))))


def _hybrid_calibrate(base_hist: pd.Series, y_hist: pd.Series) -> Tuple[str, object]:
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    X = base_hist.values.reshape(-1, 1).astype(float)
    y = y_hist.values.astype(float)
    if len(X) < 20:
        mdl = Ridge(alpha=10.0)
        mdl.fit(X, y)
        return ("ridge", mdl)
    split = int(len(X) * 0.75)
    X_tr, y_tr = X[:split], y[:split]
    X_va, y_va = X[split:], y[split:]
    cands = [
        ("ridge", Ridge(alpha=10.0)),
        ("gbr", GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=2, random_state=42)),
    ]
    best = None; best_mae = 1e18
    for name, mdl in cands:
        try:
            mdl.fit(X_tr, y_tr)
            pred = np.ravel(mdl.predict(X_va))
            mae = float(mean_absolute_error(y_va, pred)) if len(X_va) else 1e6
            if mae < best_mae:
                best = (name, mdl); best_mae = mae
        except Exception:
            continue
    if best is None:
        mdl = Ridge(alpha=10.0)
        mdl.fit(X, y)
        best = ("ridge", mdl)
    return best


def hybrid_evaluate(res_walk_csv: str, out_dir: str,
                    eval_start: Optional[str] = None, eval_end: Optional[str] = None,
                    train_window_days: int = 240, calib_window_days: int = 84,
                    step_days: int = 1, retrain_each_anchor: bool = False) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    y = _hybrid_parse_res_walk(res_walk_csv)
    if eval_end:
        e_end = pd.to_datetime(eval_end).normalize()
    else:
        e_end = y.index.max()
    if eval_start:
        e_start = pd.to_datetime(eval_start).normalize()
    else:
        e_start = max(y.index.min(), e_end - pd.Timedelta(days=119))
    dates = pd.date_range(e_start, e_end, freq=f"{max(1,int(step_days))}D")
    results = []
    cached_models_h = None; cached_weights_h = None; cached_calib = None
    for anchor in dates:
        if anchor - pd.Timedelta(days=1) not in y.index:
            continue
        hist_end = anchor - pd.Timedelta(days=1)
        hist_start = max(y.index.min(), hist_end - pd.Timedelta(days=train_window_days-1))
        y_hist = y.loc[(y.index >= hist_start) & (y.index <= hist_end)].astype(float)
        if len(y_hist) < 60:
            continue
        if retrain_each_anchor or cached_models_h is None:
            rows_h = {1: [], 2: [], 3: []}; ys_h = {1: [], 2: [], 3: []}
            for t in pd.date_range(hist_start, hist_end - pd.Timedelta(days=3), freq="D"):
                for h in (1, 2, 3):
                    feats = _hybrid_make_basic_feats(y, t, h)
                    rows_h[h].append(feats)
                    y_tgt = y.loc[t + pd.Timedelta(days=h)] if (t + pd.Timedelta(days=h)) in y.index else np.nan
                    ys_h[h].append(float(y_tgt) if np.isfinite(y_tgt) else np.nan)
            models_h = {}; weights_h = {}
            for h in (1, 2, 3):
                dfX = pd.DataFrame(rows_h[h]); s = pd.Series(ys_h[h])
                mask = np.isfinite(s.values) & dfX.notna().all(axis=1).values
                dfX = dfX.loc[mask]; s = s.loc[mask]
                if len(dfX) < 40: continue
                mdl, w = _hybrid_fit_shortterm_ensemble(dfX, s)
                models_h[h] = mdl; weights_h[h] = w
            cached_models_h, cached_weights_h = models_h, weights_h
        else:
            models_h, weights_h = cached_models_h, cached_weights_h
        calib_until = hist_end
        calib_from = max(y.index.min(), calib_until - pd.Timedelta(days=calib_window_days-1))
        base_hist = []; y_cal = []
        for t in pd.date_range(calib_from, calib_until, freq="D"):
            b = _hybrid_morioka_base(y, t, 1)
            base_hist.append(b)
            y_cal.append(float(y.loc[t + pd.Timedelta(days=1)]) if (t + pd.Timedelta(days=1)) in y.index else np.nan)
        base_hist = pd.Series(base_hist, index=pd.date_range(calib_from, calib_until, freq="D"))
        y_cal = pd.Series(y_cal, index=base_hist.index)
        maskc = np.isfinite(base_hist.values) & np.isfinite(y_cal.values)
        if retrain_each_anchor or cached_calib is None:
            name_cal, mdl_cal = _hybrid_calibrate(base_hist.loc[maskc], y_cal.loc[maskc]) if maskc.any() else ("ridge", None)
            cached_calib = (name_cal, mdl_cal)
        else:
            name_cal, mdl_cal = cached_calib
        for h in range(1, 8):
            d = anchor + pd.Timedelta(days=h)
            if d not in y.index:
                continue
            if h <= 3 and models_h and (h in models_h):
                feats = _hybrid_make_basic_feats(y, anchor, h)
                X_row = pd.DataFrame([feats])
                yhat = _hybrid_predict_shortterm(models_h[h], weights_h[h], X_row)
            else:
                base_pred = _hybrid_morioka_base(y, anchor, h)
                try:
                    yhat = float(np.ravel(mdl_cal.predict(np.array([[base_pred]], dtype=float)))[0]) if mdl_cal is not None else float(base_pred)
                except Exception:
                    yhat = float(base_pred)
                yhat = float(max(0.0, yhat))
            results.append({"anchor": str(anchor.date()), "date": str(d.date()), "h": int(h), "y_true": float(y.loc[d]), "y_pred": float(yhat)})
    if not results:
        raise RuntimeError("ハイブリッド評価結果が空です。評価期間や履歴を確認してください。")
    out_df = pd.DataFrame(results)
    out_df["ae"] = (out_df["y_true"] - out_df["y_pred"]).abs()
    def _metrics(df: pd.DataFrame) -> Dict[str, float]:
        yv = df["y_true"].values; yhat = df["y_pred"].values
        mae = float(np.mean(np.abs(yv - yhat))) if len(df) else float("nan")
        rmse = float(np.sqrt(np.mean((yv - yhat)**2))) if len(df) else float("nan")
        r2 = float(r2_score(yv, yhat)) if len(df) else float("nan")
        return {"N": int(len(df)), "MAE": mae, "RMSE": rmse, "R2": r2}
    metrics_all = _metrics(out_df); metrics_t1 = _metrics(out_df[out_df["h"] == 1])
    summary = {"overall": metrics_all, "t+1": metrics_t1}
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, "hybrid_results.csv")
    out_json = os.path.join(out_dir, "metrics.json")
    out_df.to_csv(out_csv, index=False)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] results -> {out_csv}")
    print(f"[SAVED] metrics -> {out_json}")
    return summary


def main():
    ap = argparse.ArgumentParser(description="品目OOF→合計direct/ブレンド（高速化・保存対応 完全修正版）")
    # 通常の学習/評価
    ap.add_argument("--raw-csv", type=str, required=False)
    ap.add_argument("--reserve-csv", type=str, default=None)
    ap.add_argument("--raw-date-col", type=str, default="伝票日付")
    ap.add_argument("--raw-item-col", type=str, default="品名")
    ap.add_argument("--raw-weight-col", type=str, default="正味重量")
    ap.add_argument("--reserve-date-col", type=str, default="予約日")
    ap.add_argument("--reserve-count-col", type=str, default="台数")
    ap.add_argument("--reserve-fixed-col", type=str, default="固定客")
    ap.add_argument("--out-dir", type=str, required=True)
    
    # DB直接取得モード（CSV廃止）
    ap.add_argument("--use-db", action="store_true",
                    help="DBから直接データ取得（CSVを使わない）")
    ap.add_argument("--db-connection-string", type=str, default=None,
                    help="PostgreSQL接続文字列（--use-db時に指定、未指定時は環境変数DATABASE_URL）")
    ap.add_argument("--actuals-start-date", type=str, default=None,
                    help="実績データ開始日（YYYY-MM-DD形式、--use-db時に必須）")
    ap.add_argument("--actuals-end-date", type=str, default=None,
                    help="実績データ終了日（YYYY-MM-DD形式、--use-db時に必須）")
    ap.add_argument("--reserve-start-date", type=str, default=None,
                    help="予約データ開始日（YYYY-MM-DD形式、--use-db時）")
    ap.add_argument("--reserve-end-date", type=str, default=None,
                    help="予約データ終了日（YYYY-MM-DD形式、--use-db時）")

    # 既存系
    ap.add_argument("--top-n", type=int, default=6)
    ap.add_argument("--min-stage1-days", type=int, default=120)
    ap.add_argument("--min-stage2-rows", type=int, default=28)
    ap.add_argument("--use-same-day-info", action="store_true")
    ap.add_argument("--no-same-day-info", dest="use_same_day_info", action="store_false")
    ap.set_defaults(use_same_day_info=True)
    ap.add_argument("--max-history-days", type=int, default=600)
    ap.add_argument("--time-decay", type=str, default="linear", choices=["none","linear","exponential"])
    ap.add_argument("--calibration-window-days", type=int, default=28)
    ap.add_argument("--calibration-window-days-tuesday", type=int, default=56)
    ap.add_argument("--zero-cap-quantile", type=float, default=0.15)
    ap.add_argument("--share-oof-models", type=int, default=2)
    ap.add_argument("--random-state", type=int, default=42)

    # 高速化系
    ap.add_argument("--retrain-interval", type=int, default=1,
                    help="walk-forwardでの再学習間隔（日）。1=毎日学習、3=3日ごとに学習")
    ap.add_argument("--n-splits", type=int, default=5, help="TimeSeriesSplit の分割数（高速化は3推奨）")
    ap.add_argument("--rf-n-estimators", type=int, default=240)
    ap.add_argument("--gbr-n-estimators", type=int, default=220)
    ap.add_argument("--n-jobs", type=int, default=1, help="Stage1を品目並列で実行する並列数（-1で全コア）")
    ap.add_argument("--disable-elastic", action="store_true", help="Stage1のElasticNetを学習スキップ（高速化）")
    ap.add_argument("--no-plots", action="store_true", help="PNG出力をスキップ（高速化）")

    # 保存
    ap.add_argument("--save-bundle", type=str, default=None, help="学習済み最終モデルバンドルをjoblib保存するパス")
    ap.add_argument("--enforce-no-leak", action="store_true", help="学習前に未来日や潜在的リークを厳格に検査する")

    # 追加: ハイブリッド週次評価（t+1~t+7）
    ap.add_argument("--hybrid-eval-res-walk", type=str, default=None, help="既存のres_walkforward.csv を指定するとハイブリッド評価のみ実行")
    ap.add_argument("--hybrid-out-dir", type=str, default=None, help="ハイブリッド評価の出力先（未指定時は out-dir/hybrid_eval）")
    ap.add_argument("--hybrid-eval-start", type=str, default=None)
    ap.add_argument("--hybrid-eval-end", type=str, default=None)
    ap.add_argument("--hybrid-train-window-days", type=int, default=240)
    ap.add_argument("--hybrid-calib-window-days", type=int, default=84)
    ap.add_argument("--hybrid-step-days", type=int, default=1)
    ap.add_argument("--hybrid-retrain-each-anchor", action="store_true")

    args = ap.parse_args()

    # 分岐: ハイブリッド評価専用モード
    if args.hybrid_eval_res_walk:
        out_dir = args.hybrid_out_dir or (os.path.join(args.out_dir, "hybrid_eval") if args.out_dir else "hybrid_eval")
        hybrid_summary = hybrid_evaluate(
            res_walk_csv=args.hybrid_eval_res_walk,
            out_dir=out_dir,
            eval_start=args.hybrid_eval_start, eval_end=args.hybrid_eval_end,
            train_window_days=args.hybrid_train_window_days,
            calib_window_days=args.hybrid_calib_window_days,
            step_days=args.hybrid_step_days,
            retrain_each_anchor=bool(args.hybrid_retrain_each_anchor),
        )
        print(json.dumps(hybrid_summary, ensure_ascii=False, indent=2))
        return

    # 通常モード（従来互換）
    if args.use_db:
        # DB直接取得モード
        from datetime import datetime
        from db_loader import load_raw_from_db, load_reserve_from_db
        
        # 日付引数の検証
        if not args.actuals_start_date or not args.actuals_end_date:
            raise ValueError(
                "--use-db requires --actuals-start-date and --actuals-end-date"
            )
        
        actuals_start = datetime.strptime(args.actuals_start_date, "%Y-%m-%d").date()
        actuals_end = datetime.strptime(args.actuals_end_date, "%Y-%m-%d").date()
        
        print(f"[DB MODE] Loading actuals from DB: {actuals_start} to {actuals_end}")
        df_raw = load_raw_from_db(
            start_date=actuals_start,
            end_date=actuals_end,
            date_col=args.raw_date_col,
            item_col=args.raw_item_col,
            weight_col=args.raw_weight_col,
            connection_string=args.db_connection_string,
        )
        print(f"[DB MODE] Loaded {len(df_raw)} actuals records from DB")
        
        # 予約データの取得（オプション）
        df_res = None
        if args.reserve_start_date and args.reserve_end_date:
            reserve_start = datetime.strptime(args.reserve_start_date, "%Y-%m-%d").date()
            reserve_end = datetime.strptime(args.reserve_end_date, "%Y-%m-%d").date()
            
            print(f"[DB MODE] Loading reserve from DB: {reserve_start} to {reserve_end}")
            df_res = load_reserve_from_db(
                start_date=reserve_start,
                end_date=reserve_end,
                date_col=args.reserve_date_col,
                count_col=args.reserve_count_col,
                fixed_col=args.reserve_fixed_col,
                connection_string=args.db_connection_string,
            )
            print(f"[DB MODE] Loaded {len(df_res)} reserve records from DB")
    else:
        # CSV読み込みモード（従来通り）
        df_raw = _read_csv(args.raw_csv)
        if df_raw is None or len(df_raw) == 0:
            raise FileNotFoundError(f"raw-csv 読み込み失敗: {args.raw_csv}")
        df_res = _read_csv(args.reserve_csv) if args.reserve_csv else None

    cfg = Config(
        top_n=args.top_n,
        min_stage1_days=args.min_stage1_days,
        min_stage2_rows=args.min_stage2_rows,
        use_same_day_info=args.use_same_day_info,
        max_history_days=args.max_history_days,
        time_decay=args.time_decay,
        calibration_window_days=args.calibration_window_days,
        calibration_window_days_tuesday=args.calibration_window_days_tuesday,
        zero_cap_quantile=args.zero_cap_quantile,
        share_oof_models=args.share_oof_models,
        random_state=args.random_state,
    )

    run_walkforward(df_raw=df_raw, df_reserve=df_res,
                    date_col=args.raw_date_col, item_col=args.raw_item_col, weight_col=args.raw_weight_col,
                    reserve_date_col=args.reserve_date_col, reserve_count_col=args.reserve_count_col, reserve_fixed_col=args.reserve_fixed_col,
                    out_dir=args.out_dir, cfg=cfg, args=args)

if __name__ == "__main__":
    main()
