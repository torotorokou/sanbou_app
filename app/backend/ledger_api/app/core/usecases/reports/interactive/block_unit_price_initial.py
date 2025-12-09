# -*- coding: utf-8 -*-

"""
Block Unit Price Interactive - Initial Step Handler
初期処理を担当するモジュール
"""

from typing import Any, Dict, List, Tuple, Union
import traceback
import pandas as pd

from app.core.domain.reports.processors.block_unit_price.process0 import (
    make_df_shipment_after_use,
)
from app.infra.report_utils import (
    get_template_config,
    MainPath,
    load_master_and_template,
    load_all_filtered_dataframes,
)
from app.infra.report_utils.domain import ReadTransportDiscount
from backend_shared.application.logging import get_module_logger, create_log_context

from .block_unit_price_utils import (
    make_session_id,
    clean_vendor_name,
    canonical_sort_labels,
    ensure_datetime_col,
    stable_entry_id,
    normalize_df_index,
    fmt_cols,
    handle_step_error,
)

# Legacy exports for compatibility
from app.core.domain.reports.processors.block_unit_price import process0 as _process0
apply_unit_price_addition = _process0.apply_unit_price_addition
apply_transport_fee_by1 = _process0.apply_transport_fee_by1

logger = get_module_logger(__name__)


# ------------------------------ Options Computation ------------------------------

