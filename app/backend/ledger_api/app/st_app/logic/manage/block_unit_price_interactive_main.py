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
    make_total_sum,
    df_cul_filtering,
    first_cell_in_template,
    make_sum_date,
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
    entry_options_map: Optional[Dict[str, List[str]]] = None      # entry_id -> options snapshot


class BlockUnitPriceInteractive(BaseInteractiveReportGenerator):
    """ブロック単価計算の対話的処理クラス (Interactive Generator)
    - Step0: フロントに渡す運搬候補行（options + initial_index）を生成
    - 識別は entry_id に統一（row_index は返さない）
    - finalize 一本化: finalize に selections を含めて送れば、選択適用→最終計算まで一括実行
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

    # 小さなヘルパー群: initial_step の per-row 処理を分離
    def _normalize_df_index(self, idx: Any) -> Union[int, str]:
        """DataFrameの内部indexを公開可能な形に正規化する（intかstr）"""
        if isinstance(idx, (int,)):
            return int(idx)
        if isinstance(idx, float) and float(idx).is_integer():
            return int(idx)
        return str(idx)

    def _compute_options_and_initial(self, row: pd.Series, df_transport_cost: pd.DataFrame) -> Tuple[List[str], int, str, str, Any]:
        """与えられた行と運賃マスターから候補ラベル配列と初期インデックスを返す。

        戻り値: (normalized_options, initial_index, gyousha_cd_str, gyousha_name, gyousha_cd_raw)
        """
        gyousha_cd_raw = row.get("業者CD", "")
        gyousha_cd_str = str(gyousha_cd_raw)
        gyousha_name = self._clean_vendor_name(row.get("業者名", gyousha_cd_raw))

        opts_df = df_transport_cost
        if "業者CD" in opts_df.columns:
            opts_df = opts_df.assign(業者CD=opts_df["業者CD"].astype(str))
        options_series = opts_df[opts_df.get("業者CD") == gyousha_cd_str]
        options = (
            options_series.get("運搬業者", pd.Series(dtype=object))
            .astype(str)
            .tolist()
        )
        normalized_options = self._canonical_sort_labels(options)

        if not normalized_options:
            self.logger.warning(
                "運搬業者候補が取得できませんでした",
                extra={"vendor_code": gyousha_cd_raw, "vendor_name": gyousha_name},
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
                    extra={"vendor_code": gyousha_cd_raw, "vendor_name": gyousha_name, "initial": initial_label_candidate},
                )

        return normalized_options, initial_index, gyousha_cd_str, gyousha_name, gyousha_cd_raw

    def _build_row_payload(self, row: pd.Series, df_idx: Any, normalized_options: List[str], initial_index: int, entry_id: str) -> Tuple[Dict[str, Any], Any]:
        """1行分の rows_payload エントリを構築し、vendor_code の値（int or raw）を返す"""
        # vendor code を数値化できれば int に変換
        gyousha_cd_raw = row.get("業者CD", "")
        try:
            vendor_code_value: Any = int(gyousha_cd_raw)
        except Exception:
            vendor_code_value = gyousha_cd_raw

        hinmei = str(row.get("品名", "")).strip()
        meisai_raw = str(row.get("明細備考", "")).strip()
        meisai = meisai_raw if meisai_raw else None
        gyousha_name = self._clean_vendor_name(row.get("業者名", gyousha_cd_raw))

        payload_entry = {
            "entry_id": entry_id,
            "vendor_code": vendor_code_value,
            "vendor_name": gyousha_name,
            "item_name": hinmei,
            "detail": meisai,
            "options": normalized_options,
            "initial_index": initial_index,
        }
        return payload_entry, df_idx

    @staticmethod
    def _error_payload(code: str, detail: str, step: int, extra: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """フロントへ明示的に通知するエラーペイロード"""
        payload: Dict[str, Any] = {"status": "error", "code": code, "detail": detail, "step": step}
        if extra:
            payload.update(extra)
        return pd.DataFrame(), payload

    @staticmethod
    def _missing_cols(df: pd.DataFrame, required: List[str]) -> List[str]:
        return [c for c in required if c not in df.columns]

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
                return self._error_payload("NO_SHIPMENT", "出荷データが見つかりません", step=0)

            mainpath = MainPath()
            reader = ReadTransportDiscount(mainpath)
            df_transport_cost = reader.load_discounted_df()  # ★ 保存前に dtype を変えない

            # 前処理
            # マスターに基づいて出荷データをフィルタ・不要行除去・運搬関連カラムを追加する
            df_shipment = make_df_shipment_after_use(master_csv, df_shipment)
            # マスターの手数料を出荷データの単価に加算して単価を補正する
            df_shipment = apply_unit_price_addition(master_csv, df_shipment)
            # 運搬社数が1の業者に対して、運搬費を運搬マスターから適用する
            df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)

            # 選択が必要な行: 運搬社数 != 1 （NaNは0とみなして抽出）
            carriers = df_shipment.get("運搬社数")
            target_rows = df_shipment if carriers is None else df_shipment[carriers.fillna(0) != 1]

            rows_payload: List[Dict[str, Any]] = []
            entry_index_map: Dict[str, Union[int, str]] = {}
            entry_options_map: Dict[str, List[str]] = {}

            for idx, row in target_rows.iterrows():
                df_idx = self._normalize_df_index(idx)

                # options と初期選択を算出
                normalized_options, initial_index, gyousha_cd_str, gyousha_name, gyousha_cd_raw = self._compute_options_and_initial(
                    row, df_transport_cost
                )

                # entry_id を先に採番（ログにも使う）
                entry_id = self._stable_entry_id(row, fallback_key=f"{gyousha_cd_str}:{df_idx}")

                payload_entry, df_idx_ret = self._build_row_payload(
                    row, df_idx, normalized_options, initial_index, entry_id
                )

                rows_payload.append(payload_entry)
                entry_index_map[entry_id] = df_idx_ret
                entry_options_map[entry_id] = normalized_options  # ★ スナップショット保存

            state = {
                "df_shipment": df_shipment,
                "master_csv": master_csv,
                "df_transport_cost": df_transport_cost,
                "session_id": session_id,
                "entry_index_map": entry_index_map,
                "entry_options_map": entry_options_map,  # ★ 追加
            }

            payload = {
                "session_id": session_id,
                "rows": rows_payload,
            }

            return state, payload
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Step 0 error: {e}")
            return self._error_payload("STEP0_EXCEPTION", str(e), step=0)

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

    # --- selections を解決して df_shipment に適用するヘルパ ---
    def _resolve_and_apply_selections(
        self,
        state: Dict[str, Any],
        selections: Dict[str, Union[int, str]],
    ) -> Dict[str, str]:
        """entry_id -> (index|label) を ラベルに正規化して df_shipment に適用。戻り値は entry_id->label"""
        if not selections:
            return {}

        df_shipment: pd.DataFrame = state["df_shipment"]
        df_transport_cost: pd.DataFrame = state["df_transport_cost"]
        entry_index_map: Dict[str, Union[int, str]] = state.get("entry_index_map", {}) or {}
        entry_options_map: Dict[str, List[str]] = state.get("entry_options_map", {}) or {}

        # 比較時だけ文字列化したローカルコピー
        opts_df = df_transport_cost
        if "業者CD" in opts_df.columns:
            opts_df = opts_df.assign(業者CD=opts_df["業者CD"].astype(str))

        resolved_entry_map: Dict[str, str] = {}

        for entry_id, value in selections.items():
            df_idx = entry_index_map.get(entry_id)
            if df_idx is None:
                continue

            try:
                row = df_shipment.loc[df_idx]
            except Exception:
                continue

            # 1) スナップショット優先
            normalized_options = entry_options_map.get(entry_id)

            # 2) 無ければ従来通り再構築
            if not normalized_options:
                gyousha_cd_str = str(row.get("業者CD", ""))
                options = (
                    opts_df[opts_df.get("業者CD") == gyousha_cd_str]
                    .get("運搬業者", pd.Series(dtype=object))
                    .astype(str)
                    .tolist()
                )
                normalized_options = self._canonical_sort_labels(options)

            if not normalized_options:
                continue

            # index or label を解決
            if isinstance(value, int):
                idx = value if 0 <= value < len(normalized_options) else 0
                label = normalized_options[idx]
            else:
                label = str(value)
                if label not in normalized_options:
                    self.logger.warning(
                        "指定ラベルが候補に無いため先頭にフォールバック",
                        extra={"entry_id": entry_id, "label": label},
                    )
                    label = normalized_options[0]

            try:
                df_shipment.loc[df_idx, "運搬業者"] = label
            except Exception:
                pass

            resolved_entry_map[entry_id] = label

        state["df_shipment"] = df_shipment
        state["selections"] = resolved_entry_map
        return resolved_entry_map

    def _handle_select_transport(
        self, state: Dict[str, Any], user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """フロントからの選択適用（entry_id に統一）"""
        selections: Dict[str, Union[int, str]] = user_input.get("selections", {}) or {}
        session_id_in = user_input.get("session_id")
        if session_id_in and state.get("session_id") and session_id_in != state["session_id"]:
            self.logger.warning(
                "session_id 不一致: 応答は継続するが結果が期待と異なる可能性あり",
                extra={"expected": state.get("session_id"), "got": session_id_in},
            )

        resolved_entry_map = self._resolve_and_apply_selections(state, selections)

        selection_summary = self._create_selection_summary(resolved_entry_map)
        payload = {
            "selection_summary": selection_summary,
            "message": "運搬業者選択を適用しました",
            "step": 1,
            "action": "select_transport",
            "session_id": state.get("session_id"),
        }
        return state, payload

    # --- finalize を selections 付きで実行する公開メソッド（一本化用） ---
    def finalize_with_optional_selections(
        self,
        state: Dict[str, Any],
        user_input: Dict[str, Any],
    ):
        """payload に selections が含まれていれば先に適用してから finalize"""
        try:
            # セッション照合（任意）
            session_id_in = user_input.get("session_id")
            if session_id_in and state.get("session_id") and session_id_in != state["session_id"]:
                self.logger.warning(
                    "session_id 不一致: finalizeは続行するが結果が期待と異なる可能性あり",
                    extra={"expected": state.get("session_id"), "got": session_id_in},
                )

            selections = user_input.get("selections") or {}
            if isinstance(selections, dict) and selections:
                self._resolve_and_apply_selections(state, selections)
                self.logger.info("finalize直前に selections を適用", extra={"count": len(selections)})

            return self.finalize_step(state)

        except Exception as e:  # noqa: BLE001
            self.logger.error(f"finalize_with_optional_selections error: {e}")
            return self._error_payload("STEP2_EXCEPTION", str(e), step=2)

    # -------- Finalize Step (Step 2) --------
    def finalize_step(self, state: Dict[str, Any]):  # type: ignore[override]
        try:
            df_shipment: pd.DataFrame = state["df_shipment"]
            df_transport_cost: pd.DataFrame = state["df_transport_cost"]
            master_csv: pd.DataFrame = state["master_csv"]

            # 必須列チェック
            missing_tc = self._missing_cols(df_transport_cost, ["業者CD", "運搬業者"])
            has_transport_fee = "運搬費" in df_transport_cost.columns
            has_weight_unit = "重量単価" in df_transport_cost.columns
            if missing_tc or (not has_transport_fee and not has_weight_unit):
                detail = "運賃マスターに必要な列が不足しています"
                extra = {
                    "where": "df_transport_cost",
                    "missing": missing_tc + ([] if (has_transport_fee or has_weight_unit) else ["運搬費 or 重量単価"]),
                }
                return self._error_payload("MISSING_COLUMNS", detail, step=2, extra=extra)

            # 出荷データの必須列チェック
            missing_ship = self._missing_cols(df_shipment, ["業者CD", "運搬業者"])
            if missing_ship:
                detail = "出荷データに必要な列が不足しています"
                extra = {"where": "df_shipment", "missing": missing_ship}
                return self._error_payload("MISSING_COLUMNS", detail, step=2, extra=extra)

            for col in ["業者CD", "運搬業者", "運搬業者名"]:
                if col in df_shipment.columns:
                    df_shipment[col] = df_shipment[col].astype(str)
                if col in df_transport_cost.columns:
                    df_transport_cost[col] = df_transport_cost[col].astype(str)

            if "運搬費" not in df_shipment.columns:
                df_shipment["運搬費"] = 0

            # 選択した運搬業者をフロントエンドからの情報で反映
            df_selected = self._merge_selected_transport_vendors(df_shipment, state)
            state["df_shipment"] = df_selected

            # ブロック単価計算パイプラインを実行
            df_after = self._run_block_unit_price_pipeline(df_selected, df_transport_cost, master_csv)

            summary = {
                "total_amount": float(df_after.get("合計金額", pd.Series(dtype=float)).sum() or 0),
                "total_transport_fee": float(df_after.get("運搬費", pd.Series(dtype=float)).sum() or 0),
                "processed_records": int(len(df_after)),
            }
            payload = {
                "status": "success",
                "summary": summary,
                "step": 2,
                "message": "ブロック単価計算が完了しました",
                "session_id": state.get("session_id"),
                "resolvedSelections": state.get("selections", {}),
            }
            final_master_csv = first_cell_in_template(df_after)
            final_master_csv = make_sum_date(final_master_csv, df_selected)
            return final_master_csv, payload
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Step 2 error: {e}")
            return self._error_payload("STEP2_EXCEPTION", str(e), step=2)

    def _merge_selected_transport_vendors(
        self, df_shipment: pd.DataFrame, state: Dict[str, Any]
    ) -> pd.DataFrame:
        selections = state.get("selections") or {}
        if not selections:
            return df_shipment.copy()

        entry_index_map: Dict[str, Union[int, str]] = state.get("entry_index_map", {}) or {}
        selected_map: Dict[Any, str] = {}

        for entry_id, vendor_label in selections.items():
            df_idx = entry_index_map.get(entry_id)
            if df_idx is None:
                continue
            selected_map[df_idx] = str(vendor_label)

        if not selected_map:
            return df_shipment.copy()

        selected_series = pd.Series(selected_map, name="運搬業者_selected")
        df_after = df_shipment.copy()
        selected_df = selected_series.to_frame()
        merged = df_after.merge(
            selected_df,
            how="left",
            left_index=True,
            right_index=True,
        )

        if "運搬業者_selected" in merged.columns:
            existing_series = (
                merged["運搬業者"]
                if "運搬業者" in merged.columns
                else pd.Series(index=merged.index, dtype=object)
            )
            merged["運搬業者"] = merged["運搬業者_selected"].combine_first(existing_series)
            merged = merged.drop(columns=["運搬業者_selected"])

        return merged

    def _run_block_unit_price_pipeline(
        self,
        df_shipment: pd.DataFrame,
        df_transport_cost: pd.DataFrame,
        master_csv: pd.DataFrame,
    ) -> pd.DataFrame:
        df_after = df_shipment.copy()
        df_after = apply_transport_fee_by_vendor(df_after, df_transport_cost)
        if "重量単価" in df_transport_cost.columns:
            df_after = apply_weight_based_transport_fee(df_after, df_transport_cost)
        df_after = make_total_sum(df_after, master_csv)
        df_after = df_cul_filtering(df_after)
        return df_after

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
                unit_series = pd.Series(pd.to_numeric(df_shipment["単価"], errors="coerce"))
                qty_series = pd.Series(pd.to_numeric(df_shipment["数量"], errors="coerce"))
                df_shipment["合計金額"] = unit_series.fillna(0) * qty_series.fillna(0)

            # 運搬費を含む総合計算
            if "運搬費" in df_shipment.columns:
                transport_series = pd.Series(pd.to_numeric(df_shipment["運搬費"], errors="coerce"))
                df_shipment["総合計"] = df_shipment.get("合計金額", 0) + transport_series.fillna(0)

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
