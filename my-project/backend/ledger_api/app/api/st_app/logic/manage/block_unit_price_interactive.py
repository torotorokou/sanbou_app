# backend/app/api/st_app/logic/manage/block_unit_price_interactive.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from app.api.st_app.config.loader.main_path import MainPath
from app.api.st_app.logic.manage.processors.block_unit_price.process0 import (
    apply_transport_fee_by1,
    apply_unit_price_addition,
    make_df_shipment_after_use,
)
from app.api.st_app.logic.manage.processors.block_unit_price.process2 import (
    apply_transport_fee_by_vendor,
    apply_weight_based_transport_fee,
)
from app.api.st_app.logic.manage.readers.read_transport_discount import (
    ReadTransportDiscount,
)
from app.api.st_app.logic.manage.utils.csv_loader import load_all_filtered_dataframes
from app.api.st_app.logic.manage.utils.load_template import load_master_and_template
from app.api.st_app.utils.config_loader import get_template_config
from app.api.st_app.utils.logger import app_logger
from backend_shared.src.api_response.response_error import ErrorApiResponse
from backend_shared.src.api_response.response_success import (
    TransportersSuccessResponse,
)


@dataclass
class TransportOption:
    """運搬業者選択肢"""

    vendor_code: str
    vendor_name: str
    transport_fee: float
    weight_unit_price: float


@dataclass
class InteractiveProcessState:
    """対話的処理の状態管理"""

    step: int  # 現在のステップ (0, 1, 2)
    df_shipment: Optional[pd.DataFrame] = None
    transport_options: Optional[List[TransportOption]] = None
    selected_vendors: Optional[Dict[str, str]] = None  # {業者名: 選択された運搬業者}
    master_csv: Optional[pd.DataFrame] = None
    df_transport_cost: Optional[pd.DataFrame] = None


