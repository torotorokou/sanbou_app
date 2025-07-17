from fastapi import APIRouter
from app.api.endpoints import ukeire_api, vendors, upload_api
from app.local_config.api_constants import UPLOAD_PREFIX, VENDORS_PREFIX, UKEIRE_PREFIX

api_router = APIRouter()
api_router.include_router(vendors.router, prefix=VENDORS_PREFIX, tags=["vendors"])
api_router.include_router(ukeire_api.router, prefix=UKEIRE_PREFIX, tags=["ukeire"])
api_router.include_router(upload_api.router, prefix=UPLOAD_PREFIX, tags=["upload"])
