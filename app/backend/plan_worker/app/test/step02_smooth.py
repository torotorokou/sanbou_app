# /backend/app/test/step02_smooth.py
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg
from common import _dsn

OUT = Path("/backend/app/test/out")

# --- デフォルト（過剰平滑を避ける設定） ---
TAU_BASE = 1.0  # EB縮約の基準強度
LAMBDA = 0.3  # cvに対する係数
CV_CAP = 0.8  # cvの上限
H = 1  # MA半窓幅（1=3点）
ALPHA = 0.65  # 戻しブレンド: 1=平滑のみ, 0=EB後そのまま
KERNEL_GAMMA = 1.0  # >1で中央重み↑（平滑弱め）


# -----------------------
# カーネル・縮約・MA
# -----------------------
def triangular_kernel(h: int, gamma: float = 1.0) -> np.ndarray:
    """三角カーネル（中央重み調整: gamma>1 で中心を強調＝平滑弱め）"""
    if h <= 0:
        return np.array([1.0], dtype=float)
    offs = np.arange(-h, h + 1)
    w = (h + 1 - np.abs(offs)).astype(float)
    if gamma != 1.0:
        w = w**gamma
    return w / w.sum()


def shrink_eb(ave: np.ndarray, n: np.ndarray, cv: np.ndarray, mu_prior: float) -> np.ndarray:
    """Empirical Bayes 縮約（n と cv に応じて mu_prior へ引き寄せ）"""
    cv_eff = np.clip(np.nan_to_num(cv, nan=0.0), 0.0, CV_CAP)
    tau = TAU_BASE * (1.0 + LAMBDA * cv_eff)
    # ave の NaN は prior で補う（n=0 も自然に prior 側へ）
    ave_filled = np.where(np.isnan(ave), mu_prior, ave)
    return (n * ave_filled + tau * mu_prior) / (n + tau + 1e-12)


def circ_ma53(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """週方向の円環移動平均（53週でラップ）"""
    L = len(x)
    y = np.empty(L, float)
    h = (len(w) - 1) // 2
    for i in range(L):
        idx = [(i + k) % L for k in range(-h, h + 1)]
        vals = x[idx]
        ww = w.copy()
        m = ~np.isnan(vals)
        if not m.any():
            y[i] = np.nan
            continue
        ww = ww * m
        ww = ww / ww.sum()
        y[i] = float(np.nansum(vals * ww))
    return y


def ma53_non_circular(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """週方向の非円環移動平均（端は縮む／重み再正規化）"""
    L = len(x)
    y = np.empty(L, float)
    h = (len(w) - 1) // 2
    for i in range(L):
        lo = max(0, i - h)
        hi = min(L, i + h + 1)
        vals = x[lo:hi]
        ww = w[h - (i - lo) : h + (hi - i)]
        m = ~np.isnan(vals)
        if not m.any():
            y[i] = np.nan
            continue
        ww = ww[m]
        ww = ww / ww.sum()
        y[i] = float(np.nansum(vals[m] * ww))
    return y


# -----------------------
# メイン処理
# -----------------------
def main():
    # ★ ここを最初に置く（SyntaxError 対策）
    global TAU_BASE, LAMBDA, CV_CAP, H, KERNEL_GAMMA, ALPHA

    ap = argparse.ArgumentParser(
        description="Weekly smoothing with EB shrinkage + (non-)circular MA and alpha blending."
    )
    ap.add_argument("--tau", type=float, default=TAU_BASE, help="EB base strength (TAU_BASE)")
    ap.add_argument("--lam", type=float, default=LAMBDA, help="EB cv coefficient (LAMBDA)")
    ap.add_argument("--cv-cap", type=float, default=CV_CAP, help="Cap for cv in EB")
    ap.add_argument("--h", type=int, default=H, help="Half window size for MA (H=1 -> 3-point)")
    ap.add_argument(
        "--kernel-gamma",
        type=float,
        default=KERNEL_GAMMA,
        help="Kernel center emphasis (>1 → smoother weaker)",
    )
    ap.add_argument("--alpha", type=float, default=ALPHA, help="Blend: alpha*smooth + (1-alpha)*EB")
    ap.add_argument(
        "--circular",
        action="store_true",
        help="Use circular MA (default: non-circular)",
    )
    args = ap.parse_args()

    # ここでモジュール変数を更新
    TAU_BASE = args.tau
    LAMBDA = args.lam
    CV_CAP = args.cv_cap
    H = args.h
    KERNEL_GAMMA = args.kernel_gamma
    ALPHA = args.alpha

    OUT.mkdir(parents=True, exist_ok=True)

    # 入力：過去5年平均＋n,cv（ビュー）
    with psycopg.connect(_dsn()) as conn:
        mv = pd.read_sql_query(
            """
            select
              scope,
              iso_week::int as iso_week,
              iso_dow::int  as iso_dow,
              ave::float8   as ave,
              n::int        as n,
              coalesce(cv, 0)::float8 as cv
            from mart.mv_inb_avg5y_day_scope
        """,
            conn,
        )

    rows: list[tuple[str, int, int, float]] = []
    w = triangular_kernel(H, gamma=KERNEL_GAMMA)

    # scope×iso_dow 毎に：EB縮約 → MA → αブレンド
    for (scope, dow), g in mv.groupby(["scope", "iso_dow"], sort=False):
        arr_ave = np.full(53, np.nan, float)
        arr_n = np.zeros(53, float)
        arr_cv = np.zeros(53, float)

        wk = g["iso_week"].to_numpy(dtype=int) - 1  # 1..53 → 0..52
        arr_ave[wk] = g["ave"].to_numpy(dtype=float)
        arr_n[wk] = g["n"].to_numpy(dtype=float)
        arr_cv[wk] = g["cv"].to_numpy(dtype=float)

        mu_prior = np.nanmean(arr_ave)
        if not np.isfinite(mu_prior):
            mask = arr_n > 0
            mu_prior = float(np.nanmean(arr_ave[mask])) if mask.any() else 0.0

        mu_post = shrink_eb(arr_ave, arr_n, arr_cv, mu_prior)

        if H <= 0 or w.size == 1:
            sm_raw = mu_post.copy()
        else:
            sm_raw = circ_ma53(mu_post, w) if args.circular else ma53_non_circular(mu_post, w)

        # 過剰平滑の抑制：戻しブレンド
        sm = ALPHA * sm_raw + (1.0 - ALPHA) * mu_post

        for k in range(53):
            rows.append((str(scope), int(k + 1), int(dow), float(sm[k])))

    out = pd.DataFrame(rows, columns=["scope", "iso_week", "iso_dow", "day_mean_smooth"])
    out.to_csv(OUT / "smooth_preview.csv", index=False)

    # 簡易チェック＋ログ
    neg = int((out["day_mean_smooth"] < 0).sum())
    nan = int(out["day_mean_smooth"].isna().sum())
    p95 = float(out["day_mean_smooth"].quantile(0.95))
    p05 = float(out["day_mean_smooth"].quantile(0.05))
    amp = p95 - p05
    print(f"[smooth] rows={len(out)} neg={neg} nan={nan} p05={p05:.3f} p95={p95:.3f} amp={amp:.3f}")
    if nan > 0:
        raise SystemExit("NaN残あり。パラメータまたは元データ要確認")
    if neg > 0:
        raise SystemExit("負値あり。要確認")


if __name__ == "__main__":
    main()
