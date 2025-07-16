from fastapi import APIRouter
from app.api.endpoints import ukeire_api, vendors

api_router = APIRouter()
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(ukeire_api.router, prefix="/ukeire", tags=["ukeire"])
