"""帳票処理の共通サービス。

責務:
- CSV 読込
- ジェネレーターの validate/format/main_process 呼び出し
- Excel/PDF をファイルとして保存し、署名付き URL を返却
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# pandas はこのモジュールでは未使用
from fastapi import UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.services.report.base_report_generator import BaseReportGenerator
from app.api.services.report.artifact_service import get_report_artifact_storage
from app.api.utils.pdf_conversion import PdfConversionError, convert_excel_to_pdf
from backend_shared.src.api_response.response_error import NoFilesUploadedResponse
from backend_shared.src.utils.csv_reader import read_csv_files
from backend_shared.src.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)


def _ensure_bytes(value: Any, *, label: str) -> bytes:
    """Ensure the provided value is bytes.

    👶 Pydantic や BytesIO など様々な型が返る可能性があるため、ここで統一しておきます。
    """

    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    try:
        # BytesIO やファイルライクオブジェクトをサポート
        if hasattr(value, "getvalue"):
            return bytes(value.getvalue())  # type: ignore[call-overload]
        if hasattr(value, "read"):
            data = value.read()
            return bytes(data)
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"{label}: could not normalise to bytes") from exc
    raise TypeError(f"{label}: unsupported type {type(value)!r}")


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

        # Step 2.5: 帳簿ごとの期間指定があれば、最小伝票日付から日/週/月でフィルタ
        period_type = getattr(generator, "period_type", None)
        if period_type:
            print(
                "\n==================== CSV日付フィルタ デバッグ開始 ===================="
            )
            # デバッグ: フィルタ前の各DataFrameのshapeとカラム名を表示
            print("[DEBUG] DataFrame shapes BEFORE filtering:")
            for csv_type, df in dfs.items():
                try:
                    shape = getattr(df, "shape", None)
                    print(f"[DEBUG] Original {csv_type}: shape={shape}")
                    print(f"[DEBUG] Columns in {csv_type}: {list(df.columns)}")
                    # 日付候補カラムの有無を表示
                    candidates = ["伝票日付", "日付", "date", "Date"]
                    found = [c for c in candidates if c in df.columns]
                    print(
                        f"[DEBUG] Candidate date columns found in {csv_type}: {found}"
                    )
                    # サンプル値表示
                    for col in found:
                        vals = df[col].head(3).tolist()
                        print(f"[DEBUG] Sample values for {col} in {csv_type}: {vals}")
                except Exception as ex:
                    print(
                        f"[DEBUG] Original {csv_type}: shape=Unknown (not a DataFrame), error={ex}"
                    )

            try:
                # 共通ユーティリティへ委譲
                dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                print(f"Applied date filtering by period: {period_type}")
                # デバッグ: フィルタ後の各DataFrameのshapeを表示
                print("[DEBUG] DataFrame shapes AFTER filtering:")
                for csv_type, df in dfs.items():
                    try:
                        shape = getattr(df, "shape", None)
                        print(f"[DEBUG] Filtered {csv_type}: shape={shape}")
                    except Exception:
                        print(
                            f"[DEBUG] Filtered {csv_type}: shape=Unknown (not a DataFrame)"
                        )
            except Exception as e:
                print(f"[WARN] Date filtering skipped due to error: {e}")
            print(
                "==================== CSV日付フィルタ デバッグ終了 ====================\n"
            )

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

        # Step 6: Excel/PDF を保存し JSON で URL を返す
        return self.create_response(generator, df_result, report_date)

    # ---------- 日付フィルタ関連（共通ユーティリティ） ----------
    # 共通化: 旧ローカル実装は date_filter_utils に移動
    # def filter_by_period_from_min_date(...): pass
    # def _find_date_column(...): pass

    def create_response(
        self,
        generator: BaseReportGenerator,
        df_result: Any,
        report_date: str,
        *,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Excel/PDF を保存し、署名付き URL を含む JSON を返却する。"""
        try:
            excel_bytes_raw = generator.generate_excel_bytes(df_result, report_date)
            excel_bytes = _ensure_bytes(excel_bytes_raw, label="excel_bytes")
            storage = get_report_artifact_storage()
            location = storage.allocate(generator.report_key, report_date)

            excel_path = storage.save_excel(location, excel_bytes)

            pdf_exists = True
            pdf_error: Optional[str] = None
            try:
                pdf_bytes = convert_excel_to_pdf(
                    excel_path,
                    output_dir=location.directory,
                    profile_dir=location.directory / "lo_profile",
                )
                storage.save_pdf(location, pdf_bytes)
            except PdfConversionError as exc:
                pdf_exists = False
                pdf_error = str(exc)

            artifact_payload = storage.build_payload(location, excel_exists=True, pdf_exists=pdf_exists)
            metadata: Dict[str, Any] = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "pdf_status": "available" if pdf_exists else "unavailable",
            }
            if pdf_error:
                metadata["pdf_error"] = pdf_error

            response_body: Dict[str, Any] = {
                "status": "success",
                "report_key": generator.report_key,
                "report_date": report_date,
                "artifact": artifact_payload,
                "metadata": metadata,
            }

            if extra_payload:
                extra = extra_payload.copy()
                extra.pop("status", None)
                response_body.update(extra)

            return JSONResponse(status_code=200, content=response_body)

        except Exception as e:
            print(f"[ERROR] Excel/PDF artifact generation failed: {e}")
            raise

    # 旧APIは撤廃（Factory廃止に伴い使用不可）
