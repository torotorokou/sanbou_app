"""帳票処理の共通サービス:
- CSV 読込
- ジェネレーターの validate/format/main_process 呼び出し
- Excel/PDF をファイルとして保存し、署名付き URL を返却
"""

from typing import Any, Dict, Optional, Tuple
import traceback

# pandas はこのモジュールでは未使用
from fastapi import UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.services.report.core.base_generators import BaseReportGenerator
from app.api.services.report.artifacts import ArtifactResponseBuilder
from backend_shared.src.api_response.response_error import NoFilesUploadedResponse
from backend_shared.src.api.error_handlers import DomainError
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
        try:
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
                print("[DEBUG] DataFrame shapes BEFORE filtering:")
                for csv_type, df in dfs.items():
                    try:
                        shape = getattr(df, "shape", None)
                        print(f"[DEBUG] Original {csv_type}: shape={shape}")
                        print(f"[DEBUG] Columns in {csv_type}: {list(df.columns)}")
                        candidates = ["伝票日付", "日付", "date", "Date"]
                        found = [c for c in candidates if c in df.columns]
                        print(
                            f"[DEBUG] Candidate date columns found in {csv_type}: {found}"
                        )
                        for col in found:
                            vals = df[col].head(3).tolist()
                            print(f"[DEBUG] Sample values for {col} in {csv_type}: {vals}")
                    except Exception as ex:
                        print(
                            f"[DEBUG] Original {csv_type}: shape=Unknown (not a DataFrame), error={ex}"
                        )

                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                    print(f"Applied date filtering by period: {period_type}")
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
            try:
                df_formatted = generator.format(dfs)
            except DomainError:
                # 既にDomainErrorの場合はそのまま再raise
                raise
            except Exception as ex:
                print(f"[ERROR] format() failed: {ex}")
                raise DomainError(
                    code="REPORT_FORMAT_ERROR",
                    status=500,
                    user_message=f"帳票データの整形中にエラーが発生しました: {str(ex)}",
                    title="データ整形エラー"
                ) from ex
            
            for csv_type, df in df_formatted.items():
                try:
                    shape = getattr(df, "shape", None)
                    print(f"Formatted {csv_type}: shape={shape}")
                except Exception:
                    pass

            # Step 4: メイン処理（ジェネレーター定義）
            print("Running main_process...")
            try:
                df_result = generator.main_process(df_formatted)
            except DomainError:
                # 既にDomainErrorの場合はそのまま再raise
                raise
            except Exception as ex:
                print("[DEBUG] main_process raised an exception:")
                print(f"[DEBUG] Exception type: {type(ex).__name__}, message: {ex}")
                tb = traceback.format_exc()
                print("[DEBUG] Traceback:\n" + tb)
                # DomainErrorに変換して詳細なエラーメッセージを提供
                raise DomainError(
                    code="REPORT_PROCESSING_ERROR",
                    status=500,
                    user_message=f"帳票の計算処理中にエラーが発生しました: {str(ex)}",
                    title="帳票処理エラー"
                ) from ex

            # Step 5: 帳票日付作成（共通: 整形後データから）
            print("Making report date...")
            report_date = generator.make_report_date(df_formatted)

            # Step 6: Excel/PDF を保存し JSON で URL を返す
            return self.create_response(generator, df_result, report_date)

        except DomainError:
            # DomainErrorはそのまま再raiseしてFastAPIのエラーハンドラに任せる
            raise
        except Exception as e:  # 予期せぬ例外をDomainErrorに変換
            print(f"[ERROR] report processing failed: {e}")
            try:
                print("[ERROR] Traceback (most recent call last):\n" + traceback.format_exc())
            except Exception:
                pass
            
            # DomainErrorとして再raiseし、エラーハンドラでProblemDetails化
            raise DomainError(
                code="REPORT_GENERATION_ERROR",
                status=500,
                user_message=f"帳票の生成中にエラーが発生しました: {str(e)}",
                title="帳票生成エラー"
            ) from e

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
        builder = ArtifactResponseBuilder()
        return builder.build(
            generator,
            df_result,
            report_date,
            extra_payload=extra_payload,
        )

    # 旧APIは撤廃（Factory廃止に伴い使用不可）
