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
from app.infra.adapters.upload.raw_data_repository import RawDataRepository

logger = logging.getLogger(__name__)


class UploadSyogunCsvUseCase:
    """将軍CSVアップロードのUseCase"""
    
    def __init__(
        self,
        raw_writer: IShogunCsvWriter,
        stg_writer: IShogunCsvWriter,
        csv_config: SyogunCsvConfigLoader,
        validator: CSVValidationResponder,
        raw_data_repo: Optional[RawDataRepository] = None,
    ):
        """
        Args:
            raw_writer: raw層へのCSV保存Port実装
            stg_writer: stg層へのCSV保存Port実装
            csv_config: CSV設定ローダー
            validator: CSVバリデーター
            raw_data_repo: log.upload_file へのアップロードログ保存用リポジトリ
        """
        self.raw_writer = raw_writer
        self.stg_writer = stg_writer
        self.csv_config = csv_config
        self.validator = validator
        self.raw_data_repo = raw_data_repo
    
    async def execute(
        self,
        receive: Optional[UploadFile],
        yard: Optional[UploadFile],
        shipment: Optional[UploadFile],
        file_type: str = "FLASH",  # 'FLASH' or 'FINAL'
        uploaded_by: Optional[str] = None,
    ) -> SuccessApiResponse | ErrorApiResponse:
        """
        将軍CSVアップロード処理を実行
        
        Args:
            receive: 受入一覧CSV
            yard: ヤード一覧CSV
            shipment: 出荷一覧CSV
            file_type: 'FLASH' または 'FINAL'
            uploaded_by: アップロードユーザー名
        
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
        
        # log.upload_file にアップロードログを作成（csv_type 単位）
        upload_file_ids: Dict[str, int] = {}
        if self.raw_data_repo:
            for csv_type, uf in uploaded_files.items():
                try:
                    content = await uf.read()
                    file_hash = self.raw_data_repo.calculate_file_hash(content)
                    uf.file.seek(0)  # read後はシークを戻す
                    
                    file_id = self.raw_data_repo.create_upload_file(
                        csv_type=csv_type,
                        file_name=uf.filename or f"{csv_type}.csv",
                        file_hash=file_hash,
                        file_type=file_type,
                        file_size_bytes=len(content),
                        uploaded_by=uploaded_by,
                    )
                    upload_file_ids[csv_type] = file_id
                    logger.info(f"Created log.upload_file entry for {csv_type}: id={file_id}")
                except Exception as e:
                    logger.error(f"Failed to create upload log for {csv_type}: {e}")
                    # ログ作成失敗でも処理は継続（ログは補助的なもの）
        
        # 1. ファイルタイプ検証（セキュリティ）
        validation_error = self._validate_file_types(uploaded_files)
        if validation_error:
            self._mark_all_as_failed(upload_file_ids, "File type validation failed")
            return validation_error
        
        # 2. CSV読込
        dfs, read_error = await self._read_csv_files(uploaded_files)
        if read_error:
            self._mark_all_as_failed(upload_file_ids, "CSV parse error")
            return read_error
        
        # 3. バリデーション
        validation_error = self._validate_csv_data(dfs, uploaded_files)
        if validation_error:
            self._mark_all_as_failed(upload_file_ids, "CSV validation failed")
            return validation_error
        
        # 4. raw層への保存（生データ = 空行削除のみ、日本語カラム名のまま）
        raw_cleaned_dfs = await self._clean_empty_rows(dfs)
        raw_result = await self._save_data(self.raw_writer, raw_cleaned_dfs, uploaded_files, "raw")
        
        # 5. フォーマット（stg層用）
        formatted_dfs, format_error = await self._format_csv_data(dfs)
        if format_error:
            self._mark_all_as_failed(upload_file_ids, "CSV format error")
            return format_error
        
        # 6. stg層への保存（フォーマット済みデータ = 英語カラム名、型変換済み）
        stg_result = await self._save_data(self.stg_writer, formatted_dfs, uploaded_files, "stg")
        
        # 7. log.upload_file のステータスを更新
        self._update_upload_logs(upload_file_ids, formatted_dfs, stg_result)
        
        # 8. レスポンス生成（raw + stg 両方の結果を統合）
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
    
    async def _clean_empty_rows(
        self, dfs: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        空行除去のみ（raw層保存用）
        日本語カラム名のまま、型変換なし
        """
        cleaned_dfs: Dict[str, pd.DataFrame] = {}
        
        for csv_type, df in dfs.items():
            original_row_count = len(df)
            df_cleaned = df.dropna(how='all')
            empty_rows_removed = original_row_count - len(df_cleaned)
            
            if empty_rows_removed > 0:
                logger.info(f"[raw] Removed {empty_rows_removed} empty rows from {csv_type} CSV")
            
            cleaned_dfs[csv_type] = df_cleaned
        
        return cleaned_dfs
    
    async def _format_csv_data(
        self, dfs: Dict[str, pd.DataFrame]
    ) -> tuple[Dict[str, pd.DataFrame], Optional[ErrorApiResponse]]:
        """
        CSVデータのフォーマット（stg層保存用）
        - 空行除去
        - カラム名を英語に変換
        - 型変換、正規化
        """
        formatted_dfs: Dict[str, pd.DataFrame] = {}
        
        for csv_type, df in dfs.items():
            try:
                # 空行除去（全カラムがNULLの行を削除）
                original_row_count = len(df)
                df_cleaned = df.dropna(how='all')
                empty_rows_removed = original_row_count - len(df_cleaned)
                
                if empty_rows_removed > 0:
                    logger.info(f"[stg] Removed {empty_rows_removed} empty rows from {csv_type} CSV")
                
                config = build_formatter_config(self.csv_config, csv_type)
                formatter = CSVFormatterFactory.get_formatter(csv_type, config)
                # CPU-bound operation: 別スレッドで実行
                formatted_df = await run_in_threadpool(formatter.format, df_cleaned)
                formatted_dfs[csv_type] = formatted_df
                logger.info(f"[stg] Formatted {csv_type}: {len(formatted_df)} rows")
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
    
    def _mark_all_as_failed(self, upload_file_ids: Dict[str, int], error_msg: str) -> None:
        """全アップロードログを失敗としてマーク"""
        if not self.raw_data_repo:
            return
        for csv_type, file_id in upload_file_ids.items():
            try:
                self.raw_data_repo.update_upload_status(
                    file_id=file_id,
                    status="failed",
                    error_message=error_msg,
                )
            except Exception as e:
                logger.error(f"Failed to update upload log for {csv_type}: {e}")
    
    def _update_upload_logs(
        self,
        upload_file_ids: Dict[str, int],
        formatted_dfs: Dict[str, pd.DataFrame],
        stg_result: Dict[str, dict],
    ) -> None:
        """
        log.upload_file のステータスを更新
        
        Args:
            upload_file_ids: csv_type -> upload_file.id のマッピング
            formatted_dfs: csv_type -> DataFrame のマッピング
            stg_result: stg層への保存結果
        """
        if not self.raw_data_repo:
            return
        
        for csv_type, file_id in upload_file_ids.items():
            try:
                result_info = stg_result.get(csv_type, {})
                is_success = result_info.get("status") == "success"
                
                if is_success:
                    # 成功: row_count を実際の行数で更新
                    row_count = result_info.get("rows_saved", len(formatted_dfs.get(csv_type, [])))
                    self.raw_data_repo.update_upload_status(
                        file_id=file_id,
                        status="success",
                        row_count=row_count,
                    )
                    logger.info(f"Marked {csv_type} upload as success: {row_count} rows")
                else:
                    # 失敗: エラーメッセージを記録
                    error_detail = result_info.get("detail", "Unknown error")
                    self.raw_data_repo.update_upload_status(
                        file_id=file_id,
                        status="failed",
                        error_message=error_detail,
                    )
                    logger.warning(f"Marked {csv_type} upload as failed: {error_detail}")
            except Exception as e:
                logger.error(f"Failed to update upload log for {csv_type}: {e}")
    
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

