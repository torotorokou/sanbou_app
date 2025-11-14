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
        raw_writer: IShogunCsvWriter,
        stg_writer: IShogunCsvWriter,
        csv_config: SyogunCsvConfigLoader,
        validator: CSVValidationResponder,
    ):
        """
        Args:
            raw_writer: raw層へのCSV保存Port実装
            stg_writer: stg層へのCSV保存Port実装
            csv_config: CSV設定ローダー
            validator: CSVバリデーター
        """
        self.raw_writer = raw_writer
        self.stg_writer = stg_writer
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
        
        # 5. raw層への保存（フォーマット済みデータをraw層にも保存）
        raw_result = await self._save_data(self.raw_writer, formatted_dfs, uploaded_files, "raw")
        
        # 6. stg層への保存（フォーマット済みデータ保存）
        stg_result = await self._save_data(self.stg_writer, formatted_dfs, uploaded_files, "stg")
        
        # 7. レスポンス生成（raw + stg両方の結果を統合）
        return self._generate_response(raw_result, stg_result)
    
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
    
    async def _save_data(
        self, 
        writer: IShogunCsvWriter,
        formatted_dfs: Dict[str, pd.DataFrame], 
        uploaded_files: Dict[str, UploadFile],
        layer_name: str
    ) -> Dict[str, dict]:
        """
        フォーマット済みCSVデータをDBに保存（raw層 or stg層）
        
        Args:
            writer: CSV保存用のwriter (raw_writer or stg_writer)
            formatted_dfs: フォーマット済みDataFrame
            uploaded_files: アップロードファイル情報
            layer_name: レイヤー名 ("raw" or "stg")
        
        Returns:
            保存結果の辞書
        """
        result: Dict[str, dict] = {}
        
        for csv_type, df in formatted_dfs.items():
            try:
                saved_count = await run_in_threadpool(writer.save_csv_by_type, csv_type, df)
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "success",
                    "rows_saved": saved_count,
                }
                logger.info(f"Saved {csv_type} to {layer_name} layer: {saved_count} rows")
            except Exception as e:
                logger.error(f"Failed to save {csv_type} to {layer_name} layer: {e}", exc_info=True)
                result[csv_type] = {
                    "filename": uploaded_files[csv_type].filename,
                    "status": "error",
                    "detail": str(e),
                }
        
        return result
    
    def _generate_response(
        self, raw_result: Dict[str, dict], stg_result: Dict[str, dict]
    ) -> SuccessApiResponse | ErrorApiResponse:
        """
        raw層とstg層の保存結果を統合してレスポンスを生成
        
        Args:
            raw_result: raw層への保存結果
            stg_result: stg層への保存結果
            
        Returns:
            統合されたレスポンス
        """
        # stg層の成功判定（主要な保存先）
        all_stg_success = all(r["status"] == "success" for r in stg_result.values())
        
        # 統合結果を生成
        combined_result = {}
        for csv_type in set(list(raw_result.keys()) + list(stg_result.keys())):
            combined_result[csv_type] = {
                "raw": raw_result.get(csv_type, {"status": "not_processed"}),
                "stg": stg_result.get(csv_type, {"status": "not_processed"}),
            }
        
        if all_stg_success:
            total_rows = sum(r["rows_saved"] for r in stg_result.values() if "rows_saved" in r)
            return SuccessApiResponse(
                code="UPLOAD_SUCCESS",
                detail=f"アップロード成功: 合計 {total_rows} 行を保存しました（raw層 + stg層）",
                result=combined_result,
                hint="データベースに保存されました",
            )
        else:
            return ErrorApiResponse(
                code="PARTIAL_SAVE_ERROR",
                detail="一部のファイル保存に失敗しました",
                result=combined_result,
                status_code=500,
            )
