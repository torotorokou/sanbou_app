"""
Backend Shared DataFrame Normalizer for SQL Database Insertion

DataFrame を SQL データベースに挿入可能な形式に正規化するユーティリティ。
全バックエンドサービスで共通利用でき、SQL保存時の型安全性を保証します。

主な機能:
- pandas nullable Int64 → Python int/None への変換
- datetime64[ns] → Python date への変換  
- object 列内の pd.Timestamp / numpy scalar の安全化
- object 列内の datetime → date or time への変換（列名で判断）
- JSON シリアライズ可能な型への統一

使用例:
    from backend_shared.infra.dataframe import to_sql_ready_df, filter_defined_columns
    
    normalized_df = to_sql_ready_df(raw_df)
    filtered_df = filter_defined_columns(normalized_df, ["id", "name", "created_at"])
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, time
from typing import Any
from backend_shared.infra.json_utils import deep_jsonable

logger = logging.getLogger(__name__)


def to_sql_ready_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame を SQL 保存可能な型に正規化
    
    以下の変換を行います:
    1. NaN/NaT → None への統一変換（最優先）
    2. pandas nullable Int64 → Python int/None (欠損値は None)
    3. datetime64[ns] → Python datetime オブジェクト（NaT は None に）
    4. object 列内の pd.Timestamp / numpy scalar を安全な型に変換
    
    Args:
        df: 正規化するDataFrame
        
    Returns:
        正規化されたDataFrame（コピー）
        
    Raises:
        なし（エラーは WARNING ログで記録）
    """
    df = df.copy()
    
    # 0) 全体を None で置き換え（NaN/NaT を確実に消す）
    df = df.where(pd.notnull(df), None)
    
    # 1) pandas nullable Int64 → Python int/None
    int64_cols = []
    for c in df.columns:
        if str(df[c].dtype) == "Int64":
            int64_cols.append(c)
            # Int64 → object に変換してから欠損を None に
            s = df[c].astype("object")
            s = s.where(s.notna(), None)
            df[c] = s
    
    if int64_cols:
        logger.debug(f"Converted Int64 → object(int|None): {int64_cols}")
    
    # 2) datetime64[ns] → Python datetime/date/time（列名で判断）
    datetime_to_datetime_cols = []  # time列はdatetimeのまま保持
    datetime_to_date_cols = []
    
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            # タイムゾーンをローカライズ（念のため）
            df[c] = df[c].dt.tz_localize(None)
            
            # 列名に "time" が含まれる場合は datetime として保持（後で time に変換）
            if "time" in c.lower():
                datetime_to_datetime_cols.append(c)
                # Python datetime に変換、NaT は None に
                def safe_to_datetime(x):
                    if pd.isna(x):
                        return None
                    try:
                        return x.to_pydatetime()
                    except (AttributeError, ValueError):
                        return None
                df[c] = df[c].map(safe_to_datetime)
            else:
                datetime_to_date_cols.append(c)
                # Python date に変換（時刻を切り捨て）
                df[c] = df[c].dt.date
                # NaT を None に置き換え
                df[c] = df[c].map(lambda x: None if pd.isna(x) else x)
            
            # Series[object] にしておく（FutureWarning 回避）
            df[c] = df[c].astype(object)
    
    if datetime_to_datetime_cols:
        logger.debug(f"Kept datetime64[ns] → datetime: {datetime_to_datetime_cols}")
    if datetime_to_date_cols:
        logger.debug(f"Converted datetime64[ns] → date: {datetime_to_date_cols}")
    
    # 3) object 列の中身を正規化
    # - datetime → time (列名に "time" が含まれる場合)
    # - Timestamp / numpy scalar → JSON互換型
    object_cols = []
    time_cols = []
    
    for c in df.columns:
        if df[c].dtype == "object":
            object_cols.append(c)
            
            # 列名に "time" が含まれる場合は datetime → time
            if "time" in c.lower():
                time_cols.append(c)
                def safe_to_time(x):
                    if x is None or pd.isna(x):
                        return None
                    if isinstance(x, datetime):
                        return x.time()
                    return x
                df[c] = df[c].map(safe_to_time)
            
            # 最後に deep_jsonable で安全化
            df[c] = df[c].map(deep_jsonable)
    
    if time_cols:
        logger.debug(f"Converted datetime → time: {time_cols}")
    if object_cols:
        logger.debug(f"Normalized object columns: {len(object_cols)} columns")
    
    return df


def filter_defined_columns(
    df: pd.DataFrame, 
    defined_cols: list[str],
    log_dropped: bool = True
) -> pd.DataFrame:
    """
    YAML スキーマに定義されたカラムのみを抽出
    
    定義外のカラムは除去し、WARNING ログを出力します。
    
    Args:
        df: フィルタ対象のDataFrame
        defined_cols: 許可されたカラム名のリスト
        log_dropped: 除去したカラムをログ出力するか（デフォルト: True）
        
    Returns:
        フィルタ済みDataFrame
        
    使用例:
        >>> df = pd.DataFrame({"id": [1, 2], "name": ["A", "B"], "extra": ["X", "Y"]})
        >>> filter_defined_columns(df, ["id", "name"])
        # WARNING: Dropping undefined columns: ['extra']
        # Returns: DataFrame with only "id" and "name"
    """
    defined = set(defined_cols)
    dropping = sorted([c for c in df.columns if c not in defined])
    
    if dropping and log_dropped:
        logger.warning(f"Dropping undefined columns: {dropping}")
    
    # 定義されたカラムのみを保持（順序は元のDataFrameに従う）
    return df[[c for c in df.columns if c in defined]]
