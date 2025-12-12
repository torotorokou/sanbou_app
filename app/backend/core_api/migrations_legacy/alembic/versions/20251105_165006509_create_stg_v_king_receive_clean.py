"""create stg.v_king_receive_clean

Revision ID: 20251105_165006509
Revises: 20251105_164859366
Create Date: 2025-11-05 07:50:07.224712
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251105_165006509"
down_revision = "20251105_164859366"
branch_labels = None
depends_on = None


def upgrade():
    # 念のため stg スキーマを用意
    op.execute("CREATE SCHEMA IF NOT EXISTS stg;")

    # IMMUTABLE関数のみで invoice_d を生成し、重複列を避けるために k.* のみにする
    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
        SELECT
          -- 文字列日付 → DATE（replace + split_part + make_date は IMMUTABLE）
          make_date(
            split_part(replace(k.invoice_date, '/', '-'), '-', 1)::int,
            split_part(replace(k.invoice_date, '/', '-'), '-', 2)::int,
            split_part(replace(k.invoice_date, '/', '-'), '-', 3)::int
          ) AS invoice_d,
          k.*  -- raw の全列をそのまま（invoice_no など重複指定はしない）
        FROM raw.receive_king_final k
        WHERE
          k.vehicle_type_code = 1
          AND k.net_weight_detail <> 0
          AND k.invoice_date ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'
          AND split_part(replace(k.invoice_date,'/','-'), '-', 2)::int BETWEEN 1 AND 12
          AND split_part(replace(k.invoice_date,'/','-'), '-', 3)::int BETWEEN 1 AND 31
        ;
        """
    )

    # （任意）権限付与：必要なロールに合わせて調整
    op.execute("GRANT USAGE ON SCHEMA stg TO myuser;")
    op.execute("GRANT SELECT ON stg.v_king_receive_clean TO myuser;")

    # （任意）メタ情報
    op.execute(
        "COMMENT ON VIEW stg.v_king_receive_clean IS 'King受入データのクレンジング済みビュー（invoice_d=DATE, フィルタ済み）';"
    )
    op.execute(
        "COMMENT ON COLUMN stg.v_king_receive_clean.invoice_d IS 'invoice_date(文字列)から生成したDATE列';"
    )


def downgrade():
    # 参照しているオブジェクトがあれば失敗するため CASCADE は付けない（必要なら手で依存解消）
    op.execute("DROP VIEW IF EXISTS stg.v_king_receive_clean;")
