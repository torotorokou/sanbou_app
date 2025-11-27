"""rename raw.receive_raw columns to english

日本語カラム名（37個）を英語カラム名 (*_text サフィックス) にリネーム
raw層はTEXT型のままだが、カラム名を英語化してコードの可読性向上

Revision ID: 20251113_170000000
Revises: 20251113_151137000
Create Date: 2025-11-13 17:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20251113_170000000'
down_revision = '20251113_151137000'
branch_labels = None
depends_on = None


# 日本語 → 英語カラム名のマッピング（37カラム）
COLUMN_RENAME_MAP = {
    "伝票日付": "slip_date_text",
    "売上日付": "sales_date_text",
    "支払日付": "payment_date_text",
    "業者CD": "vendor_cd_text",
    "業者名": "vendor_name_text",
    "伝票区分CD": "slip_type_cd_text",
    "伝票区分名": "slip_type_name_text",
    "品名CD": "item_cd_text",
    "品名": "item_name_text",
    "正味重量": "net_weight_text",
    "数量": "quantity_text",
    "単位CD": "unit_cd_text",
    "単位名": "unit_name_text",
    "単価": "unit_price_text",
    "金額": "amount_text",
    "受入番号": "receive_no_text",
    "集計項目CD": "aggregate_item_cd_text",
    "集計項目": "aggregate_item_name_text",
    "種類CD": "category_cd_text",
    "種類名": "category_name_text",
    "計量時間（総重量）": "weighing_time_gross_text",
    "計量時間（空車重量）": "weighing_time_empty_text",
    "現場CD": "site_cd_text",
    "現場名": "site_name_text",
    "荷降業者CD": "unload_vendor_cd_text",
    "荷降業者名": "unload_vendor_name_text",
    "荷降現場CD": "unload_site_cd_text",
    "荷降現場名": "unload_site_name_text",
    "運搬業者CD": "transport_vendor_cd_text",
    "運搬業者名": "transport_vendor_name_text",
    "取引先CD": "client_cd_text",
    "取引先名": "client_name_text",
    "マニ種類CD": "manifest_type_cd_text",
    "マニ種類名": "manifest_type_name_text",
    "マニフェスト番号": "manifest_no_text",
    "営業担当者CD": "sales_staff_cd_text",
    "営業担当者名": "sales_staff_name_text",
}


def upgrade():
    """
    raw.receive_raw の日本語カラム名を英語にリネーム
    """
    print("Renaming raw.receive_raw columns to English...")
    
    for jp_name, en_name in COLUMN_RENAME_MAP.items():
        try:
            # PostgreSQL では日本語カラム名はダブルクォートで囲む必要がある
            op.execute(f'ALTER TABLE raw.receive_raw RENAME COLUMN "{jp_name}" TO {en_name}')
            print(f"  ✓ '{jp_name}' → '{en_name}'")
        except Exception as e:
            print(f"  ✗ Failed to rename '{jp_name}': {e}")
            raise
    
    print(f"✓ Renamed {len(COLUMN_RENAME_MAP)} columns in raw.receive_raw to English (_text suffix)")


def downgrade():
    """
    英語カラム名を日本語に戻す
    """
    print("Reverting raw.receive_raw columns to Japanese...")
    
    # 逆マッピング
    reverse_map = {en: jp for jp, en in COLUMN_RENAME_MAP.items()}
    
    for en_name, jp_name in reverse_map.items():
        try:
            op.execute(f'ALTER TABLE raw.receive_raw RENAME COLUMN {en_name} TO "{jp_name}"')
            print(f"  ✓ '{en_name}' → '{jp_name}'")
        except Exception as e:
            print(f"  ✗ Failed to rename '{en_name}': {e}")
            raise
    
    print(f"✓ Reverted {len(reverse_map)} columns in raw.receive_raw to Japanese")
