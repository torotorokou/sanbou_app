"""UseCase: BuildTargetCardUseCase

ダッシュボードのターゲットカード表示に必要なデータを取得・構築。

設計方針（Clean Architecture準拠）:
  1. Input/Output DTOを明確に定義
  2. execute(input) -> output の標準形式を採用
  3. バリデーションはInput DTOとDomain Serviceで実施
  4. Port経由でInfra層に依存（依存性逆転）
  5. キャッシュ制御もUseCase層で実施
"""

from app.core.domain.services import target_card
from app.core.ports.dashboard_query_port import IDashboardTargetQuery
from app.core.usecases.dashboard.dto import BuildTargetCardInput, BuildTargetCardOutput
from backend_shared.application.logging import (
    create_log_context,
    get_module_logger,
    log_usecase_execution,
)

logger = get_module_logger(__name__)

# Optional TTL cache for repeated requests
# キャッシュを一時的に無効化（デバッグ用）
# 理由: CSV更新後にフロントエンドが古いデータを表示する問題を解決
# TODO: CSV更新後にキャッシュクリアを自動実行する仕組みを実装後、再度有効化
try:
    from cachetools import TTLCache

    _CACHE: TTLCache = None  # TTLCache(maxsize=512, ttl=3600)  # 一時的に無効化
    logger.info(
        "TTL cache DISABLED for BuildTargetCardUseCase (debugging)",
        extra=create_log_context(operation="init_cache", cache_enabled=False),
    )
except ImportError:
    _CACHE = None  # type: ignore
    logger.info("cachetools not installed, running without TTL cache")


class BuildTargetCardUseCase:
    """
    ターゲットカードデータ取得UseCase

    Features:
    - Port経由でリポジトリにアクセス
    - Optional TTL caching (60s) to reduce duplicate requests
    - Cache can be cleared manually via clear_cache()
    """

    def __init__(self, query: IDashboardTargetQuery):
        self._query = query

    @log_usecase_execution(usecase_name="BuildTargetCard", log_args=True)
    def execute(self, input_dto: BuildTargetCardInput) -> BuildTargetCardOutput:
        """
        ターゲットカードデータを取得・変換

        処理フロー:
          1. Input DTOのバリデーション
          2. Domain Serviceで日付をバリデーション
          3. キャッシュをチェック
          4. Repositoryから生データを取得
          5. Domain Serviceで計算・変換（達成率、差異、警告フラグ等）
          6. キャッシュに格納
          7. Output DTOに変換して返却

        Args:
            input_dto: BuildTargetCardInput

        Returns:
            BuildTargetCardOutput（ターゲット/実績データ + メタ情報）

        Raises:
            ValueError: Input DTOまたは日付が不正な場合
            InfrastructureError: DB接続エラー等（Repository層から伝播）
        """
        # 1. Input DTOのバリデーション
        input_dto.validate()

        # 2. Domain Serviceで日付バリデーション
        is_valid, error_msg = target_card.validate_target_card_date(
            input_dto.requested_date, input_dto.mode
        )
        if not is_valid:
            raise ValueError(f"Invalid target card date: {error_msg}")

        # 3. キャッシュをチェック
        cache_key = (input_dto.requested_date, input_dto.mode)
        if _CACHE is not None and cache_key in _CACHE:
            logger.debug(
                "Cache hit",
                extra=create_log_context(operation="build_target_card", cache_key=str(cache_key)),
            )
            return BuildTargetCardOutput.from_domain(_CACHE[cache_key])

        # 4. Repository経由でデータ取得（最適化クエリ: 1回のSQLで取得）
        raw_row = self._query.get_by_date_optimized(
            target_date=input_dto.requested_date, mode=input_dto.mode
        )

        # 5. Domain Serviceで変換・計算を適用
        # Note: 現在のデータ構造では複数の目標/実績ペア(month/week/day)があるため、
        # transform_target_card_dataの適用は現時点では見送り
        # 将来的には各ペアに対してachievement_rateとvarianceを計算する拡張を検討
        transformed_row = raw_row

        # 6. キャッシュに格納
        if _CACHE is not None:
            _CACHE[cache_key] = transformed_row
            logger.debug(
                "Cached result",
                extra=create_log_context(operation="build_target_card", cache_key=str(cache_key)),
            )

        # 7. Output DTOに変換
        return BuildTargetCardOutput.from_domain(transformed_row)

    @staticmethod
    def clear_cache() -> None:
        """Clear the TTL cache. Useful after CSV updates or data refreshes."""
        if _CACHE is not None:
            _CACHE.clear()
            logger.info("Target card cache cleared")
