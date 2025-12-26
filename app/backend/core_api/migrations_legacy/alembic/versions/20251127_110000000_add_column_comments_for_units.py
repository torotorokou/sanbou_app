"""add column comments for units

Revision ID: 20251127_110000000
Revises: 20251127_100000000
Create Date: 2025-11-27 11:00:00.000000

Description:
    カラムの単位をCOMMENTで明記:
    - 金額: 円 (JPY)
    - 重量: kg
    - 単価: 円/kg

    対象:
    - stg.shogun_flash_receive (主要カラム)
    - mart.v_sales_tree_detail_base (ビューの説明)

    目的:
    - ドキュメンタリティ向上
    - 単位の明示化（カラム名から単位サフィックスを削除する準備）
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251127_110000000"
down_revision = "20251127_100000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add column comments to document units"""

    print("[stg] Adding column comments to shogun_flash_receive...")

    # 金額関連
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.amount IS
        '売上金額（単位: 円）- 正味重量 × 単価で計算された取引金額'
    """
    )

    # 重量・数量関連
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.net_weight IS
        '正味重量（単位: kg）- 取引の基準となる重量'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.quantity IS
        '数量 - 取引の数量（単位はunit_nameに依存）'
    """
    )

    # 単価・単位関連
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.unit_price IS
        '単価（単位: 円/kg）- 1kgあたりの取引単価'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.unit_name IS
        '単位名 - 数量の単位（例: kg, 個, 本）'
    """
    )

    # 日付・時刻関連
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.slip_date IS
        '伝票日付（YYYY-MM-DD形式）- 伝票が発行された日付'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.sales_date IS
        '売上日（YYYY-MM-DD形式）- 取引が発生した日付'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.payment_date IS
        '入金日（YYYY-MM-DD形式）- 支払いが完了した日付'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.weighing_time_gross IS
        '総重量計量時刻（HH:MM:SS形式）- 荷受け時の計量時刻'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.weighing_time_empty IS
        '空重量計量時刻（HH:MM:SS形式）- 荷卸し後の計量時刻'
    """
    )

    # マスタ参照 - 顧客（client）
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.client_cd IS
        '顧客コード - 取引先の識別子'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.client_name IS
        '顧客名 - 取引先の正式名称'
    """
    )

    # マスタ参照 - 営業担当
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.sales_staff_cd IS
        '営業担当者コード - 担当営業の識別子'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.sales_staff_name IS
        '営業担当者名 - 担当営業の氏名'
    """
    )

    # マスタ参照 - 品目
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.item_cd IS
        '品目コード - 取引品目の識別子'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.item_name IS
        '品目名 - 取引品目の名称'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.aggregate_item_cd IS
        '集計品目コード - 集計用の品目分類識別子'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.aggregate_item_name IS
        '集計品目名 - 集計用の品目分類名称'
    """
    )

    # カテゴリ・分類
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.category_cd IS
        'カテゴリコード（1=廃棄物, 3=有価物）- 取引品目の分類コード'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.category_name IS
        'カテゴリ名 - 取引品目の分類名称'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.slip_type_cd IS
        '伝票区分コード - 取引種別の識別コード'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.slip_type_name IS
        '伝票区分名 - 売上/仕入等の取引種別名'
    """
    )

    # 伝票・マニフェスト
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.receive_no IS
        '受入番号 - 荷受けの識別番号'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.manifest_no IS
        'マニフェスト番号 - 産業廃棄物管理票の番号'
    """
    )

    # CSV取込情報
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.upload_file_id IS
        'アップロードファイルID - CSVファイルの識別子'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.source_row_no IS
        '元データ行番号 - CSVファイル内の行番号'
    """
    )

    # 論理削除
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.is_deleted IS
        '論理削除フラグ - true: 削除済み, false: 有効'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.deleted_at IS
        '削除日時（UTC） - 論理削除された日時（タイムゾーン: UTC）'
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.deleted_by IS
        '削除実行者 - 論理削除を実行したユーザーID'
    """
    )

    # 監査
    op.execute(
        """
        COMMENT ON COLUMN stg.shogun_flash_receive.created_at IS
        '作成日時（UTC） - レコードが作成された日時（タイムゾーン: UTC）'
    """
    )

    print("[mart] Adding view comment to v_sales_tree_detail_base...")

    op.execute(
        """
        COMMENT ON VIEW mart.v_sales_tree_detail_base IS
        '売上ツリー詳細ベースビュー - 廃棄物・有価物の取引明細を提供

        カラム単位:
        - amount_yen: 円 (JPY)
        - qty_kg: kg
        - unit_price_yen_per_kg: 円/kg

        用途:
        - Sales Pivot分析の基礎データ
        - 営業別・顧客別・品目別の集計
        - 時系列分析（日次・週次・月次）

        更新頻度: CSV取込時に自動更新（マテリアライズドビューの親）'
    """
    )

    print("[ok] Column comments added")


def downgrade() -> None:
    """Remove column comments"""

    print("[stg] Removing column comments from shogun_flash_receive...")

    # 金額・重量・数量・単価関連
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.amount IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.net_weight IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.quantity IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.unit_price IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.unit_name IS NULL")

    # 日付・時刻関連
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.slip_date IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.sales_date IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.payment_date IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.weighing_time_gross IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.weighing_time_empty IS NULL")

    # マスタ参照
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.client_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.client_name IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.sales_staff_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.sales_staff_name IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.item_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.item_name IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.aggregate_item_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.aggregate_item_name IS NULL")

    # カテゴリ・分類
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.category_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.category_name IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.slip_type_cd IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.slip_type_name IS NULL")

    # 伝票・マニフェスト
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.receive_no IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.manifest_no IS NULL")

    # CSV取込情報
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.upload_file_id IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.source_row_no IS NULL")

    # 論理削除
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.is_deleted IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.deleted_at IS NULL")
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.deleted_by IS NULL")

    # 監査
    op.execute("COMMENT ON COLUMN stg.shogun_flash_receive.created_at IS NULL")

    print("[mart] Removing view comment from v_sales_tree_detail_base...")
    op.execute("COMMENT ON VIEW mart.v_sales_tree_detail_base IS NULL")

    print("[ok] Column comments removed")
