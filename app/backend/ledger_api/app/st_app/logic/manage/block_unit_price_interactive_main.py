# backend/app/st_app/logic/manage/block_unit_price_interactive.py
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime
import hashlib
import secrets
import pandas as pd
import re

from app.api.services.report.base_interactive_report_generator import (
    BaseInteractiveReportGenerator,
)
from app.st_app.config.loader.main_path import MainPath
from app.st_app.logic.manage.processors.block_unit_price.process0 import (
    apply_transport_fee_by1,
    apply_unit_price_addition,
    make_df_shipment_after_use,
)
from app.st_app.logic.manage.processors.block_unit_price.process2 import (
    apply_transport_fee_by_vendor,
    apply_weight_based_transport_fee,
)
from app.st_app.logic.manage.readers.read_transport_discount import (
    ReadTransportDiscount,
)
from app.st_app.logic.manage.utils.csv_loader import load_all_filtered_dataframes
from app.st_app.logic.manage.utils.load_template import load_master_and_template
from app.st_app.utils.config_loader import get_template_config
from app.st_app.utils.logger import app_logger


# process1 Streamlit UI helpers are not used in the React interactive implementation

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
    session_id: Optional[str] = None
    entry_index_map: Optional[Dict[str, Union[int, str]]] = None  # entry_id -> df.index


