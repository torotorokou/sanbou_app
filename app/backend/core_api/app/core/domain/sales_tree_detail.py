"""
Domain models for Sales Tree Detail Lines - 売上ツリー詳細明細行ドメインモデル

機能:
  クリックした行の「最後の軸」に応じて2通りの粒度で詳細テーブルを表示:
  1. 最後の軸が item（品名）の場合 → 明細行（ほぼ生明細）
  2. 最後の軸が item 以外（顧客/日付など）の場合 → 伝票単位サマリ

設計方針:
  - Clean Architecture: Domain層のモデル定義
  - Pydantic: 型安全性とバリデーション
  - 既存のSalesTreeドメインモデルと整合性を保つ

使用例:
  # 詳細行リクエスト: 営業「山田」→顧客「泉土木」→品名「鉄くず」の明細
  req = DetailLinesRequest(
      date_from=date(2025, 10, 1),
      date_to=date(2025, 10, 31),
      last_group_by="item",
      category_kind="waste",
      rep_id=101,
      customer_id="C001",
      item_id=501
  )
"""

from datetime import date as date_type
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# ========================================
# Type Definitions
# ========================================
DetailMode = Literal["item_lines", "slip_summary"]
GroupBy = Literal["rep", "customer", "date", "item"]
CategoryKind = Literal["waste", "valuable"]


# ========================================
# Request Models
# ========================================
class DetailLinesRequest(BaseModel):
    """
    詳細明細行取得リクエスト

    SalesTreeの集計行クリック時に表示する「詳細テーブル」用データ取得リクエスト
    最後の集計軸に応じて、明細行レベル or 伝票単位サマリを返す
    """

    date_from: date_type = Field(..., description="集計開始日")
    date_to: date_type = Field(..., description="集計終了日")
    last_group_by: GroupBy = Field(
        ..., description="最後の集計軸: rep, customer, date, item"
    )
    category_kind: CategoryKind = Field(
        "waste", description="カテゴリ種別: waste, valuable"
    )

    # フィルタ条件（集計パスを再現）
    rep_id: Optional[int] = Field(None, description="営業IDフィルタ")
    customer_id: Optional[str] = Field(None, description="顧客IDフィルタ")
    item_id: Optional[int] = Field(None, description="品目IDフィルタ")
    date_value: Optional[date_type] = Field(
        None, description="日付フィルタ（mode=dateの場合）"
    )


# ========================================
# Response Models
# ========================================
class DetailLine(BaseModel):
    """
    詳細明細行（またはサマリ行）

    mode によって内容が変わる:
    - item_lines: 明細行そのまま（品名まで含む）
    - slip_summary: 伝票単位の集約（品名は含まない）
    """

    model_config = ConfigDict(populate_by_name=True)

    mode: DetailMode = Field(
        ..., description="モード: item_lines, slip_summary", serialization_alias="mode"
    )
    sales_date: date_type = Field(
        ..., description="売上日", serialization_alias="salesDate"
    )
    slip_no: int = Field(
        ..., description="伝票No（receive_no）", serialization_alias="slipNo"
    )
    rep_name: str = Field(..., description="営業名", serialization_alias="repName")
    customer_name: str = Field(
        ..., description="顧客名", serialization_alias="customerName"
    )

    # 品名情報（常に含む。slip_summaryの場合はカンマ区切り）
    item_id: Optional[int] = Field(
        None, description="品目ID（item_lines時のみ）", serialization_alias="itemId"
    )
    item_name: str = Field(
        ...,
        description="品目名（slip_summary時はカンマ区切り）",
        serialization_alias="itemName",
    )

    # 集計値
    line_count: Optional[int] = Field(
        None,
        description="明細行数（slip_summary時のみ）",
        serialization_alias="lineCount",
    )
    qty_kg: float = Field(..., description="数量（kg）", serialization_alias="qtyKg")
    unit_price_yen_per_kg: Optional[float] = Field(
        None, description="単価（円/kg）", serialization_alias="unitPriceYenPerKg"
    )
    amount_yen: float = Field(
        ..., description="金額（円）", serialization_alias="amountYen"
    )


class DetailLinesResponse(BaseModel):
    """
    詳細明細行取得レスポンス
    """

    mode: DetailMode = Field(..., description="返却データのモード")
    rows: list[DetailLine] = Field(..., description="詳細明細行リスト")
    total_count: int = Field(
        ..., description="総行数", serialization_alias="totalCount"
    )