def compute_options_and_initial(
    row: pd.Series,
    df_transport_cost: pd.DataFrame
) -> Tuple[List[str], int, str, str, Any]:
    """
    運搬業者の選択肢と初期選択インデックスを計算
    
    Returns:
        (normalized_options, initial_index, gyousha_cd_str, gyousha_name, gyousha_cd_raw)
    """
    gyousha_cd_raw = row.get("業者CD", "")
    gyousha_cd_str = str(gyousha_cd_raw)
    gyousha_name = clean_vendor_name(row.get("業者名", gyousha_cd_raw))

    opts_df = df_transport_cost
    if "業者CD" in opts_df.columns:
        opts_df = opts_df.assign(業者CD=opts_df["業者CD"].astype(str))
    
    options_series = opts_df[opts_df.get("業者CD") == gyousha_cd_str]
    options = (
        options_series.get("運搬業者", pd.Series(dtype=object))
        .astype(str)
        .tolist()
    )
    normalized_options = canonical_sort_labels(options)

    if not normalized_options:
        logger.warning(
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
            logger.warning(
                "初期選択肢が候補に存在しないため先頭へフォールバックしました",
                extra={
                    "vendor_code": gyousha_cd_raw,
                    "vendor_name": gyousha_name,
                    "initial": initial_label_candidate
                },
            )
    
    return normalized_options, initial_index, gyousha_cd_str, gyousha_name, gyousha_cd_raw


def build_row_payload(
    row: pd.Series,
    df_idx: Any,
    normalized_options: List[str],
    initial_index: int,
    entry_id: str
) -> Tuple[Dict[str, Any], Any]:
    """
    行のペイロードを構築
    
    Returns:
        (payload_entry, df_idx)
    """
    gyousha_cd_raw = row.get("業者CD", "")
    try:
        vendor_code_value: Any = int(gyousha_cd_raw)
    except Exception:
        vendor_code_value = gyousha_cd_raw

    hinmei = str(row.get("品名", "")).strip()
    meisai_raw = str(row.get("明細備考", "")).strip()
    meisai = meisai_raw if meisai_raw else None
    gyousha_name = clean_vendor_name(row.get("業者名", gyousha_cd_raw))

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


# ------------------------------ Main Initial Step ------------------------------

def execute_initial_step(df_formatted: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    初期ステップの実行
    
    Args:
        df_formatted: フォーマット済みデータフレーム辞書
    
    Returns:
        (state, payload): 状態とペイロード
    """
    try:
        # 入力ダンプ（デバッグ用）
        try:
            _df_dbg = df_formatted.get("shipment")
            if isinstance(_df_dbg, pd.DataFrame):
                logger.debug(
                    "initial_step shipmentデータ",
                    extra=create_log_context(
                        operation="initial_block_unit_price",
                        columns=list(_df_dbg.columns),
                        head=_df_dbg.head(3).to_dict()
                    )
                )
        except Exception as _e:
            logger.debug(
                "shipmentダンプ失敗",
                extra=create_log_context(operation="initialize_block_unit_price", error=str(_e))
            )

        session_id = make_session_id()

        # テンプレート設定の取得
        template_key = "block_unit_price"
        template_config = get_template_config()[template_key]
        template_name = template_config["key"]
        csv_keys = template_config["required_files"]

        # マスターCSVの読み込み
        config = get_template_config()["block_unit_price"]
        master_path = config["master_csv_path"]["vendor_code"]
        master_csv = load_master_and_template(master_path)

        # データフレームの読み込み
        df_dict = load_all_filtered_dataframes(
            df_formatted, csv_keys, template_name
        )
        df_shipment = df_dict.get("shipment")
        if df_shipment is None or df_shipment.empty:
            # エラー時は空の状態辞書を返す
            return {}, {"status": "error", "code": "NO_SHIPMENT", "detail": "出荷データが見つかりません", "step": 0}

        # 型チェック回避のため明示的にDataFrameとしてアサート
        assert isinstance(df_shipment, pd.DataFrame)

        # 運搬費用データの読み込み
        mainpath = MainPath()
        reader = ReadTransportDiscount(mainpath)
        df_transport_cost = reader.load_discounted_df()

        # 前処理
        df_shipment = make_df_shipment_after_use(master_csv, df_shipment)
        df_shipment = apply_unit_price_addition(master_csv, df_shipment)
        df_shipment = apply_transport_fee_by1(df_shipment, df_transport_cost)
        df_shipment = ensure_datetime_col(df_shipment, "伝票日付")
        
        # 型アサーション: ensure_datetime_col は DataFrame を返す
        assert isinstance(df_shipment, pd.DataFrame)

        # 選択対象行（運搬社数 != 1）の抽出
        carriers = df_shipment.get("運搬社数")
        target_rows = df_shipment if carriers is None else df_shipment[carriers.fillna(0) != 1]

        rows_payload: List[Dict[str, Any]] = []
        entry_index_map: Dict[str, Union[int, str]] = {}

        # 各行の処理
        for row_num, (idx, row) in enumerate(target_rows.iterrows()):
            df_idx = normalize_df_index(idx)
            
            # オプションと初期選択の計算
            normalized_options, initial_index, gyousha_cd_str, _, _ = compute_options_and_initial(
                row, df_transport_cost
            )
            
            # エントリIDの生成（row_numを渡して一意性を保証）
            entry_id = stable_entry_id(row, fallback_key=f"{gyousha_cd_str}:{df_idx}", row_index=row_num)
            
            # ペイロードの構築
            payload_entry, df_idx_ret = build_row_payload(
                row, df_idx, normalized_options, initial_index, entry_id
            )
            
            rows_payload.append(payload_entry)
            entry_index_map[entry_id] = df_idx_ret

        # entry_id を DataFrame に付与
        try:
            entry_series = pd.Series(
                data=list(entry_index_map.keys()),
                index=list(entry_index_map.values()),
                name="entry_id",
            )
            df_shipment = df_shipment.copy()
            df_shipment["entry_id"] = entry_series.reindex(df_shipment.index)
        except Exception:
            df_shipment = df_shipment.copy()
            df_shipment["entry_id"] = None
            for eid, idx in entry_index_map.items():
                try:
                    if idx in df_shipment.index:
                        df_shipment.loc[idx, "entry_id"] = eid
                except Exception:
                    continue

        # 状態とペイロードの構築
        state = {
            "df_shipment": df_shipment,
            "df_transport_cost": df_transport_cost,
            "master_csv": master_csv,
            "session_id": session_id,
        }
        
        payload = {
            "session_id": session_id,
            "rows": rows_payload,
        }

        # entry_idのデバッグログ
        if "entry_id" in df_shipment.columns:
            entry_id_info = {
                "total_rows": len(df_shipment),
                "entry_id_count": df_shipment["entry_id"].notna().sum(),
                "entry_id_dtype": str(df_shipment["entry_id"].dtype),
                "entry_id_sample": df_shipment["entry_id"].dropna().head(5).tolist()
            }
            logger.info(
                "INITIAL entry_id info",
                extra=create_log_context(
                    operation="initial_block_unit_price",
                    **entry_id_info
                )
            )

        logger.debug(
            f"INITIAL OK: df_shipment {fmt_cols(df_shipment)} | "
            f"transport_cost {fmt_cols(df_transport_cost)} | rows={len(rows_payload)}"
        )
        
        return state, payload

    except Exception as e:
        # 共通エラーハンドリングを使用
        context = {}
        try:
            if 'df_shipment' in locals():
                context["df_shipment_shape"] = locals()["df_shipment"].shape
            if 'rows_payload' in locals():
                context["rows_count"] = len(locals()["rows_payload"])
        except Exception:
            pass
        
        _, error_payload_dict = handle_step_error("initial", 0, e, context)
        return {}, error_payload_dict
