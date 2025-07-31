import pandas as pd
from typing import Optional
from app.api.services.manage_report_processors.factory_report.utils.config_loader import (
    get_template_config,
)
from app.api.services.manage_report_processors.factory_report.utils.load_template import (
    load_master_and_template,
)


def generate_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    集計データフレームを生成する

    Parameters:
        df (pd.DataFrame): 処理対象のデータフレーム

    Returns:
        pd.DataFrame: 集計済みのデータフレーム
    """
    try:
        config = get_template_config()["factory_report"]
        etc_path = config["master_csv_path"]["etc"]
        etc_csv = load_master_and_template(etc_path)
    except Exception as e:
        print(f"警告: etc設定の読み込みに失敗しました: {e}")
        return df

    # 1. コピーして元dfを保護
    df_sum = df.copy()

    # 2. 値列を数値に変換（NaN対応）
    if "値" in df_sum.columns:
        df_sum["値"] = pd.to_numeric(df_sum["値"], errors="coerce").fillna(0)

    # 3. カテゴリ別の合計（カテゴリ列が存在する場合のみ）
    category_sum = {}
    if "カテゴリ" in df_sum.columns:
        category_sum = df_sum.groupby("カテゴリ")["値"].sum()

    # 4. 総合計
    total_sum = df_sum["値"].sum()

    # 5. テンプレに合計をマージ
    def assign_sum(row):
        if "大項目" not in row:
            return row.get("値", 0)

        large_item = str(row["大項目"])
        if "ヤード" in large_item and "処分" not in large_item:
            return category_sum.get("ヤード", 0.0)
        elif "処分" in large_item and "ヤード" not in large_item:
            return category_sum.get("処分", 0.0)
        elif "有価" in large_item:
            return category_sum.get("有価", 0.0)
        elif "総合計" in large_item:
            return total_sum
        return row.get("値", 0)

    if "大項目" in etc_csv.columns:
        etc_csv["値"] = etc_csv.apply(assign_sum, axis=1)

        # 6. 合計_処分ヤード = 処分 + ヤード の合算
        mask_shobun_yard = etc_csv["大項目"] == "合計_処分ヤード"
        val_shobun = etc_csv.loc[etc_csv["大項目"] == "合計_処分", "値"].values
        val_yard = etc_csv.loc[etc_csv["大項目"] == "合計_ヤード", "値"].values

        if val_shobun.size > 0 and val_yard.size > 0:
            etc_csv.loc[mask_shobun_yard, "値"] = val_shobun[0] + val_yard[0]

    # 7. 元dfとetcの結合（縦方向）
    df_combined = pd.concat([df, etc_csv], ignore_index=True)

    return df_combined


def upsert_summary_row(
    df: pd.DataFrame,
    label: str,
    value: float,
    value_col: str = "値",
    label_col: str = "大項目",
) -> pd.DataFrame:
    """
    指定ラベルの行が存在すれば値を更新し、存在しなければセル列は空のまま新規行として追加する。

    Parameters:
        df (pd.DataFrame): 対象データフレーム
        label (str): "大項目" のラベル名（例："総合計" など）
        value (float): 書き込む値
        value_col (str): 値の列名
        label_col (str): ラベルの列名

    Returns:
        pd.DataFrame: 更新済みのDataFrame
    """
    df = df.copy()

    if label_col not in df.columns:
        return df

    mask = df[label_col] == label

    if mask.any():
        # 既存行があるなら値だけ更新
        df.loc[mask, value_col] = value
    else:
        # セル列には何も書かず追加（補完は別途）
        new_row = {col: "" for col in df.columns}
        new_row[label_col] = label
        new_row[value_col] = value
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    return df


def date_format(master_csv: pd.DataFrame, df_shipment: pd.DataFrame) -> pd.DataFrame:
    """
    日付フォーマットを適用する

    Parameters:
        master_csv (pd.DataFrame): マスターCSV
        df_shipment (pd.DataFrame): 出荷データ

    Returns:
        pd.DataFrame: 日付フォーマット適用済みのマスターCSV
    """
    master_csv = master_csv.copy()

    if "伝票日付" not in df_shipment.columns or df_shipment["伝票日付"].dropna().empty:
        return master_csv

    try:
        today = pd.to_datetime(df_shipment["伝票日付"].dropna().iloc[0])

        # 和暦設定（簡易版）
        if "大項目" in master_csv.columns:
            mask_wareki = master_csv["大項目"] == "和暦"
            if mask_wareki.any():
                # 簡易的な和暦変換（実際の変換ロジックは必要に応じて実装）
                wareki_str = f"令和{today.year - 2018}年{today.month}月{today.day}日"
                master_csv.loc[mask_wareki, "値"] = wareki_str

            # 月日設定
            mask_monthday = master_csv["大項目"] == "月日"
            if mask_monthday.any():
                monthday_str = f"{today.month}月{today.day}日"
                master_csv.loc[mask_monthday, "値"] = monthday_str

    except Exception as e:
        print(f"警告: 日付フォーマットの適用に失敗しました: {e}")

    return master_csv
