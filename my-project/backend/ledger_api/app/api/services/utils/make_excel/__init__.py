"""
Excel出力ユーティリティパッケージ（FastAPI用）

使用方法:
    from app.api.services.utils.make_excel import df_to_excel

    excel_bytes = df_to_excel(df, "データ")
"""

__version__ = "1.0.0"
__author__ = "Backend Team"

# 主要な関数をパッケージレベルでエクスポート
from .excel_utils import (
    df_to_excel,
    simple_df_to_excel,
    formatted_df_to_excel,
    template_df_to_excel,
    safe_excel_value,
)

from .fastapi_excel_response import (
    create_excel_response,
    create_excel_bytes_response,
    excel_from_csv_data,
    excel_from_dict_list,
)

__all__ = [
    # excel_utils
    "df_to_excel",
    "simple_df_to_excel",
    "formatted_df_to_excel",
    "template_df_to_excel",
    "safe_excel_value",
    # fastapi_excel_response
    "create_excel_response",
    "create_excel_bytes_response",
    "excel_from_csv_data",
    "excel_from_dict_list",
]
