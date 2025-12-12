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

CSV種別とMV更新の対応:
  - "receive": 将軍速報CSV（flash）と将軍最終CSV（final）の両方に対応
    - mv_receive_daily: final優先、なければflashを使用
    - mv_target_card_per_day: mv_receive_dailyに依存
  - "yard": 将軍ヤードCSV（flash/final）に対応（将来実装）
  - "shipment": 将軍出荷CSV（flash/final）に対応（将来実装）

注意事項:
  - REFRESH CONCURRENTLY には UNIQUE INDEX が必要
  - 既存のデータがない場合、初回更新は CONCURRENTLY を使わない
  - 更新エラーはログに記録するが、アップロード処理全体は失敗させない
  - 複数MV更新時、1つのMV更新が失敗しても残りのMVの更新を継続（2025-12-12修正）
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
    マテリアライズドビュー更新専用リポジトリ
    
    UseCase層から利用される統一インターフェースを提供：
    - refresh_for_csv_type(): csv_type指定でMV更新
    - refresh_for_csv_kind(): csv_kind指定でMV更新（csv_type自動抽出）
    - refresh_for_csv_types(): 複数csv_typeのバッチ更新
    """
    
    # 更新対象のマテリアライズドビュー定義
    # csv_type ごとに更新すべき MV のリスト
    # Note: クォートなしの形式を使用（PostgreSQL標準）
    MV_MAPPINGS = {
        "receive": [
            f"{SCHEMA_MART}.{MV_RECEIVE_DAILY}",  # 日次受入集計MV（基礎データ）
            f"{SCHEMA_MART}.{MV_TARGET_CARD_PER_DAY}",  # 目標カードMV（mv_receive_dailyに依存）
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
    
    @staticmethod
    def extract_csv_type_from_csv_kind(csv_kind: str) -> Optional[str]:
        """
        csv_kind から csv_type（データ方向）を抽出
        
        Args:
            csv_kind: CSV種別（例: 'shogun_flash_receive', 'shogun_final_yard'）
            
        Returns:
            csv_type: データ方向（'receive', 'yard', 'shipment'）、抽出できない場合はNone
        
        Examples:
            >>> MaterializedViewRefresher.extract_csv_type_from_csv_kind('shogun_flash_receive')
            'receive'
            >>> MaterializedViewRefresher.extract_csv_type_from_csv_kind('shogun_final_shipment')
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
            True: MV更新が必要、False: MV更新不要
        
        Note:
            現在は 'receive' のみMV更新対応済み
        """
        supported_types = ['receive']
        
        if csv_type not in supported_types:
            logger.debug(
                f"[MV_REFRESH] csv_type='{csv_type}' does not require MV refresh "
                f"(supported: {supported_types})",
                extra=create_log_context(operation="check_mv_support", csv_type=csv_type)
            )
            return False
        
        return True
    
    def refresh_for_csv_type(self, csv_type: str) -> None:
        """
        指定された csv_type に関連するマテリアライズドビューを更新
        
        Args:
            csv_type: 'receive' / 'yard' / 'shipment'
            
        Raises:
            Exception: MV更新に失敗した場合（呼び出し側でハンドリング推奨）
            
        Note:
            - csv_type='receive' の場合、将軍速報CSV（flash）と将軍最終CSV（final）の両方に対応
            - MVは自動的にfinal版を優先し、なければflash版のデータを使用する
            - MV更新は依存関係の順序で実行（例: mv_receive_daily → mv_target_card_per_day）
        """
        mv_list = self.MV_MAPPINGS.get(csv_type, [])
        
        if not mv_list:
            logger.info(
                "No MV defined for csv_type, skipping refresh",
                extra=create_log_context(operation="refresh_views", csv_type=csv_type)
            )
            return
        
        logger.info(
            f"[MV_REFRESH] Starting refresh for csv_type='{csv_type}' with {len(mv_list)} MV(s)",
            extra=create_log_context(operation="refresh_views", csv_type=csv_type, mv_count=len(mv_list), mv_list=mv_list)
        )
        
        success_count = 0
        failed_mvs = []
        
        for mv_name in mv_list:
            try:
                self._refresh_single_mv(mv_name)
                # 各MV更新後にcommitして、次のMVが最新データを参照できるようにする
                # これにより、依存関係のあるMV（例: mv_target_card_per_day）が
                # 更新済みの基礎MV（例: mv_receive_daily）のデータを確実に参照できる
                self.db.commit()
                logger.debug(
                    f"[MV_REFRESH] Committed after refreshing {mv_name}",
                    extra=create_log_context(operation="refresh_views", mv_name=mv_name)
                )
                success_count += 1
            except Exception as e:
                failed_mvs.append(mv_name)
                logger.error(
                    f"[MV_REFRESH] MV refresh failed: {mv_name}",
                    extra=create_log_context(operation="refresh_views", mv_name=mv_name, error=str(e)),
                    exc_info=True
                )
                # エラー時はロールバックして次のMVの更新を試みる
                self.db.rollback()
                # 個別MVの失敗は記録するが、全体処理は継続
                # 次のMVの更新を試みる
        
        # 全体の結果サマリーをログ出力
        if failed_mvs:
            logger.warning(
                f"[MV_REFRESH] ⚠️ Refresh completed with errors for csv_type='{csv_type}': {success_count}/{len(mv_list)} succeeded",
                extra=create_log_context(
                    operation="refresh_views",
                    csv_type=csv_type,
                    success_count=success_count,
                    failed_count=len(failed_mvs),
                    failed_mvs=failed_mvs
                )
            )
        else:
            logger.info(
                f"[MV_REFRESH] ✅ All MVs refreshed successfully for csv_type='{csv_type}' ({success_count}/{len(mv_list)})",
                extra=create_log_context(
                    operation="refresh_views",
                    csv_type=csv_type,
                    success_count=success_count
                )
            )
    
    def _refresh_single_mv(self, mv_name: str) -> None:
        """
        単一のマテリアライズドビューを更新
        
        Args:
            mv_name: マテリアライズドビュー名（例: 'mart.mv_target_card_per_day'）
            
        Note:
            まずCONCURRENTLYで更新を試み、権限エラーの場合は通常のREFRESHにフォールバック。
            CONCURRENTLY: ロックを最小化（SELECT は可能、UPDATE は待機）、UNIQUE INDEX が必要
            
            ⚠️ 重要: このメソッドはcommit()を呼びません。呼び出し側（refresh_for_csv_type）で
            各MV更新後にcommit()を呼び、依存関係のあるMVが最新データを参照できるようにします。
            通常のREFRESH: ACCESS EXCLUSIVEロック（短時間のロック、SELECT も待機）
            
        Raises:
            Exception: 更新に失敗した場合
              - MVが存在しない場合
              - その他のDB エラー
        """
        try:
            logger.info(
                f"[MV_REFRESH] Refreshing MV: {mv_name}",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name)
            )
            
            # まずCONCURRENTLYで試す
            try:
                sql = text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};")
                self.db.execute(sql)
                # NOTE: commit()はUseCaseレイヤーで実行（トランザクション境界の統一）
                logger.debug(f"[MV_REFRESH] Used CONCURRENTLY for {mv_name}")
            except Exception as concurrent_error:
                # CONCURRENTLYで失敗した場合（権限エラーなど）、通常のREFRESHにフォールバック
                error_msg = str(concurrent_error).lower()
                if "permission denied" in error_msg or "insufficient privilege" in error_msg:
                    logger.warning(
                        f"[MV_REFRESH] CONCURRENTLY failed due to permission, falling back to normal REFRESH for {mv_name}",
                        extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name, fallback_reason="permission")
                    )
                    # 通常のREFRESH（短時間ロック）
                    sql = text(f"REFRESH MATERIALIZED VIEW {mv_name};")
                    self.db.execute(sql)
                    # NOTE: commit()はUseCaseレイヤーで実行
                    logger.debug(f"[MV_REFRESH] Used normal REFRESH for {mv_name}")
                else:
                    # その他のエラーは再raise
                    raise
            
            # 更新後の行数を取得（確認用）
            count_sql = text(f"SELECT COUNT(*) FROM {mv_name};")
            result = self.db.execute(count_sql)
            row_count = result.scalar()
            
            logger.info(
                f"[MV_REFRESH] ✅ MV refresh successful: {mv_name} ({row_count} rows)",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name, row_count=row_count)
            )
            
        except Exception as e:
            # NOTE: rollback()はUseCaseレイヤーで実行（例外は再raiseのみ）
            
            # エラーの種類を特定
            error_msg = str(e).lower()
            if "unique index" in error_msg or "index" in error_msg:
                error_detail = (
                    f"UNIQUE INDEX が存在しない可能性があります。"
                    f"CONCURRENTLY オプションには UNIQUE INDEX が必要です。"
                    f"migration を確認してください。"
                )
            elif "does not exist" in error_msg:
                error_detail = f"マテリアライズドビュー '{mv_name}' が存在しません。"
            else:
                error_detail = f"予期しないエラー: {str(e)}"
            
            logger.error(
                f"[MV_REFRESH] ❌ MV refresh failed: {mv_name} - {error_detail}",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name, error=str(e), error_detail=error_detail),
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
    
    def refresh_for_csv_types(
        self,
        csv_types: List[str],
        operation_name: str = "mv_refresh_batch"
    ) -> None:
        """
        複数の csv_type に対してMV更新を一括実行
        
        Args:
            csv_types: 更新対象の csv_type リスト（例: ['receive', 'shipment']）
            operation_name: ログ用の操作名
        
        Note:
            - 各csv_typeごとに独立して処理（1つ失敗しても他は継続）
            - エラーはログに記録するが、例外は再raiseしない
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
        
        for csv_type in csv_types:
            try:
                logger.info(
                    f"[MV_REFRESH] Processing csv_type='{csv_type}'",
                    extra=create_log_context(operation=operation_name, csv_type=csv_type)
                )
                
                self.refresh_for_csv_type(csv_type)
                
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
                # 例外は再raiseしない（親処理の成功を維持）
    
    def refresh_for_csv_kind(
        self,
        csv_kind: str,
        operation_name: str = "mv_refresh_after_delete"
    ) -> None:
        """
        CSV種別（csv_kind）からcsvタイプを自動抽出してMV更新
        
        Args:
            csv_kind: CSV種別（例: 'shogun_flash_receive', 'shogun_final_receive'）
            operation_name: ログ用の操作名
        
        Note:
            CSV削除時など、csv_kindしか分からない状況で使用。
            内部でcsv_typeを自動抽出し、MV更新必要性を判定します。
        """
        # csv_kind から csv_type を抽出
        csv_type = self.extract_csv_type_from_csv_kind(csv_kind)
        if not csv_type:
            logger.warning(
                f"[MV_REFRESH] Could not extract csv_type from csv_kind='{csv_kind}', "
                f"skipping MV refresh",
                extra=create_log_context(operation=operation_name, csv_kind=csv_kind)
            )
            return
        
        # MV更新が必要かチェック
        if not self.should_refresh_mv_for_csv_type(csv_type):
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
        
        # MV更新実行（エラーハンドリング込み）
        try:
            self.refresh_for_csv_type(csv_type)
            logger.info(
                f"[MV_REFRESH] ✅ Successfully refreshed all MVs after CSV operation (csv_kind={csv_kind}, csv_type={csv_type})",
                extra=create_log_context(operation=operation_name, csv_kind=csv_kind, csv_type=csv_type)
            )
        except Exception as e:
            # MV更新の失敗は警告のみ（親処理自体は成功として扱う）
            logger.error(
                f"[MV_REFRESH] ⚠️ Failed to refresh MVs after CSV operation: {e}",
                extra=create_log_context(operation=operation_name, csv_kind=csv_kind, csv_type=csv_type, error=str(e)),
                exc_info=True
            )
            # 例外は再raiseしない
