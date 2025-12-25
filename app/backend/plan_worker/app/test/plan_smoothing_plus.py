from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

# 平滑モード定義
SmoothingMethod = Literal["median_then_mean", "mean_only", "gaussian"]


# ------------------------------------------------------------
# 設定クラス
# ------------------------------------------------------------
@dataclass(frozen=True)
class SmoothConfig:
    intraweek_window: int = 3
    intraweek_method: SmoothingMethod = "median_then_mean"
    within_week_rel_cap: float = 1.6
    min_open_days_for_smooth: int = 2

    scope_weight_multiplier: dict[str, float] | None = None

    bridge_smooth_enabled: bool = True
    bridge_smooth_window: int = 5
    bridge_smooth_scope_values: tuple[str, ...] = ("biz",)


# ------------------------------------------------------------
# 共通関数
# ------------------------------------------------------------
def _ensure_odd(n: int) -> int:
    n = max(1, int(n))
    return n if n % 2 == 1 else n + 1


def rolling_smooth(
    s: pd.Series,
    window: int,
    method: SmoothingMethod = "median_then_mean",
    center: bool = True,
) -> pd.Series:
    """ロール平滑（中央値→平均 / 平均 / ガウス）"""
    w = _ensure_odd(window)
    if w <= 1:
        return s.astype(float)
    x = s.astype(float).fillna(0.0)

    if method == "median_then_mean":
        med = x.rolling(window=w, center=center, min_periods=1).median()
        sm = med.rolling(window=w, center=center, min_periods=1).mean()
        return sm.fillna(0.0)

    elif method == "mean_only":
        return x.rolling(window=w, center=center, min_periods=1).mean().fillna(0.0)

    elif method == "gaussian":
        sigma = w / 2.0
        arr = x.to_numpy(dtype=float)
        smoothed = gaussian_filter1d(arr, sigma=sigma, mode="nearest")
        return pd.Series(smoothed, index=s.index)

    else:
        raise ValueError(f"Unknown smoothing method: {method}")


# ------------------------------------------------------------
# グループ正規化
# ------------------------------------------------------------
def normalize_to_group_sum(
    df: pd.DataFrame, group_keys: Iterable[str], col: str, target_sum: float
) -> pd.Series:
    cur = float(df[col].sum())
    if cur <= 0.0:
        return df[col]
    return df[col] * (target_sum / cur)


# ------------------------------------------------------------
# 週内パイプライン（日曜・祝日固定対応）
# ------------------------------------------------------------
def apply_intraweek_pipeline(
    df_week: pd.DataFrame,
    weight_raw_col: str,
    weight_col: str,
    cfg: SmoothConfig,
    scope_col: str | None = None,
) -> pd.DataFrame:
    """
    前提: df_week は同一 (month_date, iso_year, iso_week)
    ・scope倍率適用
    ・営業日が少ない週は等分
    ・平滑 → 相対キャップ → 正規化
    ・日曜・祝日・closed は固定
    """
    g = df_week.copy()
    w = g[weight_raw_col].astype(float).fillna(0.0)

    # --- ★ 日曜・祝日・閉所日 固定処理 ---
    if scope_col:
        fixed_mask = g[scope_col].isin(["sun", "hol", "closed"])
        if fixed_mask.any():
            # そのまま固定
            g.loc[fixed_mask, weight_col] = w[fixed_mask]
        # 平日だけ処理対象
        g_proc = g.loc[~fixed_mask].copy()
    else:
        g_proc = g.copy()
    # ----------------------------------------

    if g_proc.empty:
        return g

    open_mask = g_proc[weight_raw_col] > 0

    # 1) scope倍率
    if scope_col and cfg.scope_weight_multiplier:
        factors = (
            g_proc[scope_col]
            .map(lambda v: float(cfg.scope_weight_multiplier.get(str(v), 1.0)))
            .astype(float)
        )
        w_scaled = np.where(open_mask, g_proc[weight_raw_col] * factors, 0.0).astype(float)
    else:
        w_scaled = g_proc[weight_raw_col].astype(float)

    # 2) 営業日が少ない週
    open_days = int(open_mask.sum())
    if open_days < int(cfg.min_open_days_for_smooth):
        w_small = np.where(open_mask, w_scaled, 0.0)
        s = float(np.sum(w_small))
        g_proc[weight_col] = np.where(open_mask, (w_small / s) if s > 0 else 0.0, 0.0)
    else:
        # 3) 平滑
        w_for_roll = pd.Series(np.where(open_mask, w_scaled, np.nan), index=g_proc.index)
        w_sm = rolling_smooth(
            w_for_roll, window=cfg.intraweek_window, method=cfg.intraweek_method
        ).fillna(0.0)
        # 4) キャップ
        open_mean = float(w_sm[open_mask].mean()) if open_days > 0 else 0.0
        if open_mean > 0.0:
            w_cap = np.where(
                open_mask,
                np.minimum(w_sm, open_mean * float(cfg.within_week_rel_cap)),
                0.0,
            )
        else:
            w_cap = np.where(open_mask, w_sm, 0.0)
        # 5) 正規化
        s = float(np.sum(w_cap))
        g_proc[weight_col] = np.where(open_mask, (w_cap / s) if s > 0 else 0.0, 0.0)

    # 結合（固定行はそのまま）
    g.loc[g_proc.index, weight_col] = g_proc[weight_col]
    return g


# ------------------------------------------------------------
# 月またぎブリッジ平滑（ガウス対応）
# ------------------------------------------------------------
def bridge_smooth_across_months_and_renorm(
    df: pd.DataFrame,
    date_col: str,
    month_key: str,
    target_col: str,
    scope_col: str,
    scope_values: tuple[str, ...],
    window: int,
    method: SmoothingMethod = "gaussian",
) -> pd.DataFrame:
    """月境界を越えて連続ロール平滑 → 月ごとにKPI値へ再スケール"""
    out = df.copy().sort_values(date_col)
    month_totals = out.groupby(month_key, as_index=True)[target_col].sum()

    mask = out[scope_col].isin(scope_values)  # 平日のみ
    s = out.loc[mask, target_col].astype(float)
    if len(s) > 0:
        out.loc[mask, target_col] = rolling_smooth(s, window=window, method=method)

    def _renorm(g: pd.DataFrame) -> pd.DataFrame:
        tgt = float(month_totals.loc[g[month_key].iloc[0]])
        cur = float(g[target_col].sum())
        if cur > 0:
            g[target_col] = g[target_col] * (tgt / cur)
        return g

    return out.groupby(month_key, group_keys=False).apply(_renorm, include_groups=True)