class BlockUnitPriceInteractive(BaseInteractiveReportGenerator):
    """ブロック単価計算の対話的処理クラス (Interactive Generator)
    - Step0: フロントに渡す運搬候補行（options + initial_index）を生成
    - 識別は entry_id に統一（row_index は返さない）
    """

    # ビジネス順のための簡易定数（必要に応じて調整）
    _CARRIER_ORDER = {"オネスト": 0, "シェノンビ": 1, "エコライン": 2}
    _VEHICLE_ORDER = {"ウイング": 0, "コンテナ": 1, None: 2}

    def __init__(self, files: Optional[Dict[str, Any]] = None):
        super().__init__(report_key="block_unit_price", files=files or {})
        self.logger = app_logger()

    # -------- Helpers --------
    @staticmethod
    def _make_session_id() -> str:
        return f"bup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"

    @classmethod
    def _parse_label(cls, lbl: str) -> Tuple[int, int, int, str]:
        """ラベルから (carrierOrder, vehicleOrder, sharedFlag, lbl) を返すソートキー"""
        s = lbl or ""
        # キャリア
        if s.startswith("オネスト"):
            c = "オネスト"
        elif s.startswith("シェノンビ"):
            c = "シェノンビ"
        elif "エコライン" in s:
            c = "エコライン"
        else:
            c = "zzz"
        c_ord = cls._CARRIER_ORDER.get(c, 99)
        # 車種
        if "ウイング" in s:
            v_ord = cls._VEHICLE_ORDER["ウイング"]
        elif "コンテナ" in s:
            v_ord = cls._VEHICLE_ORDER["コンテナ"]
        else:
            v_ord = cls._VEHICLE_ORDER[None]
        # 合積は最後
        shared_flag = 1 if "合積" in s else 0
        return (c_ord, v_ord, shared_flag, s)

    @classmethod
    def _canonical_sort_labels(cls, labels: List[str]) -> List[str]:
        """重複除去 + ビジネス順で安定ソート"""
        uniq = {str(x).strip() for x in labels if isinstance(x, str) and str(x).strip()}
        return sorted(uniq, key=cls._parse_label)

    @staticmethod
    def _clean_vendor_name(name: Any) -> str:
        s = str(name or "")
        # ベンダ名の末尾に付く（ 123 ）のような注釈を除去
        return re.sub(r"（\s*\d+\s*）", "", s)

    @staticmethod
    def _safe_int(v: Any) -> Union[int, Any]:
        try:
            if isinstance(v, float) and float(v).is_integer():
                return int(v)
            return int(v)  # 文字列数値も int 化
        except Exception:
            return v

    @staticmethod
    def _stable_entry_id(row: pd.Series, fallback_key: str) -> str:
        """内容ベースの安定IDを作成（行の再並び替えでも不変）"""
        parts = [
            str(row.get("業者CD", "")),
            str(row.get("品名", "")),
            str(row.get("明細備考", "")),
            str(row.get("伝票番号", "")),  # あれば
            str(row.get("行番号", "")),    # あれば
        ]
        base = "|".join(parts).strip("|")
        if not base:
            base = fallback_key
        h = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
        return f"bup_{h}"

    # -------- Step 0 --------
    def initial_step(self, df_formatted: Dict[str, Any]):  # type: ignore[override]
        try:
            # Debug: inspect incoming formatted shipment
            try:
                _df_dbg = df_formatted.get("shipment")
                if isinstance(_df_dbg, pd.DataFrame):
                    print("[DEBUG] initial_step shipment columns:", list(_df_dbg.columns))
                    print("[DEBUG] initial_step shipment head:", _df_dbg.head(3).to_dict())
            except Exception as _e:  # noqa: BLE001
                print("[DEBUG] failed to dump incoming shipment:", _e)

            session_id = self._make_session_id()

            template_key = "block_unit_price"
            template_config = get_template_config()[template_key]
            template_name = template_config["key"]
            csv_keys = template_config["required_files"]

            # master
            config = get_template_config()["block_unit_price"]
            master_path = config["master_csv_path"]["vendor_code"]
            master_csv = load_master_and_template(master_path)

            df_dict = load_all_filtered_dataframes(df_formatted, csv_keys, template_name)
            df_shipment = df_dict.get("shipment")
            if df_shipment is None:
                raise ValueError("出荷データが見つかりません")

            mainpath = MainPath()
            reader = ReadTransportDiscount(mainpath)
            df_transport_cost = reader.load_discounted_df()

            # 前処理
            df_shipment = make_df_shipment_after_use(master_csv, df_shipment)
            df_shipment = apply_unit_price_addition(master_csv, df_shipment)
            df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)

            # 選択が必要な行: 運搬社数 != 1 （NaNは0とみなして抽出）
            carriers = df_shipment.get("運搬社数")
            if carriers is None:
                target_rows = df_shipment
            else:
                target_rows = df_shipment[carriers.fillna(0) != 1]

            rows_payload: List[Dict[str, Any]] = []
            entry_index_map: Dict[str, Union[int, str]] = {}

            # 比較時の型ブレを避けるため、業者CDは文字列で比較
            df_transport_cost = df_transport_cost.copy()
            if "業者CD" in df_transport_cost.columns:
                df_transport_cost["業者CD"] = df_transport_cost["業者CD"].astype(str)

            for idx, row in target_rows.iterrows():
                # DataFrameの内部index（非公開・識別不可）
                if isinstance(idx, (int,)):
                    df_idx: Union[int, str] = int(idx)
                elif isinstance(idx, float) and float(idx).is_integer():
                    df_idx = int(idx)
                else:
                    df_idx = str(idx)

                gyousha_cd_raw = row.get("業者CD", "")
                gyousha_cd_str = str(gyousha_cd_raw)
                gyousha_name = self._clean_vendor_name(row.get("業者名", gyousha_cd_raw))
                hinmei = str(row.get("品名", "")).strip()
                meisai_raw = str(row.get("明細備考", "")).strip()
                meisai = meisai_raw if meisai_raw else None

                # entry_id を先に採番（ログにも使う）
                entry_id = self._stable_entry_id(row, fallback_key=f"{gyousha_cd_str}:{df_idx}")

                # options: list of 運搬業者 from df_transport_cost matching 業者CD
                options_series = df_transport_cost[df_transport_cost.get("業者CD") == gyousha_cd_str]
                options = (
                    options_series.get("運搬業者", pd.Series(dtype=object))
                    .astype(str)
                    .tolist()
                )
                normalized_options = self._canonical_sort_labels(options)

                if not normalized_options:
                    self.logger.warning(
                        "運搬業者候補が取得できませんでした",
                        extra={"vendor_code": gyousha_cd_raw, "vendor_name": gyousha_name, "entry_id": entry_id},
                    )

                initial_label_candidate = str(row.get("運搬業者", "")).strip()
                if not initial_label_candidate and normalized_options:
                    initial_label_candidate = normalized_options[0]

                if normalized_options and initial_label_candidate in normalized_options:
                    initial_index = normalized_options.index(initial_label_candidate)
                else:
                    initial_index = 0
                    if initial_label_candidate:
                        self.logger.warning(
                            "初期選択肢が候補に存在しないため先頭へフォールバックしました",
                            extra={"vendor_code": gyousha_cd_raw, "vendor_name": gyousha_name, "entry_id": entry_id,
                                   "initial": initial_label_candidate},
                        )

                vendor_code_value: Any
                try:
                    vendor_code_value = int(gyousha_cd_raw)
                except Exception:
                    vendor_code_value = gyousha_cd_raw

                rows_payload.append(
                    {
                        "entry_id": entry_id,           # ★ 識別はこれのみ
                        "vendor_code": vendor_code_value,
                        "vendor_name": gyousha_name,
                        "item_name": hinmei,
                        "detail": meisai,
                        "options": normalized_options,  # ラベル配列（ビジネス順で安定）
                        "initial_index": initial_index, # 初期選択のインデックス
                    }
                )
                entry_index_map[entry_id] = df_idx

            state = {
                "df_shipment": df_shipment,
                "master_csv": master_csv,
                "df_transport_cost": df_transport_cost,
                "session_id": session_id,
                "entry_index_map": entry_index_map,
            }

            payload = {
                "session_id": session_id,
                "rows": rows_payload,
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
            "1": self._handle_select_transport,  # 数値指定互換（エンドポイント都合）
        }

    def _handle_select_transport(
        self, state: Dict[str, Any], user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """フロントからの選択適用（entry_id に統一）
        user_input 例:
        {
          "session_id": "...",  # 任意（あれば照合）
          "selections": { "bup_ab12cd34ef": 6, "bup_deadbeef01": "エコライン（コンテナ）・合積" }
        }
        """
        selections: Dict[str, Union[int, str]] = user_input.get("selections", {}) or {}
        session_id_in = user_input.get("session_id")
        if session_id_in and state.get("session_id") and session_id_in != state["session_id"]:
            self.logger.warning(
                "session_id 不一致: 応答は継続するが結果が期待と異なる可能性あり",
                extra={"expected": state.get("session_id"), "got": session_id_in},
            )

        df_shipment: pd.DataFrame = state["df_shipment"]
        df_transport_cost: pd.DataFrame = state["df_transport_cost"]
        entry_index_map: Dict[str, Union[int, str]] = state.get("entry_index_map", {}) or {}

        # 比較時の型ブレを避けるため、業者CDは文字列で比較
        df_transport_cost = df_transport_cost.copy()
        if "業者CD" in df_transport_cost.columns:
            df_transport_cost["業者CD"] = df_transport_cost["業者CD"].astype(str)

        # entry_id -> label へ正規化
        resolved_entry_map: Dict[str, str] = {}

        for entry_id, value in selections.items():
            if entry_id not in entry_index_map:
                # 無効な entry_id はスキップ
                continue
            df_idx = entry_index_map[entry_id]

            try:
                row = df_shipment.loc[df_idx]
            except Exception:
                continue

            gyousha_cd_str = str(row.get("業者CD", ""))
            # 候補を initial_step と同じルールで復元
            df_opts = df_transport_cost[df_transport_cost.get("業者CD") == gyousha_cd_str]
            options = (
                df_opts.get("運搬業者", pd.Series(dtype=object))
                .astype(str)
                .tolist()
            )
            normalized_options = self._canonical_sort_labels(options)
            if not normalized_options:
                continue

            if isinstance(value, int):
                selected_index = value
                if selected_index < 0 or selected_index >= len(normalized_options):
                    selected_index = 0
                label = normalized_options[selected_index]
            else:
                label = str(value)
                # ラベルが候補に無い場合は先頭へ
                if label not in normalized_options:
                    self.logger.warning(
                        "指定ラベルが候補に存在しないため先頭へフォールバックしました",
                        extra={"entry_id": entry_id, "label": label},
                    )
                    label = normalized_options[0]

            resolved_entry_map[entry_id] = label

        # 実適用（df.index へ変換）
        for entry_id, label in resolved_entry_map.items():
            df_idx = entry_index_map.get(entry_id)
            if df_idx is None:
                continue
            try:
                df_shipment.loc[df_idx, "運搬業者"] = label
            except Exception:
                pass

        state["df_shipment"] = df_shipment
        state["selections"] = selections

        selection_summary = self._create_selection_summary(resolved_entry_map)
        payload = {
            "selection_summary": selection_summary,
            "message": "運搬業者選択を適用しました",
            "step": 1,
            "action": "select_transport",
            "session_id": state.get("session_id"),
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

            print("[DEBUG] finalize_step df_shipment columns:", list(df_shipment.columns))
            if "運搬費" not in df_shipment.columns:
                print("[DEBUG] 運搬費列が無いため 0 で追加")
                df_shipment["運搬費"] = 0

            df_shipment = apply_transport_fee_by_vendor(df_shipment, df_transport_cost)
            df_shipment = apply_weight_based_transport_fee(df_shipment, df_transport_cost)

            final_master_csv = self._create_final_master_csv(df_shipment, master_csv)
            summary = {
                "total_amount": float(df_shipment["合計金額"].sum() if "合計金額" in df_shipment.columns else 0),
                "total_transport_fee": float(df_shipment["運搬費"].sum() if "運搬費" in df_shipment.columns else 0),
                "processed_records": int(len(df_shipment)),
            }
            payload = {
                "summary": summary,
                "step": 2,
                "message": "ブロック単価計算が完了しました",
                "session_id": state.get("session_id"),
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
        options: List[TransportOption] = []
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

    def _create_selection_summary(
        self, resolved_entry_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """選択結果の確認用サマリー（entry_idベース）"""
        summary: Dict[str, Any] = {"selections": {}, "affected_records": {}}
        for entry_id, label in resolved_entry_map.items():
            summary["selections"][entry_id] = label
            summary["affected_records"][entry_id] = {
                "transport_vendor": label,
                "record_count": 1,
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
                self.logger.warning("マスターCSVが空のため、処理済み出荷データを返します")
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
                    master_csv = pd.concat([master_csv, summary_by_vendor], ignore_index=True)

            return master_csv

        except Exception as e:
            self.logger.error(f"最終マスターCSV作成中にエラー: {e}")
            return master_csv
