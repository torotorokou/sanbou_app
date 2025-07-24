import pandas as pd
from .type_parser_map import type_formatting_map, type_parser_map


# CSVフォーマットの型変換を行うユーティリティ
def apply_column_formatting(
    df: pd.DataFrame, columns_def: dict[str, dict]
) -> pd.DataFrame:
    """
    YAML定義に基づき、DataFrameの各列に型変換処理を適用する。
    """

    for ja_col, props in columns_def.items():
        typ = props.get("type")
        func = type_formatting_map.get(typ)

        if not func:
            print(f"[WARN] 未対応の型: {typ}")
            continue

        if ja_col not in df.columns:
            print(f"[WARN] カラム '{ja_col}' が存在しません。スキップされます。")
            continue

        try:
            df = func(df, ja_col)
        except Exception as e:
            print(f"[ERROR] カラム '{ja_col}' の型変換中にエラー発生: {e}")
    return df


def apply_column_type_parsing(
    df: pd.DataFrame, columns_def: dict[str, dict]
) -> pd.DataFrame:
    """
    YAML定義に基づき、DataFrameの各列に型変換（pandasのdtype変換）を適用する。
    整形（空白・カンマ除去など）は別処理に委譲する。
    """
    for ja_col, props in columns_def.items():
        typ = props.get("type")
        if typ is None:
            continue

        func = type_parser_map.get(typ)
        if not func:
            print(f"[WARN] 未対応の型: {typ}")
            continue

        if ja_col not in df.columns:
            print(f"[WARN] カラム '{ja_col}' が存在しません。スキップされます。")
            continue

        try:
            df = func(df, ja_col)  # 明示的に型変換
        except Exception as e:
            print(f"[ERROR] カラム '{ja_col}' の型変換中にエラー発生: {e}")
    return df
