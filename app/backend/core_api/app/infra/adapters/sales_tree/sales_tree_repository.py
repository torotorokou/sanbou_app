"""
Sales Tree Repository - {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} からのデータ取得

売上ツリー分析用のリポジトリ実装
データソース: {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} (明細レベルの事実テーブルビュー)
  → stg.v_active_shogun_final_receive (確定受入データ、is_deleted=falseのみ) ※2025-12-01より変更
  → backend_shared.db.names の定数を使用してDBオブジェクト参照
"""

import csv
import io

from app.core.domain.sales_tree import (
    AxisMode,
    CategoryKind,
    CursorPage,
    DailyPoint,
    DailySeriesRequest,
    ExportRequest,
    MetricEntry,
    PivotRequest,
    SummaryRequest,
    SummaryRow,
)
from app.core.domain.sales_tree_detail import (
    DetailLine,
    DetailLinesRequest,
    DetailLinesResponse,
)
from app.infra.db.db import get_engine
from app.infra.db.sql_loader import load_sql
from backend_shared.application.logging import create_log_context, get_module_logger
from backend_shared.db.names import (
    SCHEMA_MART,
    V_SALES_TREE_DETAIL_BASE,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = get_module_logger(__name__)


class SalesTreeRepository:
    """
    売上ツリー分析Repository

    データソース: mart.v_sales_tree_detail_base
    - sales_date, rep_id, rep_name, customer_id, customer_name,
      item_id, item_name, amount_yen, qty_kg, slip_no
    - 集計時に line_count=COUNT(*) と slip_count=COUNT(DISTINCT slip_no) を計算
    """

    def __init__(self, db: Session):
        self.db = db
        self._engine = get_engine()
        # Pre-load SQL templates
        self._fetch_summary_sql_template = load_sql(
            "sales_tree/sales_tree_repo__fetch_summary.sql"
        )
        self._fetch_daily_series_sql_template = load_sql(
            "sales_tree/sales_tree_repo__fetch_daily_series.sql"
        )
        self._fetch_pivot_sql_template = load_sql(
            "sales_tree/sales_tree_repo__fetch_pivot.sql"
        )
        self._export_csv_sql_template = load_sql(
            "sales_tree/sales_tree_repo__export_csv.sql"
        )
        self._fetch_detail_lines_item_sql_template = load_sql(
            "sales_tree/sales_tree_repo__fetch_detail_lines_item.sql"
        )
        self._fetch_detail_lines_slip_sql_template = load_sql(
            "sales_tree/sales_tree_repo__fetch_detail_lines_slip.sql"
        )
        # Pre-load and format static SQL queries (simple SELECT DISTINCT)
        template_reps = load_sql("sales_tree/sales_tree_repo__get_sales_reps.sql")
        self._get_sales_reps_sql = text(
            template_reps.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
            )
        )
        template_customers = load_sql("sales_tree/sales_tree_repo__get_customers.sql")
        self._get_customers_sql = text(
            template_customers.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
            )
        )
        template_items = load_sql("sales_tree/sales_tree_repo__get_items.sql")
        self._get_items_sql = text(
            template_items.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
            )
        )

    def fetch_summary(self, req: SummaryRequest) -> list[SummaryRow]:
        """
        サマリーデータ取得

        機能:
          - 営業ごとに、指定軸（customer/item/date）でTOP-N集計
          - ソート項目: amount, qty, slip_count, line_count, unit_price, date, name
          - フィルタ: rep_ids, filter_ids（軸IDの絞り込み）

        処理フロー:
          1. {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} から期間・営業でフィルタ
          2. mode に応じて GROUP BY 軸を切り替え
             - customer: customer_id, customer_name
             - item: item_id, item_name
             - date: sales_date, sales_date
          3. 集計時に line_count=COUNT(*) と slip_count=COUNT(DISTINCT slip_no) を両方計算
          4. rep_id ごとに TOP-N を抽出（Window Function: ROW_NUMBER()）
          5. 営業ごとに SummaryRow として集約

        パフォーマンス最適化:
          - Window FunctionでDB側でTOP-N抽出（Pythonループより高速）
          - {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} は明細レベルの事実テーブル

        Args:
            req: SummaryRequest（date_from, date_to, mode, rep_ids, filter_ids, top_n, sort_by, order）

        Returns:
            list[SummaryRow]: 営業ごとのサマリーデータ（metrics に TOP-N 集計を格納）
        """
        try:
            logger.info(
                "fetch_summary開始",
                extra=create_log_context(
                    operation="fetch_summary",
                    mode=req.mode,
                    date_from=str(req.date_from),
                    date_to=str(req.date_to),
                    rep_ids=req.rep_ids,
                    category_kind=req.category_kind,
                ),
            )

            # 軸カラムの決定
            axis_id_col, axis_name_col = self._get_axis_columns(req.mode)

            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to",
                "category_cd = :category_cd",
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
                "category_cd": self._category_kind_to_cd(req.category_kind),
            }

            if req.rep_ids:
                # rep_ids は integer のリスト - PostgreSQL配列構文を使用
                rep_ids_str = ", ".join(str(rid) for rid in req.rep_ids)
                where_clauses.append(f"rep_id = ANY(ARRAY[{rep_ids_str}])")

            if req.filter_ids:
                # filter_ids はaxis_id_colの型に応じて処理
                # customer_id: text, item_id: integer, sales_date: date
                if req.mode == "customer":
                    where_clauses.append("customer_id = ANY(:filter_ids)")
                    params["filter_ids"] = req.filter_ids
                elif req.mode == "item":
                    # item_id は integer なので変換
                    where_clauses.append("item_id = ANY(:filter_ids)")
                    params["filter_ids"] = [int(fid) for fid in req.filter_ids]
                elif req.mode == "date":
                    # sales_date は date なので変換
                    where_clauses.append("sales_date = ANY(:filter_ids)")
                    params["filter_ids"] = [str(fid) for fid in req.filter_ids]

            where_sql = " AND ".join(where_clauses)

            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()

            # SQL テンプレートに置換（外部ファイルから読み込み済み）
            sql_str = self._fetch_summary_sql_template.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                axis_id_col=axis_id_col,
                axis_name_col=axis_name_col,
                where_sql=where_sql,
                sort_col=sort_col,
                order_dir=order_dir,
            )

            params["top_n"] = req.top_n if req.top_n > 0 else 999999

            with self._engine.begin() as conn:
                result = conn.execute(text(sql_str), params).mappings().all()

            # 営業ごとにグルーピング
            summary_dict: dict[int, SummaryRow] = {}
            for row in result:
                rep_id = row["rep_id"]
                if rep_id not in summary_dict:
                    summary_dict[rep_id] = SummaryRow(
                        rep_id=rep_id, rep_name=row["rep_name"], metrics=[]
                    )

                # MetricEntry作成
                axis_id_str = str(row["axis_id"])
                date_key = axis_id_str if req.mode == "date" else None

                line_count = (
                    int(row["line_count"]) if row["line_count"] is not None else 0
                )
                slip_count = (
                    int(row["slip_count"]) if row["slip_count"] is not None else 0
                )

                # ルール: 商品軸の場合は件数(line_count)、それ以外は台数(slip_count)
                count = line_count if req.mode == "item" else slip_count

                metric = MetricEntry(
                    id=axis_id_str,
                    name=row["axis_name"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    line_count=line_count,
                    slip_count=slip_count,
                    count=count,
                    unit_price=(
                        float(row["unit_price"])
                        if row["unit_price"] is not None
                        else None
                    ),
                    date_key=date_key,
                )
                summary_dict[rep_id].metrics.append(metric)

            result_list = list(summary_dict.values())
            logger.info(
                "fetch_summary完了",
                extra=create_log_context(
                    operation="fetch_summary", reps_count=len(result_list)
                ),
            )
            return result_list

        except Exception as e:
            logger.error(
                "fetch_summaryエラー",
                extra=create_log_context(operation="fetch_summary", error=str(e)),
                exc_info=True,
            )
            raise

    def fetch_daily_series(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """
        日次推移データ取得

        指定条件（営業/顧客/品目）での日別集計を返す
        """
        try:
            logger.info(
                "fetch_daily_series開始",
                extra=create_log_context(
                    operation="fetch_daily_series",
                    date_from=str(req.date_from),
                    date_to=str(req.date_to),
                    rep_id=req.rep_id,
                    customer_id=req.customer_id,
                    item_id=req.item_id,
                ),
            )

            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to",
                "category_cd = :category_cd",
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
                "category_cd": self._category_kind_to_cd(req.category_kind),
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

            # SQL テンプレートに置換（外部ファイルから読み込み済み）
            sql_str = self._fetch_daily_series_sql_template.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                where_sql=where_sql,
            )

            with self._engine.begin() as conn:
                result = conn.execute(text(sql_str), params).mappings().all()

            points = [
                DailyPoint(
                    date=row["date"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    line_count=(
                        int(row["line_count"]) if row["line_count"] is not None else 0
                    ),
                    slip_count=(
                        int(row["slip_count"]) if row["slip_count"] is not None else 0
                    ),
                    count=(
                        int(row["slip_count"]) if row["slip_count"] is not None else 0
                    ),  # 日次推移は台数を使用
                    unit_price=(
                        float(row["unit_price"])
                        if row["unit_price"] is not None
                        else None
                    ),
                )
                for row in result
            ]

            logger.info(
                "fetch_daily_series完了",
                extra=create_log_context(
                    operation="fetch_daily_series", points_count=len(points)
                ),
            )
            return points

        except Exception as e:
            logger.error(
                "fetch_daily_seriesエラー",
                extra=create_log_context(operation="fetch_daily_series", error=str(e)),
                exc_info=True,
            )
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
            logger.info(
                "fetch_pivot開始",
                extra=create_log_context(
                    operation="fetch_pivot",
                    base_axis=req.base_axis,
                    base_id=str(req.base_id),
                    target_axis=req.target_axis,
                    date_from=str(req.date_from),
                    date_to=str(req.date_to),
                    rep_ids=req.rep_ids,
                    category_kind=req.category_kind,
                ),
            )

            # 軸カラムの決定
            base_id_col, _ = self._get_axis_columns(req.base_axis)
            target_id_col, target_name_col = self._get_axis_columns(req.target_axis)

            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to",
                "category_cd = :category_cd",
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
                "category_cd": self._category_kind_to_cd(req.category_kind),
            }

            # baseAxisフィルタ
            if req.base_axis == "customer":
                where_clauses.append("customer_id = :base_id")
                params["base_id"] = req.base_id
            elif req.base_axis == "item":
                where_clauses.append("item_id = :base_id")
                params["base_id"] = int(req.base_id)
            elif req.base_axis == "date":
                where_clauses.append("sales_date = :base_id")
                params["base_id"] = req.base_id

            # rep_idsフィルタ
            if req.rep_ids:
                # PostgreSQL配列構文を使用: = ANY(ARRAY[val1, val2, ...])
                rep_ids_str = ", ".join(str(rid) for rid in req.rep_ids)
                where_clauses.append(f"rep_id = ANY(ARRAY[{rep_ids_str}])")

            where_sql = " AND ".join(where_clauses)

            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()

            # カーソル（オフセット）
            offset = int(req.cursor) if req.cursor else 0
            page_size = 30  # 固定ページサイズ
            limit = req.top_n if req.top_n > 0 else 999999

            # SQL テンプレートに置換（外部ファイルから読み込み済み）
            sql_str = self._fetch_pivot_sql_template.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                target_id_col=target_id_col,
                target_name_col=target_name_col,
                where_sql=where_sql,
                sort_col=sort_col,
                order_dir=order_dir,
            )

            params["limit"] = limit
            params["page_size"] = page_size
            params["offset"] = offset

            logger.info(
                "fetch_pivot SQL実行",
                extra=create_log_context(
                    operation="fetch_pivot", where_sql=where_sql, params=str(params)
                ),
            )

            with self._engine.begin() as conn:
                result = conn.execute(text(sql_str), params).mappings().all()

            # MetricEntry作成
            rows = []
            for row in result:
                target_id_str = str(row["target_id"])
                date_key = target_id_str if req.target_axis == "date" else None

                line_count = (
                    int(row["line_count"]) if row["line_count"] is not None else 0
                )
                slip_count = (
                    int(row["slip_count"]) if row["slip_count"] is not None else 0
                )

                # ルール: target_axisが商品の場合は件数(line_count)、それ以外は台数(slip_count)
                count = line_count if req.target_axis == "item" else slip_count

                metric = MetricEntry(
                    id=target_id_str,
                    name=row["target_name"],
                    amount=float(row["amount"]) if row["amount"] is not None else 0.0,
                    qty=float(row["qty"]) if row["qty"] is not None else 0.0,
                    line_count=line_count,
                    slip_count=slip_count,
                    count=count,
                    unit_price=(
                        float(row["unit_price"])
                        if row["unit_price"] is not None
                        else None
                    ),
                    date_key=date_key,
                )
                rows.append(metric)

            # 次ページカーソル
            next_cursor = None
            if len(rows) == page_size:
                next_cursor = str(offset + page_size)

            logger.info(
                "fetch_pivot完了",
                extra=create_log_context(
                    operation="fetch_pivot",
                    rows_count=len(rows),
                    next_cursor=next_cursor,
                ),
            )
            return CursorPage(rows=rows, next_cursor=next_cursor)

        except Exception as e:
            logger.error(
                "fetch_pivotエラー",
                extra=create_log_context(operation="fetch_pivot", error=str(e)),
                exc_info=True,
            )
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

    @staticmethod
    def _category_kind_to_cd(category_kind: CategoryKind) -> int:
        """
        CategoryKindをcategory_cdに変換

        waste: 1 (処分費のみ)
        valuable: 3 (有価物)

        注: category_cd=2 (運搬費) は除外
        """
        return 1 if category_kind == "waste" else 3

    def get_sales_reps(self, category_kind: CategoryKind = "waste") -> list[dict]:
        """
        【SalesTree分析専用】営業フィルタ候補を取得

        NOTE: これは「営業マスタAPI」ではありません。
        {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} から SELECT DISTINCT で動的に取得します。

        Args:
            category_kind: カテゴリ種別（'waste' or 'valuable'）

        Returns:
            list[dict]: [{"rep_id": int, "rep_name": str}, ...]
        """
        try:
            category_cd = self._category_kind_to_cd(category_kind)
            # SQL は __init__ で読み込み済み
            logger.info(
                f"Executing get_sales_reps SQL with category_kind={category_kind}, category_cd={category_cd}"
            )
            with self._engine.begin() as conn:
                result = (
                    conn.execute(self._get_sales_reps_sql, {"category_cd": category_cd})
                    .mappings()
                    .all()
                )

            reps = [
                {"rep_id": row["rep_id"], "rep_name": row["rep_name"]} for row in result
            ]
            logger.info(
                f"get_sales_reps: Retrieved {len(reps)} reps from mart.v_sales_tree_detail_base"
            )
            if reps:
                logger.info(f"First rep: {reps[0]}")
            else:
                logger.warning(
                    "No sales reps found in {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)}"
                )
            return reps
        except Exception as e:
            logger.error(f"Error in get_sales_reps: {str(e)}", exc_info=True)
            raise

    def get_customers(self, category_kind: CategoryKind = "waste") -> list[dict]:
        """
        【SalesTree分析専用】顧客フィルタ候補を取得

        NOTE: これは「顧客マスタAPI」ではありません。
        {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} から SELECT DISTINCT で動的に取得します。

        Args:
            category_kind: カテゴリ種別（'waste' or 'valuable'）

        Returns:
            list[dict]: [{"customer_id": str, "customer_name": str}, ...]
        """
        try:
            category_cd = self._category_kind_to_cd(category_kind)
            # SQL は __init__ で読み込み済み
            logger.info(
                f"Executing get_customers SQL with category_kind={category_kind}, category_cd={category_cd}"
            )
            with self._engine.begin() as conn:
                result = (
                    conn.execute(self._get_customers_sql, {"category_cd": category_cd})
                    .mappings()
                    .all()
                )

            customers = [
                {
                    "customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                }
                for row in result
            ]
            logger.info(
                f"get_customers: Retrieved {len(customers)} customers from mart.v_sales_tree_detail_base"
            )
            if not customers:
                logger.warning(
                    "No customers found in {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)}"
                )
            return customers
        except Exception as e:
            logger.error(f"Error in get_customers: {str(e)}", exc_info=True)
            raise

    def get_items(self, category_kind: CategoryKind = "waste") -> list[dict]:
        """
        【SalesTree分析専用】商品フィルタ候補を取得

        NOTE: これは「商品マスタAPI」ではありません。
        {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} から SELECT DISTINCT で動的に取得します。

        Args:
            category_kind: カテゴリ種別（'waste' or 'valuable'）

        Returns:
            list[dict]: [{"item_id": int, "item_name": str}, ...]
        """
        try:
            category_cd = self._category_kind_to_cd(category_kind)
            # SQL は __init__ で読み込み済み
            logger.info(
                f"Executing get_items SQL with category_kind={category_kind}, category_cd={category_cd}"
            )
            with self._engine.begin() as conn:
                result = (
                    conn.execute(self._get_items_sql, {"category_cd": category_cd})
                    .mappings()
                    .all()
                )

            items = [
                {"item_id": row["item_id"], "item_name": row["item_name"]}
                for row in result
            ]
            logger.info(
                f"get_items: Retrieved {len(items)} items from mart.v_sales_tree_detail_base"
            )
            if not items:
                logger.warning(
                    "No items found in {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)}"
                )
            return items
        except Exception as e:
            logger.error(f"Error in get_items: {str(e)}", exc_info=True)
            raise

    def export_csv(self, req: ExportRequest) -> bytes:
        """
        CSV Export

        指定条件でサマリーデータをCSV形式で出力
        """
        try:
            logger.info(
                f"export_csv: mode={req.mode}, date_from={req.date_from}, date_to={req.date_to}"
            )

            # 軸カラムの決定
            axis_id_col, axis_name_col = self._get_axis_columns(req.mode)

            # WHERE句構築
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to",
                "category_cd = :category_cd",
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
                "category_cd": self._category_kind_to_cd(req.category_kind),
            }

            if req.rep_ids:
                where_clauses.append("rep_id = ANY(:rep_ids)")
                params["rep_ids"] = req.rep_ids

            if req.filter_ids:
                if req.mode == "customer":
                    where_clauses.append("customer_id = ANY(:filter_ids)")
                    params["filter_ids"] = req.filter_ids
                elif req.mode == "item":
                    where_clauses.append("item_id = ANY(:filter_ids)")
                    params["filter_ids"] = [int(fid) for fid in req.filter_ids]
                elif req.mode == "date":
                    where_clauses.append("sales_date = ANY(:filter_ids)")
                    params["filter_ids"] = [str(fid) for fid in req.filter_ids]

            where_sql = " AND ".join(where_clauses)

            # ソート項目のマッピング
            sort_col = self._get_sort_column(req.sort_by)
            order_dir = req.order.upper()

            # SQL テンプレートに置換（外部ファイルから読み込み済み）
            sql_str = self._export_csv_sql_template.format(
                schema_mart=SCHEMA_MART,
                v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                axis_id_col=axis_id_col,
                axis_name_col=axis_name_col,
                where_sql=where_sql,
                sort_col=sort_col,
                order_dir=order_dir,
            )

            with self._engine.begin() as conn:
                result = conn.execute(text(sql_str), params).mappings().all()

            # CSV生成
            output = io.StringIO()
            writer = csv.writer(output)

            # ヘッダー
            axis_label = (
                "顧客"
                if req.mode == "customer"
                else "品目" if req.mode == "item" else "日付"
            )
            count_label = "件数" if req.mode == "item" else "台数"
            writer.writerow(
                [
                    "営業ID",
                    "営業名",
                    f"{axis_label}ID",
                    f"{axis_label}名",
                    "売上金額（円）",
                    "数量（kg）",
                    count_label,
                    "単価（円/kg）",
                ]
            )

            # データ行
            for row in result:
                # ルール: 商品軸の場合は件数(line_count)、それ以外は台数(slip_count)
                count_value = (
                    row["line_count"] if req.mode == "item" else row["slip_count"]
                )

                writer.writerow(
                    [
                        row["rep_id"],
                        row["rep_name"],
                        row["axis_id"],
                        row["axis_name"],
                        f"{row['amount']:.2f}" if row["amount"] else "0.00",
                        f"{row['qty']:.2f}" if row["qty"] else "0.00",
                        count_value or 0,
                        f"{row['unit_price']:.2f}" if row["unit_price"] else "",
                    ]
                )

            # UTF-8 BOM付きでエンコード
            csv_content = output.getvalue()
            csv_bytes = b"\xef\xbb\xbf" + csv_content.encode("utf-8")

            logger.info(f"export_csv: generated {len(result)} rows")
            return csv_bytes

        except Exception as e:
            logger.error(f"Error in export_csv: {str(e)}", exc_info=True)
            raise

    def fetch_detail_lines(self, req: DetailLinesRequest) -> DetailLinesResponse:
        """
        詳細明細行取得（SalesTree集計行クリック時の詳細表示用）

        最後の集計軸に応じて粒度を切り替える:
        - last_group_by が 'item' の場合:
            → {fq(SCHEMA_MART, V_SALES_TREE_DETAIL_BASE)} の明細行（GROUP BY なし）
        - それ以外の場合:
            → sales_date, slip_no で GROUP BY した伝票単位のサマリ

        Args:
            req: DetailLinesRequest（期間、集計軸、フィルタ条件）

        Returns:
            DetailLinesResponse: 詳細明細行（mode + rows + total_count）
        """
        try:
            logger.info(
                f"fetch_detail_lines: last_group_by={req.last_group_by}, date_from={req.date_from}, date_to={req.date_to}"
            )

            # WHERE句構築（共通フィルタ）
            where_clauses = [
                "sales_date BETWEEN :date_from AND :date_to",
                "category_cd = :category_cd",
            ]
            params: dict = {
                "date_from": req.date_from,
                "date_to": req.date_to,
                "category_cd": self._category_kind_to_cd(req.category_kind),
            }

            # フィルタ条件追加（集計パスを再現）
            if req.rep_id is not None:
                where_clauses.append("rep_id = :rep_id")
                params["rep_id"] = req.rep_id

            if req.customer_id is not None:
                where_clauses.append("customer_id = :customer_id")
                params["customer_id"] = req.customer_id

            if req.item_id is not None:
                where_clauses.append("item_id = :item_id")
                params["item_id"] = req.item_id

            if req.date_value is not None:
                where_clauses.append("sales_date = :date_value")
                params["date_value"] = req.date_value

            where_sql = " AND ".join(where_clauses)

            # モード判定とSQL構築
            if req.last_group_by == "item":
                # 品名で終わる → 明細行そのまま（外部ファイルから読み込み済み）
                mode = "item_lines"
                sql_str = self._fetch_detail_lines_item_sql_template.format(
                    schema_mart=SCHEMA_MART,
                    v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                    where_sql=where_sql,
                )
            else:
                # それ以外 → 伝票単位で集約（外部ファイルから読み込み済み）
                mode = "slip_summary"
                sql_str = self._fetch_detail_lines_slip_sql_template.format(
                    schema_mart=SCHEMA_MART,
                    v_sales_tree_detail_base=V_SALES_TREE_DETAIL_BASE,
                    where_sql=where_sql,
                )

            with self._engine.begin() as conn:
                result = conn.execute(text(sql_str), params).mappings().all()

            # レスポンス構築
            rows: list[DetailLine] = []
            for r in result:
                qty = float(r["qty_kg"] or 0)
                amount = float(r["amount_yen"] or 0)
                unit_price = amount / qty if qty != 0 else None

                if mode == "item_lines":
                    rows.append(
                        DetailLine(
                            mode=mode,
                            sales_date=r["sales_date"],
                            slip_no=int(r["slip_no"]),
                            rep_name=r["rep_name"],
                            customer_name=r["customer_name"],
                            item_id=(
                                int(r["item_id"]) if r["item_id"] is not None else None
                            ),
                            item_name=r["item_name"],
                            line_count=None,
                            qty_kg=qty,
                            unit_price_yen_per_kg=unit_price,
                            amount_yen=amount,
                        )
                    )
                else:  # slip_summary
                    rows.append(
                        DetailLine(
                            mode=mode,
                            sales_date=r["sales_date"],
                            slip_no=int(r["slip_no"]),
                            rep_name=r["rep_name"],
                            customer_name=r["customer_name"],
                            item_id=None,
                            item_name=r["item_name"],  # カンマ区切りの品目名
                            line_count=int(r["line_count"] or 0),
                            qty_kg=qty,
                            unit_price_yen_per_kg=unit_price,
                            amount_yen=amount,
                        )
                    )

            logger.info(f"fetch_detail_lines: returned {len(rows)} rows (mode={mode})")
            return DetailLinesResponse(mode=mode, rows=rows, total_count=len(rows))

        except Exception as e:
            logger.error(f"Error in fetch_detail_lines: {str(e)}", exc_info=True)
            raise
