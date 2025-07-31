"""
改良されたmanage_reportエンドポイントの例

BaseReportGeneratorクラスと先ほど作成したExcel機能を統合した、
初心者にもわかりやすいエンドポイントの実装例です。
"""

import os
import pandas as pd
from fastapi import APIRouter, UploadFile, Form, File, HTTPException
from backend_shared.src.response_utils import api_response

from backend_shared.config.config_loader import (
    SyogunCsvConfigLoader,
    ReportTemplateConfigLoader,
)
from backend_shared.src.csv_validator.csv_upload_validator_api import (
    CSVValidationResponder,
)

from backend_shared.src.csv_formatter.formatter_factory import CSVFormatterFactory
from backend_shared.src.csv_formatter.formatter_config import build_formatter_config

# 改良されたレポート生成機能をインポート
from app.api.services.report_generator import get_report_generator
from backend_shared.src.report_checker.check_csv_files import check_csv_files

from app.local_config.paths import MANAGE_REPORT_OUTPUT_DIR, MANAGE_REPORT_URL_BASE

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANAGE_REPORT_DIR = os.path.join(BASE_DIR, "static", "manage_report")
os.makedirs(MANAGE_REPORT_DIR, exist_ok=True)


@router.post("/report/manage")
async def generate_pdf(
    report_key: str = Form(...),
    shipment: UploadFile = File(None),
    yard: UploadFile = File(None),
    receive: UploadFile = File(None),
):
    """
    帳票生成エンドポイント（改良版）

    CSVファイルをアップロードして、指定された種類の帳票を生成し、
    PDFとExcelファイルを作成してダウンロードURLを返します。

    Args:
        report_key: 帳票の種類（factory_report, balance_sheet等）
        shipment: 出荷データCSVファイル（オプション）
        yard: ヤードデータCSVファイル（オプション）
        receive: 受入データCSVファイル（オプション）

    Returns:
        dict: PDF・ExcelのダウンロードURL等を含むレスポンス
    """
    try:
        # STEP 1: アップロードされたファイルをDataFrameに変換
        print(f"[INFO] 帳票生成開始: {report_key}")

        files = {
            k: v
            for k, v in {
                "shipment": shipment,
                "yard": yard,
                "receive": receive,
            }.items()
            if v is not None
        }

        # DataFrameに変換
        dfs = {}
        for k, f in files.items():
            f.file.seek(0)
            dfs[k] = pd.read_csv(f.file)
            f.file.seek(0)
            print(f"[INFO] {k}ファイル読み込み: {len(dfs[k])}行")

        # STEP 2: CSVバリデーション（列名・日付チェック）
        print("[INFO] CSVバリデーション開始")

        # 列名チェック
        config_loader = SyogunCsvConfigLoader()
        required_columns = {
            k: config_loader.get_expected_headers(k) for k in files.keys()
        }

        validator = CSVValidationResponder(required_columns)

        # 列名バリデーション
        res = validator.validate_columns(dfs, files)
        if res:
            return res

        # 日付バリデーション
        res = validator.validate_denpyou_date_exists(dfs, files)
        if res:
            return res

        res = validator.validate_denpyou_date_consistency(dfs)
        if res:
            return res

        print("[INFO] CSVバリデーション完了")

        # STEP 3: データフォーマット（列名変更・型変換等）
        print("[INFO] データフォーマット開始")

        loader = SyogunCsvConfigLoader()
        df_formatted = {}
        for csv_type, df in dfs.items():
            config = build_formatter_config(loader, csv_type)
            formatter = CSVFormatterFactory.get_formatter(csv_type, config)
            df_formatted[csv_type] = formatter.format(df)
            print(f"[INFO] {csv_type}フォーマット完了: {len(df_formatted[csv_type])}行")

        # STEP 4: レポート生成器を取得して帳票生成
        print(f"[INFO] レポート生成器取得: {report_key}")

        output_dir = os.path.join(MANAGE_REPORT_OUTPUT_DIR, report_key)
        generator = get_report_generator(report_key, output_dir, df_formatted)

        # 前処理: 必要なファイルチェック
        generator.preprocess(report_key)
        print("[INFO] 前処理完了")

        # メイン処理: 帳票データ生成
        result_df = generator.main_process()
        print(f"[INFO] メイン処理完了: {len(result_df)}行のデータ生成")

        # STEP 5: PDF・Excel出力
        print("[INFO] ファイル生成開始")

        # PDF生成（現在はダミー実装）
        pdf_name = generator.generate_pdf("report.pdf")
        print(f"[INFO] PDF生成完了: {pdf_name}")

        # Excel生成（高品質なExcel機能を使用）
        excel_name = generator.generate_excel("report.xlsx")
        print(f"[INFO] Excel生成完了: {excel_name}")

        # STEP 6: レスポンス作成
        url_base = f"{MANAGE_REPORT_URL_BASE}/{report_key}"

        response_data = {
            "pdf_url": f"{url_base}/{pdf_name}",
            "excel_url": f"{url_base}/{excel_name}",
            "download_pdf_name": pdf_name,
            "download_excel_name": excel_name,
            "generated_records": len(result_df),  # 生成されたデータ行数
            "report_type": report_key,
        }

        print(f"[INFO] 帳票生成完了: {report_key}")

        return api_response(
            status_code=200,
            status_str="success",
            code="REPORT_CREATED",
            detail=f"{report_key}帳簿が正常に作成されました。",
            result=response_data,
        )

    except ValueError as ve:
        # 設定エラーやデータエラー
        print(f"[ERROR] データエラー: {ve}")
        return api_response(
            status_code=400,
            status_str="error",
            code="DATA_ERROR",
            detail=f"データ処理エラー: {str(ve)}",
            result=None,
        )

    except FileNotFoundError as fe:
        # ファイルが見つからない
        print(f"[ERROR] ファイルエラー: {fe}")
        return api_response(
            status_code=404,
            status_str="error",
            code="FILE_NOT_FOUND",
            detail=f"ファイルが見つかりません: {str(fe)}",
            result=None,
        )

    except Exception as e:
        # その他の予期しないエラー
        print(f"[ERROR] 予期しないエラー: {e}")
        import traceback

        traceback.print_exc()

        return api_response(
            status_code=500,
            status_str="error",
            code="INTERNAL_ERROR",
            detail=f"内部エラーが発生しました: {str(e)}",
            result=None,
        )


