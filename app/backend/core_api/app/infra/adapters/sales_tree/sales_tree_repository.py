"""
Sales Tree Repository - sandbox.v_sales_tree_daily からのデータ取得

売上ツリー分析用のリポジトリ実装
データソース: sandbox.v_sales_tree_daily (Materialized View の公開ビュー)
"""
import logging
import csv
import io
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.sales_tree import (
    SummaryRequest,
    SummaryRow,
    MetricEntry,
    DailySeriesRequest,
    DailyPoint,
    PivotRequest,
    CursorPage,
    ExportRequest,
    AxisMode,
)
from app.infra.db.db import get_engine

logger = logging.getLogger(__name__)


class SalesTreeRepository:
    """
    売上ツリー分析Repository
    
    データソース: sandbox.v_sales_tree_daily
    - sales_date, rep_id, rep_name, customer_id, customer_name,
      item_id, item_name, amount_yen, qty_ton, slip_count
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._engine = get_engine()
    
    def fetch_summary(self, req: SummaryRequest) -> list[SummaryRow]:
        """
        サマリーデータ取得
        
        営業ごとに、指定軸（customer/item/date）でTOP-N集計
        
        処理フロー:
        1. v_sales_tree_daily から期間・営業でフィルタ
        2. mode に応じて GROUP BY 軸を切り替え
        3. rep_id ごとに TOP-N を抽出（Window Function or Python側ソート）
        """
        try:
            logger.info(f"fetch_summary: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}, rep_ids={req.rep_ids}")
            
            # 軸カラムの決定
            axis_id_col, axis_name_col = self._get_axis_columns(req.mode)
            
            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to"
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
            }
            
            if req.rep_ids:
                # rep_ids は integer のリスト
                where_clauses.append(f"rep_id = ANY(:rep_ids)")
                params["rep_ids"] = req.rep_ids
            
            if req.filter_ids:
                # filter_ids はaxis_id_colの型に応じて処理
                # customer_id: text, item_id: integer, sales_date: date
                if req.mode == "customer":
                    where_clauses.append(f"customer_id = ANY(:filter_ids)")
                    params["filter_ids"] = req.filter_ids
                elif req.mode == "item":
                    # item_id は integer なので変換
                    where_clauses.append(f"item_id = ANY(:filter_ids)")
                    params["filter_ids"] = [int(fid) for fid in req.filter_ids]
                elif req.mode == "date":
                    # sales_date は date なので変換
                    where_clauses.append(f"sales_date = ANY(:filter_ids)")
                    params["filter_ids"] = [str(fid) for fid in req.filter_ids]
            
            where_sql = " AND ".join(where_clauses)
            
            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()
            
            # TOP-N制限
            limit_sql = "" if req.top_n == 0 else f"LIMIT {req.top_n}"
            
            # SQL構築（営業ごとにWINDOW関数でランキング）
            # ただし、PostgreSQLのWINDOW関数でTOP-Nを抽出するのは複雑なため、
            # ここでは営業ごとに全データを取得してPython側でTOP-N抽出
            sql = f"""
WITH aggregated AS (
    SELECT
        rep_id,
        rep_name,
        {axis_id_col} AS axis_id,
        {axis_name_col} AS axis_name,
        SUM(amount_yen) AS amount,
        SUM(qty_kg) AS qty,
        SUM(slip_count) AS slip_count,
        CASE
            WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg)
            ELSE NULL
        END AS unit_price
    FROM sandbox.v_sales_tree_daily
    WHERE {where_sql}
    GROUP BY rep_id, rep_name, {axis_id_col}, {axis_name_col}
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY rep_id ORDER BY {sort_col} {order_dir}) AS rn
    FROM aggregated
)
SELECT
    rep_id,
    rep_name,
    axis_id,
    axis_name,
    amount,
    qty,
    slip_count,
    unit_price
