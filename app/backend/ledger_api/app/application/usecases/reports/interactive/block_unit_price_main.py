# -*- coding: utf-8 -*-

"""
Block Unit Price Interactive - Main Entry Point
インタラクティブブロック単価計算のメインエントリポイント
"""

from typing import Any, Callable, Dict, Optional, Tuple, Union
import pandas as pd

from app.application.usecases.report.base_generators import (
    BaseInteractiveReportGenerator,
)
from app.infra.report_utils import app_logger

# 分離したモジュールをインポート
from .block_unit_price_initial import execute_initial_step
from .block_unit_price_finalize import (
    execute_finalize_step,
    execute_finalize_with_optional_selections,
)
from .block_unit_price_utils import (
    canonical_sort_labels,
)

logger = app_logger()


class BlockUnitPriceInteractive(BaseInteractiveReportGenerator):
    """ブロック単価インタラクティブレポート生成クラス"""
    
    def __init__(self, files: Optional[Dict[str, Any]] = None):
        super().__init__(report_key="block_unit_price", files=files or {})
        self.logger = logger

    def initial_step(self, df_formatted: Dict[str, Any]):  # type: ignore[override]
        """初期ステップ: 運搬業者選択肢を生成"""
        return execute_initial_step(df_formatted)

    def get_step_handlers(self) -> Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Tuple[Dict[str, Any], Dict[str, Any]]]]:  # type: ignore[override]
        """ステップハンドラーを返す"""
        return {
            "select_transport": self._handle_select_transport,
            "1": self._handle_select_transport,
        }

    def _resolve_and_apply_selections(
        self, 
        state: Dict[str, Any], 
        selections: Dict[str, Union[int, str]]
    ) -> Dict[str, str]:
        """選択を解決してstateに適用"""
        if not selections:
            state["selections"] = {}
            return {}
        
        df_shipment: pd.DataFrame = state["df_shipment"]
        df_transport_cost: Optional[pd.DataFrame] = state.get("df_transport_cost")
        opts_df = (
            df_transport_cost.copy() 
            if isinstance(df_transport_cost, pd.DataFrame) 
            else pd.DataFrame()
        )
        if not opts_df.empty and "業者CD" in opts_df.columns:
            opts_df = opts_df.assign(業者CD=opts_df["業者CD"].astype(str))

        resolved_entry_map: Dict[str, str] = {}
        for entry_id, value in selections.items():
            matches = df_shipment.index[df_shipment.get("entry_id") == entry_id]
            if len(matches) == 0:
                self.logger.warning(
                    f"selection skip: entry_id not found: {entry_id}"
                )
                continue
            
            row = df_shipment.loc[matches[0]]
            gyousha_cd_str = str(row.get("業者CD", ""))
            normalized_options = []
            
            if not opts_df.empty:
                options = (
                    opts_df[opts_df.get("業者CD") == gyousha_cd_str]
                    .get("運搬業者", pd.Series(dtype=object))
                    .astype(str)
                    .tolist()
                )
                normalized_options = canonical_sort_labels(options)
            
            if isinstance(value, int) and normalized_options:
                idx_choice = value if 0 <= value < len(normalized_options) else 0
                label = normalized_options[idx_choice]
            else:
                label = str(value)
                if normalized_options and label not in normalized_options:
                    self.logger.warning(
                        f"指定ラベルが候補に無い: entry_id={entry_id}, label={label}"
                    )
                    label = normalized_options[0] if normalized_options else label
            
            resolved_entry_map[entry_id] = label
        
        state["selections"] = resolved_entry_map
        self.logger.debug(
            f"selections resolved: count={len(resolved_entry_map)}"
        )
        return resolved_entry_map

    def _handle_select_transport(
        self, 
        state: Dict[str, Any], 
        user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """運搬業者選択ハンドラー"""
        selections: Dict[str, Union[int, str]] = (
            user_input.get("selections", {}) or {}
        )
        resolved_entry_map = self._resolve_and_apply_selections(state, selections)
        selection_summary = self._create_selection_summary(resolved_entry_map)
        
        payload = {
            "selection_summary": selection_summary,
            "message": "運搬業者選択を受け取りました",
            "step": 1,
            "action": "select_transport",
            "session_id": state.get("session_id"),
        }
        return state, payload

    def finalize_with_optional_selections(
        self, 
        state: Dict[str, Any], 
        user_input: Dict[str, Any]
    ):
        """オプション選択付き最終処理"""
        return execute_finalize_with_optional_selections(state, user_input)

    def finalize_step(self, state: Dict[str, Any]):  # type: ignore[override]
        """最終ステップ: ブロック単価計算を実行"""
        return execute_finalize_step(state)

    def _create_selection_summary(
        self, 
        resolved_entry_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """選択サマリーを作成"""
        summary: Dict[str, Any] = {"selections": {}, "affected_records": {}}
        for entry_id, label in resolved_entry_map.items():
            summary["selections"][entry_id] = label
            summary["affected_records"][entry_id] = {
                "transport_vendor": label, 
                "record_count": 1
            }
        return summary
