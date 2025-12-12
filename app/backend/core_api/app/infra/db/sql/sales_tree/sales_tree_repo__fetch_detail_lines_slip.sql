-- Sales Tree 詳細明細行取得（伝票サマリレベル）
--
-- 集計軸が品目以外の場合、伝票単位でGROUP BYして返す
--
-- パラメータ:
--   :date_from   - 開始日
--   :date_to     - 終了日
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--   （rep_id, customer_id, item_id, date_value は動的WHERE句に含まれる）
--
-- 動的置換:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー
--   {where_sql}                - 動的WHERE句

SELECT
    sales_date,
    slip_no,
    MAX(rep_name) AS rep_name,
    MAX(customer_name) AS customer_name,
    STRING_AGG(DISTINCT item_name, ', ' ORDER BY item_name) AS item_name,
    COUNT(*) AS line_count,
    SUM(qty_kg) AS qty_kg,
    SUM(amount_yen) AS amount_yen
FROM "{schema_mart}"."{v_sales_tree_detail_base}"
WHERE {where_sql}
GROUP BY
    sales_date,
    slip_no
ORDER BY
    sales_date,
    slip_no
