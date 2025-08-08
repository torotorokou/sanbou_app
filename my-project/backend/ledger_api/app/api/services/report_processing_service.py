# backend/app/api/services/report_processing_service.py

from typing import Any, Dict, Optional, Tuple

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from app.api.services.csv_formatter_service import CsvFormatterService
from app.api.services.csv_validator_facade import CsvValidatorService
from app.api.services.report.base_report_generator import BaseReportGenerator
from app.api.services.report.generator_factory import get_report_generator
from app.api.utils.excel_pdf_zip_utils import create_excel_bytes, generate_excel_pdf_zip
from backend_shared.src.api_response.response_error import NoFilesUploadedResponse
from backend_shared.src.utils.csv_reader import read_csv_files


class ReportProcessingService:
    """
    帳票処理の共通サービスクラス

    全ての帳票エンドポイントで共通の処理フローを提供します：
    1. ファイル取得・検証
    2. CSVバリデーション・フォーマット変換
    3. 帳票生成
    4. Excel・PDF・ZIP生成
    """

    def __init__(self):
        self.validator_service = CsvValidatorService()
        self.formatter_service = CsvFormatterService()

    def process_uploaded_files(
        self, files: Dict[str, UploadFile]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """
        アップロードされたファイルの処理（読み込み・バリデーション・フォーマット）

        Args:
            files: アップロードされたファイル辞書

        Returns:
            Tuple[フォーマット済みDataFrame辞書, エラーレスポンス]
        """
        # ファイル未アップロードチェック
        if not files:
            print("No files uploaded.")
            return None, NoFilesUploadedResponse()

        print(f"Uploaded files: {list(files.keys())}")

        # CSV読込処理
        dfs, error = read_csv_files(files)
        if error:
            return None, error

        # CSVデータのバリデーション処理
        validation_error = self.validator_service.validate(dfs, files)
        if validation_error:
            print(f"Validation error: {validation_error}")
            return None, validation_error

        # データフォーマット変換処理
        print("Formatting DataFrames...")
        df_formatted = self.formatter_service.format(dfs)
        for csv_type, df in df_formatted.items():
            print(f"Formatted {csv_type}: shape={df.shape}")

        return df_formatted, None

    def generate_report_with_generator(
        self, report_key: str, df_formatted: Dict[str, Any]
    ) -> Tuple[
        Optional[BaseReportGenerator], Optional[Any], Optional[str], Optional[Exception]
    ]:
        """
        帳票ジェネレーターを使用した帳票生成

        Args:
            report_key: 帳票キー
            df_formatted: フォーマット済みDataFrame辞書

        Returns:
            Tuple[ジェネレーター, 結果DataFrame, 帳票日付, エラー]
        """
        try:
            print("Preparing report generator...")
            # 帳票生成器の取得
            generator = get_report_generator(report_key, df_formatted)

            print("Running preprocess...")
            # 前処理の実行
            generator.preprocess(report_key)

            print("Running main_process...")
            # メイン処理の実行
            df_result = generator.main_process()

            print("Making report date...")
            # 帳票日付の生成
            report_date = generator.make_report_date(df_formatted)

            return generator, df_result, report_date, None

        except Exception as e:
            print(f"[ERROR] Report generation failed: {e}")
            return None, None, None, e

    def create_response(
        self,
        generator: BaseReportGenerator,
        df_result: Any,
        report_date: str,
        report_key: str,
    ) -> StreamingResponse:
        """
        Excel・PDF・ZIP レスポンスの生成

        Args:
            generator: 帳票ジェネレーター
            df_result: 処理結果DataFrame
            report_date: 帳票日付
            report_key: 帳票キー

        Returns:
            StreamingResponse: ZIP圧縮されたファイルレスポンス
        """
        try:
            # Excel出力処理
            excel_bytes = create_excel_bytes(generator, df_result, report_date)

            # ZIP作成＆レスポンス返却
            return generate_excel_pdf_zip(excel_bytes, report_key, report_date)

        except Exception as e:
            print(f"[ERROR] Excel/PDF/ZIP generation failed: {e}")
            raise

    def process_complete_flow(
        self, report_key: str, files: Dict[str, UploadFile]
    ) -> StreamingResponse:
        """
        完全な帳票処理フローの実行

        Args:
            report_key: 帳票キー
            files: アップロードファイル辞書

        Returns:
            StreamingResponse: 処理結果のZIPファイル
        """
        # Step 1: ファイル処理
        df_formatted, error = self.process_uploaded_files(files)
        if error:
            return error.to_json_response()

        # Step 2: 帳票生成
        if df_formatted is None:
            raise ValueError("Data formatting failed")

        generator, df_result, report_date, gen_error = (
            self.generate_report_with_generator(report_key, df_formatted)
        )
        if gen_error or generator is None or df_result is None or report_date is None:
            raise gen_error or ValueError("Report generation failed")

        # Step 3: レスポンス生成
        return self.create_response(generator, df_result, report_date, report_key)
