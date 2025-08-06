import pandas as pd
from backend_shared.src.csv_formatter.type_parser_map import (
    type_formatting_map,
    type_parser_map,
)


def apply_column_cleaning(
    df: pd.DataFrame, columns_def: dict[str, dict]
) -> pd.DataFrame:
    """
    各列に対して「値そのものの整形」を行う処理（型変換前の前処理）。

    【用途】
    - カンマや空白・記号を除去したり、全角→半角変換、不要文字除去、金額のカンマ除去など
    - 例えば ' 1,000 ' → '1000' のような「値のクリーンアップ」
    - 型変換（int/float等）を安全に行うための準備

    【引数】
    df : pd.DataFrame
        変換対象のDataFrame
    columns_def : dict[str, dict]
        カラム名ごとの型情報・定義

    【戻り値】
    pd.DataFrame : 整形済みDataFrame
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
            # 例：金額カラムならカンマ除去やstrip、日付なら文字列整形など
            df = func(df, ja_col)
        except Exception as e:
            print(f"[ERROR] カラム '{ja_col}' の値整形中にエラー発生: {e}")
            print(f"[DEBUG] サンプルデータ: {df[ja_col].head()}")
            # エラーが発生してもスキップして処理を続行
    return df


def apply_column_type_parsing(
    df: pd.DataFrame, columns_def: dict[str, dict]
) -> pd.DataFrame:
    """
    各列に対して「pandasのデータ型変換（dtype変換）」を適用する処理（本番の型変換）。

    【用途】
    - 文字列やfloatを「int型」「float型」「datetime型」などにpandasとして明示的に変換
    - 例えば '1000' → 1000（int型）や '2023-01-01' → datetime型 など
    - 整形前に空白やカンマ除去（apply_column_formatting）を済ませておく前提

    【引数】
    df : pd.DataFrame
        変換対象のDataFrame
    columns_def : dict[str, dict]
        カラム名ごとの型情報・定義

    【戻り値】
    pd.DataFrame : 型変換済みDataFrame

    【注意】
    - ここで空欄（NaN）をそのままint型にしようとするとエラーになるため、事前にfillna(0)等で埋める実装が必要
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
            # 例：int型変換やdatetime型変換など
            df = func(df, ja_col)  # 明示的に型変換
        except Exception as e:
            print(f"[ERROR] カラム '{ja_col}' の型変換中にエラー発生: {e}")
            print(f"[DEBUG] サンプルデータ: {df[ja_col].head()}")
            print(f"[DEBUG] データ型: {df[ja_col].dtype}")
            # エラーが発生してもスキップして処理を続行
    return df


def dedupe_and_aggregate(
    df: pd.DataFrame, unique_keys: list, agg_map: dict
) -> pd.DataFrame:
    """
    unique_keys でグループ化し、agg_map で指定した方法（sum, mean, first など）で集計し重複を解消する。

    【用途】
    - 伝票番号や日付、業者コードなどの「一意キー」で重複しているデータを集計・統合する
    - 例えば同じ伝票日付・業者の行を合計値や平均値で1行にまとめる

    【引数】
    df : pd.DataFrame
        対象のDataFrame
    unique_keys : list
        集約・重複解消のためのカラム名リスト
    agg_map : dict
        集計方法の辞書（{カラム名: 'sum'|'mean'|'first' など}）

    【戻り値】
    pd.DataFrame : 重複解消＆集計後のDataFrame
    """
    if not unique_keys or not agg_map:
        return df

    df = df.copy()
    # グループIDを全行に付与
    df["_dup_group_id"] = pd.factorize(
        df[unique_keys].astype(str).agg("-".join, axis=1)
    )[0]

    # _dup_group_idで集約
    grouped = df.groupby("_dup_group_id", dropna=False)

    # 集約してリセット
    df_agg = grouped.agg(agg_map).reset_index(drop=True)

    # _dup_group_id を削除して返す
    return df_agg.drop(columns="_dup_group_id", errors="ignore")
