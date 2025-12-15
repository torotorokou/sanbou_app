-- Sales Tree サマリー集計
--
-- 営業ごとに指定軸（customer/item/date）でTOP-N集計を行います。
-- CTE + Window Function (ROW_NUMBER) でランキング取得。
--
-- パラメータ:
--   :date_from   - 開始日
--   :date_to     - 終了日
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--   :top_n       - TOP-N件数（0の場合は全件）
--
-- 動的置換（Python側で文字列置換）:
--   {schema_mart}                 - mart スキーマ
--   {v_sales_tree_detail_base}    - mart.v_sales_tree_detail_base ビュー
--   {axis_id_col}                 - 集計軸IDカラム (customer_id / item_id / sales_date)
--   {axis_name_col}               - 集計軸名カラム (customer_name / item_name / TO_CHAR(...))
--   {where_sql}                   - 動的WHERE句（rep_ids, filter_ids含む）
--   {sort_col}                    - ソート列 (amount / qty / slip_count / unit_price)
--   {order_dir}                   - ソート方向 (ASC / DESC)

WITH aggregated AS (
    SELECT
        rep_id,
        rep_name,
        {axis_id_col} AS axis_id,
        {axis_name_col} AS axis_name,
        SUM(amount_yen) AS amount,
        SUM(qty_kg) AS qty,
        COUNT(*) AS line_count,
        COUNT(DISTINCT slip_no) AS slip_count,
        CASE
            WHEN SUM(qty_kg) > 0 THEN SUM(amount_yen) / SUM(qty_kg)
            ELSE NULL
        END AS unit_price
    FROM "{schema_mart}"."{v_sales_tree_detail_base}"
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
    line_count,
    slip_count,
    unit_price
FROM ranked
WHERE rn <= :top_n OR :top_n = 0
ORDER BY rep_id, rn
