-- Sales Tree CSV エクスポート用集計
--
-- 営業別・指定軸での全データ集計（ページングなし）
--
-- パラメータ:
--   :date_from   - 開始日
--   :date_to     - 終了日
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--
-- 動的置換:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー
--   {axis_id_col}              - 集計軸IDカラム
--   {axis_name_col}            - 集計軸名カラム
--   {where_sql}                - 動的WHERE句
--   {sort_col}                 - ソート列
--   {order_dir}                - ソート方向

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
FROM aggregated
ORDER BY rep_id, {sort_col} {order_dir}
