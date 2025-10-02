"""
管理表（management_sheet）生成モジュール

このモジュールは、以下の各帳票ロジックを統合して管理表を作成します。
  - 工場日報（factory_report）
  - 搬出入（balance_sheet）
  - ABC（average_sheet）
  - スクラップ・選別

役割:
  1) テンプレートおよび必要CSVの読み込み
  2) 各処理の実行（処理は processors.management_sheet.* に委譲）
  3) 追加情報（日時・その他）を付与
  4) すべてを縦結合して最終DataFrameを返す

将来的には services/report 配下へ完全移行予定です。
"""

import pandas as pd
from app.st_app.utils.logger import app_logger
from app.st_app.logic.manage.utils.csv_loader import load_all_filtered_dataframes
from app.st_app.logic.manage.utils.load_template import load_master_and_template
from app.st_app.utils.config_loader import get_template_config
from app.st_app.logic.manage.processors.management_sheet.factory_report import (
    update_from_factory_report,
)
from app.st_app.logic.manage.processors.management_sheet.balance_sheet import (
    update_from_balance_sheet,
)
from app.st_app.logic.manage.processors.management_sheet.average_sheet import (
    update_from_average_sheet,
)
from app.st_app.logic.manage.processors.management_sheet.sukurappu_senbetu import (
    scrap_senbetsu,
)

from app.st_app.logic.manage.processors.management_sheet.manage_etc import (
    manage_etc,
)


def process(dfs: dict) -> pd.DataFrame:
    """
    管理表テンプレート用のメイン処理関数。

    - 入力: dfs（キー: ファイル識別子, 値: pandas.DataFrame）
    - 出力: 管理表の最終DataFrame（テンプレートレイアウトに整形済み）

    エラー時は処理対象のDataFrameが空になる可能性があるため、呼び出し側での検証を推奨します。
    """
    logger = app_logger()

    # --- ① マスターCSVの読み込み ---
    config = get_template_config()["management_sheet"]
    master_path = config["master_csv_path"]["management_sheet"]
    master_csv = load_master_and_template(master_path)

    # --- ② テンプレート設定と対象CSVの読み込み ---
    template_key = "management_sheet"
    template_config = get_template_config()[template_key]
    template_name = template_config["key"]
    csv_keys = template_config["required_files"]
    logger.info(f"[テンプレート設定読込] key={template_key}, files={csv_keys}")

    # 必要CSVを読み込み（アップロード済みdfsからフィルタ適用）
    df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
    df_receive = df_dict.get("receive")
    # df_shipment = df_dict.get("shipment")
    # df_yard = df_dict.get("yard")

    # --- ③ 各処理の適用 ---
    logger.info("▶️ 管理表_工場日報からの読込（factory_report → management_sheet 反映）")
    master_csv = update_from_factory_report(dfs, master_csv)

    logger.info("▶️ 管理表_搬出入からの読込（balance_sheet → management_sheet 反映）")
    master_csv = update_from_balance_sheet(dfs, master_csv)

    logger.info("▶️ 管理表_ABCからの読込（average_sheet → management_sheet 反映）")
    master_csv = update_from_average_sheet(dfs, master_csv)

    logger.info("▶️ スクラップ・選別（receive を参照）")
    master_csv = scrap_senbetsu(df_receive, master_csv)

    logger.info("▶️ 日付・その他（テンプレートへの最終差し込み）")
    etc_df = manage_etc(df_receive)

    logger.info("▶️ 結合（本体 + 付帯情報）")
    df_final = pd.concat([master_csv, etc_df], axis=0, ignore_index=True)

    return df_final
