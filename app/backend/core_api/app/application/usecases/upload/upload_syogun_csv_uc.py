"""
UseCase: UploadSyogunCsvUseCase

将軍CSV（receive/yard/shipment）のアップロード処理を担当。
アプリケーションとして「何を・どの順で」行うかを記述。

処理フロー:
  1. CSV読込（DataFrame化）
  2. バリデーション（カラム、日付の一貫性）
  3. フォーマット（型変換、正規化）
  4. DB保存（Adapter経由）
  5. レスポンス生成

設計方針:
  - ビジネスロジックはここに集約（Router には書かない）
  - 外部依存（DB、ファイル等）は Port 経由で注入
  - backend_shared の既存 validator/formatter を活用
"""
import logging
from typing import Dict, Optional
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
import pandas as pd

from backend_shared.infrastructure.config.config_loader import SyogunCsvConfigLoader
from backend_shared.usecases.csv_validator.csv_upload_validator_api import CSVValidationResponder
from backend_shared.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.usecases.csv_formatter.formatter_config import build_formatter_config
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

from app.domain.ports.csv_writer_port import IShogunCsvWriter

logger = logging.getLogger(__name__)


class UploadSyogunCsvUseCase:
    """将軍CSVアップロードのUseCase"""
    
    def __init__(
        self,
        csv_writer: IShogunCsvWriter,
        csv_config: SyogunCsvConfigLoader,
        validator: CSVValidationResponder,
    ):
        """
        Args:
            csv_writer: CSV保存のPort実装（Adapter）
            csv_config: CSV設定ローダー
            validator: CSVバリデーター
        """
        self.csv_writer = csv_writer
        self.csv_config = csv_config
        self.validator = validator
    
    async def execute(
        self,
        receive: Optional[UploadFile],
        yard: Optional[UploadFile],
        shipment: Optional[UploadFile],
    ) -> SuccessApiResponse | ErrorApiResponse:
        """
        将軍CSVアップロード処理を実行
        
        Args:
            receive: 受入一覧CSV
            yard: ヤード一覧CSV
            shipment: 出荷一覧CSV
        
        Returns:
            SuccessApiResponse または ErrorApiResponse
        """
        logger.info("Start syogun CSV upload usecase")
        
        # 入力ファイルの整理
        file_inputs = {"receive": receive, "yard": yard, "shipment": shipment}
        uploaded_files = {k: v for k, v in file_inputs.items() if v and v.filename}
        
        if not uploaded_files:
            return ErrorApiResponse(
                code="NO_FILES",
                detail="少なくとも1つのCSVファイルをアップロードしてください",
                status_code=400
            )
        
        # 1. ファイルタイプ検証（セキュリティ）
        validation_error = self._validate_file_types(uploaded_files)
        if validation_error:
            return validation_error
        
        # 2. CSV読込
        dfs, read_error = await self._read_csv_files(uploaded_files)
        if read_error:
            return read_error
        
        # 3. バリデーション
        validation_error = self._validate_csv_data(dfs, uploaded_files)
        if validation_error:
            return validation_error
        
        # 4. フォーマット
        formatted_dfs, format_error = await self._format_csv_data(dfs)
        if format_error:
            return format_error
        
        # 5. 保存
        result = await self._save_csv_data(formatted_dfs, uploaded_files)
        
        # 6. レスポンス生成
        return self._generate_response(result)
    
    def _validate_file_types(self, uploaded_files: Dict[str, UploadFile]) -> Optional[ErrorApiResponse]:
        """ファイルタイプの検証（MIME type + 拡張子）"""
        ALLOWED_CT = {"text/csv", "application/vnd.ms-excel"}
        
        for k, f in uploaded_files.items():
            if not f.filename:
                continue
            name = f.filename.lower()
            if not (name.endswith(".csv") or (f.content_type and f.content_type in ALLOWED_CT)):
                return ErrorApiResponse(
                    code="INVALID_FILE_TYPE",
                    detail=f"{k}: CSVファイルではありません（拡張子またはMIMEタイプを確認）",
                    status_code=400,
                )
        return None
    
    async def _read_csv_files(
        self, uploaded_files: Dict[str, UploadFile]
    ) -> tuple[Dict[str, pd.DataFrame], Optional[ErrorApiResponse]]:
        """CSVファイルをDataFrameに読み込み"""
        dfs: Dict[str, pd.DataFrame] = {}
        
        async def _read_one(uf: UploadFile) -> pd.DataFrame:
            """pandas.read_csv を別スレッドで実行（asyncイベントループをブロックしない）"""
            uf.file.seek(0)
            def _read_csv(bio):
                return pd.read_csv(bio, encoding="utf-8")
            return await run_in_threadpool(_read_csv, uf.file)
        
        for csv_type, uf in uploaded_files.items():
            try:
                df = await _read_one(uf)
                dfs[csv_type] = df
                logger.info(f"Loaded {csv_type} CSV: {len(df)} rows, {len(df.columns)} cols")
            except Exception as e:
                logger.error(f"Failed to parse {csv_type} CSV: {e}")
                return {}, ErrorApiResponse(
                    code="CSV_PARSE_ERROR",
                    detail=f"{csv_type}のCSVを読み込めません: {str(e)}",
                    status_code=400
                )
        
        return dfs, None
    
    def _validate_csv_data(
        self, dfs: Dict[str, pd.DataFrame], uploaded_files: Dict[str, UploadFile]
    ) -> Optional[ErrorApiResponse]:
        """CSVデータのバリデーション"""
        # カラム検証
        validation_error = self.validator.validate_columns(dfs, uploaded_files)
        if validation_error:
            return validation_error
        
        # 日付存在チェック
        date_exists_error = self.validator.validate_denpyou_date_exists(dfs, uploaded_files)
        if date_exists_error:
            return date_exists_error
        
        # 複数ファイルの場合、日付一貫性チェック
        if len(dfs) > 1:
            date_consistency_error = self.validator.validate_denpyou_date_consistency(dfs)
            if date_consistency_error:
                return date_consistency_error
        
        return None
    
    async def _format_csv_data(
        self, dfs: Dict[str, pd.DataFrame]
    ) -> tuple[Dict[str, pd.DataFrame], Optional[ErrorApiResponse]]:
        """CSVデータのフォーマット（型変換、正規化）"""
        formatted_dfs: Dict[str, pd.DataFrame] = {}
        
        for csv_type, df in dfs.items():
            try:
                config = build_formatter_config(self.csv_config, csv_type)
                formatter = CSVFormatterFactory.get_formatter(csv_type, config)
                # CPU-bound operation: 別スレッドで実行
                formatted_df = await run_in_threadpool(formatter.format, df)
                formatted_dfs[csv_type] = formatted_df
                logger.info(f"Formatted {csv_type}: {len(formatted_df)} rows")
            except Exception as e:
                logger.error(f"Failed to format {csv_type}: {e}", exc_info=True)
                return {}, ErrorApiResponse(
                    code="FORMAT_ERROR",
                    detail=f"{csv_type}のフォーマット失敗: {str(e)}",
                    status_code=400,
                    hint="カラム名や型変換エラーの可能性があります",
                )
        
        return formatted_dfs, None
    
    async def _save_csv_data(
        self, formatted_dfs: Dict[str, pd.DataFrame], uploaded_files: Dict[str, UploadFile]
    ) -> Dict[str, dict]:
        """フォーマット済みCSVデータをDBに保存"""
        result: Dict[str, dict] = {}
        
        for csv_type, df in formatted_dfs.items():
            try:
                saved_count = await run_in_threadpool(self.csv_writer.save_csv_by_type, csv_type, df)
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "success",
                    "rows_saved": saved_count,
                }
                logger.info(f"Saved {csv_type}: {saved_count} rows")
            except Exception as e:
                logger.error(f"Failed to save {csv_type} to DB: {e}", exc_info=True)
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "error",
                    "detail": str(e),
                }
        
        return result
    
    def _generate_response(self, result: Dict[str, dict]) -> SuccessApiResponse | ErrorApiResponse:
        """保存結果からレスポンスを生成"""
        all_success = all(r["status"] == "success" for r in result.values())
        
        if all_success:
            total_rows = sum(r["rows_saved"] for r in result.values())
            return SuccessApiResponse(
                code="UPLOAD_SUCCESS",
                detail=f"アップロード成功: 合計 {total_rows} 行を保存しました",
                result=result,
                hint="データベースに保存されました",
            )
        else:
            return ErrorApiResponse(
                code="PARTIAL_SAVE_ERROR",
                detail="一部のファイル保存に失敗しました",
                result=result,
                status_code=500,
            )
