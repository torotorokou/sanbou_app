from pydantic import BaseModel
from typing import Optional


class Vendor(BaseModel):
    vendor_cd: int
    vendor_abbr_name: Optional[str]
