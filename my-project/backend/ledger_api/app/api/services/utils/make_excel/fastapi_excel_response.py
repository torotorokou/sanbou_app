"""
FastAPI用Excel出力レスポンスヘルパー

FastAPIエンドポイントでExcelファイルをダウンロード可能な形式で返すためのヘルパー関数
"""

from fastapi import Response
from fastapi.responses import StreamingResponse
import pandas as pd
from pathlib import Path
from typing import Optional, Union
from io import BytesIO
import logging

from .excel_utils import df_to_excel

logger = logging.getLogger(__name__)


def create_excel_response(
    df: pd.DataFrame,
    filename: str = "data.xlsx",
    sheet_name: str = "データ",
    use_formatting: bool = True,
    template_path: Optional[Union[str, Path]] = None,
) -> StreamingResponse:
    """
    DataFrameをExcelファイルとしてダウンロード可能なレスポンスに変換

    Args:
        df: 出力するDataFrame
        filename: ダウンロード時のファイル名
        sheet_name: シート名
        use_formatting: フォーマットを適用するか
        template_path: テンプレートファイルのパス（オプション）

    Returns:
        StreamingResponse: FastAPIのStreamingResponse

    Example:
        @app.get("/download-excel")
        async def download_excel():
            df = pd.DataFrame({"列1": [1, 2, 3], "列2": ["A", "B", "C"]})
            return create_excel_response(df, "sample.xlsx")
    """
    try:
        # Excel生成
        excel_data = df_to_excel(
            df=df,
            sheet_name=sheet_name,
            use_formatting=use_formatting,
            template_path=template_path,
        )

        # StreamingResponseを作成
        response = StreamingResponse(
            BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

        logger.info(f"Excel出力レスポンス作成成功: {filename}, {len(excel_data)} bytes")
        return response

    except Exception as e:
        logger.error(f"Excel出力レスポンス作成エラー: {e}")
        raise


def create_excel_bytes_response(
    df: pd.DataFrame,
    filename: str = "data.xlsx",
    sheet_name: str = "データ",
    use_formatting: bool = True,
    template_path: Optional[Union[str, Path]] = None,
) -> Response:
    """
    DataFrameをExcelファイルのbytesレスポンスとして返す（より軽量）

    Args:
        df: 出力するDataFrame
        filename: ダウンロード時のファイル名
        sheet_name: シート名
        use_formatting: フォーマットを適用するか
        template_path: テンプレートファイルのパス（オプション）

    Returns:
        Response: FastAPIのResponse
    """
    try:
        # Excel生成
        excel_data = df_to_excel(
            df=df,
            sheet_name=sheet_name,
            use_formatting=use_formatting,
            template_path=template_path,
        )

        # Responseを作成
        response = Response(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

        logger.info(
            f"Excelバイトレスポンス作成成功: {filename}, {len(excel_data)} bytes"
        )
        return response

    except Exception as e:
        logger.error(f"Excelバイトレスポンス作成エラー: {e}")
        raise


def excel_from_csv_data(
    csv_data: str,
    filename: str = "converted.xlsx",
    sheet_name: str = "データ",
    use_formatting: bool = True,
    delimiter: str = ",",
) -> StreamingResponse:
    """
    CSV文字列データをExcelレスポンスに変換

    Args:
        csv_data: CSV形式の文字列データ
        filename: ダウンロード時のファイル名
        sheet_name: シート名
        use_formatting: フォーマットを適用するか
        delimiter: CSVの区切り文字

    Returns:
        StreamingResponse: FastAPIのStreamingResponse
    """
    try:
        # CSV文字列をDataFrameに変換
        from io import StringIO

        df = pd.read_csv(StringIO(csv_data), delimiter=delimiter)

        # Excel出力
        return create_excel_response(
            df=df,
            filename=filename,
            sheet_name=sheet_name,
            use_formatting=use_formatting,
        )

    except Exception as e:
        logger.error(f"CSV→Excel変換エラー: {e}")
        raise


def excel_from_dict_list(
    data: list,
    filename: str = "data.xlsx",
    sheet_name: str = "データ",
    use_formatting: bool = True,
) -> StreamingResponse:
    """
    辞書のリストをExcelレスポンスに変換

    Args:
        data: 辞書のリスト（DataFrameに変換される）
        filename: ダウンロード時のファイル名
        sheet_name: シート名
        use_formatting: フォーマットを適用するか

    Returns:
        StreamingResponse: FastAPIのStreamingResponse

    Example:
        data = [
            {"name": "田中", "age": 30, "city": "東京"},
            {"name": "佐藤", "age": 25, "city": "大阪"}
        ]
        return excel_from_dict_list(data, "users.xlsx")
    """
    try:
        # 辞書リストをDataFrameに変換
        df = pd.DataFrame(data)

        # Excel出力
        return create_excel_response(
            df=df,
            filename=filename,
            sheet_name=sheet_name,
            use_formatting=use_formatting,
        )

    except Exception as e:
        logger.error(f"辞書リスト→Excel変換エラー: {e}")
        raise
