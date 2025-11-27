"""
業者コード・取引先コードの正規化ユーティリティ

CSV から読み込んだコードの先頭ゼロを削除し、統一フォーマットに変換する。
"""
from typing import Optional, List
import pandas as pd


def normalize_client_code(value) -> Optional[str]:
    """
    取引先コード(client_cd)を正規化
    
    Args:
        value: コード値 (str, int, float, None)
        
    Returns:
        正規化されたコード文字列 or None
        
    Examples:
        >>> normalize_client_code('000244')
        '244'
        >>> normalize_client_code('000003')
        '3'
        >>> normalize_client_code('0000')
        '0'
        >>> normalize_client_code('123')
        '123'
        >>> normalize_client_code('')
        None
        >>> normalize_client_code(None)
        None
        >>> normalize_client_code(244)
        '244'
    """
    # NaN または空文字は None
    if pd.isna(value) or value == '':
        return None
    
    # 文字列に変換して前後の空白削除
    code_str = str(value).strip()
    
    if not code_str:
        return None
    
    # 全部0の場合は '0' を返す
    if code_str.replace('0', '') == '':
        return '0'
    
    # 先頭の0を削除
    return code_str.lstrip('0')


def normalize_dataframe_client_codes(
    df: pd.DataFrame, 
    column: str = '取引先CD'
) -> pd.DataFrame:
    """
    DataFrameの取引先CDカラムを一括正規化
    
    Args:
        df: 対象DataFrame
        column: 正規化するカラム名（デフォルト: '取引先CD'）
        
    Returns:
        正規化済みのDataFrame（コピー）
    """
    df = df.copy()
    if column in df.columns:
        df[column] = df[column].apply(normalize_client_code)
    return df
