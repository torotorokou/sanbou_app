"""
DataFrame の日付関連共通ユーティリティ

- 日付列候補の推定
- 最小日付を起点にした期間フィルタ（oneday / oneweek / onemonth / all）
"""

from typing import Any, Dict, List, Optional

import pandas as pd

try:
    # 既存ユーティリティ（曜日括弧除去）
    from backend_shared.utils.dataframe_utils import remove_weekday_parentheses
except Exception:  # フォールバック

    def remove_weekday_parentheses(df, column):  # type: ignore
        return df


DEFAULT_DATE_CANDIDATES = ["伝票日付", "日付", "date", "Date"]


def find_date_column(df: Any, candidates: List[str]) -> Optional[str]:
    """候補名から最初に見つかった日付列名を返す。なければNone。

    - 候補は順序を尊重
    - 大文字小文字のゆらぎにも対応
    """
    try:
        cols = list(df.columns)
    except Exception:
        return None

    for c in candidates:
        if c in cols:
            return c

    lower_map = {str(c).lower(): c for c in cols}
    for c in candidates:
        lc = str(c).lower()
        if lc in lower_map:
            return lower_map[lc]
    return None


def filter_by_period_from_min_date(
    dfs: Dict[str, Any],
    period_type: str,
    date_candidates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    各CSVの最小日付を起点に、指定期間で各DataFrameをフィルタ。

    Args:
        dfs: CSV名 -> DataFrame の辞書
        period_type: "oneday" | "oneweek" | "onemonth" | "all" | "none"
        date_candidates: 日付列名の候補（未指定時は DEFAULT_DATE_CANDIDATES）

    Returns:
        フィルタ済みの DataFrame 辞書
    """
    if not date_candidates:
        date_candidates = DEFAULT_DATE_CANDIDATES

    # 事前に曜日括弧を除去
    for name, df in dfs.items():
        if not hasattr(df, "columns"):
            continue
        for col in date_candidates:
            if col in getattr(df, "columns", []):
                try:
                    dfs[name] = remove_weekday_parentheses(df, col)
                    print(f"[DEBUG] remove_weekday_parentheses applied to {name}.{col}")
                except Exception as ex:
                    print(
                        f"[WARN] remove_weekday_parentheses failed for {name}.{col}: {ex}"
                    )

    # 最小日付の決定
    min_date = None
    for name, df in dfs.items():
        if not hasattr(df, "__dataframe__") and not hasattr(df, "columns"):
            continue
        col = find_date_column(df, date_candidates)
        if not col:
            continue
        sr = pd.to_datetime(df[col], errors="coerce")
        local_min = sr.min()
        if pd.isna(local_min):
            continue
        min_date = local_min if min_date is None else min(min_date, local_min)

    if min_date is None:
        print("[INFO] No date column found across CSVs. Skipping date filtering.")
        return dfs

    min_date = pd.to_datetime(min_date).normalize()

    # 期間終端
    p = (period_type or "all").lower()
    if p in ("all", "none"):
        return dfs
    elif p == "oneday":
        end_date = min_date
    elif p == "oneweek":
        end_date = min_date + pd.Timedelta(days=6)
    elif p == "onemonth":
        end_date = (min_date + pd.DateOffset(months=1)) - pd.Timedelta(days=1)
    else:
        raise ValueError(f"Unknown period_type: {period_type}")

    filtered: Dict[str, Any] = {}
    for name, df in dfs.items():
        if not hasattr(df, "columns"):
            filtered[name] = df
            continue
        col = find_date_column(df, date_candidates)
        if not col:
            filtered[name] = df
            continue
        sr = pd.to_datetime(df[col], errors="coerce").dt.normalize()
        mask = (sr >= min_date) & (sr <= end_date)
        try:
            filtered_df = df.loc[mask].copy()
        except Exception:
            filtered_df = df
        filtered[name] = filtered_df

    print(
        f"[INFO] Date filter applied from {min_date.date()} to {end_date.date()} (period={p})"
    )
    return filtered
