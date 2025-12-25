import pandas as pd

from app.infra.report_utils.formatters import (
    get_weekday_japanese,
    round_value_column_generic,
    set_value_fast_safe,
)
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.utils.dataframe_utils_optimized import clean_na_strings_vectorized


logger = get_module_logger(__name__)


def tikan(df):
    return df.rename(columns={"ABC業者_他": "大項目"})


def aggregate_vehicle_data(
    df_receive: pd.DataFrame, master_csv: pd.DataFrame, master_columns_keys: list
) -> pd.DataFrame:
    abc_to_cd = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}

    for abc_label, item_cd in abc_to_cd.items():
        filtered = df_receive[df_receive["集計項目CD"] == item_cd]
        # 最適化: clean_na_strings_vectorizedを使用（10-100倍高速化）
        cleaned_weight = clean_na_strings_vectorized(filtered["正味重量"])
        total_weight = pd.to_numeric(cleaned_weight, errors="coerce").sum()
        total_car = filtered["受入番号"].nunique()
        unit_price = total_weight / total_car if total_car > 0 else 0

        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, [abc_label, None, "重量"], total_weight
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, [abc_label, None, "台数"], total_car
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, [abc_label, None, "台数単価"], unit_price
        )

        logger.info(
            f"[{abc_label}] 台数: {total_car}, 重量: {total_weight:.2f}, 単価: {unit_price:.2f}"
        )

    return master_csv


def calculate_item_summary(
    df_receive: pd.DataFrame, master_csv: pd.DataFrame, master_columns_keys
) -> pd.DataFrame:
    unit_name = "kg"
    voucher_type = "売上"

    abc_to_cd = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
    item_to_cd = {"混合廃棄物A": 1, "混合廃棄物B": 2, "混合廃棄物(焼却物)": 4}

    for abc_key, abc_cd in abc_to_cd.items():
        for item_name, item_cd in item_to_cd.items():
            filtered = df_receive[
                (df_receive["伝票区分名"] == voucher_type)
                & (df_receive["単位名"] == unit_name)
                & (df_receive["集計項目CD"] == abc_cd)
                & (df_receive["品名CD"] == item_cd)
            ]

            # 最適化: clean_na_strings_vectorizedを使用（10-100倍高速化）
            cleaned_weight = clean_na_strings_vectorized(filtered["正味重量"])
            cleaned_sell = clean_na_strings_vectorized(filtered["金額"])
            total_weight = pd.to_numeric(cleaned_weight, errors="coerce").sum()
            total_sell = pd.to_numeric(cleaned_sell, errors="coerce").sum()
            ave_sell = total_sell / total_weight if total_weight > 0 else 0

            master_csv = set_value_fast_safe(
                master_csv,
                master_columns_keys,
                [abc_key, "平均単価", item_name],
                ave_sell,
            )
            master_csv = set_value_fast_safe(
                master_csv,
                master_columns_keys,
                [abc_key, "kg", item_name],
                total_weight,
            )
            master_csv = set_value_fast_safe(
                master_csv,
                master_columns_keys,
                [abc_key, "売上", item_name],
                total_sell,
            )

            if total_weight == 0:
                logger.warning(
                    "ABC重量0のため単価が0",
                    extra=create_log_context(
                        operation="calculate_abc_unit_prices",
                        abc_key=abc_key,
                        item_name=item_name,
                    ),
                )

    return master_csv


