"""add customer count columns to reserve_daily_manual

Revision ID: 20251219_002
Revises: 20251219_001
Create Date: 2025-12-19 12:00:00.000000

Purpose:
- Add total_customer_count and fixed_customer_count columns to stg.reserve_daily_manual
- Enable manual input of customer counts (enterprise counts, not truck counts)
- Maintain backward compatibility with existing data (NULL allowed)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251219_002'
down_revision: Union[str, None] = '20251218_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add customer count columns to reserve_daily_manual"""
    
    # 1. Add columns (NULL allowed for backward compatibility)
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        ADD COLUMN IF NOT EXISTS total_customer_count integer NULL;
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        ADD COLUMN IF NOT EXISTS fixed_customer_count integer NULL;
    """)
    
    # 2. Add constraints
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        ADD CONSTRAINT chk_total_customer_count_non_negative 
        CHECK (total_customer_count IS NULL OR total_customer_count >= 0);
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        ADD CONSTRAINT chk_fixed_customer_count_non_negative 
        CHECK (fixed_customer_count IS NULL OR fixed_customer_count >= 0);
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        ADD CONSTRAINT chk_fixed_customer_count_not_exceed_total 
        CHECK (
            fixed_customer_count IS NULL 
            OR total_customer_count IS NULL 
            OR fixed_customer_count <= total_customer_count
        );
    """)
    
    # 3. Add comments
    op.execute("""
        COMMENT ON COLUMN stg.reserve_daily_manual.total_customer_count 
        IS '予約企業数（手入力、NULLの場合はstg.reserve_customer_dailyから算出）';
    """)
    
    op.execute("""
        COMMENT ON COLUMN stg.reserve_daily_manual.fixed_customer_count 
        IS '固定客企業数（手入力、NULLの場合はstg.reserve_customer_dailyから算出）';
    """)


def downgrade() -> None:
    """Remove customer count columns from reserve_daily_manual"""
    
    # 1. Drop constraints
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        DROP CONSTRAINT IF EXISTS chk_fixed_customer_count_not_exceed_total;
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        DROP CONSTRAINT IF EXISTS chk_fixed_customer_count_non_negative;
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        DROP CONSTRAINT IF EXISTS chk_total_customer_count_non_negative;
    """)
    
    # 2. Drop columns
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        DROP COLUMN IF EXISTS fixed_customer_count;
    """)
    
    op.execute("""
        ALTER TABLE stg.reserve_daily_manual
        DROP COLUMN IF EXISTS total_customer_count;
    """)
