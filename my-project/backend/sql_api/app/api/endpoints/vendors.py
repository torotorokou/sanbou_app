# app/api/endpoints/vendors.py

from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import get_engine
from app.schemas.vendor import Vendor
from typing import List
from app.config.api_constants import VENDORS_PREFIX

router = APIRouter()


@router.get(VENDORS_PREFIX, response_model=List[Vendor])
def get_vendors():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT vendor_cd, vendor_abbr_name
                FROM config.vendors
            """)
        )
        vendors = [dict(row._mapping) for row in result]
    return vendors
