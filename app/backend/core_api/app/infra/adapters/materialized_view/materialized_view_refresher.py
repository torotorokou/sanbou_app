"""
Materialized View Refresher (Simplified)

マテリアライズドビュー（MV）の更新を担当するシンプルなリポジトリ。
Clean Architecture の Infra 層に配置。

設計方針:
  - シンプル: 各MV更新は独立した操作
  - 確実性: 各MV更新後にセッションをflush
  - 保守性: 最小限のコードで明確な動作

CSV種別とMV更新の対応:
  - "receive": mv_receive_daily → mv_target_card_per_day の順で更新
  - "yard": 将来実装
  - "shipment": 将来実装

重要: 
  - mv_target_card_per_dayはmv_receive_dailyに依存するため、
    必ずmv_receive_dailyを先に更新してから更新する
  - 各MV更新後にセッションをflushして変更を確定
"""
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import (
    SCHEMA_MART,
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
)

logger = get_module_logger(__name__)


class MaterializedViewRefresher:
    """
    マテリアライズドビュー更新リポジトリ（シンプル版）
    
    主要メソッド:
    - refresh_for_csv_type(): csv_type指定でMV更新
    - refresh_for_csv_kind(): csv_kind指定でMV更新（削除時用）
    """
    
    # csv_type ごとに更新すべき MV のリスト（順序重要！）
    MV_MAPPINGS = {
        "receive": [
            f"{SCHEMA_MART}.{MV_RECEIVE_DAILY}",      # 1. 基礎MV（先に更新）
            f"{SCHEMA_MART}.{MV_TARGET_CARD_PER_DAY}", # 2. 依存MV（後で更新）
        ],
        "shipment": [],  # 将来実装
        "yard": [],       # 将来実装
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def refresh_for_csv_type(self, csv_type: str, auto_commit: bool = True) -> None:
        """
        指定されたcsv_typeに関連する全MVを順番に更新
        
        Args:
            csv_type: 'receive' / 'yard' / 'shipment'
            auto_commit: 各MV更新後にcommit()するか（デフォルト: True）
        
        Note:
            - MVは定義された順序で更新（依存関係を考慮）
            - 1つのMV更新が失敗しても、残りのMVは更新を試みる
            - auto_commit=Trueの場合、各MV更新後にcommitして
              依存MVが最新データを参照できるようにする
        """
        mv_list = self.MV_MAPPINGS.get(csv_type, [])
        if not mv_list:
            logger.info(f"[MV_REFRESH] No MVs defined for csv_type='{csv_type}'")
            return
        
        logger.info(
            f"[MV_REFRESH] 🔄 Starting refresh for csv_type='{csv_type}' ({len(mv_list)} MVs)",
            extra=create_log_context(
                operation="refresh_for_csv_type",
                csv_type=csv_type,
                mv_count=len(mv_list),
                mv_list=mv_list
            )
        )
        
        success_count = 0
        for mv_name in mv_list:
            try:
                self._refresh_mv(mv_name)
                # 各MV更新後にcommitして、依存MVが最新データを参照できるようにする
                if auto_commit:
                    self.db.commit()
                success_count += 1
            except Exception as e:
                logger.error(
                    f"[MV_REFRESH] ❌ Failed to refresh {mv_name}: {e}",
                    extra=create_log_context(operation="refresh_mv", mv_name=mv_name, error=str(e)),
                    exc_info=True
                )
                if auto_commit:
                    self.db.rollback()
                # 失敗しても次のMVの更新を続行
        
        if success_count == len(mv_list):
            logger.info(
                f"[MV_REFRESH] ✅ All {success_count} MVs refreshed successfully for csv_type='{csv_type}'",
                extra=create_log_context(operation="refresh_for_csv_type", csv_type=csv_type, success_count=success_count)
            )
        else:
            logger.warning(
                f"[MV_REFRESH] ⚠️ {success_count}/{len(mv_list)} MVs refreshed for csv_type='{csv_type}'",
                extra=create_log_context(operation="refresh_for_csv_type", csv_type=csv_type, success_count=success_count, total=len(mv_list))
            )
    
    def _refresh_mv(self, mv_name: str) -> None:
        """
        単一のMVを更新（内部メソッド）
        
        Args:
            mv_name: 完全修飾MV名（例: 'mart.mv_receive_daily'）
        
        Note:
            - まずCONCURRENTLYを試み、失敗したら通常のREFRESHにフォールバック
        """
        logger.info(f"[MV_REFRESH] Refreshing {mv_name}...")
        
        try:
            # CONCURRENTLY: ロックを最小化、UNIQUE INDEXが必要
            sql = text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name}")
            self.db.execute(sql)
        except Exception as e:
            error_str = str(e).lower()
            # 権限エラーまたはUNIQUE INDEXなしの場合、通常のREFRESHにフォールバック
            if any(x in error_str for x in ["permission", "privilege", "unique", "concurrent"]):
                logger.warning(f"[MV_REFRESH] Falling back to normal REFRESH for {mv_name}")
                sql = text(f"REFRESH MATERIALIZED VIEW {mv_name}")
                self.db.execute(sql)
            else:
                raise
        
        # 更新後の行数をログ出力
        count_result = self.db.execute(text(f"SELECT COUNT(*) FROM {mv_name}"))
        row_count = count_result.scalar()
        
        logger.info(
            f"[MV_REFRESH] ✅ {mv_name} refreshed ({row_count} rows)",
            extra=create_log_context(operation="refresh_mv", mv_name=mv_name, row_count=row_count)
        )
    
    def refresh_for_csv_kind(self, csv_kind: str, operation_name: str = "mv_refresh_after_csv_operation") -> None:
        """
        csv_kindからcsv_typeを抽出してMV更新（CSV削除時用）
        
        Args:
            csv_kind: CSV種別（例: 'shogun_flash_receive', 'shogun_final_receive'）
            operation_name: ログ用の操作名
        """
        csv_type = self._extract_csv_type(csv_kind)
        if not csv_type:
            logger.debug(f"[MV_REFRESH] No MV refresh needed for csv_kind='{csv_kind}'")
            return
        
        logger.info(
            f"[MV_REFRESH] CSV operation detected: csv_kind='{csv_kind}' → csv_type='{csv_type}'",
            extra=create_log_context(operation=operation_name, csv_kind=csv_kind, csv_type=csv_type)
        )
        
        try:
            self.refresh_for_csv_type(csv_type)
        except Exception as e:
            # MV更新失敗はログに記録するが、呼び出し元の処理は失敗させない
            logger.error(
                f"[MV_REFRESH] ❌ MV refresh failed for csv_kind='{csv_kind}': {e}",
                extra=create_log_context(operation=operation_name, csv_kind=csv_kind, error=str(e)),
                exc_info=True
            )
    
    def _extract_csv_type(self, csv_kind: str) -> Optional[str]:
        """
        csv_kindからcsv_typeを抽出
        
        Args:
            csv_kind: 例: 'shogun_flash_receive', 'shogun_final_shipment'
        
        Returns:
            csv_type: 'receive', 'yard', 'shipment', またはNone
        """
        # 形式: shogun_(flash|final)_(receive|yard|shipment)
        parts = csv_kind.split('_')
        if len(parts) >= 3:
            csv_type = parts[-1]  # 最後の部分を取得
            if csv_type in self.MV_MAPPINGS:
                return csv_type
        return None
    
    # ===== 後方互換性のためのメソッド =====
    
    def refresh_all_receive_mvs(self) -> None:
        """受入関連の全MVを更新（後方互換性用）"""
        self.refresh_for_csv_type("receive")
    
    @staticmethod
    def extract_csv_type_from_csv_kind(csv_kind: str) -> Optional[str]:
        """静的メソッド版のcsv_type抽出（後方互換性用）"""
        parts = csv_kind.split('_')
        if len(parts) >= 3:
            csv_type = parts[-1]
            if csv_type in ['receive', 'yard', 'shipment']:
                return csv_type
        return None
    
    @staticmethod
    def should_refresh_mv_for_csv_type(csv_type: str) -> bool:
        """csv_typeがMV更新対象かどうかを判定（後方互換性用）"""
        return csv_type in ['receive']  # 現在はreceiveのみ対応
