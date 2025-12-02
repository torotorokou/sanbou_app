"""
Materialized View Refresher

マテリアライズドビュー（MV）の更新を担当する専用リポジトリ。
Clean Architecture の Infra 層に配置。

責務:
  - REFRESH MATERIALIZED VIEW の実行
  - ログ出力と例外処理
  - 複数MVの一括更新サポート

設計方針:
  - 単一責任の原則（SRP）: MV更新のみに特化
  - 疎結合: UseCase から DI 経由で注入
  - 拡張性: 新しい MV を容易に追加可能
"""
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)


class MaterializedViewRefresher:
    """マテリアライズドビュー更新専用リポジトリ"""
    
    # 更新対象のマテリアライズドビュー定義
    # csv_type ごとに更新すべき MV のリスト
    MV_MAPPINGS = {
        "receive": [
            "mart.mv_target_card_per_day",
            # 将来的に追加する受入関連MVをここに列挙
        ],
        "shipment": [
            # 出荷関連MVをここに追加（将来）
        ],
        "yard": [
            # ヤード関連MVをここに追加（将来）
        ],
    }
    
    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def refresh_for_csv_type(self, csv_type: str) -> None:
        """
        指定された csv_type に関連するマテリアライズドビューを更新
        
        Args:
            csv_type: 'receive' / 'yard' / 'shipment'
            
        Raises:
            Exception: MV更新に失敗した場合（呼び出し側でハンドリング推奨）
        """
        mv_list = self.MV_MAPPINGS.get(csv_type, [])
        
        if not mv_list:
            logger.info(
                "No MV defined, skipping refresh",
                extra=create_log_context(operation="refresh_views", csv_type=csv_type)
            )
            return
        
        logger.info(
            "Starting MV refresh",
            extra=create_log_context(operation="refresh_views", csv_type=csv_type, mv_count=len(mv_list), mv_list=mv_list)
        )
        
        for mv_name in mv_list:
            try:
                self._refresh_single_mv(mv_name)
            except Exception as e:
                logger.error(
                    "MV refresh failed",
                    extra=create_log_context(operation="refresh_views", mv_name=mv_name, error=str(e)),
                    exc_info=True
                )
                # 個別MVの失敗は記録するが、全体処理は継続
                # 呼び出し側で必要に応じて再 raise を判断
                raise
    
    def _refresh_single_mv(self, mv_name: str) -> None:
        """
        単一のマテリアライズドビューを更新
        
        Args:
            mv_name: マテリアライズドビュー名（例: 'mart.mv_target_card_per_day'）
            
        Note:
            CONCURRENTLY オプションを使用してロックを最小化
            （UNIQUE INDEX が必要）
        """
        try:
            logger.info(
                "Refreshing MV",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name)
            )
            
            # REFRESH MATERIALIZED VIEW CONCURRENTLY を実行
            # CONCURRENTLY: ロックを最小化（SELECT は可能、UPDATE は待機）
            # UNIQUE INDEX が必要（既に migration で作成済み）
            sql = text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};")
            
            self.db.execute(sql)
            self.db.commit()
            
            logger.info(
                "MV refresh successful",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name)
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "MV refresh error",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name, error=str(e)),
                exc_info=True
            )
            raise
    
    def refresh_all_receive_mvs(self) -> None:
        """
        受入関連の全マテリアライズドビューを更新
        
        Convenience method for explicit receive MV refresh.
        """
        self.refresh_for_csv_type("receive")
    
    def list_available_mvs(self, csv_type: Optional[str] = None) -> List[str]:
        """
        利用可能なマテリアライズドビューのリストを取得
        
        Args:
            csv_type: 特定の csv_type に絞る場合（None の場合は全て）
            
        Returns:
            MV名のリスト
        """
        if csv_type:
            return self.MV_MAPPINGS.get(csv_type, [])
        
        # 全MVを flatten して返す
        all_mvs = []
        for mvs in self.MV_MAPPINGS.values():
            all_mvs.extend(mvs)
        return all_mvs
