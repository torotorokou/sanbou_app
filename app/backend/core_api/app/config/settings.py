"""
Settings and configuration for core_api.
Database table names and schema settings can be customized via environment variables.
"""
import os
from typing import Dict

# ========================================
# Shogun CSV Upload Settings
# ========================================

# Schema for raw CSV data
SHOGUN_CSV_SCHEMA = os.getenv("SHOGUN_CSV_SCHEMA", "raw")

# Table names for each CSV type
SHOGUN_TABLE_RECEIVE = os.getenv("SHOGUN_TABLE_RECEIVE", "receive_shogun_flash")
SHOGUN_TABLE_YARD = os.getenv("SHOGUN_TABLE_YARD", "yard_shogun_flash")
SHOGUN_TABLE_SHIPMENT = os.getenv("SHOGUN_TABLE_SHIPMENT", "shipment_shogun_flash")

# Mapping from CSV type to table name
SHOGUN_CSV_TABLE_MAPPING: Dict[str, str] = {
    "receive": SHOGUN_TABLE_RECEIVE,
    "yard": SHOGUN_TABLE_YARD,
    "shipment": SHOGUN_TABLE_SHIPMENT,
}

# CSV temporary storage directory
CSV_TEMP_DIR = os.getenv("CSV_TEMP_DIR", "/backend/app/data/syogun_csv")

# ========================================
# Database Connection
# ========================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@db:5432/sanbou_dev")
