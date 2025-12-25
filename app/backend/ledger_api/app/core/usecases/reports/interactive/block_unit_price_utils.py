"""
Block Unit Price Interactive - Utility Functions
共通ユーティリティ関数とデータクラス
"""

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype as _is_dt

from backend_shared.application.logging import create_log_context, get_module_logger


logger = get_module_logger(__name__)


# ------------------------------ dataclasses ------------------------------


@dataclass
class TransportOption:
    """運搬オプション"""

    vendor_code: str
    vendor_name: str
    transport_fee: float


@dataclass
class InteractiveProcessState:
    """インタラクティブ処理の状態"""

    step: int
    df_shipment: pd.DataFrame | None = None
    transport_options: list[TransportOption] | None = None
    selected_vendors: dict[str, str] | None = None
    master_csv: pd.DataFrame | None = None
    df_transport_cost: pd.DataFrame | None = None
    session_id: str | None = None


# ------------------------------ Session Management ------------------------------


def make_session_id() -> str:
    """セッションIDを生成"""
    return f"bup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"


def stable_entry_id(row: pd.Series, fallback_key: str, row_index: int = 0) -> str:
    """行の安定したエントリIDを生成

    Args:
        row: データ行
        fallback_key: フォールバックキー
        row_index: 行インデックス（一意性を保証するため）
    """
    parts = [
        str(row.get("業者CD", "")),
        str(row.get("品名", "")),
        str(row.get("明細備考", "")),
        str(row.get("伝票番号", "")),
        str(row.get("行番号", "")),
        str(row_index),  # インデックスを追加して一意性を保証
    ]
    base = "|".join(parts).strip("|") or fallback_key
    h = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    return f"bup_{h}"


# ------------------------------ Data Formatting ------------------------------


def clean_vendor_name(name: Any) -> str:
    """業者名をクリーンアップ"""
    s = str(name or "")
    return re.sub(r"（\s*\d+\s*）", "", s)


def safe_int(v: Any) -> int | Any:
    """安全に整数に変換"""
    try:
        if isinstance(v, float) and float(v).is_integer():
            return int(v)
        return int(v)
    except Exception:
        return v


def normalize_df_index(idx: Any) -> int | str:
    """DataFrameのインデックスを正規化"""
    if isinstance(idx, (int,)):
        return int(idx)
    if isinstance(idx, float) and float(idx).is_integer():
        return int(idx)
    return str(idx)


# ------------------------------ Sorting & Ordering ------------------------------

_CARRIER_ORDER = {"オネスト": 0, "シェノンビ": 1, "エコライン": 2}
_VEHICLE_ORDER = {"ウイング": 0, "コンテナ": 1, None: 2}


def parse_label(lbl: str) -> tuple[int, int, int, str]:
    """ラベルを解析してソート用のタプルを返す"""
    s = lbl or ""
    if s.startswith("オネスト"):
        c = "オネスト"
    elif s.startswith("シェノンビ"):
        c = "シェノンビ"
    elif "エコライン" in s:
        c = "エコライン"
    else:
        c = "zzz"
    c_ord = _CARRIER_ORDER.get(c, 99)

    if "ウイング" in s:
        v_ord = _VEHICLE_ORDER["ウイング"]
    elif "コンテナ" in s:
        v_ord = _VEHICLE_ORDER["コンテナ"]
    else:
        v_ord = _VEHICLE_ORDER[None]

    shared_flag = 1 if "合積" in s else 0
    return (c_ord, v_ord, shared_flag, s)


def canonical_sort_labels(labels: list[str]) -> list[str]:
    """ラベルを正規化してソート"""
    uniq = {str(x).strip() for x in labels if isinstance(x, str) and str(x).strip()}
    return sorted(uniq, key=parse_label)


# ------------------------------ Date Handling ------------------------------


