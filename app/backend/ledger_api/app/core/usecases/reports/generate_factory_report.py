"""
Generate Factory Report UseCase.

工場日報生成のアプリケーションロジックを提供します。

👶 UseCase の責務:
1. CSV 読み込み（Port 経由）
2. データ検証
3. ドメインロジック呼び出し（既存の services/report/ledger/factory_report.process）
4. Excel/PDF 生成
5. 保存と署名付き URL 返却（Port 経由）

外部依存（pandas, ファイルシステム等）は Port を通して抽象化されています。
"""

from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

from fastapi import UploadFile
from fastapi.responses import JSONResponse

from app.core.ports import CsvGateway, ReportRepository
from app.core.ports.report_repository import ArtifactUrls
from backend_shared.adapters.fastapi.error_handlers import DomainError
from backend_shared.utils.date_filter_utils import (
    filter_by_period_from_min_date as shared_filter_by_period_from_min_date,
)

# 既存のドメインロジックを再利用（将来的には Entity に移行）
from app.api.services.report.ledger.factory_report import process as factory_report_process
from app.api.services.report.utils.io import write_values_to_template
from app.api.services.report.utils.config import get_template_config
from app.api.utils.pdf_conversion import convert_excel_to_pdf


class GenerateFactoryReportUseCase:
    """工場日報生成 UseCase."""

    def __init__(
        self,
        csv_gateway: CsvGateway,
        report_repository: ReportRepository,
    ):
        """
        UseCase の初期化.

        Args:
            csv_gateway: CSV 読み込み・検証・整形の抽象インターフェース
            report_repository: レポート保存の抽象インターフェース

        👶 依存性注入（DI）により、テスト時はモック実装を渡せます。
        """
        self.csv_gateway = csv_gateway
        self.report_repository = report_repository

    def execute(
        self,
        files: Dict[str, UploadFile],
        period_type: Optional[str] = None,
    ) -> JSONResponse:
        """
        工場日報生成の実行.

        Args:
            files: アップロードされた CSV ファイル（shipment, yard, receive 等）
            period_type: 期間指定（"oneday" | "oneweek" | "onemonth"）

        Returns:
            JSONResponse: 署名付き URL を含むレスポンス

        Raises:
            DomainError: ビジネスルール違反や処理失敗時
        """
        try:
            # Step 1: CSV 読み込み（Port 経由）
            print(f"[UseCase] Step 1: CSV 読み込み - files: {list(files.keys())}")
            dfs, error = self.csv_gateway.read_csv_files(files)
            if error:
                print(f"[UseCase] CSV 読み込みエラー: {error}")
                return error.to_json_response()

            assert dfs is not None

            # Step 2: 検証（Port 経由）
            print("[UseCase] Step 2: CSV 検証")
            validation_error = self.csv_gateway.validate_csv_structure(dfs, files)
            if validation_error:
                print(f"[UseCase] 検証エラー: {validation_error}")
                return validation_error.to_json_response()

            # Step 2.5: 期間フィルタ適用（オプション）
            if period_type:
                print(f"[UseCase] Step 2.5: 期間フィルタ適用 - {period_type}")
                try:
                    dfs = shared_filter_by_period_from_min_date(dfs, period_type)
                    print(f"[UseCase] 期間フィルタ完了: {period_type}")
                except Exception as e:
                    print(f"[UseCase] 期間フィルタスキップ（エラー）: {e}")

            # Step 3: 整形（Port 経由）
            print("[UseCase] Step 3: CSV 整形")
            try:
                df_formatted = self.csv_gateway.format_csv_data(dfs)
            except DomainError:
                raise
            except Exception as ex:
                print(f"[UseCase] 整形エラー: {ex}")
                raise DomainError(
                    code="REPORT_FORMAT_ERROR",
                    status=500,
                    user_message=f"帳票データの整形中にエラーが発生しました: {str(ex)}",
                    title="データ整形エラー",
                ) from ex

            # Step 4: レポート日付の決定
            report_date = self._extract_report_date(df_formatted)
            print(f"[UseCase] Step 4: レポート日付 - {report_date}")

            # Step 5: ドメインロジック実行（既存の process 関数を利用）
            print("[UseCase] Step 5: ドメインロジック実行")
            try:
                result_df = factory_report_process(df_formatted)
            except Exception as ex:
                print(f"[UseCase] ドメインロジックエラー: {ex}")
                raise DomainError(
                    code="REPORT_GENERATION_ERROR",
                    status=500,
                    user_message=f"工場日報の生成中にエラーが発生しました: {str(ex)}",
                    title="レポート生成エラー",
                ) from ex

            # Step 6: Excel 生成
            print("[UseCase] Step 6: Excel 生成")
            excel_bytes = self._generate_excel(result_df, report_date)

            # Step 7: PDF 生成
            print("[UseCase] Step 7: PDF 生成")
            pdf_bytes = self._generate_pdf(excel_bytes)

            # Step 8: 保存と署名付き URL 生成（Port 経由）
            print("[UseCase] Step 8: 保存と URL 生成")
            artifact_urls = self.report_repository.save_report(
                report_key="factory_report",
                report_date=report_date,
                excel_bytes=excel_bytes,
                pdf_bytes=pdf_bytes,
            )

            # Step 9: レスポンス返却
            print(f"[UseCase] Step 9: 完了 - URLs: {artifact_urls.to_dict()}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "工場日報の生成が完了しました",
                    "report_date": report_date.isoformat(),
                    **artifact_urls.to_dict(),
                },
            )

        except DomainError:
            # DomainError はそのまま再 raise
            raise
        except Exception as ex:
            print(f"[UseCase] 予期しないエラー: {ex}")
            import traceback
            traceback.print_exc()
            raise DomainError(
                code="INTERNAL_ERROR",
                status=500,
                user_message="工場日報の生成中に予期しないエラーが発生しました",
                title="内部エラー",
            ) from ex

    def _extract_report_date(self, df_formatted: Dict[str, Any]) -> date:
        """
        整形後データからレポート日付を抽出.

        複数の候補列から最初に見つかった有効な日付を使用します。
        見つからない場合は今日の日付にフォールバックします。
        """
        if not df_formatted:
            return datetime.now().date()

        date_candidates = ["伝票日付", "日付", "date", "Date"]

        for df in df_formatted.values():
            if not hasattr(df, "columns") or df.empty:
                continue

            for col in date_candidates:
                if col not in df.columns:
                    continue

                first_value = df[col].iloc[0]
                if isinstance(first_value, str):
                    try:
                        from datetime import datetime as dt
                        return dt.strptime(first_value, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        continue
                elif hasattr(first_value, "date"):
                    return first_value.date()

        # フォールバック: 今日の日付
        return datetime.now().date()

    def _generate_excel(self, result_df: Any, report_date: date) -> BytesIO:
        """
        DataFrame から Excel バイトストリームを生成.

        既存の write_values_to_template を利用します。
        """
        template_key = "factory_report"
        template_config = get_template_config()[template_key]
        template_path = template_config["template_path"]
        
        # 日付文字列を生成（シート名用）
        extracted_date = report_date.strftime("%Y年%m月%d日")

        excel_bytes = write_values_to_template(
            df=result_df,
            template_path=template_path,
            extracted_date=extracted_date,
        )

        return excel_bytes

    def _generate_pdf(self, excel_bytes: BytesIO) -> BytesIO:
        """
        Excel バイトストリームから PDF を生成.

        既存の convert_excel_to_pdf を利用します（一時ファイル経由）。
        """
        # 一時ファイルに Excel を書き出し
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_excel:
            tmp_excel.write(excel_bytes.getvalue())
            tmp_excel_path = Path(tmp_excel.name)

        try:
            # PDF に変換
            pdf_bytes_raw = convert_excel_to_pdf(tmp_excel_path)
            
            # BytesIO にラップして返却
            pdf_bytes = BytesIO(pdf_bytes_raw)
            return pdf_bytes
        finally:
            # 一時ファイルを削除
            if tmp_excel_path.exists():
                tmp_excel_path.unlink()
