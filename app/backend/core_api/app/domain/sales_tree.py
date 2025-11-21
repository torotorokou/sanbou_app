"""
Domain models for Sales Tree Analytics - 売上ツリー分析ドメインモデル

機能:
  1. サマリーデータ: 営業×軸別の集計(TOP-N対応)
  2. 日次推移データ: 指定条件での日別集計
  3. Pivotデータ: 固定軸に対する別軸での展開(ドリルダウン)

設計方針:
  - Clean Architecture: Domain層のモデル定義
  - Pydantic: 型安全性とバリデーション
  - フレームワーク非依存: FastAPIの外でも使用可能

使用例:
  # サマリーリクエスト: 顧客別TOP20
  req = SummaryRequest(
      date_from=date(2025, 10, 1),
      date_to=date(2025, 10, 31),
      mode="customer",
      rep_ids=[101, 102],
      top_n=20,
      sort_by="amount",
      order="desc"
  )
"""
from datetime import date as date_type
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ========================================
# Type Definitions
# ========================================
AxisMode = Literal["customer", "item", "date"]
SortKey = Literal["amount", "qty", "slip_count", "unit_price", "date", "name"]
SortOrder = Literal["asc", "desc"]


# ========================================
# Request Models
# ========================================
class SummaryRequest(BaseModel):
    """
    サマリーデータ取得リクエスト
    
    営業ごとに、指定された軸（顧客/品目/日付）でTOP-N集計を取得
    """
    date_from: date_type = Field(..., description="集計開始日")
    date_to: date_type = Field(..., description="集計終了日")
    mode: AxisMode = Field(..., description="集計軸: customer, item, date")
    rep_ids: list[int] = Field(default_factory=list, description="営業IDフィルタ（空=全営業）")
    filter_ids: list[str] = Field(default_factory=list, description="軸IDフィルタ（空=全データ）")
    top_n: int = Field(50, description="TOP-N件数（0=全件）")
    sort_by: SortKey = Field("amount", description="ソート項目")
    order: SortOrder = Field("desc", description="ソート順")


class DailySeriesRequest(BaseModel):
    """
    日次推移データ取得リクエスト
    
    指定された条件（営業/顧客/品目）での日別推移を取得
    """
    date_from: date_type = Field(..., description="取得開始日")
    date_to: date_type = Field(..., description="取得終了日")
    rep_id: Optional[int] = Field(None, description="営業IDフィルタ")
    customer_id: Optional[str] = Field(None, description="顧客IDフィルタ")
    item_id: Optional[int] = Field(None, description="品目IDフィルタ")


class PivotRequest(BaseModel):
    """
    Pivotデータ取得リクエスト（詳細ドリルダウン用）
    
    固定軸（baseAxis + baseId）に対して、別の軸（targetAxis）で展開
    例: 顧客「泉土木」に対して、品目別の内訳を取得
    """
    date_from: date_type = Field(..., description="集計開始日")
    date_to: date_type = Field(..., description="集計終了日")
    base_axis: AxisMode = Field(..., description="固定軸: customer, item, date")
    base_id: str = Field(..., description="固定値ID（顧客ID/品目ID/日付文字列）")
    rep_ids: list[int] = Field(default_factory=list, description="営業IDフィルタ（空=全営業）")
    target_axis: AxisMode = Field(..., description="展開軸: customer, item, date")
    top_n: int = Field(50, description="TOP-N件数（0=全件）")
    sort_by: SortKey = Field("amount", description="ソート項目")
    order: SortOrder = Field("desc", description="ソート順")
    cursor: Optional[str] = Field(None, description="ページネーションカーソル（オフセット値）")


# ========================================
# Response Models
# ========================================
class MetricEntry(BaseModel):
    """
    メトリクスエントリ（集計結果1行）
    """
    id: str = Field(..., description="ID（顧客ID, 品目ID, 日付文字列など）")
    name: str = Field(..., description="名称（顧客名, 品目名, 日付文字列など）")
    amount: float = Field(..., description="売上金額（円）")
    qty: float = Field(..., description="数量（kg）")
    slip_count: int = Field(..., description="伝票枚数")
    unit_price: Optional[float] = Field(None, description="単価（円/kg）")
    date_key: Optional[str] = Field(None, description="日付キー（mode=dateの場合のみ）")


class SummaryRow(BaseModel):
    """
    営業ごとのサマリー行
    """
    rep_id: int = Field(..., description="営業ID")
    rep_name: str = Field(..., description="営業名")
    metrics: list[MetricEntry] = Field(default_factory=list, description="TOP-Nメトリクス")


class DailyPoint(BaseModel):
    """
    日次推移データポイント
    """
    date: date_type = Field(..., description="日付")
    amount: float = Field(..., description="売上金額（円）")
    qty: float = Field(..., description="数量（kg）")
    slip_count: int = Field(..., description="伝票件数")
    unit_price: Optional[float] = Field(None, description="単価（円/kg）")


class CursorPage(BaseModel):
    """
    カーソルベースページネーション結果
    """
    rows: list[MetricEntry] = Field(..., description="データ行")
    next_cursor: Optional[str] = Field(None, description="次ページのカーソル（なければNull）")


class ExportRequest(BaseModel):
    """
    CSV Export リクエスト
    
    指定された条件でCSVファイルを生成
    """
    date_from: date_type = Field(..., description="集計開始日")
    date_to: date_type = Field(..., description="集計終了日")
    mode: AxisMode = Field(..., description="集計軸: customer, item, date")
    rep_ids: list[int] = Field(default_factory=list, description="営業IDフィルタ（空=全営業）")
    filter_ids: list[str] = Field(default_factory=list, description="軸IDフィルタ（空=全データ）")
    sort_by: SortKey = Field("amount", description="ソート項目")
    order: SortOrder = Field("desc", description="ソート順")