class BlockUnitPriceInteractive:
    """ブロック単価計算の対話的処理クラス"""

    def __init__(self):
        self.logger = app_logger()

    def start_process(self, dfs: Dict[str, Any]) -> dict:
        """
        処理開始（Step 0）

        Returns:
            Dict: {
                "status": "success",
                "data": {...}
            }
        """
        self.logger.info("▶️ ブロック単価計算処理開始（対話版 Step 0）")

        # --- 設定とマスターデータの読み込み ---
        template_key = "block_unit_price"
        template_config = get_template_config()[template_key]
        template_name = template_config["key"]
        csv_keys = template_config["required_files"]

        # マスターデータ
        config = get_template_config()["block_unit_price"]
        master_path = config["master_csv_path"]["vendor_code"]
        master_csv = load_master_and_template(master_path)

        # 運搬費データ
        mainpath = MainPath()
        reader = ReadTransportDiscount(mainpath)
        df_transport_cost = reader.load_discounted_df()

        # 出荷データ
        df_dict = load_all_filtered_dataframes(dfs, csv_keys, template_name)
        df_shipment = df_dict.get("shipment")

        if df_shipment is None:
            return {"status": "error", "message": "出荷データが見つかりません"}

        # 基本処理の実行
        df_shipment = make_df_shipment_after_use(master_csv, df_shipment)
        df_shipment = apply_unit_price_addition(master_csv, df_shipment)
        df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)

        # 識別ナンバーの追加
        df_shipment = df_shipment.reset_index(drop=True)
        df_shipment["識別子"] = df_shipment.index.map(lambda x: f"id_{x}")

        # 運搬業者が1以外のものをピックアップ
        target_rows = df_shipment[df_shipment["運搬社数"] != 1].copy()
        target_rows = target_rows[
            [
                "識別子",
                "業者CD",
                "業者名",
                "品名",
                "明細備考",
            ]
        ]

        # 運搬業者の選択肢を追加
        transporter_map = df_transport_cost.groupby("業者CD")["運搬業者"].apply(list)
        target_rows["運搬業者リスト"] = target_rows["業者CD"].map(transporter_map)

        # カラムを英語名に変換
        col_map = {
            "識別子": "id",
            "業者CD": "vendor_code",
            "業者名": "vendor_name",
            "品名": "item_name",
            "明細備考": "detail_note",
            "運搬業者リスト": "transporters",
        }
        df_english = target_rows.rename(columns=col_map)

        # Json形式に変換
        json_data = df_english.to_dict(orient="records")

        return {"status": "success", "data": json_data}

    def process_selection(
        self, session_data: Dict[str, Any], selections: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        運搬業者選択処理（Step 1）

        Args:
            session_data: 前のステップで保存されたセッションデータ
            selections: {業者名: 選択された運搬業者コード}

        Returns:
            Dict: 処理結果とStep 2への準備情報
        """
        self.logger.info("▶️ 運搬業者選択処理（対話版 Step 1）")

        try:
            # セッションデータから復元
            df_shipment = pd.read_json(session_data["df_shipment_json"])
            master_csv = pd.read_json(session_data["master_csv_json"])
            df_transport_cost = pd.read_json(session_data["df_transport_cost_json"])

            # 選択結果を適用
            df_shipment = self._apply_transport_selections(
                df_shipment, df_transport_cost, selections
            )

            # 選択結果の確認データを準備
            selection_summary = self._create_selection_summary(df_shipment, selections)

            return {
                "status": "success",
                "step": 1,
                "message": "運搬業者選択を適用しました。確認してください。",
                "data": {
                    "selection_summary": selection_summary,
                    "session_data": {
                        "df_shipment_json": df_shipment.to_json(),
                        "master_csv_json": master_csv.to_json(),
                        "df_transport_cost_json": df_transport_cost.to_json(),
                        "selections": selections,
                    },
                },
            }

        except Exception as e:
            self.logger.error(f"Step 1 処理中にエラー: {e}")
            return {
                "status": "error",
                "message": f"運搬業者選択処理中にエラーが発生しました: {str(e)}",
            }

    def finalize_calculation(
        self, session_data: Dict[str, Any], confirmed: bool = True
    ) -> Dict[str, Any]:
        """
        最終計算処理（Step 2）

        Args:
            session_data: 前のステップで保存されたセッションデータ
            confirmed: 選択内容の確認フラグ

        Returns:
            Dict: 最終的な計算結果
        """
        self.logger.info("▶️ 最終計算処理（対話版 Step 2）")

        if not confirmed:
            return {
                "status": "cancelled",
                "message": "処理がキャンセルされました。Step 1に戻ってください。",
            }

        try:
            # セッションデータから復元
            df_shipment = pd.read_json(session_data["df_shipment_json"])
            master_csv = pd.read_json(session_data["master_csv_json"])
            df_transport_cost = pd.read_json(session_data["df_transport_cost_json"])

            # 最終的な運搬費計算
            df_shipment = apply_transport_fee_by_vendor(df_shipment, df_transport_cost)
            df_shipment = apply_weight_based_transport_fee(
                df_shipment, df_transport_cost
            )

            # 最終マスターCSV作成
            final_master_csv = self._create_final_master_csv(df_shipment, master_csv)

            return {
                "status": "completed",
                "step": 2,
                "message": "ブロック単価計算が完了しました。",
                "data": {
                    "result_csv": final_master_csv.to_dict("records"),
                    "summary": {
                        "total_amount": df_shipment["合計金額"].sum()
                        if "合計金額" in df_shipment.columns
                        else 0,
                        "total_transport_fee": df_shipment["運搬費"].sum()
                        if "運搬費" in df_shipment.columns
                        else 0,
                        "processed_records": len(df_shipment),
                    },
                },
            }

        except Exception as e:
            self.logger.error(f"Step 2 処理中にエラー: {e}")
            return {
                "status": "error",
                "message": f"最終計算処理中にエラーが発生しました: {str(e)}",
            }

    def _prepare_transport_options(
        self, df_transport: pd.DataFrame, df_shipment: pd.DataFrame
    ) -> List[TransportOption]:
        """運搬業者選択肢を準備"""
        options = []

        if not df_transport.empty:
            for _, row in df_transport.iterrows():
                options.append(
                    TransportOption(
                        vendor_code=row.get("業者CD", ""),
                        vendor_name=row.get("運搬業者", ""),
                        transport_fee=row.get("運搬費", 0),
                        weight_unit_price=row.get("重量単価", 0),
                    )
                )

        return options

    def _apply_transport_selections(
        self,
        df_shipment: pd.DataFrame,
        df_transport: pd.DataFrame,
        selections: Dict[str, str],
    ) -> pd.DataFrame:
        """選択された運搬業者を適用"""

        # 業者名ごとに運搬業者を設定
        for vendor_name, transport_vendor in selections.items():
            mask = df_shipment["業者名"] == vendor_name
            df_shipment.loc[mask, "運搬業者"] = transport_vendor

        return df_shipment

    def _create_selection_summary(
        self, df_shipment: pd.DataFrame, selections: Dict[str, str]
    ) -> Dict[str, Any]:
        """選択結果の確認用サマリーを作成"""
        summary = {"selections": selections, "affected_records": {}}

        for vendor_name, transport_vendor in selections.items():
            mask = df_shipment["業者名"] == vendor_name
            affected_count = mask.sum()
            summary["affected_records"][vendor_name] = {
                "transport_vendor": transport_vendor,
                "record_count": int(affected_count),
            }

        return summary

    def _create_final_master_csv(
        self, df_shipment: pd.DataFrame, master_csv: pd.DataFrame
    ) -> pd.DataFrame:
        """最終マスターCSV作成（block_unit_price_react.pyと同じロジック）"""
        try:
            # 基本的な合計計算
            if "単価" in df_shipment.columns and "数量" in df_shipment.columns:
                df_shipment["合計金額"] = pd.to_numeric(
                    df_shipment["単価"], errors="coerce"
                ).fillna(0) * pd.to_numeric(
                    df_shipment["数量"], errors="coerce"
                ).fillna(0)

            # 運搬費を含む総合計算
            if "運搬費" in df_shipment.columns:
                df_shipment["総合計"] = df_shipment.get("合計金額", 0) + pd.to_numeric(
                    df_shipment["運搬費"], errors="coerce"
                ).fillna(0)

            # マスターCSVが空の場合は出荷データを返す
            if master_csv.empty:
                self.logger.warning(
                    "マスターCSVが空のため、処理済み出荷データを返します"
                )
                return df_shipment

            # 業者別集計
            if "業者名" in df_shipment.columns:
                summary_by_vendor = (
                    df_shipment.groupby("業者名")
                    .agg({"合計金額": "sum", "運搬費": "sum", "総合計": "sum"})
                    .reset_index()
                )

                # マスターCSVと結合
                if "業者名" in master_csv.columns:
                    master_csv = master_csv.merge(
                        summary_by_vendor,
                        on="業者名",
                        how="left",
                        suffixes=("", "_new"),
                    )
                else:
                    master_csv = pd.concat(
                        [master_csv, summary_by_vendor], ignore_index=True
                    )

            return master_csv

        except Exception as e:
            self.logger.error(f"最終マスターCSV作成中にエラー: {e}")
            return master_csv
