-- Sales Tree 詳細明細行取得（品目レベル）
--
-- 集計軸が品目の場合、明細行をそのまま返す（GROUP BY なし）
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
    rep_name,
    customer_name,
    item_id,
    item_name,
    qty_kg,
    amount_yen
FROM "{schema_mart}"."{v_sales_tree_detail_base}"
WHERE {where_sql}
ORDER BY
    sales_date,
    slip_no,
    item_id
