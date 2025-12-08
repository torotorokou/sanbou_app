"""
multiply_optimized.py

multiply_columns の最適化版。
既に型変換済みのDataFrameを前提とし、不要なcopy()を削減する。

従来版（multiply.py）との違い:
- copy()を削除（呼び出し元で管理）
- clean_na_stringsとto_numericをスキップ（前処理済みを前提）
- 純粋な掛け算のみ実行

使用条件:
- 入力DataFrameが既に数値型に変換済みであること
- 入力DataFrameが書き換え可能なコピーであること
"""
import pandas as pd
from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


def multiply_columns_optimized(
    df: pd.DataFrame, 
    col1: str, 
    col2: str, 
    result_col: str = "値",
    skip_type_conversion: bool = False
) -> pd.DataFrame:
    """
    指定された2列を掛け算して新しい列に保存する最適化版関数。
    
    Parameters
    ----------
    df : pd.DataFrame
        対象のDataFrame（既にcopy()済みで書き換え可能）
    col1 : str
        掛け算する1つ目の列名
    col2 : str
        掛け算する2つ目の列名
    result_col : str, default "値"
        計算結果を格納する列名
    skip_type_conversion : bool, default False
        Trueの場合、型変換をスキップ（既に数値型の場合）
    
    Returns
    -------
    pd.DataFrame
        掛け算列を追加したDataFrame（入力と同じオブジェクト）
    
    Notes
    -----
    - 従来のmultiply_columnsと異なり、copy()を実行しない
    - skip_type_conversion=Trueの場合、clean_na_stringsとto_numericもスキップ
    - パフォーマンス重視の設計
    """
    if not skip_type_conversion:
        # 従来と同じ型変換処理（互換性のため残す）
        from backend_shared.utils.dataframe_utils import clean_na_strings
        
        df[col1] = df[col1].apply(clean_na_strings)
        df[col2] = df[col2].apply(clean_na_strings)
        df[col1] = pd.to_numeric(df[col1], errors="coerce")
        df[col2] = pd.to_numeric(df[col2], errors="coerce")
    
    # 掛け算実行（inplace更新）
    df[result_col] = df[col1] * df[col2]
    
    return df
