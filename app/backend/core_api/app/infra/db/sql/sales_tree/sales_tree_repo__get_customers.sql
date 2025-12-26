-- Sales Tree 顧客フィルタ候補取得
--
-- SalesTree分析専用の顧客リストを動的に取得
--
-- パラメータ:
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--
-- 動的置換:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー

SELECT DISTINCT
    customer_id,
    customer_name
FROM "{schema_mart}"."{v_sales_tree_detail_base}"
WHERE customer_id IS NOT NULL AND customer_name IS NOT NULL
  AND category_cd = :category_cd
ORDER BY customer_id
