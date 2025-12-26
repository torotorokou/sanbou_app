from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

SmoothingMethod = Literal["median_then_mean", "mean_only"]


# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
@dataclass(frozen=True)
class SmoothConfig:
    # 週内スムージング
    intraweek_window: int = 3  # 奇数推奨（1で無効）
    intraweek_method: SmoothingMethod = "median_then_mean"
    within_week_rel_cap: float = 1.6  # 週平均×倍率 上限
    min_open_days_for_smooth: int = 2  # これ未満は例外処理

    # 日タイプ倍率（例：平日=1.0, 日曜=0.6, 祝日=0.8 など）
    scope_weight_multiplier: dict[str, float] | None = None

    # 月またぎブリッジ平滑
    bridge_smooth_enabled: bool = True
    bridge_smooth_window: int = 5
    bridge_smooth_scope_values: tuple[str, ...] = ("biz",)  # 平日のみ等


# ------------------------------------------------------------
# 共通ユーティリティ
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
    """外れ値に強いロール（中央値→平均）。"""
    w = _ensure_odd(window)
    if w <= 1:
        return s.astype(float)
    x = s.astype(float)
    if method == "median_then_mean":
        med = x.rolling(window=w, center=center, min_periods=1).median()
        sm = med.rolling(window=w, center=center, min_periods=1).mean()
        return sm.fillna(0.0)
    else:
        return x.rolling(window=w, center=center, min_periods=1).mean().fillna(0.0)


def normalize_to_group_sum(
    df: pd.DataFrame, group_keys: Iterable[str], col: str, target_sum: float
) -> pd.Series:
    cur = float(df[col].sum())
    if cur <= 0.0:
        return df[col]
    return df[col] * (target_sum / cur)


# ------------------------------------------------------------
# 週内パイプライン（倍率→平滑→相対キャップ→正規化）
# ------------------------------------------------------------
def apply_intraweek_pipeline(
    df_week: pd.DataFrame,
    weight_raw_col: str,
    weight_col: str,
    cfg: SmoothConfig,
    scope_col: str | None = None,
) -> pd.DataFrame:
    """
    前提: df_week は 1週ぶん（同じ (month_date, iso_year, iso_week)）。
    1) scope倍率適用（開いている日にのみ）
    2) 営業日が少ない週の例外処理（開いてる日に100%を等比配分）
    3) ローリング平滑（閉所日は NaN 扱いで“にじみ”を防ぐ）
    4) 相対キャップ（開いている日の平均×倍率）
    5) 合計=1に再正規化（開いている日だけで）
    ※ 閉所日は常に0のまま固定
    """
    g = df_week.copy()
    w = g[weight_raw_col].astype(float).fillna(0.0)

    # 開いている日（raw>0）
    open_mask = w > 0

    # 1) scope倍率（開いている日にのみ適用）
    if scope_col and cfg.scope_weight_multiplier:
        factors = (
            g[scope_col]
            .map(lambda v: float(cfg.scope_weight_multiplier.get(str(v), 1.0)))
            .astype(float)
        )
        w = np.where(open_mask, w * factors, 0.0).astype(float)

    # 2) 営業日が少ない週
    open_days = int(open_mask.sum())
    if open_days < int(cfg.min_open_days_for_smooth):
        w_small = np.where(open_mask, w, 0.0).astype(float)
        s = float(w_small.sum())
        g[weight_col] = np.where(open_mask, (w_small / s) if s > 0 else 0.0, 0.0)
        return g

    # 3) 平滑（閉所日は NaN 扱い → ロール後に 0 に戻す）
    w_for_roll = pd.Series(np.where(open_mask, w, np.nan), index=g.index)
    w_sm = rolling_smooth(
        w_for_roll, window=cfg.intraweek_window, method=cfg.intraweek_method
    ).fillna(0.0)

    # 4) 相対キャップ（開いている日の平均ベース）
    open_mean = float(w_sm[open_mask].mean()) if open_days > 0 else 0.0
    if open_mean > 0.0:
        w_cap = np.where(
            open_mask, np.minimum(w_sm, open_mean * float(cfg.within_week_rel_cap)), 0.0
        )
    else:
        w_cap = np.where(open_mask, w_sm, 0.0)

    # 5) 正規化（開いている日のみで1に）
    s = float(np.sum(w_cap))
    g[weight_col] = np.where(open_mask, (w_cap / s) if s > 0 else 0.0, 0.0)
    return g


# ------------------------------------------------------------
# 月またぎブリッジ平滑（全期間ロール→月ごと再正規化）
# ------------------------------------------------------------
def bridge_smooth_across_months_and_renorm(
    df: pd.DataFrame,
    date_col: str,
    month_key: str,
    target_col: str,
    scope_col: str,
    scope_values: tuple[str, ...],
    window: int,
    method: SmoothingMethod = "median_then_mean",
) -> pd.DataFrame:
    """
    月境界を越えて連続ロール → その後、各月の合計を元の月合計にスケールバック（KPI一致を維持）。
    scope_values（例: ('biz',)）で対象（平日のみ等）を限定。
    """
    out = df.copy().sort_values(date_col)

    # 月合計を保存
    month_totals = out.groupby(month_key, as_index=True)[target_col].sum()

    # ロール適用対象（選択scopeのみ）
    mask = out[scope_col].isin(scope_values)
    s = out.loc[mask, target_col].astype(float)
    if len(s) > 0:
        out.loc[mask, target_col] = rolling_smooth(s, window=window, method=method)

    # 月合計に戻す
    def _renorm(g: pd.DataFrame) -> pd.DataFrame:
        tgt = float(month_totals.loc[g[month_key].iloc[0]])
        cur = float(g[target_col].sum())
        if cur > 0:
            g[target_col] = g[target_col] * (tgt / cur)
        return g

    return out.groupby(month_key, group_keys=False).apply(_renorm, include_groups=True)
