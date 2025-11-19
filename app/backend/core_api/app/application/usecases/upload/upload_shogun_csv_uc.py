"""
UseCase: UploadShogunCsvUseCase

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
  - 非同期アップロード対応: start_async_upload で受付のみ行い、重い処理はバックグラウンドタスクへ
"""
import logging
from typing import Dict, Optional, List, Any
from fastapi import UploadFile, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
import pandas as pd

from backend_shared.infrastructure.config.config_loader import ShogunCsvConfigLoader
from backend_shared.usecases.csv_validator.csv_upload_validator_api import CSVValidationResponder
from backend_shared.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.usecases.csv_formatter.formatter_config import build_formatter_config
from backend_shared.adapters.presentation import SuccessApiResponse, ErrorApiResponse

from app.domain.ports.csv_writer_port import IShogunCsvWriter
from app.infra.adapters.upload.raw_data_repository import RawDataRepository
from app.infra.adapters.materialized_view.materialized_view_refresher import MaterializedViewRefresher

logger = logging.getLogger(__name__)


class UploadShogunCsvUseCase:
    """将軍CSVアップロードのUseCase"""
    
    def __init__(
        self,
        raw_writer: IShogunCsvWriter,
        stg_writer: IShogunCsvWriter,
        csv_config: ShogunCsvConfigLoader,
        validator: CSVValidationResponder,
        raw_data_repo: Optional[RawDataRepository] = None,
        mv_refresher: Optional[MaterializedViewRefresher] = None,
    ):
        """
        Args:
            raw_writer: raw層へのCSV保存Port実装
            stg_writer: stg層へのCSV保存Port実装
            csv_config: CSV設定ローダー
            validator: CSVバリデーター
            raw_data_repo: log.upload_file へのアップロードログ保存用リポジトリ
            mv_refresher: マテリアライズドビュー更新用リポジトリ（Optional）
        """
        self.raw_writer = raw_writer
        self.stg_writer = stg_writer
        self.csv_config = csv_config
        self.validator = validator
        self.raw_data_repo = raw_data_repo
        self.mv_refresher = mv_refresher
    
    async def start_async_upload(
        self,
        background_tasks: BackgroundTasks,
        receive: Optional[UploadFile],
        yard: Optional[UploadFile],
        shipment: Optional[UploadFile],
        file_type: str = "FLASH",
        uploaded_by: Optional[str] = None,
    ) -> SuccessApiResponse | ErrorApiResponse:
        """
        非同期アップロードを開始（軽量バリデーション→即座に受付完了レスポンス→重い処理はバックグラウンド）
        
        Args:
            background_tasks: FastAPI BackgroundTasks
            receive: 受入一覧CSV
            yard: ヤード一覧CSV
            shipment: 出荷一覧CSV
            file_type: 'FLASH' または 'FINAL'
            uploaded_by: アップロードユーザー名
        
        Returns:
            受付成功: upload_file_ids を含む SuccessApiResponse（即座）
            バリデーションエラー: ErrorApiResponse
        """
        logger.info("Start async shogun CSV upload (acceptance phase)")
        
        # 入力ファイルの整理
        file_inputs = {"receive": receive, "yard": yard, "shipment": shipment}
        uploaded_files = {k: v for k, v in file_inputs.items() if v and v.filename}
        
        if not uploaded_files:
            return ErrorApiResponse(
                code="NO_FILES",
                detail="少なくとも1つのCSVファイルをアップロードしてください",
                status_code=400
            )
        
        # 1. 軽量バリデーション（拡張子、MIME type）
        validation_error = self._validate_file_types(uploaded_files)
        if validation_error:
            return validation_error
        
        # 2. 重複チェック＋log.upload_fileへの登録（pending状態）
        upload_file_ids: Dict[str, int] = {}
        duplicate_files: Dict[str, Dict[str, Any]] = {}
        
        if self.raw_data_repo:
            for csv_type, uf in uploaded_files.items():
                try:
                    content = await uf.read()
                    file_hash = self.raw_data_repo.calculate_file_hash(content)
                    uf.file.seek(0)
                    
                    # 重複チェック
                    duplicate_info = self.raw_data_repo.check_duplicate_upload(
                        csv_type=csv_type,
                        file_hash=file_hash,
                        file_type=file_type,
                        file_name=uf.filename,
                        file_size_bytes=len(content),
                    )
                    
                    if duplicate_info:
                        duplicate_files[csv_type] = duplicate_info
                        logger.warning(f"Duplicate file detected: {csv_type}")
                    else:
                        # 重複でない場合のみログ作成
                        file_id = self.raw_data_repo.create_upload_file(
                            csv_type=csv_type,
                            file_name=uf.filename or f"{csv_type}.csv",
                            file_hash=file_hash,
                            file_type=file_type,
                            file_size_bytes=len(content),
                            uploaded_by=uploaded_by,
                        )
                        upload_file_ids[csv_type] = file_id
                        logger.info(f"Created upload_file entry (pending): {csv_type} id={file_id}")
                except Exception as e:
                    logger.error(f"Failed to process {csv_type}: {e}")
                    return ErrorApiResponse(
                        code="UPLOAD_PREPARATION_ERROR",
                        detail=f"{csv_type}の処理に失敗しました: {str(e)}",
                        status_code=500,
                    )
        
        # 重複ファイルがある場合は409を返す
        if duplicate_files:
            duplicate_details = []
            for csv_type, info in duplicate_files.items():
                duplicate_details.append({
                    "csv_type": csv_type,
                    "file_name": info["file_name"],
                    "uploaded_at": info["uploaded_at"].isoformat() if info.get("uploaded_at") else None,
                    "uploaded_by": info.get("uploaded_by"),
                    "match_type": info["match_type"],
                })
            
            return ErrorApiResponse(
                code="DUPLICATE_FILE",
                detail=f"同じファイルが既にアップロード済みです: {', '.join(duplicate_files.keys())}",
                status_code=409,
                result={"duplicates": duplicate_details}
            )
        
        # 3. バックグラウンドタスクに重い処理を登録
        #    UploadFileはメモリ上にバッファされているので、バックグラウンドでも読み取り可能
        #    ただし、ファイル内容を bytes で保持してバックグラウンドに渡す
        file_contents = {}
        for csv_type, uf in uploaded_files.items():
            uf.file.seek(0)
            file_contents[csv_type] = {
                "content": await uf.read(),
                "filename": uf.filename,
            }
        
        background_tasks.add_task(
            self._process_csv_in_background,
            file_contents=file_contents,
            upload_file_ids=upload_file_ids,
            file_type=file_type,
        )
        
        # 4. 即座に受付完了レスポンスを返す
        return SuccessApiResponse(
            code="UPLOAD_ACCEPTED",
            detail=f"CSVアップロードを受け付けました。処理中です。",
            result={
                "upload_file_ids": upload_file_ids,
                "status": "processing",
            },
            hint="処理完了まで数秒～数十秒かかる場合があります。",
        )
    
    async def _process_csv_in_background(
        self,
        file_contents: Dict[str, Dict[str, Any]],
        upload_file_ids: Dict[str, int],
        file_type: str,
    ) -> None:
        """
        バックグラウンドで実行される重い処理
        
        Args:
            file_contents: csv_type -> {"content": bytes, "filename": str}
            upload_file_ids: csv_type -> upload_file.id
            file_type: 'FLASH' or 'FINAL'
        """
        try:
            logger.info(f"Background processing started for upload_file_ids: {upload_file_ids}")
            
            # ステータスを processing に更新
            if self.raw_data_repo:
                for csv_type, file_id in upload_file_ids.items():
                    self.raw_data_repo.update_upload_status(file_id=file_id, status="processing")
            
            # CSV読込
            import io
            dfs: Dict[str, pd.DataFrame] = {}
            for csv_type, file_info in file_contents.items():
                try:
                    content_io = io.BytesIO(file_info["content"])
                    df = pd.read_csv(content_io, encoding="utf-8")
                    dfs[csv_type] = df
                    logger.info(f"[BG] Loaded {csv_type}: {len(df)} rows")
                except Exception as e:
                    logger.error(f"[BG] Failed to parse {csv_type}: {e}")
                    self._mark_all_as_failed(upload_file_ids, f"CSV parse error: {csv_type}")
                    return
            
            # バリデーション（ファイル名用のダミーUploadFile作成）
            dummy_files = {}
            for csv_type, file_info in file_contents.items():
                class DummyUploadFile:
                    def __init__(self, filename):
                        self.filename = filename
                dummy_files[csv_type] = DummyUploadFile(file_info["filename"])
            
            validation_error = self._validate_csv_data(dfs, dummy_files)
            if validation_error:
                logger.error(f"[BG] Validation failed: {validation_error.detail}")
                self._mark_all_as_failed(upload_file_ids, f"Validation error: {validation_error.detail}")
                return
            
            # source_row_no 追加
            dfs_with_row_no = self._add_source_row_numbers(dfs)
            
            # raw層保存
            raw_cleaned_dfs = await self._clean_empty_rows(dfs_with_row_no)
            raw_result = await self._save_data(
                self.raw_writer, raw_cleaned_dfs, dummy_files, "raw", upload_file_ids
            )
            
            # フォーマット
            formatted_dfs, format_error = await self._format_csv_data(dfs_with_row_no)
            if format_error:
                logger.error(f"[BG] Format failed: {format_error.detail}")
                self._mark_all_as_failed(upload_file_ids, f"Format error: {format_error.detail}")
                return
            
            # stg層保存
            stg_result = await self._save_data(
                self.stg_writer, formatted_dfs, dummy_files, "stg", upload_file_ids
            )
            
            # ステータス更新
            self._update_upload_logs(upload_file_ids, formatted_dfs, stg_result)
            
            logger.info(f"[BG] Background processing completed successfully for: {list(upload_file_ids.keys())}")
            
        except Exception as e:
            logger.exception(f"[BG] Unexpected error in background processing: {e}")
            self._mark_all_as_failed(upload_file_ids, f"Internal error: {str(e)}")
    
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
        logger.info("Start shogun CSV upload usecase")
        
        # 入力ファイルの整理
        file_inputs = {"receive": receive, "yard": yard, "shipment": shipment}
        uploaded_files = {k: v for k, v in file_inputs.items() if v and v.filename}
        
        if not uploaded_files:
            return ErrorApiResponse(
                code="NO_FILES",
                detail="少なくとも1つのCSVファイルをアップロードしてください",
                status_code=400
            )
        
        # log.upload_file への登録前に重複チェック
        duplicate_files: Dict[str, Dict[str, Any]] = {}
        if self.raw_data_repo:
            for csv_type, uf in uploaded_files.items():
                try:
                    content = await uf.read()
                    file_hash = self.raw_data_repo.calculate_file_hash(content)
                    uf.file.seek(0)  # read後はシークを戻す
                    
                    # 重複チェック（成功済みファイルのみ）
                    duplicate_info = self.raw_data_repo.check_duplicate_upload(
                        csv_type=csv_type,
                        file_hash=file_hash,
                        file_type=file_type,
                        file_name=uf.filename,
                        file_size_bytes=len(content),
                        # row_count は CSV読込後に判明するため、ここでは None
                    )
                    
                    if duplicate_info:
                        duplicate_files[csv_type] = duplicate_info
                        logger.warning(
                            f"Duplicate file detected: {csv_type} - "
                            f"existing_id={duplicate_info['id']}, "
                            f"match_type={duplicate_info['match_type']}"
                        )
                except Exception as e:
                    logger.error(f"Failed to check duplicate for {csv_type}: {e}")
        
        # 重複ファイルが検出された場合、409 Conflict を返す
        if duplicate_files:
            duplicate_details = []
            for csv_type, info in duplicate_files.items():
                duplicate_details.append({
                    "csv_type": csv_type,
                    "file_name": info["file_name"],
                    "uploaded_at": info["uploaded_at"].isoformat() if info.get("uploaded_at") else None,
                    "uploaded_by": info.get("uploaded_by"),
                    "match_type": info["match_type"],
                })
            
            return ErrorApiResponse(
                code="DUPLICATE_FILE",
                detail=f"同じファイルが既にアップロード済みです: {', '.join(duplicate_files.keys())}",
                status_code=409,
                result={"duplicates": duplicate_details}
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
        
        # 4. source_row_no の採番(1-indexed)
        dfs_with_row_no = self._add_source_row_numbers(dfs)
        logger.info(f"[TRACE] dfs_with_row_no has {len(dfs_with_row_no)} items: {list(dfs_with_row_no.keys())}")
        
        # 5. raw層への保存(生データ = 空行削除のみ、日本語カラム名のまま)
        raw_cleaned_dfs = await self._clean_empty_rows(dfs_with_row_no)
        logger.info(f"[TRACE] raw_cleaned_dfs has {len(raw_cleaned_dfs)} items: {list(raw_cleaned_dfs.keys())}")
        raw_result = await self._save_data(
            self.raw_writer, raw_cleaned_dfs, uploaded_files, "raw", upload_file_ids
        )
        
        # 6. フォーマット（stg層用）
        formatted_dfs, format_error = await self._format_csv_data(dfs_with_row_no)
        if format_error:
            self._mark_all_as_failed(upload_file_ids, "CSV format error")
            return format_error
        
        # 7. stg層への保存（フォーマット済みデータ = 英語カラム名、型変換済み）
        stg_result = await self._save_data(
            self.stg_writer, formatted_dfs, uploaded_files, "stg", upload_file_ids
        )
        
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
    
    def _add_source_row_numbers(self, dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        各DataFrameに source_row_no カラムを追加（1-indexed）
        
        Args:
            dfs: csv_type -> DataFrame のマッピング
            
        Returns:
            source_row_no カラムが追加された DataFrame のマッピング
        """
        result_dfs = {}
        for csv_type, df in dfs.items():
            df_copy = df.copy()
            # 1-indexed で行番号を付与（CSVのヘッダー行の次が1行目）
            df_copy['source_row_no'] = range(1, len(df_copy) + 1)
            result_dfs[csv_type] = df_copy
            logger.debug(f"Added source_row_no to {csv_type}: 1 to {len(df_copy)}")
        
        return result_dfs
    
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
        - tracking columns (upload_file_id, source_row_no) を保持
        """
        formatted_dfs: Dict[str, pd.DataFrame] = {}
        
        # tracking columns のカラム名定義（保守性向上のため定数化）
        TRACKING_COLUMNS = ['upload_file_id', 'source_row_no']
        
        for csv_type, df in dfs.items():
            try:
                logger.info(f"[DEBUG] Starting format for {csv_type}: {len(df)} rows, columns={list(df.columns)[:10]}...")
                
                # 1. tracking columns を一時保存（存在する場合のみ）
                tracking_data = {}
                for col in TRACKING_COLUMNS:
                    if col in df.columns:
                        tracking_data[col] = df[col].copy()
                        logger.info(f"[DEBUG] Preserved tracking column '{col}' for {csv_type}: sample values={df[col].head(3).tolist()}")
                
                # 2. 空行除去（全カラムがNULLの行を削除）
                original_row_count = len(df)
                df_cleaned = df.dropna(how='all')
                empty_rows_removed = original_row_count - len(df_cleaned)
                
                if empty_rows_removed > 0:
                    logger.info(f"[stg] Removed {empty_rows_removed} empty rows from {csv_type} CSV")
                    
                    # 空行削除後、tracking columns のインデックスも調整
                    for col, data in tracking_data.items():
                        tracking_data[col] = data.loc[df_cleaned.index]
                
                # 3. フォーマット処理（業務カラムの変換）
                config = build_formatter_config(self.csv_config, csv_type)
                formatter = CSVFormatterFactory.get_formatter(csv_type, config)
                logger.info(f"[DEBUG] Before formatter for {csv_type}: {len(df_cleaned)} rows, columns={list(df_cleaned.columns)[:10]}...")
                # CPU-bound operation: 別スレッドで実行
                formatted_df = await run_in_threadpool(formatter.format, df_cleaned)
                logger.info(f"[DEBUG] After formatter for {csv_type}: {len(formatted_df)} rows, columns={list(formatted_df.columns)[:10]}...")
                
                # 4. tracking columns を復元（フォーマット後のDataFrameに再結合）
                for col, data in tracking_data.items():
                    if len(formatted_df) == len(data):
                        # 行数が一致する場合はそのまま代入
                        formatted_df[col] = data.values
                        logger.info(f"[DEBUG] Restored tracking column '{col}' to formatted {csv_type}: sample values={formatted_df[col].head(3).tolist()}")
                    else:
                        # 行数が不一致の場合は警告（通常は発生しないはず）
                        logger.error(
                            f"[DEBUG] Row count mismatch for {csv_type}: "
                            f"formatted={len(formatted_df)}, tracking={len(data)}. "
                            f"Skipping restoration of '{col}'"
                        )
                
                formatted_dfs[csv_type] = formatted_df
                logger.info(f"[stg] Formatted {csv_type}: {len(formatted_df)} rows")
                logger.info(f"[DEBUG] Final columns for {csv_type}: {list(formatted_df.columns)}")
                logger.info(f"[DEBUG] Has upload_file_id: {'upload_file_id' in formatted_df.columns}, Has source_row_no: {'source_row_no' in formatted_df.columns}")
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
        layer_name: str,
        upload_file_ids: Optional[Dict[str, int]] = None,
    ) -> Dict[str, dict]:
        """
        フォーマット済みCSVデータをDBに保存（raw層 or stg層）
        
        Args:
            writer: CSV保存用のwriter (raw_writer or stg_writer)
            formatted_dfs: フォーマット済みDataFrame
            uploaded_files: アップロードファイル情報
            layer_name: レイヤー名 ("raw" or "stg")
            upload_file_ids: log.upload_file.id のマッピング（csv_type -> file_id）
        
        Returns:
            保存結果の辞書
        """
        result: Dict[str, dict] = {}
        
        for csv_type, df in formatted_dfs.items():
            try:
                logger.info(f"[DEBUG] Saving {csv_type} to {layer_name}: {len(df)} rows, columns={list(df.columns)[:15]}")
                
                # upload_file_id を DataFrame に追加
                df_to_save = df.copy()
                if upload_file_ids and csv_type in upload_file_ids:
                    file_id = upload_file_ids[csv_type]
                    df_to_save['upload_file_id'] = file_id
                    logger.info(f"[DEBUG] Added upload_file_id={file_id} to {csv_type} ({layer_name}), now columns={list(df_to_save.columns)[:15]}")
                
                logger.info(f"[DEBUG] Before save {layer_name}: upload_file_id={'upload_file_id' in df_to_save.columns}, source_row_no={'source_row_no' in df_to_save.columns}")
                logger.info(f"[DEBUG] Sample row for {csv_type}: {df_to_save.head(1).to_dict('records')}")
                
                saved_count = await run_in_threadpool(writer.save_csv_by_type, csv_type, df_to_save)
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
        log.upload_file のステータスを更新し、必要に応じてマテリアライズドビューを更新
        
        Args:
            upload_file_ids: csv_type -> upload_file.id のマッピング
            formatted_dfs: csv_type -> DataFrame のマッピング
            stg_result: stg層への保存結果
        """
        if not self.raw_data_repo:
            return
        
        # マテビュー更新が必要な csv_type のリスト
        mv_refresh_needed = []
        
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
                    
                    # ★ 受入CSVの成功時のみマテビュー更新リストに追加
                    # （現状、MVが定義されているのは receive のみ）
                    if csv_type == "receive":
                        mv_refresh_needed.append(csv_type)
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
        
        # ★ マテリアライズドビューの更新（受入CSV成功時のみ）
        self._refresh_materialized_views(mv_refresh_needed)
    
    def _refresh_materialized_views(self, csv_types: List[str]) -> None:
        """
        指定された csv_type に関連するマテリアライズドビューを更新
        
        Args:
            csv_types: 更新対象の csv_type リスト（例: ['receive', 'shipment']）
            
        Note:
            - エラーが発生してもアップロード処理全体は失敗させない
            - ログに記録して処理を継続
        """
        if not self.mv_refresher:
            logger.debug("MaterializedViewRefresher not injected, skipping MV refresh")
            return
        
        if not csv_types:
            logger.debug("No csv_types provided for MV refresh")
            return
        
        for csv_type in csv_types:
            try:
                logger.info(f"Starting materialized view refresh for csv_type='{csv_type}'")
                self.mv_refresher.refresh_for_csv_type(csv_type)
                logger.info(f"Successfully refreshed materialized views for csv_type='{csv_type}'")
            except Exception as e:
                # マテビュー更新失敗はログに記録するが、アップロード処理は成功扱い
                logger.error(
                    f"Failed to refresh materialized views for csv_type='{csv_type}': {e}",
                    exc_info=True
                )
                # 呼び出し側には影響を与えない（アップロード自体は成功している）
    
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

