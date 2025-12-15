-- Sales Tree 日次推移データ取得
--
-- 指定条件（営業/顧客/品目）での日別集計を返す
--
-- パラメータ:
--   :date_from   - 開始日
--   :date_to     - 終了日
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--   :rep_id      - 営業ID（オプション）
--   :customer_id - 顧客ID（オプション）
--   :item_id     - 品目ID（オプション）
--
-- 動的置換（Python側で文字列置換）:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー
--   {where_sql}                - 動的WHERE句

SELECT
    sales_date AS date,
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
GROUP BY sales_date
ORDER BY sales_date
