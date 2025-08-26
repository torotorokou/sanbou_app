# backend/app/api/st_app/logic/manage/block_unit_price_interactive.py

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from app.api.services.report.base_interactive_report_generator import (
    BaseInteractiveReportGenerator,
)
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


class BlockUnitPriceInteractive(BaseInteractiveReportGenerator):
    """ブロック単価計算の対話的処理クラス (Interactive Generator)"""

    def __init__(self, files: Optional[Dict[str, Any]] = None):
        super().__init__(report_key="block_unit_price", files=files or {})
        self.logger = app_logger()

    # -------- Step 0 --------
    def initial_step(self, df_formatted: Dict[str, Any]):  # type: ignore[override]
        try:
            # Debug: inspect incoming formatted shipment
            try:
                _df_dbg = df_formatted.get("shipment")
                if isinstance(_df_dbg, pd.DataFrame):
                    print(
                        "[DEBUG] initial_step shipment columns:", list(_df_dbg.columns)
                    )
                    print(
                        "[DEBUG] initial_step shipment head:", _df_dbg.head(3).to_dict()
                    )
            except Exception as _e:  # noqa: BLE001
                print("[DEBUG] failed to dump incoming shipment:", _e)
            template_key = "block_unit_price"
            template_config = get_template_config()[template_key]
            template_name = template_config["key"]
            csv_keys = template_config["required_files"]

            # master
            config = get_template_config()["block_unit_price"]
            master_path = config["master_csv_path"]["vendor_code"]
            master_csv = load_master_and_template(master_path)

            df_dict = load_all_filtered_dataframes(
                df_formatted, csv_keys, template_name
            )
            df_shipment = df_dict.get("shipment")
            if df_shipment is None:
                raise ValueError("出荷データが見つかりません")

            mainpath = MainPath()
            reader = ReadTransportDiscount(mainpath)
            df_transport_cost = reader.load_discounted_df()

            df_shipment = make_df_shipment_after_use(master_csv, df_shipment)
            df_shipment = apply_unit_price_addition(master_csv, df_shipment)
            df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)

            transport_options = self._prepare_transport_options(
                df_transport_cost, df_shipment
            )

            state = {
                "df_shipment": df_shipment,
                "master_csv": master_csv,
                "df_transport_cost": df_transport_cost,
            }
            payload = {
                "transport_options": [t.__dict__ for t in transport_options],
                "step": 0,
                "message": "初期処理完了",
            }
            return state, payload
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Step 0 error: {e}")
            return {}, {"status": "error", "message": str(e), "step": 0}

    # -------- Generic Step Handlers --------
    def get_step_handlers(
        self,
    ) -> Dict[
        str,
        Callable[
            [Dict[str, Any], Dict[str, Any]], Tuple[Dict[str, Any], Dict[str, Any]]
        ],
    ]:  # type: ignore[override]
        return {
            "select_transport": self._handle_select_transport,
            "1": self._handle_select_transport,  # 数値指定互換
        }

    def _handle_select_transport(
        self, state: Dict[str, Any], user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        selections: Dict[str, str] = user_input.get("selections", {})
        df_shipment: pd.DataFrame = state["df_shipment"]
        df_transport_cost: pd.DataFrame = state["df_transport_cost"]
        df_shipment = self._apply_transport_selections(
            df_shipment, df_transport_cost, selections
        )
        state["df_shipment"] = df_shipment
        state["selections"] = selections
        selection_summary = self._create_selection_summary(df_shipment, selections)
        payload = {
            "selection_summary": selection_summary,
            "message": "運搬業者選択を適用しました",
            "step": 1,
            "action": "select_transport",
        }
        return state, payload

    # -------- Finalize Step (Step 2) --------
    def finalize_step(self, state: Dict[str, Any]):  # type: ignore[override]
        try:
            df_shipment: pd.DataFrame = state["df_shipment"]
            df_transport_cost: pd.DataFrame = state["df_transport_cost"]
            master_csv: pd.DataFrame = state["master_csv"]

            # Ensure consistent dtypes for merge/join operations
            for col in ["運搬業者", "運搬業者名"]:
                if col in df_shipment.columns:
                    df_shipment[col] = df_shipment[col].astype(str)
                if col in df_transport_cost.columns:
                    df_transport_cost[col] = df_transport_cost[col].astype(str)

            print(
                "[DEBUG] finalize_step df_shipment columns:", list(df_shipment.columns)
            )
            if "運搬費" not in df_shipment.columns:
                print("[DEBUG] 運搬費列が無いため 0 で追加")
                df_shipment["運搬費"] = 0

            df_shipment = apply_transport_fee_by_vendor(df_shipment, df_transport_cost)
            df_shipment = apply_weight_based_transport_fee(
                df_shipment, df_transport_cost
            )

            final_master_csv = self._create_final_master_csv(df_shipment, master_csv)
            summary = {
                "total_amount": float(
                    df_shipment["合計金額"].sum()
                    if "合計金額" in df_shipment.columns
                    else 0
                ),
                "total_transport_fee": float(
                    df_shipment["運搬費"].sum()
                    if "運搬費" in df_shipment.columns
                    else 0
                ),
                "processed_records": int(len(df_shipment)),
            }
            payload = {
                "summary": summary,
                "step": 2,
                "message": "ブロック単価計算が完了しました",
            }
            return final_master_csv, payload
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Step 2 error: {e}")
            return pd.DataFrame(), {"status": "error", "message": str(e), "step": 2}

    # 旧 process_selection / finalize_calculation は BaseInteractiveReportGenerator 経由に移行

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
        df_transport: pd.DataFrame,  # noqa: ARG002 - 参照保持で将来利用
        selections: Dict[str, str],
    ) -> pd.DataFrame:
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
