"""
マテリアライズドビュー更新のヘルパークラス

UseCase間で共通化されたMV更新ロジックを提供します。
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend_shared.application.logging import create_log_context, get_module_logger
from app.infra.adapters.materialized_view.materialized_view_refresher import (
    MaterializedViewRefresher,
)

logger = get_module_logger(__name__)


class MaterializedViewRefreshHelper:
    """
    マテリアライズドビュー更新の共通ロジックを提供するヘルパークラス
    
    UseCase間でMV更新処理を統一し、保守性を向上させます。
    """
    
    @staticmethod
    def extract_csv_type_from_csv_kind(csv_kind: str) -> Optional[str]:
        """
        csv_kind から csv_type（データ方向）を抽出
        
        Args:
            csv_kind: CSV種別（例: 'shogun_flash_receive', 'shogun_final_yard'）
            
        Returns:
            csv_type: データ方向（'receive', 'yard', 'shipment'）
                     抽出できない場合は None
        
        Examples:
            >>> extract_csv_type_from_csv_kind('shogun_flash_receive')
            'receive'
            >>> extract_csv_type_from_csv_kind('shogun_final_shipment')
            'shipment'
        """
        parts = csv_kind.split('_')
        if len(parts) >= 3:
            csv_type = parts[2]  # receive / yard / shipment
            if csv_type in ['receive', 'yard', 'shipment']:
                return csv_type
        
        logger.warning(
            f"[MV_REFRESH] Unexpected csv_kind format: '{csv_kind}', "
            f"expected format: 'shogun_(flash|final)_(receive|yard|shipment)'",
            extra=create_log_context(operation="extract_csv_type", csv_kind=csv_kind)
        )
        return None
    
    @staticmethod
    def should_refresh_mv_for_csv_type(csv_type: str) -> bool:
        """
        指定された csv_type に対してMV更新が必要かを判定
        
        Args:
            csv_type: データ方向（'receive', 'yard', 'shipment'）
            
        Returns:
            True: MV更新が必要
            False: MV更新不要
        
        Note:
            現在は 'receive' のみMV更新対応済み
            将来的に 'yard', 'shipment' も対応可能
        """
        # 現在は受入CSV（receive）のみMV更新対応
        supported_types = ['receive']
        
        if csv_type not in supported_types:
            logger.debug(
                f"[MV_REFRESH] csv_type='{csv_type}' does not require MV refresh "
                f"(supported: {supported_types})",
                extra=create_log_context(operation="check_mv_support", csv_type=csv_type)
            )
            return False
        
        return True
    
    @staticmethod
    def refresh_mv_for_csv_types(
        db: Session,
        csv_types: List[str],
        operation_name: str = "mv_refresh"
    ) -> None:
        """
        指定された csv_type リストに対してMV更新を実行
        
        Args:
            db: データベースセッション
            csv_types: 更新対象の csv_type リスト（例: ['receive']）
            operation_name: ログ用の操作名（デフォルト: 'mv_refresh'）
        
        Note:
            - エラーが発生しても例外は再raiseせず、ログに記録のみ
            - 各csv_typeごとに独立して処理（1つ失敗しても他は継続）
            - アップロード/削除処理の成功には影響しない
        """
        if not csv_types:
            logger.debug(
                "[MV_REFRESH] No csv_types provided, skipping MV refresh",
                extra=create_log_context(operation=operation_name)
            )
            return
        
        logger.info(
            f"[MV_REFRESH] Starting MV refresh for {len(csv_types)} csv_type(s): {csv_types}",
            extra=create_log_context(operation=operation_name, csv_types=csv_types)
        )
        
        mv_refresher = MaterializedViewRefresher(db)
        
        for csv_type in csv_types:
            try:
                logger.info(
                    f"[MV_REFRESH] Processing csv_type='{csv_type}'",
                    extra=create_log_context(operation=operation_name, csv_type=csv_type)
                )
                
                mv_refresher.refresh_for_csv_type(csv_type)
                
                logger.info(
                    f"[MV_REFRESH] ✅ Successfully refreshed MVs for csv_type='{csv_type}'",
                    extra=create_log_context(
                        operation=operation_name,
                        csv_type=csv_type,
                        status="success"
                    )
                )
            except Exception as e:
                # MV更新失敗はログに記録するが、呼び出し元の処理は継続
                logger.error(
                    f"[MV_REFRESH] ⚠️ Failed to refresh MVs for csv_type='{csv_type}': {e}",
                    extra=create_log_context(
                        operation=operation_name,
                        csv_type=csv_type,
                        status="error",
                        error=str(e)
                    ),
                    exc_info=True
                )
                # 例外は再raiseしない（アップロード/削除処理自体は成功している）
    
    @staticmethod
    def refresh_mv_for_csv_kind(
        db: Session,
        csv_kind: str,
        operation_name: str = "mv_refresh_after_delete"
    ) -> None:
        """
        CSV種別（csv_kind）からcsvタイプを抽出し、MV更新を実行
        
        Args:
            db: データベースセッション
            csv_kind: CSV種別（例: 'shogun_flash_receive'）
            operation_name: ログ用の操作名（デフォルト: 'mv_refresh_after_delete'）
        
        Note:
            CSV削除時など、csv_kindしか分からない状況で使用します。
        """
        # csv_kind から csv_type を抽出
        csv_type = MaterializedViewRefreshHelper.extract_csv_type_from_csv_kind(csv_kind)
        if not csv_type:
            logger.warning(
                f"[MV_REFRESH] Could not extract csv_type from csv_kind='{csv_kind}', "
                f"skipping MV refresh",
                extra=create_log_context(operation=operation_name, csv_kind=csv_kind)
            )
            return
        
        # MV更新が必要かチェック
        if not MaterializedViewRefreshHelper.should_refresh_mv_for_csv_type(csv_type):
            return
        
        logger.info(
            f"[MV_REFRESH] CSV operation for csv_kind='{csv_kind}' (csv_type='{csv_type}'), "
            f"refreshing materialized views...",
            extra=create_log_context(
                operation=operation_name,
                csv_kind=csv_kind,
                csv_type=csv_type
            )
        )
        
        # MV更新実行
        MaterializedViewRefreshHelper.refresh_mv_for_csv_types(
            db=db,
            csv_types=[csv_type],
            operation_name=operation_name
        )
