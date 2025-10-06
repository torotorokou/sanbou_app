# --- 標準ライブラリ ---
import os
from typing import Annotated
import pandas as pd

# --- FastAPI関連 ---
from fastapi import APIRouter, UploadFile, File, status

# --- アプリ設定・定数 ---
from app.local_config.api_constants import SYOGUN_CSV_ROUTE
from backend_shared.infrastructure.config.paths import SAVE_DIR_TEMP

# --- ユーティリティ ---
from backend_shared.adapters.presentation.response_utils import api_response
from app.api.utils.csv_processor import CSVProcessor

# --- 設定ローダー ---
from backend_shared.infrastructure.config.config_loader import SyogunCsvConfigLoader

# --- CSVアップロード関連サービス ---
from backend_shared.usecases.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)
from app.api.services.csv_upload.storage import CSVUploadTempStorage, CSVUploadSQL
from app.api.services.csv_upload.rename import rename_for_sql

# --- CSVフォーマット関連 ---
from backend_shared.usecases.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.usecases.csv_formatter.formatter_config import build_formatter_config

# --- データベース関連 ---
from app.api.services.deduplicator import Deduplicator
from app.db.database import get_engine

# --- ルーター定義 ---
router = APIRouter()
os.makedirs(SAVE_DIR_TEMP, exist_ok=True)


