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
"""
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import (
    SCHEMA_MART,
    MV_RECEIVE_DAILY,
    MV_TARGET_CARD_PER_DAY,
    fq,
)

logger = get_module_logger(__name__)


class MaterializedViewRefresher:
    """マテリアライズドビュー更新専用リポジトリ"""
    
    # 更新対象のマテリアライズドビュー定義
    # csv_type ごとに更新すべき MV のリスト
    # backend_shared.db.names の定数を使用してタイポ防止
    MV_MAPPINGS = {
        "receive": [
            fq(SCHEMA_MART, MV_RECEIVE_DAILY),  # 日次受入集計MV（基礎データ）
            fq(SCHEMA_MART, MV_TARGET_CARD_PER_DAY),  # 目標カードMV（mv_receive_dailyに依存）
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
            
        Note:
            - csv_type='receive' の場合、将軍速報CSV（flash）と将軍最終CSV（final）の両方に対応
            - MVは自動的にfinal版を優先し、なければflash版のデータを使用する
        """
        mv_list = self.MV_MAPPINGS.get(csv_type, [])
        
        if not mv_list:
            logger.info(
                "No MV defined, skipping refresh",
                extra=create_log_context(operation="refresh_views", csv_type=csv_type)
            )
            return
        
        logger.info(
            f"[MV_REFRESH] Starting refresh for csv_type='{csv_type}'",
            extra=create_log_context(operation="refresh_views", csv_type=csv_type, mv_count=len(mv_list), mv_list=mv_list)
        )
        
        success_count = 0
        failed_mvs = []
        
        for mv_name in mv_list:
            try:
                self._refresh_single_mv(mv_name)
                success_count += 1
            except Exception as e:
                failed_mvs.append(mv_name)
                logger.error(
                    f"[MV_REFRESH] MV refresh failed: {mv_name}",
                    extra=create_log_context(operation="refresh_views", mv_name=mv_name, error=str(e)),
                    exc_info=True
                )
                # 個別MVの失敗は記録するが、全体処理は継続
                # 呼び出し側で必要に応じて再 raise を判断
                raise
        
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
            CONCURRENTLY オプションを使用してロックを最小化
            （UNIQUE INDEX が必要）
            
        Raises:
            Exception: 更新に失敗した場合
              - UNIQUE INDEX が存在しない場合
              - MVが存在しない場合
              - その他のDB エラー
        """
        try:
            logger.info(
                f"[MV_REFRESH] Refreshing MV: {mv_name}",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name)
            )
            
            # REFRESH MATERIALIZED VIEW CONCURRENTLY を実行
            # CONCURRENTLY: ロックを最小化（SELECT は可能、UPDATE は待機）
            # UNIQUE INDEX が必要（既に migration で作成済み）
            sql = text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name};")
            
            self.db.execute(sql)
            self.db.commit()
            
            # 更新後の行数を取得（確認用）
            count_sql = text(f"SELECT COUNT(*) FROM {mv_name};")
            result = self.db.execute(count_sql)
            row_count = result.scalar()
            
            logger.info(
                f"[MV_REFRESH] ✅ MV refresh successful: {mv_name} ({row_count} rows)",
                extra=create_log_context(operation="refresh_single_mv", mv_name=mv_name, row_count=row_count)
            )
            
        except Exception as e:
            self.db.rollback()
            
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