FROM ranked
WHERE rn <= :top_n OR :top_n = 0
ORDER BY rep_id, rn
            """
            
            params["top_n"] = req.top_n if req.top_n > 0 else 999999
            
            with self._engine.begin() as conn:
                result = conn.execute(text(sql), params).mappings().all()
            
            # 営業ごとにグルーピング
            summary_dict: dict[int, SummaryRow] = {}
            for row in result:
                rep_id = row["rep_id"]
                if rep_id not in summary_dict:
                    summary_dict[rep_id] = SummaryRow(
                        rep_id=rep_id,
                        rep_name=row["rep_name"],
                        metrics=[]
                    )
                
                # MetricEntry作成
                axis_id_str = str(row["axis_id"])
                date_key = axis_id_str if req.mode == "date" else None
                
                metric = MetricEntry(
                    id=axis_id_str,
                    name=row["axis_name"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    slip_count=int(row["slip_count"]) if row["slip_count"] is not None else 0,
                    unit_price=float(row["unit_price"]) if row["unit_price"] is not None else None,
                    date_key=date_key
                )
                summary_dict[rep_id].metrics.append(metric)
            
            result_list = list(summary_dict.values())
            logger.info(f"fetch_summary: returned {len(result_list)} reps")
            return result_list
        
        except Exception as e:
            logger.error(f"Error in fetch_summary: {str(e)}", exc_info=True)
            raise
    
    def fetch_daily_series(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """
        日次推移データ取得
        
        指定条件（営業/顧客/品目）での日別集計を返す
        """
        try:
            logger.info(f"fetch_daily_series: date_from={req.date_from}, date_to={req.date_to}, rep_id={req.rep_id}, customer_id={req.customer_id}, item_id={req.item_id}")
            
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to"
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
            }
            
            if req.rep_id is not None:
                where_clauses.append("rep_id = :rep_id")
                params["rep_id"] = req.rep_id
            
            if req.customer_id is not None:
                where_clauses.append("customer_id = :customer_id")
                params["customer_id"] = req.customer_id
            
            if req.item_id is not None:
                where_clauses.append("item_id = :item_id")
                params["item_id"] = req.item_id
            
            where_sql = " AND ".join(where_clauses)
            
            sql = f"""
SELECT
    sales_date AS date,
    SUM(amount_yen) AS amount,
    SUM(qty_kg) AS qty,
    SUM(slip_count) AS slip_count,
    CASE
        WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg)
        ELSE NULL
    END AS unit_price
FROM sandbox.v_sales_tree_daily
WHERE {where_sql}
GROUP BY sales_date
ORDER BY sales_date
            """
            
            with self._engine.begin() as conn:
                result = conn.execute(text(sql), params).mappings().all()
            
            points = [
                DailyPoint(
                    date=row["date"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    slip_count=int(row["slip_count"]) if row["slip_count"] is not None else 0,
                    unit_price=float(row["unit_price"]) if row["unit_price"] is not None else None
                )
                for row in result
            ]
            
            logger.info(f"fetch_daily_series: returned {len(points)} points")
            return points
        
        except Exception as e:
            logger.error(f"Error in fetch_daily_series: {str(e)}", exc_info=True)
            raise
    
    def fetch_pivot(self, req: PivotRequest) -> CursorPage:
        """
        Pivotデータ取得（詳細ドリルダウン）
        
        固定軸（baseAxis + baseId）に対して、別の軸（targetAxis）で展開
        例: 顧客「泉土木」(base) に対して、品目別(target)の内訳を取得
        
        処理フロー:
        1. baseAxisとbaseIdでフィルタ
        2. targetAxisでGROUP BY集計
        3. ソート・TOP-N・ページネーション適用
        """
        try:
            logger.info(f"fetch_pivot: base={req.base_axis}:{req.base_id}, target={req.target_axis}, date_from={req.date_from}, date_to={req.date_to}")
            
            # 軸カラムの決定
            base_id_col, _ = self._get_axis_columns(req.base_axis)
            target_id_col, target_name_col = self._get_axis_columns(req.target_axis)
            
            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to"
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
            }
            
            # baseAxisフィルタ
            if req.base_axis == "customer":
                where_clauses.append(f"customer_id = :base_id")
                params["base_id"] = req.base_id
            elif req.base_axis == "item":
                where_clauses.append(f"item_id = :base_id")
                params["base_id"] = int(req.base_id)
            elif req.base_axis == "date":
                where_clauses.append(f"sales_date = :base_id")
                params["base_id"] = req.base_id
            
            # rep_idsフィルタ
            if req.rep_ids:
                where_clauses.append(f"rep_id = ANY(:rep_ids)")
                params["rep_ids"] = req.rep_ids
            
            where_sql = " AND ".join(where_clauses)
            
            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()
            
            # カーソル（オフセット）
            offset = int(req.cursor) if req.cursor else 0
            page_size = 30  # 固定ページサイズ
            limit = req.top_n if req.top_n > 0 else 999999
            
            # SQL構築
            sql = f"""
