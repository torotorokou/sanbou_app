import pandas as pd

from backend_shared.utils.dataframe_utils_optimized import clean_na_strings_vectorized
from app.infra.report_utils.formatters import set_value_fast_safe
from app.infra.report_utils.formatters import (
    to_japanese_era,
    to_japanese_month_day,
)


def generate_summary_dataframe(df: pd.DataFrame, master_csv_etc: pd.DataFrame = None) -> pd.DataFrame:
    """
    合計行を追加する。
    
    Args:
        df: 処理対象のDataFrame
        master_csv_etc: etc合計行マスターCSV（事前読み込み済み）。Noneの場合は合計行なしでそのまま返す。
    
    Returns:
        pd.DataFrame: 合計行追加済みのDataFrame
    
    Notes:
        - Step 5最適化: master_csv_etcを引数で受け取ることでI/O削減
    """
    if master_csv_etc is None or master_csv_etc.empty:
        # etc テンプレートが無い場合は加算行なしでそのまま返す
        print(
            "[WARN] etcマスターCSVが提供されていません。合計行の追加をスキップします。"
        )
        return df.copy()
    
    etc_csv = master_csv_etc

    df_sum = df.copy()

    # 値列を数値に変換（NaN対応）
    # 最適化: clean_na_strings_vectorizedを使用（10-100倍高速化）
    df_sum["値"] = clean_na_strings_vectorized(df_sum["値"])
    df_sum["値"] = pd.to_numeric(df_sum["値"], errors="coerce").fillna(0)

    # カテゴリ別の合計
    category_sum = df_sum.groupby("カテゴリ")["値"].sum()

    # 総合計
    total_sum = df_sum["値"].sum()

    # 最適化: apply(axis=1)をベクトル化（条件マスクで直接代入）
    # デフォルトは既存の値を保持
    etc_csv["値"] = etc_csv["値"].copy()
    
    # 各条件に対してマスクを作成して値を代入
    mask_yard = etc_csv["大項目"].str.contains("ヤード", na=False) & ~etc_csv["大項目"].str.contains("処分", na=False)
    mask_shobun = etc_csv["大項目"].str.contains("処分", na=False) & ~etc_csv["大項目"].str.contains("ヤード", na=False)
    mask_yuuka = etc_csv["大項目"].str.contains("有価", na=False)
    mask_total = etc_csv["大項目"].str.contains("総合計", na=False)
    
    etc_csv.loc[mask_yard, "値"] = category_sum.get("ヤード", 0.0)
    etc_csv.loc[mask_shobun, "値"] = category_sum.get("処分", 0.0)
    etc_csv.loc[mask_yuuka, "値"] = category_sum.get("有価", 0.0)
    etc_csv.loc[mask_total, "値"] = total_sum

    # 合計_処分ヤード = 処分 + ヤード
    mask_shobun_yard = etc_csv["大項目"] == "合計_処分ヤード"
    val_shobun = etc_csv.loc[etc_csv["大項目"] == "合計_処分", "値"].values
    val_yard = etc_csv.loc[etc_csv["大項目"] == "合計_ヤード", "値"].values

    if len(val_shobun) > 0 and len(val_yard) > 0:
        etc_csv.loc[mask_shobun_yard, "値"] = val_shobun[0] + val_yard[0]

    df_combined = pd.concat([df, etc_csv], ignore_index=True)

    return df_combined


def upsert_summary_row(
    df: pd.DataFrame,
    label: str,
    value: float,
    value_col: str = "値",
    label_col: str = "大項目",
) -> pd.DataFrame:
    mask = df[label_col] == label

    if mask.any():
        df.loc[mask, value_col] = value
    else:
        new_row = {
            label_col: label,
            value_col: value,
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df


def date_format(master_csv, df_shipment):
    try:
        if df_shipment is None or df_shipment.empty or "伝票日付" not in df_shipment.columns:
            raise ValueError("shipment日付が取得できません")
        today = pd.to_datetime(df_shipment["伝票日付"].dropna().iloc[0])
    except Exception:
        today = pd.Timestamp.today().normalize()

    match_columns = ["大項目"]
    match_value = ["和暦"]
    master_csv = set_value_fast_safe(
        master_csv, match_columns, match_value, to_japanese_era(today)
    )

    match_columns = ["大項目"]
    match_value = ["月日"]
    master_csv = set_value_fast_safe(
        master_csv, match_columns, match_value, to_japanese_month_day(today)
    )

    return master_csv
