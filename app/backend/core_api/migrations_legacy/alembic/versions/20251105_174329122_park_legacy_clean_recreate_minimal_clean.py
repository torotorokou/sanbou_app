"""park legacy clean & recreate minimal clean

Revision ID: 20251105_174329122
Revises: 20251105_174016896
Create Date: 2025-11-05 08:43:29.934476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251105_174329122'
down_revision = '20251105_174016896'
branch_labels = None
depends_on = None


SQL_RENAME_LEGACY = """
DO $$
BEGIN
  IF to_regclass('stg.v_king_receive_clean') IS NOT NULL THEN
    -- 旧版を退避
    EXECUTE 'ALTER VIEW stg.v_king_receive_clean RENAME TO v_king_receive_clean_legacy';
  END IF;
END $$;
"""

# _min と同等の最小版定義で clean を新規作成（生の raw から）
SQL_CREATE_MINIMAL_CLEAN = """
CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
SELECT
  make_date(
    split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 1)::int,
    split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int,
    split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int
  ) AS invoice_d,
  k.invoice_no,
  k.net_weight_detail,
  k.amount
FROM raw.receive_king_final k
WHERE
  k.vehicle_type_code = 1
  AND k.net_weight_detail <> 0
  AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
  AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 2)::int BETWEEN 1 AND 12
  AND split_part(replace(k.invoice_date::text, '/', '-')::text, '-', 3)::int BETWEEN 1 AND 31;
"""

def upgrade():
    with op.get_context().autocommit_block():
        op.execute(sa.text(SQL_RENAME_LEGACY))
        op.execute(sa.text(SQL_CREATE_MINIMAL_CLEAN))
        op.execute(sa.text("GRANT SELECT ON stg.v_king_receive_clean TO myuser;"))

def downgrade():
    # 簡易ロールバック：新cleanをDROPし、legacyがあれば元名に戻す
    with op.get_context().autocommit_block():
        op.execute(sa.text("DROP VIEW IF EXISTS stg.v_king_receive_clean;"))
        op.execute(sa.text("""
        DO $$
        BEGIN
          IF to_regclass('stg.v_king_receive_clean_legacy') IS NOT NULL THEN
            EXECUTE 'ALTER VIEW stg.v_king_receive_clean_legacy RENAME TO v_king_receive_clean';
          END IF;
        END $$;
        """))