WITH aggregated AS (
    SELECT
        {target_id_col} AS target_id,
        {target_name_col} AS target_name,
        SUM(amount_yen) AS amount,
        SUM(qty_kg) AS qty,
        SUM(slip_count) AS slip_count,
        CASE
            WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg)
            ELSE NULL
        END AS unit_price
    FROM sandbox.v_sales_tree_daily
    WHERE {where_sql}
    GROUP BY {target_id_col}, {target_name_col}
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY {sort_col} {order_dir}) AS rn
    FROM aggregated
)
SELECT
    target_id,
    target_name,
    amount,
    qty,
    slip_count,
    unit_price
FROM ranked
WHERE rn <= :limit
ORDER BY rn
LIMIT :page_size OFFSET :offset
            """
            
            params["limit"] = limit
            params["page_size"] = page_size
            params["offset"] = offset
            
            with self._engine.begin() as conn:
                result = conn.execute(text(sql), params).mappings().all()
            
            # MetricEntry作成
            rows = []
            for row in result:
                target_id_str = str(row["target_id"])
                date_key = target_id_str if req.target_axis == "date" else None
                
                metric = MetricEntry(
                    id=target_id_str,
                    name=row["target_name"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    slip_count=int(row["slip_count"]) if row["slip_count"] is not None else 0,
                    unit_price=float(row["unit_price"]) if row["unit_price"] is not None else None,
                    date_key=date_key
                )
                rows.append(metric)
            
            # 次ページカーソル
            next_cursor = None
            if len(rows) == page_size:
                next_cursor = str(offset + page_size)
            
            logger.info(f"fetch_pivot: returned {len(rows)} rows, next_cursor={next_cursor}")
            return CursorPage(rows=rows, next_cursor=next_cursor)
        
        except Exception as e:
            logger.error(f"Error in fetch_pivot: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _get_axis_columns(mode: AxisMode) -> tuple[str, str]:
        """軸モードからカラム名を取得"""
        if mode == "customer":
            return "customer_id", "customer_name"
        elif mode == "item":
            return "item_id", "item_name"
        elif mode == "date":
            return "sales_date", "TO_CHAR(sales_date, 'YYYY-MM-DD')"
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    @staticmethod
    def _get_sort_column(sort_by: str) -> str:
        """ソートキーからSQL列名を取得"""
        mapping = {
            "amount": "amount",
            "qty": "qty",
            "slip_count": "slip_count",
            "unit_price": "unit_price",
            "date": "target_id",  # date modeの場合、target_idが日付
            "name": "target_name",
        }
        return mapping.get(sort_by, "amount")
    
    def get_sales_reps(self) -> list[dict]:
        """
        営業マスタを取得
        
        Returns:
            list[dict]: [{"rep_id": int, "rep_name": str}, ...]
        """
        try:
            sql = """
SELECT DISTINCT
    rep_id,
    rep_name
FROM sandbox.v_sales_tree_daily
WHERE rep_id IS NOT NULL AND rep_name IS NOT NULL
ORDER BY rep_id
            """
            with self._engine.begin() as conn:
                result = conn.execute(text(sql)).mappings().all()
            
            return [
                {"rep_id": row["rep_id"], "rep_name": row["rep_name"]}
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error in get_sales_reps: {str(e)}", exc_info=True)
            raise
    
    def get_customers(self) -> list[dict]:
        """
        顧客マスタを取得
        
        Returns:
            list[dict]: [{"customer_id": str, "customer_name": str}, ...]
        """
        try:
            sql = """
SELECT DISTINCT
    customer_id,
    customer_name