# 追加: 生成されたファイルの一覧取得エンドポイント
@router.get("/report/list/{report_key}")
async def list_generated_reports(report_key: str):
    """
    指定されたレポートタイプの生成済みファイル一覧を取得

    Args:
        report_key: レポートの種類

    Returns:
        dict: 生成済みファイルの一覧
    """
    try:
        output_dir = os.path.join(MANAGE_REPORT_OUTPUT_DIR, report_key)

        if not os.path.exists(output_dir):
            return api_response(
                status_code=404,
                status_str="error",
                code="DIRECTORY_NOT_FOUND",
                detail=f"レポートディレクトリが見つかりません: {report_key}",
                result=None,
            )

        # ディレクトリ内のファイル一覧取得
        files = []
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            if os.path.isfile(filepath):
                file_info = {
                    "filename": filename,
                    "size": os.path.getsize(filepath),
                    "created": os.path.getctime(filepath),
                    "url": f"{MANAGE_REPORT_URL_BASE}/{report_key}/{filename}",
                }
                files.append(file_info)

        return api_response(
            status_code=200,
            status_str="success",
            code="FILES_LISTED",
            detail=f"{report_key}の生成済みファイル一覧を取得しました",
            result={"report_key": report_key, "file_count": len(files), "files": files},
        )

    except Exception as e:
        return api_response(
            status_code=500,
            status_str="error",
            code="LIST_ERROR",
            detail=f"ファイル一覧取得エラー: {str(e)}",
            result=None,
        )


"""
📚 初心者向け解説：

1. 【データの流れ】
   CSV → DataFrame → バリデーション → フォーマット → 帳票生成 → PDF/Excel出力

2. 【主要なクラス】
   - BaseReportGenerator: 共通的なPDF/Excel生成機能
   - 各サブクラス: 個別の帳票生成ロジック（main_process）
   - Excel機能: 高品質なExcel出力（日本語フォント付き）

3. 【エラーハンドリング】
   - ValueError: データの問題
   - FileNotFoundError: ファイルの問題
   - Exception: その他の予期しない問題

4. 【拡張方法】
   - 新しい帳票タイプ: BaseReportGeneratorを継承
   - PDF機能強化: generate_pdfメソッドをreportlabで実装
   - Excel機能拡張: テンプレート機能やグラフ機能を追加

5. 【テスト方法】
   - test_report_generator.pyでユニットテスト
   - Postmanやcurlでエンドポイントテスト
   - 生成されたファイルをExcel/PDFビューアで確認
"""