# --- 統括サービス ---
class CSVImportService:
    def __init__(self, file_inputs: dict[str, UploadFile]):
        """
        CSVImportServiceの初期化。
        ファイル入力情報を元に、必要なヘッダー情報やバリデータ、ストレージなどをセットアップします。
        """
        self.processor = CSVProcessor()  # CSVファイルの読み込み・処理用
        self.config_loader = SyogunCsvConfigLoader()  # 設定ファイルのローダー

        # ファイル種別ごとに必要なヘッダー情報を取得
        self.required_columns = {
            name: self.config_loader.get_expected_headers(name)
            for name in file_inputs.keys()
        }

        self.validator = CSVValidationResponder(
            self.required_columns
        )  # バリデーション用
        self.storage = CSVUploadTempStorage()  # 一時保存用

    def _format_csv_dataframe(self, name: str, df):
        """
        指定されたファイル種別・DataFrameを、設定に従って整形（フォーマット変換・不要な列の削除など）します。
        Args:
            name (str): ファイル種別（例：shipment, receive, yard）
            df (DataFrame): 読み込んだCSVデータ
        Returns:
            DataFrame: 整形済みのデータ
        """
        config = build_formatter_config(self.config_loader, name)
        formatter = CSVFormatterFactory.get_formatter(name, config)
        return formatter.format(df)

    def _extract_new_rows_from_db(self, rename_dfs, deduplicator, date_col):
        """
        データベースに既に存在するデータと重複していない新規データのみ抽出します。
        Args:
            rename_dfs (dict): SQL保存用にヘッダー名を変更したDataFrame群
            deduplicator (Deduplicator): 重複チェック用サービス
            date_col (str): 伝票日付のカラム名
        Returns:
            dict: 新規データのみのDataFrame群
        """
        df_only_new = {}
        for name, df in rename_dfs.items():
            # ファイル種別ごとにユニークキーを取得し、重複行を除外
            unique_en_keys = self.config_loader.get_unique_en_keys(name)
            df_only_new[name] = deduplicator.extract_new_rows(
                df_new=df,
                table_name=name,
                unique_keys=unique_en_keys,
                date_col=date_col,
            )
        return df_only_new

    def _save_new_rows_to_db(self, df_only_new, sql_saver, schema):
        """
        新規データのみデータベースに保存します。
        Args:
            df_only_new (dict): 新規データのみのDataFrame群
            sql_saver (CSVUploadSQL): SQL保存サービス
            schema (str): 保存先スキーマ名
        """
        for name, df_new in df_only_new.items():
            table_name = name
            # DataFrameを指定スキーマ・テーブルに保存
            sql_saver.save_dataframe(df_new, schema=schema, table_name=table_name)

    async def process_upload(self, file_inputs: dict[str, UploadFile]):
        """
        アップロードされたCSVファイル群を検証・整形し、データベース・一時保存ディレクトリへ保存する一連の処理。
        各ステップごとに分かりやすいコメントを記載。
        Args:
            file_inputs (dict): アップロードされたファイル群
        Returns:
            dict: APIレスポンス
        """
        # 1. ファイルが選択されているかチェック（空ファイルチェック）
        if missing := self.validator.check_missing_file(file_inputs):
            # ファイル未選択時はエラーを返す
            return api_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                status_str="error",
                code="MISSING_FILE",
                detail=f"{missing}ファイルが選択されていません。",
            )

        # 2. CSVファイルを読み込む（UploadFile → pandas.DataFrame）
        dfs = {}
        for name, file in file_inputs.items():
            # 各ファイルを非同期でDataFrameに変換
            df = await self.processor.read_csv_file(file)
            dfs[name] = df

        # 3. 必須カラムが揃っているかチェック
        if res := self.validator.validate_columns(dfs, file_inputs):
            # 必須カラムが不足している場合はエラー
            return res

        # 4. 伝票日付カラムが存在するかチェック
        if res := self.validator.validate_denpyou_date_exists(dfs, file_inputs):
            # 伝票日付が無い場合はエラー
            return res

        # 5. 伝票日付が全ファイルで一致しているかチェック
        # if res := self.validator.validate_denpyou_date_consistency(dfs):
        #     # 伝票日付が一致しない場合はエラー
        #     return res

        # 6. CSVデータを整形（フォーマット変換・不要な列の削除など）
        formatted_dfs = {}
        for name, df in dfs.items():
            # ファイル種別ごとに整形
            formatted_dfs[name] = self._format_csv_dataframe(name, df)

        # 7. SQL保存用にヘッダー名を変更（日本語→英語など）
        rename_dfs = {}
        for name, df in formatted_dfs.items():
            # DB保存用にヘッダー名を変換
            rename_dfs[name] = rename_for_sql(name, df, self.config_loader)

        # 8. データベースに既に存在するデータと重複していないかチェック
        db_engine = get_engine()
        schema = "raw_temp"
        deduplicator = Deduplicator(engine=db_engine, schema=schema)
        date_col = "slip_date"  # 伝票日付のカラム名
        # 新規データのみ抽出
        df_only_new = self._extract_new_rows_from_db(rename_dfs, deduplicator, date_col)

        # 9. 新規データのみデータベースに保存
        if any(not df.empty for df in df_only_new.values()):
            # 1つでも新規データがあれば保存処理
            sql_saver = CSVUploadSQL(engine=db_engine)
            schema = "raw_temp"
            self._save_new_rows_to_db(df_only_new, sql_saver, schema)
        else:
            return api_response(
                status_code=status.HTTP_200_OK,
                status_str="warning",
                code="NO_NEW_DATA",
                detail="新規データはありませんでした。",
            )

        # 10. 一時保存ディレクトリにも保存（SQL保存とは別管理）
        self.storage.save_to_temp(
            dfs=rename_dfs, file_inputs=file_inputs, processor=self.processor
        )

        # 11. 全て正常終了した場合のレスポンス
        return api_response(
            status_code=status.HTTP_200_OK,
            status_str="success",
            code="SUCCESS",
            detail="全てのファイルが正常にアップロード・検証されました。",
        )


# --- FastAPIルート定義 ---
@router.post(SYOGUN_CSV_ROUTE, summary="将軍CSVファイルをアップロード")
async def upload_csv(
    shipment: Annotated[UploadFile | None, File(description="出荷CSV")] = None,
    receive: Annotated[UploadFile | None, File(description="受入CSV")] = None,
    yard: Annotated[UploadFile | None, File(description="ヤードCSV")] = None,
):
    file_inputs = {
        "shipment": shipment,
        "receive": receive,
        "yard": yard,
    }
    # Noneのものは除外
    file_inputs = {k: v for k, v in file_inputs.items() if v is not None}
    service = CSVImportService(file_inputs)
    return await service.process_upload(file_inputs)
