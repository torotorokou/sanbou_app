import pandas as pd

from app.infra.report_utils import get_template_config
from app.infra.report_utils import load_master_and_template
from app.infra.report_utils import clean_na_strings
from app.infra.report_utils.formatters import set_value_fast_safe
from app.infra.report_utils.formatters import (
    to_japanese_era,
    to_japanese_month_day,
)


def generate_summary_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    config = get_template_config()["factory_report"]
    etc_path = config["master_csv_path"].get("etc")
    try:
        etc_csv = load_master_and_template(etc_path)
    except Exception as e:
        # etc テンプレートが無い場合は加算行なしでそのまま返す
        print(
            f"[WARN] etcマスターCSVの読み込みに失敗: {etc_path} reason={e}. 合計行の追加をスキップします。"
        )
        return df.copy()

    df_sum = df.copy()

    # 値列を数値に変換（NaN対応）
    df_sum["値"] = df_sum["値"].apply(clean_na_strings)
    df_sum["値"] = pd.to_numeric(df_sum["値"], errors="coerce").fillna(0)

    # カテゴリ別の合計
    category_sum = df_sum.groupby("カテゴリ")["値"].sum()

    # 総合計
    total_sum = df_sum["値"].sum()

    def assign_sum(row):
        if "ヤード" in row["大項目"] and "処分" not in row["大項目"]:
            return category_sum.get("ヤード", 0.0)
        elif "処分" in row["大項目"] and "ヤード" not in row["大項目"]:
            return category_sum.get("処分", 0.0)
        elif "有価" in row["大項目"]:
            return category_sum.get("有価", 0.0)
        elif "総合計" in row["大項目"]:
            return total_sum
        return row["値"]

    etc_csv["値"] = etc_csv.apply(assign_sum, axis=1)

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
