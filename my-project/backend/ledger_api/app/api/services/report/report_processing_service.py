"""
帳票処理の共通サービス

責務:
- CSV読込
- ジェネレーターの validate/format/main_process 呼び出し
- ZIP の生成とレスポンス返却（Excel生成はジェネレーター側）
"""

from typing import Any, Dict, Optional, Tuple

from fastapi import UploadFile
from fastapi.responses import Response, StreamingResponse

from app.api.services.report.base_report_generator import BaseReportGenerator
from app.api.utils.excel_pdf_zip_utils import generate_excel_pdf_zip
from backend_shared.src.api_response.response_error import NoFilesUploadedResponse
from backend_shared.src.utils.csv_reader import read_csv_files


class ReportProcessingService:
    """帳票処理の共通サービスクラス"""

    def __init__(self):
        pass

    def _read_uploaded_files(
        self, files: Dict[str, UploadFile]
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """CSV読込のみを担当。空チェックも含む。"""
        if not files:
            print("No files uploaded.")
            return None, NoFilesUploadedResponse()

        print(f"Uploaded files: {list(files.keys())}")

        dfs, error = read_csv_files(files)
        if error:
            return None, error
        return dfs, None

    def run(
        self, generator: BaseReportGenerator, files: Dict[str, UploadFile]
    ) -> Response:
        """
        完全な帳票処理フローを実行（Factory不要・各エンドポイントがGeneratorを生成）
        """
        # Step 1: CSV読込
        dfs, error = self._read_uploaded_files(files)
        if error:
            return error.to_json_response()

        assert dfs is not None

        # Step 2: 検証（ジェネレーター定義）
        validation_error = generator.validate(dfs, files)
        if validation_error:
            print(f"Validation error: {validation_error}")
            return validation_error.to_json_response()

        # Step 3: 整形（ジェネレーター定義）
        print("Formatting DataFrames...")
        df_formatted = generator.format(dfs)
        for csv_type, df in df_formatted.items():
            try:
                shape = getattr(df, "shape", None)
                print(f"Formatted {csv_type}: shape={shape}")
            except Exception:
                pass

        # Step 4: メイン処理（ジェネレーター定義）
        print("Running main_process...")
        df_result = generator.main_process(df_formatted)

        # Step 5: 帳票日付作成（共通: 整形後データから）
        print("Making report date...")
        report_date = generator.make_report_date(df_formatted)

        # Step 6: Excel/PDF/ZIP レスポンス
        return self.create_response(generator, df_result, report_date)

    def create_response(
        self, generator: BaseReportGenerator, df_result: Any, report_date: str
    ) -> StreamingResponse:
        """
        Excel・PDF・ZIP レスポンスの生成

        Args:
            generator: 帳票ジェネレーター
            df_result: 処理結果DataFrame
            report_date: 帳票日付

        Returns:
            StreamingResponse: ZIP圧縮されたファイルレスポンス
        """
        try:
            # Excel出力処理はジェネレーターに統一
            excel_bytes = generator.generate_excel_bytes(df_result, report_date)

            # ZIP作成＆レスポンス返却
            return generate_excel_pdf_zip(
                excel_bytes, generator.report_key, report_date
            )

        except Exception as e:
            print(f"[ERROR] Excel/PDF/ZIP generation failed: {e}")
            raise

    # 旧APIは撤廃（Factory廃止に伴い使用不可）
