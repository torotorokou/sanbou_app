"""
UseCase: CreateForecastJobUseCase

予測ジョブの作成を担当。

設計方針:
  - Port経由でJobRepositoryにアクセス
  - ビジネスロジックはここに集約
  - Domain Servicesでバリデーションロジックを再利用
"""

from datetime import date as date_type

from app.core.domain.models import ForecastJobCreate, ForecastJobResponse, PredictionDTO
from app.core.domain.services import forecasting
from app.core.ports.forecast_port import (
    IForecastJobRepository,
    IForecastQueryRepository,
)


class CreateForecastJobUseCase:
    """
    予測ジョブ作成UseCase

    機能:
      - 予測ジョブをlog.forecast_jobテーブルに登録（status='pending'）
      - ジョブIDを返却し、フロントエンドでポーリング可能にする

    設計方針:
      - 重い予測計算は別プロセス（plan_worker）で実行
      - このUseCaseはジョブ登録のみ担当（責務の分離）
      - Port経由でJobRepositoryにアクセス（DIP: Dependency Inversion Principle）
      - Domain Servicesでビジネスルールを適用
    """

    def __init__(self, job_repo: IForecastJobRepository):
        """
        Args:
            job_repo: 予測ジョブリポジトリのPort実装
        """
        self._job_repo = job_repo

    def execute(self, req: ForecastJobCreate) -> ForecastJobResponse:
        """
        予測ジョブを作成してキューに登録

        処理フロー:
          1. Domain Serviceで日付範囲をバリデーション
          2. job_repo.queue_forecast_job() でジョブをキューに登録
          3. 登録されたジョブIDでジョブ情報を取得
          4. ForecastJobResponse に変換して返却

        Args:
            req: ジョブ作成リクエスト（job_type, target_from, target_to, actor, payload_json）

        Returns:
            ForecastJobResponse: 作成されたジョブ情報（job_id, status='pending'等）

        Raises:
            ValueError: 日付範囲が不正な場合
            RuntimeError: ジョブ作成後の取得に失敗した場合
        """
        # Domain Serviceでバリデーション
        is_valid, error_msg = forecasting.validate_forecast_date_range(
            req.target_from, req.target_to
        )
        if not is_valid:
            raise ValueError(f"Invalid forecast date range: {error_msg}")

        job_id = self._job_repo.queue_forecast_job(
            job_type=req.job_type,
            target_from=req.target_from,
            target_to=req.target_to,
            actor=req.actor or "system",
            payload_json=req.payload_json,
        )

        job = self._job_repo.get_job_by_id(job_id)
        if not job:
            raise RuntimeError(f"Failed to retrieve created job {job_id}")

        return ForecastJobResponse.model_validate(job)


class GetForecastJobStatusUseCase:
    """
    予測ジョブステータス取得UseCase

    機能:
      - ジョブIDからジョブのステータスを取得（フロントエンドでのポーリング用）
      - ステータス: pending, running, completed, failed

    使用例:
      - フロントエンドが5秒ごとにポーリングしてジョブの進捗を確認
      - completed になったら結果取得APIを呼び出す
    """

    def __init__(self, job_repo: IForecastJobRepository):
        """
        Args:
            job_repo: 予測ジョブリポジトリのPort実装
        """
        self._job_repo = job_repo

    def execute(self, job_id: int) -> ForecastJobResponse | None:
        """
        ジョブIDでステータスを取得

        Args:
            job_id: ジョブID

        Returns:
            ForecastJobResponse: ジョブ情報（status, created_at, updated_at等）
            None: ジョブが見つからない場合
        """
        job = self._job_repo.get_job_by_id(job_id)
        if not job:
            return None

        return ForecastJobResponse.model_validate(job)


class GetPredictionsUseCase:
    """
    予測結果取得UseCase

    機能:
      - 指定期間の予測結果を取得
      - Domain Servicesでビジネスルールを適用
    """

    def __init__(self, query_repo: IForecastQueryRepository):
        self._query_repo = query_repo

    def execute(self, from_: date_type, to_: date_type) -> list[PredictionDTO]:
        """
        指定期間の予測結果を取得

        処理フロー:
          1. Domain Serviceで日付範囲をバリデーション
          2. Repositoryから予測データを取得
          3. Domain Serviceでビジネスルールを適用（丸め、補正等）
          4. DTOに変換して返却

        Args:
            from_: 開始日
            to_: 終了日

        Returns:
            List[PredictionDTO]: 予測結果リスト

        Raises:
            ValueError: 日付範囲が不正な場合
        """
        # Domain Serviceでバリデーション
        is_valid, error_msg = forecasting.validate_forecast_date_range(from_, to_)
        if not is_valid:
            raise ValueError(f"Invalid prediction date range: {error_msg}")

        # Repositoryから生データ取得
        raw_predictions = self._query_repo.get_predictions_in_range(from_, to_)

        # Domain Serviceでビジネスルール適用
        adjusted_predictions = forecasting.apply_business_rules_to_predictions(
            raw_predictions
        )

        # DTOに変換
        return [PredictionDTO(**p) for p in adjusted_predictions]
        """
        指定期間の予測結果を取得

        Args:
            from_: 開始日
            to_: 終了日

        Returns:
            List[PredictionDTO]: 予測結果リスト
        """
        return self._query_repo.list_predictions(from_, to_)
