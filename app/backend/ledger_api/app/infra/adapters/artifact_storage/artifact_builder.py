"""Artifact response builder.

Excel/PDF の生成・保存と、署名付きURLの JSON ペイロード組み立てを汎用化したヘルパークラス。

🔄 リファクタリング: Excel同期 + PDF非同期の2段階構成に対応
- build(): Excel生成→即座にレスポンス返却（pdf_status: "pending"）
- generate_pdf_background(): バックグラウンドでPDF生成
- get_pdf_status(): PDFステータス確認
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Optional, TYPE_CHECKING

from fastapi.responses import JSONResponse
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_iso
from backend_shared.application.logging import get_module_logger

if TYPE_CHECKING:
    from app.core.usecases.reports.base_generators import BaseReportGenerator

from app.infra.adapters.artifact_storage.artifact_service import (
    get_report_artifact_storage,
    ArtifactLocation,
)
from app.infra.adapters.file_processing.pdf_conversion import PdfConversionError, convert_excel_to_pdf

logger = get_module_logger(__name__)

# PDFステータスの型定義
PdfStatus = Literal["pending", "ready", "error"]


def _ensure_bytes(value: Any, *, label: str) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    try:
        if hasattr(value, "getvalue"):
            return bytes(value.getvalue())  # type: ignore[call-overload]
        if hasattr(value, "read"):
            data = value.read()
            return bytes(data)
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"{label}: could not normalise to bytes") from exc
    raise TypeError(f"{label}: unsupported type {type(value)!r}")


class ArtifactResponseBuilder:
    """Excel/PDF の生成とアーティファクト JSON の組み立てを担当するクラス。
    
    🔄 リファクタリング: 2段階構成
    - build(): Excel生成 → 即座にレスポンス（PDF生成はバックグラウンド）
    - build_sync(): 従来通りExcel+PDFを同期生成（後方互換用）
    """

    def build(
        self,
        generator: BaseReportGenerator,
        df_result: Any,
        report_date: str,
        *,
        extra_payload: Optional[Dict[str, Any]] = None,
        async_pdf: bool = True,
    ) -> JSONResponse:
        """レポートを生成してレスポンスを返す。
        
        Args:
            generator: レポート生成器
            df_result: 処理結果DataFrame
            report_date: レポート日付
            extra_payload: 追加のペイロード
            async_pdf: True=PDF非同期生成, False=同期生成（従来互換）
        """
        try:
            excel_bytes_raw = generator.generate_excel_bytes(df_result, report_date)
            excel_bytes = _ensure_bytes(excel_bytes_raw, label="excel_bytes")

            storage = get_report_artifact_storage()
            location = storage.allocate(generator.report_key, report_date)

            excel_path = storage.save_excel(location, excel_bytes)

            if async_pdf:
                # 非同期モード: PDFは後でバックグラウンドで生成
                artifact_payload = storage.build_payload(location, excel_exists=True, pdf_exists=False)
                # report_token を追加（PDFステータス確認用）
                artifact_payload["report_token"] = location.token
                
                metadata: Dict[str, Any] = {
                    "generated_at": format_datetime_iso(now_in_app_timezone()),
                    "pdf_status": "pending",
                    "excel_path": str(excel_path),
                }

                response_body: Dict[str, Any] = {
                    "status": "success",
                    "report_key": generator.report_key,
                    "report_date": report_date,
                    "artifact": artifact_payload,
                    "metadata": metadata,
                }
                
                logger.info(
                    "Excel生成完了（PDF非同期モード）",
                    extra={
                        "report_key": generator.report_key,
                        "report_date": report_date,
                        "report_token": location.token,
                    },
                )
            else:
                # 同期モード: 従来通りPDFも同時に生成
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
                artifact_payload["report_token"] = location.token
                
                metadata = {
                    "generated_at": format_datetime_iso(now_in_app_timezone()),
                    "pdf_status": "ready" if pdf_exists else "error",
                }
                if pdf_error:
                    metadata["pdf_error"] = pdf_error

                response_body = {
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
            logger.error(f"ArtifactResponseBuilder failed: {e}", exc_info=True)
            raise


def generate_pdf_background(
    report_key: str,
    report_date: str,
    report_token: str,
    excel_path_str: str,
) -> None:
    """バックグラウンドでPDFを生成する関数。
    
    FastAPIのBackgroundTasksから呼び出される。
    🚀 高速化: 即座に実行開始してレスポンス待機なし
    
    Args:
        report_key: レポートキー
        report_date: レポート日付
        report_token: レポートトークン（ディレクトリ識別用）
        excel_path_str: Excelファイルのパス（文字列）
    """
    import time
    start_time = time.time()
    
    logger.info(
        "PDF生成開始（バックグラウンド）",
        extra={
            "report_key": report_key,
            "report_date": report_date,
            "report_token": report_token,
        },
    )
    
    try:
        excel_path = Path(excel_path_str)
        if not excel_path.exists():
            logger.error(f"Excel file not found: {excel_path}")
            return
        
        output_dir = excel_path.parent
        profile_dir = output_dir / "lo_profile"
        
        # PDF変換実行
        pdf_bytes = convert_excel_to_pdf(
            excel_path,
            output_dir=output_dir,
            profile_dir=profile_dir,
        )
        
        # PDF保存
        storage = get_report_artifact_storage()
        # locationを再構築
        location = ArtifactLocation(
            root_dir=storage.root_dir,
            report_key=report_key,
            report_date=report_date,
            token=report_token,
            file_base=excel_path.stem,  # Excel名から拡張子を除いた部分
        )
        storage.save_pdf(location, pdf_bytes)
        
        elapsed = time.time() - start_time
        logger.info(
            "PDF生成完了（バックグラウンド）",
            extra={
                "report_key": report_key,
                "report_date": report_date,
                "report_token": report_token,
                "elapsed_seconds": round(elapsed, 3),
            },
        )
        
    except PdfConversionError as exc:
        elapsed = time.time() - start_time
        logger.error(
            "PDF生成失敗（バックグラウンド）",
            extra={
                "report_key": report_key,
                "report_date": report_date,
                "report_token": report_token,
                "error": str(exc),
                "elapsed_seconds": round(elapsed, 3),
            },
        )
    except Exception as exc:
        logger.exception(
            "PDF生成中に予期しないエラー（バックグラウンド）",
            extra={
                "report_key": report_key,
                "report_date": report_date,
                "report_token": report_token,
            },
        )


def get_pdf_status(
    report_key: str,
    report_date: str,
    report_token: str,
) -> Dict[str, Any]:
    """PDFのステータスを確認する。
    
    Args:
        report_key: レポートキー
        report_date: レポート日付
        report_token: レポートトークン
        
    Returns:
        Dict with status ("pending", "ready", "error") and optional pdf_url
    """
    storage = get_report_artifact_storage()
    
    # locationを再構築してPDFパスを推測
    # file_baseはreport_key-report_dateの形式
    from app.infra.adapters.artifact_storage.artifact_service import _sanitize_segment
    file_base = _sanitize_segment(f"{report_key}-{report_date}")
    
    location = ArtifactLocation(
        root_dir=storage.root_dir,
        report_key=report_key,
        report_date=report_date,
        token=report_token,
        file_base=file_base,
    )
    
    pdf_path = location.file_path(".pdf")
    excel_path = location.file_path(".xlsx")
    
    # Excelが存在しない場合はトークンが無効
    if not excel_path.exists():
        return {
            "status": "error",
            "message": "Invalid report token or report not found",
        }
    
    if pdf_path.exists():
        # PDFが存在する → ready
        pdf_filename = f"{file_base}.pdf"
        pdf_url = storage.signer.create_url(
            location.relative_path(pdf_filename),
            disposition="inline",
        )
        return {
            "status": "ready",
            "pdf_url": pdf_url,
        }
    else:
        # PDFがまだない → pending
        return {
            "status": "pending",
        }
