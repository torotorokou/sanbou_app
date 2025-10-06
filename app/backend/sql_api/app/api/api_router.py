from fastapi import APIRouter
# from __archive__ import ukeire_api, vendors  # REMOVED: __archive__ directory no longer exists
from app.api.endpoints import syogun_csv_upload
from app.local_config.api_constants import UPLOAD_PREFIX  # , VENDORS_PREFIX, UKEIRE_PREFIX

api_router = APIRouter()
# api_router.include_router(vendors.router, prefix=VENDORS_PREFIX, tags=["vendors"])
# api_router.include_router(ukeire_api.router, prefix=UKEIRE_PREFIX, tags=["ukeire"])
api_router.include_router(syogun_csv_upload.router, prefix=UPLOAD_PREFIX, tags=["upload"])