FROM sandbox.v_sales_tree_daily
WHERE customer_id IS NOT NULL AND customer_name IS NOT NULL
ORDER BY customer_id
            """
            with self._engine.begin() as conn:
                result = conn.execute(text(sql)).mappings().all()
            
            return [
                {"customer_id": row["customer_id"], "customer_name": row["customer_name"]}
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error in get_customers: {str(e)}", exc_info=True)
            raise
    
    def get_items(self) -> list[dict]:
        """
        品目マスタを取得
        
        Returns:
            list[dict]: [{"item_id": int, "item_name": str}, ...]
        """
        try:
            sql = """
SELECT DISTINCT
    item_id,
    item_name
FROM sandbox.v_sales_tree_daily
WHERE item_id IS NOT NULL AND item_name IS NOT NULL
ORDER BY item_id
            """
            with self._engine.begin() as conn:
                result = conn.execute(text(sql)).mappings().all()
            
            return [
                {"item_id": row["item_id"], "item_name": row["item_name"]}
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error in get_items: {str(e)}", exc_info=True)
            raise
    
    def export_csv(self, req: ExportRequest) -> bytes:
        """
        CSV Export
        
        指定条件でサマリーデータをCSV形式で出力
        """
        try:
            logger.info(f"export_csv: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}")
            
            # 軸カラムの決定
            axis_id_col, axis_name_col = self._get_axis_columns(req.mode)
            
            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to"
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
            }
            
            if req.rep_ids:
                where_clauses.append(f"rep_id = ANY(:rep_ids)")
                params["rep_ids"] = req.rep_ids
            
            if req.filter_ids:
                if req.mode == "customer":
                    where_clauses.append(f"customer_id = ANY(:filter_ids)")
                    params["filter_ids"] = req.filter_ids
                elif req.mode == "item":
                    where_clauses.append(f"item_id = ANY(:filter_ids)")
                    params["filter_ids"] = [int(fid) for fid in req.filter_ids]
                elif req.mode == "date":
                    where_clauses.append(f"sales_date = ANY(:filter_ids)")
                    params["filter_ids"] = [str(fid) for fid in req.filter_ids]
            
            where_sql = " AND ".join(where_clauses)
            
            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()
            
            # SQL構築
            sql = f"""
WITH aggregated AS (
    SELECT
        rep_id,
        rep_name,
        {axis_id_col} AS axis_id,
        {axis_name_col} AS axis_name,
        SUM(amount_yen) AS amount,
        SUM(qty_kg) AS qty,
        SUM(slip_count) AS slip_count,
        CASE
            WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg)
            ELSE NULL
        END AS unit_price
    FROM sandbox.v_sales_tree_daily
    WHERE {where_sql}
    GROUP BY rep_id, rep_name, {axis_id_col}, {axis_name_col}
)
SELECT
    rep_id,
    rep_name,
    axis_id,
    axis_name,
    amount,
    qty,
    slip_count,
    unit_price
FROM aggregated
ORDER BY rep_id, {sort_col} {order_dir}
            """
            
            with self._engine.begin() as conn:
                result = conn.execute(text(sql), params).mappings().all()
            
            # CSV生成
            output = io.StringIO()
            writer = csv.writer(output)
            
            # ヘッダー
            axis_label = "顧客" if req.mode == "customer" else "品目" if req.mode == "item" else "日付"
            writer.writerow([
                "営業ID",
                "営業名",
                f"{axis_label}ID",
                f"{axis_label}名",
                "売上金額（円）",
                "数量（kg）",
                "伝票枚数",
                "売単価（円/kg）"
            ])
            
            # データ行
            for row in result:
                writer.writerow([
                    row["rep_id"],
                    row["rep_name"],
                    row["axis_id"],
                    row["axis_name"],
                    f"{row['amount']:.2f}" if row["amount"] else "0.00",
                    f"{row['qty']:.2f}" if row["qty"] else "0.00",
                    row["slip_count"] or 0,
                    f"{row['unit_price']:.2f}" if row["unit_price"] else ""
                ])
            
            # UTF-8 BOM付きでエンコード
            csv_content = output.getvalue()
            csv_bytes = b'\xef\xbb\xbf' + csv_content.encode('utf-8')
            
            logger.info(f"export_csv: generated {len(result)} rows")
            return csv_bytes
        
        except Exception as e:
            logger.error(f"Error in export_csv: {str(e)}", exc_info=True)
            raise
