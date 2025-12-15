"""
CSV Forecast Result Repository

CSVファイルから予測結果を読み込むリポジトリ実装。

設計方針:
- CSVファイルのパスは設定から取得
- ファイルが存在しない場合はNoneを返す（例外は投げない）
- CSV解析エラーは例外として投げる
"""
import logging
from pathlib import Path
from typing import Optional
from datetime import date
import pandas as pd

from app.core.domain.forecast_result import ForecastResult, ForecastResultRecord

logger = logging.getLogger(__name__)


class CsvForecastResultRepository:
    """
    CSVファイルから予測結果を読み込むリポジトリ
    
    責務:
    - 指定されたCSVファイルの読み込み
    - DataFrame → ForecastResult への変換
    - ファイル不在時の適切な処理
    
    Example:
        >>> repo = CsvForecastResultRepository(
        ...     daily_csv_pattern="/backend/output/tplus1_pred_*.csv",
        ...     output_dir=Path("/backend/output"),
        ... )
        >>> result = repo.get_daily_result()
    """
    
    def __init__(
        self,
        output_dir: Path,
        gamma_output_dir: Path,
        daily_csv_pattern: str = "tplus1_pred_*.csv",
        monthly_csv_name: str = "blended_future_forecast.csv",
        weekly_csv_name: str = "weekly_allocated_forecast.csv",
        landing_14d_pattern: str = "prediction_14d.csv",
        landing_21d_pattern: str = "prediction_21d.csv",
    ):
        """
        Args:
            output_dir: 出力ディレクトリ（日次・着地用）
            gamma_output_dir: Gammaモデル出力ディレクトリ（月次・週次用）
            daily_csv_pattern: 日次予測CSVのパターン
            monthly_csv_name: 月次予測CSVの名前
            weekly_csv_name: 週次予測CSVの名前
            landing_14d_pattern: 14日着地予測CSVのパターン
            landing_21d_pattern: 21日着地予測CSVのパターン
        """
        self.output_dir = output_dir
        self.gamma_output_dir = gamma_output_dir
        self.daily_csv_pattern = daily_csv_pattern
        self.monthly_csv_name = monthly_csv_name
        self.weekly_csv_name = weekly_csv_name
        self.landing_14d_pattern = landing_14d_pattern
        self.landing_21d_pattern = landing_21d_pattern
    
    def _find_latest_csv(self, directory: Path, pattern: str) -> Optional[Path]:
        """
        パターンに一致する最新のCSVファイルを見つける
        
        Args:
            directory: 検索ディレクトリ
            pattern: ファイル名パターン
        
        Returns:
            Path: 見つかったファイルパス（存在しない場合はNone）
        """
        try:
            files = list(directory.glob(pattern))
            if not files:
                return None
            # 最新のファイルを返す（mtime順）
            return max(files, key=lambda p: p.stat().st_mtime)
        except Exception as e:
            logger.warning(f"Error finding CSV: {e}")
            return None
    
    def _read_csv_to_result(
        self,
        csv_path: Path,
        model_type: str,
        date_column: str = "date",
        value_column: str = "total_pred",
        lower_column: Optional[str] = "total_pred_low_1sigma",
        upper_column: Optional[str] = "total_pred_high_1sigma",
        p50_column: Optional[str] = "p50",
        p90_column: Optional[str] = "p90",
    ) -> ForecastResult:
        """
        CSVファイルを読み込んでForecastResultに変換
        
        Args:
            csv_path: CSVファイルパス
            model_type: モデルタイプ
            date_column: 日付カラム名
            value_column: 予測値カラム名
            lower_column: 信頼区間下限カラム名
            upper_column: 信頼区間上限カラム名
            p50_column: 中央値カラム名
            p90_column: 90パーセンタイルカラム名
        
        Returns:
            ForecastResult: 予測結果
        
        Raises:
            ValueError: CSVの解析に失敗
        """
        try:
            df = pd.read_csv(csv_path)
            
            if df.empty:
                logger.warning(f"Empty CSV file: {csv_path}")
                return ForecastResult(
                    model_type=model_type,
                    records=[],
                    csv_path=str(csv_path),
                )
            
            # 必須カラムの確認
            if date_column not in df.columns or value_column not in df.columns:
                raise ValueError(
                    f"Required columns not found. Available: {list(df.columns)}"
                )
            
            # レコードに変換
            records = []
            for _, row in df.iterrows():
                # 日付の解析
                try:
                    date_value = pd.to_datetime(row[date_column]).date()
                except Exception as e:
                    logger.warning(f"Invalid date format: {row[date_column]}, {e}")
                    continue
                
                record = ForecastResultRecord(
                    date=date_value,
                    predicted_value=float(row[value_column]),
                    confidence_lower=float(row[lower_column]) if lower_column and lower_column in df.columns else None,
                    confidence_upper=float(row[upper_column]) if upper_column and upper_column in df.columns else None,
                    p50=float(row[p50_column]) if p50_column and p50_column in df.columns else None,
                    p90=float(row[p90_column]) if p90_column and p90_column in df.columns else None,
                    raw_data=row.to_dict(),  # 全カラムを保持
                )
                records.append(record)
            
            # 生成日時を取得（ファイルのmtime）
            generated_at = date.fromtimestamp(csv_path.stat().st_mtime)
            
            return ForecastResult(
                model_type=model_type,
                generated_at=generated_at,
                records=records,
                csv_path=str(csv_path),
            )
            
        except Exception as e:
            logger.error(f"Failed to read CSV {csv_path}: {e}", exc_info=True)
            raise ValueError(f"Failed to read CSV: {e}") from e
    
    def get_daily_result(self) -> Optional[ForecastResult]:
        """日次予測結果を取得（t+1/t+7）"""
        csv_path = self._find_latest_csv(self.output_dir, self.daily_csv_pattern)
        if not csv_path:
            logger.info(f"Daily forecast CSV not found in {self.output_dir}")
            return None
        
        logger.info(f"Reading daily forecast from {csv_path}")
        return self._read_csv_to_result(
            csv_path=csv_path,
            model_type="daily",
            date_column="date",
            value_column="total_pred",
            lower_column="total_pred_low_1sigma",
            upper_column="total_pred_high_1sigma",
            p50_column="p50",
            p90_column="p90",
        )
    
    def get_monthly_result(self) -> Optional[ForecastResult]:
        """月次予測結果を取得（Gamma Recency + Blend）"""
        csv_path = self.gamma_output_dir / self.monthly_csv_name
        if not csv_path.exists():
            logger.info(f"Monthly forecast CSV not found: {csv_path}")
            return None
        
        logger.info(f"Reading monthly forecast from {csv_path}")
        return self._read_csv_to_result(
            csv_path=csv_path,
            model_type="monthly",
            date_column="year_month",
            value_column="blended_pred",
            lower_column="blended_pred_minus_sigma",
            upper_column="blended_pred_plus_sigma",
        )
    
    def get_weekly_result(self) -> Optional[ForecastResult]:
        """週次予測結果を取得（週次配分）"""
        csv_path = self.gamma_output_dir / self.weekly_csv_name
        if not csv_path.exists():
            logger.info(f"Weekly forecast CSV not found: {csv_path}")
            return None
        
        logger.info(f"Reading weekly forecast from {csv_path}")
        return self._read_csv_to_result(
            csv_path=csv_path,
            model_type="weekly",
            date_column="week_start_date",
            value_column="weekly_forecast_value",
            lower_column="weekly_forecast_value_minus_sigma",
            upper_column="weekly_forecast_value_plus_sigma",
        )
    
    def get_landing_result(self, day: int = 14) -> Optional[ForecastResult]:
        """月次着地予測結果を取得（14日/21日）"""
        pattern = self.landing_14d_pattern if day == 14 else self.landing_21d_pattern
        csv_path = self._find_latest_csv(self.output_dir, pattern)
        
        if not csv_path:
            logger.info(f"Landing forecast CSV not found (day={day}) in {self.output_dir}")
            return None
        
        logger.info(f"Reading landing forecast from {csv_path}")
        return self._read_csv_to_result(
            csv_path=csv_path,
            model_type=f"landing_{day}d",
            date_column="year_month",
            value_column="Y_pred",
            lower_column="Y_low_68",
            upper_column="Y_high_68",
        )
