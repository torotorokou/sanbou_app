"""fix v_king_receive_clean to use net_weight_detail column

このマイグレーションは、stg.v_king_receive_clean VIEW の定義を修正します。

問題:
- 現在の VIEW 定義は `net_weight AS net_weight_detail` を使用している
- WHERE 句も `net_weight <> 0` でフィルタしている
- これにより、Python 側の「正味重量_明細」(net_weight_detail) ではなく、
  伝票全体の正味重量 (net_weight) を参照してしまい、トン数が水増しされている

修正内容:
- SELECT 句: `net_weight_detail` カラムをそのまま使用する
- WHERE 句: `net_weight_detail <> 0` でフィルタする
- その他のロジック（日付変換、vehicle_type_code = 1、日付バリデーション）は維持

影響:
- mart.v_receive_daily が stg.v_king_receive_clean を参照しているため、
  KING のトン数集計が正しい明細単位の値になる

Revision ID: 20251121_100000000
Revises: 20251120_200000000
Create Date: 2025-11-21 10:00:00.000000
"""

from alembic import op

revision = "20251121_100000000"
down_revision = "20251120_200000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    stg.v_king_receive_clean を修正:
    - net_weight → net_weight_detail に変更
    - フィルタ条件も net_weight_detail を使用
    """

    print("[stg.v_king_receive_clean] Fixing VIEW to use net_weight_detail column...")

    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
        SELECT
          make_date(
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 1)::integer,
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer,
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer
          ) AS invoice_d,
          k.invoice_no,
          k.net_weight_detail,
          k.amount
        FROM stg.receive_king_final k
        WHERE
          k.vehicle_type_code = 1
          AND k.net_weight_detail <> 0
          AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text
          AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer BETWEEN 1 AND 12
          AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer BETWEEN 1 AND 31;
    """
    )

    print("[ok] stg.v_king_receive_clean now uses net_weight_detail column correctly")


def downgrade() -> None:
    """
    元の（誤った）定義に戻す: net_weight AS net_weight_detail
    """

    print(
        "[stg.v_king_receive_clean] Reverting to old definition (net_weight AS net_weight_detail)..."
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW stg.v_king_receive_clean AS
        SELECT
          make_date(
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 1)::integer,
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer,
            split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer
          ) AS invoice_d,
          k.invoice_no,
          k.net_weight AS net_weight_detail,
          k.amount
        FROM stg.receive_king_final k
        WHERE
          k.vehicle_type_code = 1
          AND k.net_weight <> 0
          AND k.invoice_date::text ~ '^[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}$'::text
          AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 2)::integer BETWEEN 1 AND 12
          AND split_part(replace(k.invoice_date::text, '/'::text, '-'::text), '-'::text, 3)::integer BETWEEN 1 AND 31;
    """
    )

    print("[ok] stg.v_king_receive_clean reverted to old definition")
