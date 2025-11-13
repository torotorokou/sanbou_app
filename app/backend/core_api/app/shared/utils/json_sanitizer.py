"""
JSON互換性を保証するためのサニタイザ

pandas.Timestamp、numpy型、datetime型など、JSON直列化で失敗する型を
再帰的にJSON互換な型に変換する最後の砦。

Usage:
    from app.shared.utils.json_sanitizer import deep_jsonable
    
    payload = row.to_dict()
    payload = deep_jsonable(payload)  # 最終バリア
    orm_object = Model(**payload)
"""
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Any


def _to_jsonable(v: Any) -> Any:
    """単一の値をJSON互換な型に変換"""
    # 最優先: NaN/NaT の検出（pd.Timestamp('NaT') もこれでキャッチ）
    if pd.isna(v):  # pd.NA, np.nan, pd.NaT など
        return None
    if isinstance(v, pd.Timestamp):
        # NaT は上でキャッチされるが、念のため
        return v.to_pydatetime().isoformat()
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return None if np.isnan(v) else float(v)
    # datetime, date, time をそのまま返す（SQL 保存用）
    if isinstance(v, (datetime, date, time)):
        return v
    return v


def deep_jsonable(obj: Any) -> Any:
    """
    オブジェクトを再帰的にJSON互換に変換
    
    dict, list, tuple を再帰的に走査し、すべての値を
    JSON直列化可能な型に変換する。
    
    Args:
        obj: 変換対象のオブジェクト
        
    Returns:
        JSON互換に変換されたオブジェクト
    """
    if isinstance(obj, dict):
        return {k: deep_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [deep_jsonable(x) for x in obj]
    return _to_jsonable(obj)