def summarize_item_and_abc_totals(master_csv: pd.DataFrame, master_columns_keys) -> pd.DataFrame:
    item_to_cd = {"混合廃棄物A": 1, "混合廃棄物B": 2, "混合廃棄物(焼却物)": 4}
    for item_name in item_to_cd.keys():
        filtered = master_csv[master_csv["品目_台数他"] == item_name]
        total_weight = filtered[filtered["kg売上平均単価"] == "kg"]["値"].sum()
        total_sell = filtered[filtered["kg売上平均単価"] == "売上"]["値"].sum()
        ave_sell = total_sell / total_weight if total_weight > 0 else 0

        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, ["合計", "平均単価", item_name], ave_sell
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, ["合計", "kg", item_name], total_weight
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, ["合計", "売上", item_name], total_sell
        )

    for abc_key in ["A", "B", "C", "D", "E", "F"]:
        filtered = master_csv[master_csv["ABC業者_他"] == abc_key]
        total_weight = filtered[filtered["kg売上平均単価"] == "kg"]["値"].sum()
        total_sell = filtered[filtered["kg売上平均単価"] == "売上"]["値"].sum()
        ave_sell = total_sell / total_weight if total_weight > 0 else 0

        master_csv = set_value_fast_safe(
            master_csv,
            master_columns_keys,
            [abc_key, "平均単価", "3品目合計"],
            ave_sell,
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, [abc_key, "kg", "3品目合計"], total_weight
        )
        master_csv = set_value_fast_safe(
            master_csv, master_columns_keys, [abc_key, "売上", "3品目合計"], total_sell
        )

    filtered = master_csv[master_csv["品目_台数他"] == "3品目合計"]
    total_weight = filtered[filtered["kg売上平均単価"] == "kg"]["値"].sum()
    total_sell = filtered[filtered["kg売上平均単価"] == "売上"]["値"].sum()
    ave_sell = total_sell / total_weight if total_weight > 0 else 0

    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", "平均単価", "3品目合計"], ave_sell
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", "kg", "3品目合計"], total_weight
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", "売上", "3品目合計"], total_sell
    )

    return master_csv


def calculate_final_totals(
    df_receive: pd.DataFrame, master_csv: pd.DataFrame, master_columns_keys
) -> pd.DataFrame:
    total_car = master_csv[master_csv["品目_台数他"] == "台数"]["値"].sum()
    total_weight = master_csv[master_csv["品目_台数他"] == "重量"]["値"].sum()
    unit_price = total_weight / total_car if total_car > 0 else 0

    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", None, "台数"], total_car
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", None, "重量"], total_weight
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["合計", None, "台数単価"], unit_price
    )

    filtered = df_receive[(df_receive["伝票区分名"] == "売上") & (df_receive["単位名"] == "kg")]
    # 最適化: clean_na_strings_vectorizedを使用（10-100倍高速化）
    cleaned_weight_all = clean_na_strings_vectorized(filtered["正味重量"])
    cleaned_sell_all = clean_na_strings_vectorized(filtered["金額"])
    total_weight_all = pd.to_numeric(cleaned_weight_all, errors="coerce").sum()
    total_sell_all = pd.to_numeric(cleaned_sell_all, errors="coerce").sum()
    average_price_all = total_sell_all / total_weight_all if total_sell_all > 0 else 0

    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["総品目㎏", None, None], total_weight_all
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["総品目売上", None, None], total_sell_all
    )
    master_csv = set_value_fast_safe(
        master_csv,
        master_columns_keys,
        ["総品目平均単価", None, None],
        average_price_all,
    )

    total_sell_3items = master_csv[
        (master_csv["ABC業者_他"] == "合計")
        & (master_csv["kg売上平均単価"] == "売上")
        & (master_csv["品目_台数他"] == "3品目合計")
    ]["値"].sum()

    total_weight_3items = master_csv[
        (master_csv["ABC業者_他"] == "合計")
        & (master_csv["kg売上平均単価"] == "kg")
        & (master_csv["品目_台数他"] == "3品目合計")
    ]["値"].sum()

    other_sell = total_sell_all - total_sell_3items
    other_weight = total_weight_all - total_weight_3items
    other_avg_price = other_sell / other_weight if other_sell > 0 else 0

    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["その他品目㎏", None, None], other_weight
    )
    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["その他品目売上", None, None], other_sell
    )
    master_csv = set_value_fast_safe(
        master_csv,
        master_columns_keys,
        ["その他品目平均単価", None, None],
        other_avg_price,
    )

    return master_csv


def set_report_date_info(
    df_receive: pd.DataFrame, master_csv: pd.DataFrame, master_columns_keys
) -> pd.DataFrame:
    today = pd.to_datetime(df_receive["伝票日付"].dropna().iloc[0])
    weekday = get_weekday_japanese(today)
    formatted_date = today.strftime("%m/%d")

    master_csv = set_value_fast_safe(
        master_csv, master_columns_keys, ["日付", None, None], formatted_date
    )
    master_csv = set_value_fast_safe(master_csv, master_columns_keys, ["曜日", None, None], weekday)

    logger.info(
        "日付設定完了",
        extra=create_log_context(
            operation="apply_date_and_weekday", date=formatted_date, weekday=weekday
        ),
    )
    return master_csv


def apply_rounding(master_csv: pd.DataFrame, master_columns_keys) -> pd.DataFrame:
    return round_value_column_generic(master_csv, master_columns_keys)