def ensure_datetime_col(df: pd.DataFrame | None, col: str = "伝票日付") -> pd.DataFrame | None:
    """指定列をdatetimeに変換"""
    if df is None or col not in df.columns:
        return df

    s = df[col]
    try:
        if _is_dt(s):
            return df

        if pd.api.types.is_integer_dtype(s) or pd.api.types.is_float_dtype(s):
            ser = pd.to_numeric(s, errors="coerce")
            valid = ser.dropna()
            if len(valid) == 0:
                df[col] = pd.to_datetime(ser, errors="coerce")
                return df

            max_abs = float(valid.abs().max())
            if max_abs > 1e17:
                unit = "ns"
            elif max_abs > 1e14:
                unit = "us"
            elif max_abs > 1e11:
                unit = "ms"
            else:
                unit = "s"

            logger.debug(
                "epoch形式検出",
                extra=create_log_context(
                    operation="normalize_datetime_columns", column=col, unit=unit
                ),
            )
            df[col] = pd.to_datetime(ser, unit=unit, errors="coerce")
            return df

        df[col] = pd.to_datetime(s, errors="coerce")
        return df
    except Exception as e:
        logger.warning(
            "日付正規化失敗",
            extra=create_log_context(
                operation="normalize_datetime_columns",
                column=col,
                error_type=type(e).__name__,
                error=str(e),
            ),
        )
        return df


# ------------------------------ Error Handling ------------------------------


def error_payload(
    code: str, detail: str, step: int, extra: dict[str, Any] | None = None
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """統一フォーマットでエラーペイロードを返す"""
    payload: dict[str, Any] = {
        "status": "error",
        "code": code,
        "detail": detail,
        "step": step,
    }
    if extra:
        payload.update({"extra": extra})
    # 第1戻り値はダミー（DFを期待する共通I/Fのため）
    return pd.DataFrame(), payload


def missing_cols(df: pd.DataFrame, required: list[str]) -> list[str]:
    """必須カラムの不足をチェック"""
    return [c for c in required if c not in df.columns]


def handle_step_error(
    step_name: str,
    step_number: int,
    error: Exception,
    context: dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """ステップエラーを統一的に処理

    Args:
        step_name: ステップ名（例: "initial", "finalize"）
        step_number: ステップ番号
        error: 発生した例外
        context: 追加コンテキスト情報

    Returns:
        エラーペイロード
    """
    import traceback

    tb = traceback.format_exc(limit=5)
    error_type = type(error).__name__
    error_msg = str(error)

    extra_data: dict[str, Any] = {
        "err_type": error_type,
        "err": error_msg,
        "traceback": tb,
    }

    if context:
        extra_data.update(context)

    logger.error(
        f"{step_name} step error",
        extra=create_log_context(
            operation=f"block_unit_price_{step_name}",
            step=step_number,
            error_type=error_type,
            error_msg=error_msg,
            **extra_data,
        ),
    )

    return error_payload(
        code=f"STEP{step_number}_EXCEPTION",
        detail=error_msg,
        step=step_number,
        extra=extra_data,
    )


# ------------------------------ Debug Helpers ------------------------------


def fmt_cols(df: pd.DataFrame | None) -> str:
    """DataFrameのカラム情報をフォーマット"""
    if df is None:
        return "None"
    try:
        return f"shape={df.shape}, cols={list(df.columns)}"
    except Exception as e:
        return f"<fmt_cols_error:{e}>"


def fmt_head_rows(df: pd.DataFrame | None, n: int = 3) -> str:
    """DataFrameの先頭行をフォーマット"""
    if df is None:
        return "None"
    try:
        return df.head(n).to_dict(orient="list").__repr__()
    except Exception as e:
        return f"<fmt_head_error:{e}>"


def series_sample(df: pd.DataFrame | None, col: str, k: int = 5) -> list[Any]:
    """カラムのサンプル値を取得"""
    try:
        if df is None or col not in df.columns:
            return []
        return list(df[col].dropna().astype(str).unique()[:k])
    except Exception:
        return []


def log_checkpoint(tag: str, df_a: pd.DataFrame | None, df_b: pd.DataFrame | None = None) -> None:
    """チェックポイントログを出力"""
    msg = f"DBG checkpoint[{tag}] A({fmt_cols(df_a)})"
    if df_b is not None:
        msg += f" | B({fmt_cols(df_b)})"
    try:
        if df_a is not None:
            msg += f" | A.has_運搬費={ '運搬費' in df_a.columns }"
            if "運搬費" in df_a.columns:
                msg += f" | A.運搬費.notna={int(df_a['運搬費'].notna().sum())}"
        if df_b is not None and hasattr(df_b, "columns"):
            msg += f" | B.has_運搬費={ '運搬費' in df_b.columns }"
    except Exception:
        pass
    logger.debug(msg)
