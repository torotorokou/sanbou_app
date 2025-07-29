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


def dedupe_and_aggregate(
    df: pd.DataFrame, unique_keys: list, agg_map: dict
) -> pd.DataFrame:
    """
    unique_keys: 集約のキー
    agg_map: {カラム名: 'sum'|'first'|'mean' など}
    全行にグループIDを付与して一発でagg処理。unique_keysで重複がなければ元dfそのまま返す。
    """
    if not unique_keys or not agg_map:
        return df

    df = df.copy()
    # グループIDを全行に付与
    df["_dup_group_id"] = pd.factorize(
        df[unique_keys].astype(str).agg("-".join, axis=1)
    )[0]

    # _dup_group_id が重複している行だけ抽出
    is_duplicated = df["_dup_group_id"].duplicated(keep=False)
    df_dup = df[is_duplicated]

    # _dup_group_idで集約
    grouped = df.groupby("_dup_group_id", dropna=False)

    # 集約してリセット
    df_agg = grouped.agg(agg_map).reset_index(drop=True)

    # _dup_group_id を削除して返す
    return df_agg.drop(columns="_dup_group_id", errors="ignore")
