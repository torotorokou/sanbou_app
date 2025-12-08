# -*- coding: utf-8 -*-

"""
Block Unit Price Interactive - Main Entry Point
インタラクティブブロック単価計算のメインエントリポイント

最適化履歴:
- Step 1 (2025-12-08): 処理フローの可視化とタイミングログ追加
"""

from typing import Any, Callable, Dict, Optional, Tuple, Union
import time
import pandas as pd

from app.core.usecases.reports.base_generators import (
    BaseInteractiveReportGenerator,
)
from backend_shared.application.logging import get_module_logger

# 分離したモジュールをインポート
from .block_unit_price_initial import execute_initial_step
from .block_unit_price_finalize import (
    execute_finalize_step,
    execute_finalize_with_optional_selections,
)
from .block_unit_price_utils import (
    canonical_sort_labels,
)

logger = get_module_logger(__name__)


class BlockUnitPriceInteractive(BaseInteractiveReportGenerator):
    """
    ブロック単価インタラクティブレポート生成クラス
    
    処理フロー:
    ----------------------------------------
    Step 0 (initial_step): 初期処理
      - 出荷データの読み込みとフィルタリング
      - 運搬業者選択肢の生成
      - セッション状態の初期化
    
    Step 1 (select_transport): 運搬業者選択
      - ユーザーの選択内容を受信
      - 選択内容の妥当性検証
      - state更新
    
    Step 2 (finalize): 最終計算
      - ブロック単価計算
      - 運搬費用計算
      - 帳票生成とZIPファイル化
    
    最適化ポイント:
      - 各ステップの処理時間を計測
      - copy()操作の最小化
      - ベクトル化による高速化
    ----------------------------------------
    """
    
    def __init__(self, files: Optional[Dict[str, Any]] = None):
        super().__init__(report_key="block_unit_price", files=files or {})
        self.logger = logger
        # 最新の日付のみを対象とする
        self.period_type = "oneday"
        self.date_filter_strategy = "max"

    def initial_step(self, df_formatted: Dict[str, Any]):  # type: ignore[override]
        """
        初期ステップ: 運搬業者選択肢を生成
        
        処理内容:
        1. 出荷データの読み込み
        2. 運搬業者マスタの取得
        3. 選択肢の生成
        4. セッション状態の作成
        """
        step_start = time.time()
        self.logger.info("Step 0: 初期処理開始（運搬業者選択肢生成）")
        
        result = execute_initial_step(df_formatted)
        
        elapsed_ms = round((time.time() - step_start) * 1000, 2)
        self.logger.info(
            "Step 0: 初期処理完了",
            extra={"elapsed_ms": elapsed_ms}
        )
        return result

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
    def _handle_select_transport(
        self, 
        state: Dict[str, Any], 
        user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        運搬業者選択ハンドラー
        
        処理内容:
        1. ユーザー選択内容の取得
        2. 選択内容の解決と検証
        3. state更新
        """
        step_start = time.time()
        self.logger.info("Step 1: 運搬業者選択処理開始")
        
        selections: Dict[str, Union[int, str]] = (
            user_input.get("selections", {}) or {}
        )
        resolved_entry_map = self._resolve_and_apply_selections(state, selections)
        selection_summary = self._create_selection_summary(resolved_entry_map)
        
        elapsed_ms = round((time.time() - step_start) * 1000, 2)
        self.logger.info(
            "Step 1: 運搬業者選択処理完了",
            extra={
                "selections_count": len(resolved_entry_map),
                "elapsed_ms": elapsed_ms
            }
        )
        
        payload = {
            "selection_summary": selection_summary,
            "message": "運搬業者選択を受け取りました",
            "step": 1,
            "action": "select_transport",
            "session_id": state.get("session_id"),
        }
        return state, payload
        state: Dict[str, Any], 
        user_input: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """運搬業者選択ハンドラー"""
        selections: Dict[str, Union[int, str]] = (
            user_input.get("selections", {}) or {}
        )
        resolved_entry_map = self._resolve_and_apply_selections(state, selections)
    def finalize_step(self, state: Dict[str, Any]):  # type: ignore[override]
        """
        最終ステップ: ブロック単価計算を実行
        
        処理内容:
        1. ブロック単価計算
        2. 運搬費用計算
        3. 帳票生成
        4. ZIPファイル化
        """
        step_start = time.time()
        self.logger.info("Step 2: 最終計算処理開始（ブロック単価計算）")
        
        result = execute_finalize_step(state)
        
        elapsed_ms = round((time.time() - step_start) * 1000, 2)
        self.logger.info(
            "Step 2: 最終計算処理完了",
            extra={"elapsed_ms": elapsed_ms}
        )
        return result
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
