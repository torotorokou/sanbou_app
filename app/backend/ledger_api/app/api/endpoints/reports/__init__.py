# backend/app/api/endpoints/reports/__init__.py

from fastapi import APIRouter

from . import (
    average_sheet,
    balance_sheet,
    block_unit_price,
    factory_report,
    management_sheet,
)

# 帳票系APIの統合ルーター
reports_router = APIRouter()

# 各帳票のルーターを統合
reports_router.include_router(
    factory_report.router, prefix="/factory_report", tags=["Factory Report"]
)

reports_router.include_router(
    balance_sheet.router, prefix="/balance_sheet", tags=["Balance Sheet"]
)

reports_router.include_router(
    average_sheet.router, prefix="/average_sheet", tags=["Average Sheet"]
)


reports_router.include_router(
    block_unit_price.router, prefix="/block_unit_price", tags=["Block Unit Price"]
)


reports_router.include_router(
    management_sheet.router, prefix="/management_sheet", tags=["Management Sheet"]
)

# 必要に応じて他の帳票エンドポイントも追加
# reports_router.include_router(
#     management_sheet.router,
#     prefix="/management_sheet",
#     tags=["Management Sheet"]
# )

# reports_router.include_router(
#     average_sheet.router,
#     prefix="/average_sheet",
#     tags=["Average Sheet"]
# )
