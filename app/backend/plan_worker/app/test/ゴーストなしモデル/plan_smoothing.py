from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Optional, Tuple

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
    within_week_rel_cap: float = 1.6  # （平日）週平均×倍率 上限
    min_open_days_for_smooth: int = 2  # これ未満は例外処理（開いてる日に100%）

    # 日タイプ倍率（例：平日=1.0, 日曜=1.0, 祝日=1.0）
    scope_weight_multiplier: Optional[Dict[str, float]] = None

    # 週内スムージングの対象スコープ（Bモード：平日のみ）
    intraweek_smooth_scope_values: Tuple[str, ...] = ("biz",)

    # 非平日（sun/hol）の週内1日あたり上限シェア（例: 0.08 = 8%）
    non_biz_scopes: Tuple[str, ...] = ("sun", "hol")
    non_biz_share_cap_per_day: Optional[float] = 0.08

    # 任意：1日あたりの全体上限シェア（尖り対策）。Noneで無効
    per_day_share_cap: Optional[float] = None

    # 月またぎブリッジ平滑
    bridge_smooth_enabled: bool = True
    bridge_smooth_window: int = 5
    bridge_smooth_scope_values: Tuple[str, ...] = ("biz",)  # 平日のみ等


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
# 週内パイプライン（Bモード）
#   ・倍率 →（平日だけ）平滑 →（平日だけ）相対キャップ
#   ・一旦正規化 → 非平日シェア上限でクリップ → 余りを平日に再配分 → 最終正規化
# ------------------------------------------------------------
def apply_intraweek_pipeline(
    df_week: pd.DataFrame,
    weight_raw_col: str,
    weight_col: str,
    cfg: SmoothConfig,
    scope_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    前提: df_week は 1週ぶん（同じ (month_date, iso_year, iso_week)）。

    1) scope倍率適用
    2) 平日open日が少ない週はフォールバック（開いてる日に均等）
    3) （平日だけ）ロール平滑
    4) （平日だけ）相対キャップ（平日平均×cap）
    5) 合計=1に正規化
    6) 非平日（日曜/祝日）の1日上限シェアでクリップ → 余りを平日に比例再配分
    7) 任意の1日上限シェア（全体）で再クリップ → 余りを平日に比例再配分
    """
    g = df_week.copy()

    # 0) 下ごしらえ
    w = g[weight_raw_col].astype(float).fillna(0.0)
    if scope_col and cfg.scope_weight_multiplier:
        mult = (
            g[scope_col]
            .map(lambda v: float(cfg.scope_weight_multiplier.get(str(v), 1.0)))
            .astype(float)
        )
        w = (w * mult).astype(float)

    if scope_col:
        biz_mask = g[scope_col].isin(cfg.intraweek_smooth_scope_values)
        nonbiz_mask = g[scope_col].isin(cfg.non_biz_scopes)
        sun_mask = g[scope_col] == "sun"
        hol_mask = g[scope_col] == "hol"
    else:
        biz_mask = pd.Series(True, index=g.index)
        nonbiz_mask = pd.Series(False, index=g.index)
        sun_mask = hol_mask = pd.Series(False, index=g.index)

    # 1) 平日open日が少ない週（フォールバック：開いている日に均等→非平日キャップ→平日に再配分）
    open_biz_days = int((w[biz_mask] > 0).sum())
    if open_biz_days < int(cfg.min_open_days_for_smooth):
        # 均等化 → 合計=1
        w2 = (w > 0).astype(float)
        s = float(w2.sum())
        w_norm = (w2 / s) if s > 0 else w2

        # 非平日（日/祝）の1日上限シェアでクリップ → 余りを平日に比例配分
        w_norm = _clip_and_redistribute(
            w_norm,
            clip_mask=(sun_mask | hol_mask),
            per_day_cap=cfg.non_biz_share_cap_per_day,
            redistribute_mask=biz_mask,
        )

        # 任意の全体1日上限シェア（指定時のみ）
        if cfg.per_day_share_cap is not None:
            w_norm = _clip_and_redistribute(
                w_norm,
                clip_mask=(w_norm > 0),
                per_day_cap=cfg.per_day_share_cap,
                redistribute_mask=biz_mask,
            )

        # 最終正規化
        total = float(w_norm.sum())
        g[weight_col] = (w_norm / total) if total > 0 else w_norm
        return g

    # 2) （平日だけ）平滑
    w_sm = w.copy()
    if biz_mask.any():
        w_sm.loc[biz_mask] = rolling_smooth(
            w.loc[biz_mask], window=cfg.intraweek_window, method=cfg.intraweek_method
        )

    # 3) （平日だけ）相対キャップ（平日平均×cap）
    if cfg.within_week_rel_cap and cfg.within_week_rel_cap > 0 and biz_mask.any():
        biz_vals = w_sm.loc[biz_mask].to_numpy(dtype=float)
        m = float(biz_vals.mean()) if len(biz_vals) else 0.0
        if m > 0:
            upper = m * float(cfg.within_week_rel_cap)
            w_sm.loc[biz_mask] = np.minimum(biz_vals, upper)

    # 4) 一旦 合計=1 に正規化
    s = float(w_sm.sum())
    w_norm = (w_sm / s) if s > 0 else w_sm

    # 5) 非平日（日曜/祝日）の1日上限シェアを適用 → 余りを平日に按分
    w_norm = _clip_and_redistribute(
        w_norm,
        clip_mask=(sun_mask | hol_mask),
        per_day_cap=cfg.non_biz_share_cap_per_day,
        redistribute_mask=biz_mask,
    )

    # 6) 任意の全体1日上限シェア（尖り抑制）
    if cfg.per_day_share_cap is not None:
        w_norm = _clip_and_redistribute(
            w_norm,
            clip_mask=(w_norm > 0),
            per_day_cap=cfg.per_day_share_cap,
            redistribute_mask=biz_mask,
        )

    # 最終
    g[weight_col] = w_norm / float(w_norm.sum()) if float(w_norm.sum()) > 0 else w_norm
    return g


# ---- クリップ＆再配分ユーティリティ ----------------------------------------
def _clip_and_redistribute(
    w_norm: pd.Series,
    clip_mask: pd.Series,
    per_day_cap: Optional[float],
    redistribute_mask: pd.Series,
) -> pd.Series:
    """
    w_norm: 合計=1の重みベクトルを想定（厳密でなくてもOK）。capで超過をクリップし、余剰を再配分。
    clip_mask: クリップ対象（日曜/祝日など）
    per_day_cap: 1日あたり上限（Noneなら何もしない）
    redistribute_mask: 余剰を配る対象（通常は平日）
    """
    v = w_norm.astype(float).copy()
    if per_day_cap is None:
        return v

    # クリップ
    over = clip_mask & (v > per_day_cap)
    if over.any():
        v.loc[over] = per_day_cap

    # 余った分を平日に比例配分
    deficit = 1.0 - float(v.sum())
    if abs(deficit) < 1e-12:
        return v

    base = v.loc[redistribute_mask & (v > 0)]
    base_sum = float(base.sum())
    if base_sum > 0:
        v.loc[base.index] += (base / base_sum) * deficit
    else:
        # 平日に重みがない→全体に均等配分
        pos = v > 0
        cnt = int(pos.sum())
        if cnt > 0:
            v.loc[pos] += deficit / cnt

    # 最終正規化
    total = float(v.sum())
    return v / total if total > 0 else v


# ------------------------------------------------------------
# 月またぎブリッジ平滑（全期間ロール→月ごと再正規化）
# ------------------------------------------------------------
def bridge_smooth_across_months_and_renorm(
    df: pd.DataFrame,
    date_col: str,
    month_key: str,
    target_col: str,
    scope_col: str,
    scope_values: Tuple[str, ...],
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

    # ロール適用対象（例：平日のみ）
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
