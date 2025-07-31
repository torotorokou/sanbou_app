import pandas as pd
from app.api.services.manage_report_processors.factory_report.utils.logger import (
    app_logger,
)
from app.api.services.manage_report_processors.factory_report.utils.config_loader import (
    get_template_config,
)
from app.api.services.manage_report_processors.factory_report.utils.load_template import (
    load_master_and_template,
)
from app.api.services.manage_report_processors.factory_report.utils.excel_tools import (
    add_label_rows_and_restore_sum,
)
from app.api.services.manage_report_processors.factory_report.processors.summary import (
    summary_apply_by_sheet,
)
from app.api.services.manage_report_processors.factory_report.utils.summary_tools import (
    summarize_value_by_cell_with_label,
)


def process_yard(df_yard: pd.DataFrame, df_shipment: pd.DataFrame) -> pd.DataFrame:
    """
    出荷ヤードパートの帳票生成処理。

    Parameters:
        df_yard : pd.DataFrame
            ヤード一覧のDataFrame
        df_shipment : pd.DataFrame
            出荷一覧のDataFrame

    Returns:
        pd.DataFrame
            整形された出荷ヤード帳票のDataFrame
    """
    logger = app_logger()

    # --- ① マスターCSVの読み込み ---
    try:
        config = get_template_config()["factory_report"]
        master_path = config["master_csv_path"]["yard"]
        master_csv = load_master_and_template(master_path)
    except Exception as e:
        logger.error(f"マスターCSVの読み込みに失敗しました: {e}")
        # フォールバック: 空のデータフレームを返す
        return pd.DataFrame(
            columns=["大項目", "セル", "値", "セルロック", "順番", "カテゴリ"]
        )

    # --- ② ヤードの値集計処理 ---
    updated_master_csv = apply_yard_summary(master_csv, df_yard, df_shipment)

    # --- ③ 品目単位でヤード名をマージし、合計を計算 ---
    if "ヤード名" in updated_master_csv.columns:
        updated_with_sum = summarize_value_by_cell_with_label(
            updated_master_csv, cell_col="ヤード名", label_col="セル"
        )
    else:
        updated_with_sum = updated_master_csv

    # フォーマット修正
    final_df = format_table(updated_with_sum)

    logger.info("✅ 出荷ヤードの帳票生成が完了しました。")
    return final_df


def apply_yard_summary(
    master_csv: pd.DataFrame, df_yard: pd.DataFrame, df_shipment: pd.DataFrame
) -> pd.DataFrame:
    """
    ヤードデータの集計処理を適用

    Parameters:
        master_csv (pd.DataFrame): マスターCSV
        df_yard (pd.DataFrame): ヤードデータ
        df_shipment (pd.DataFrame): 出荷データ

    Returns:
        pd.DataFrame: 更新されたマスターCSV
    """
    logger = app_logger()

    # デバッグ情報：入力データのカラムを確認
    logger.info(f"🔍 df_yard のカラム: {df_yard.columns.tolist()}")
    logger.info(f"🔍 df_shipment のカラム: {df_shipment.columns.tolist()}")

    df_map = {"ヤード": df_yard, "出荷": df_shipment}

    sheet_key_pairs = [
        ("ヤード", ["品名"]),
        ("出荷", ["品名"]),
    ]

    master_csv_updated = master_csv.copy()

    for sheet_name, key_cols in sheet_key_pairs:
        if sheet_name in df_map:
            data_df = df_map[sheet_name]
            logger.info(f"🔍 {sheet_name} データのカラム: {data_df.columns.tolist()}")
            logger.info(
                f"🔍 {sheet_name} データに '正味重量' カラムが存在: {'正味重量' in data_df.columns}"
            )

            master_csv_updated = summary_apply_by_sheet(
                master_csv=master_csv_updated,
                data_df=data_df,
                sheet_name=sheet_name,
                key_cols=key_cols,
            )

    return master_csv_updated


def format_table(master_csv: pd.DataFrame) -> pd.DataFrame:
    """
    出荷ヤードのマスターCSVから必要な列を整形し、カテゴリを付与する。

    Parameters:
        master_csv : pd.DataFrame
            出荷ヤードの帳票CSV（"ヤード名", "セル", "値" を含む）

    Returns:
        pd.DataFrame : 整形後の出荷ヤードデータ
    """
    # 利用可能な列を確認
    available_columns = master_csv.columns.tolist()
    required_columns = ["セル", "値"]

    # 必要な列が存在するかチェック
    missing_columns = [col for col in required_columns if col not in available_columns]
    if missing_columns:
        print(f"警告: 必要な列が不足しています: {missing_columns}")
        # 不足している列を空で追加
        for col in missing_columns:
            master_csv[col] = ""

    # ヤード名または大項目列を探す
    label_col = None
    if "ヤード名" in available_columns:
        label_col = "ヤード名"
    elif "大項目" in available_columns:
        label_col = "大項目"
    else:
        print(
            "警告: ヤード名または大項目列が見つかりません。空の大項目列を作成します。"
        )
        master_csv["大項目"] = ""
        label_col = "大項目"

    # 抽出する列を決定
    extract_columns = [label_col, "セル", "値"]

    # オプション列を追加（存在する場合）
    optional_columns = ["セルロック", "順番"]
    for col in optional_columns:
        if col in available_columns:
            extract_columns.append(col)
        else:
            master_csv[col] = ""
            extract_columns.append(col)

    # 必要列を抽出
    format_df = master_csv[extract_columns].copy()

    # 置換
    if label_col != "大項目":
        format_df.rename(columns={label_col: "大項目"}, inplace=True)

    # カテゴリ列を追加
    format_df["カテゴリ"] = "ヤード"

    return format_df
