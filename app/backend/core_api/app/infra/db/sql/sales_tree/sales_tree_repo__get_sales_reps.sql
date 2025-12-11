-- Sales Tree 営業フィルタ候補取得
--
-- SalesTree分析専用の営業リストを動的に取得
-- 
-- パラメータ:
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--
-- 動的置換:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー

SELECT DISTINCT
    rep_id,
    rep_name
FROM "{schema_mart}"."{v_sales_tree_detail_base}"
WHERE rep_id IS NOT NULL AND rep_name IS NOT NULL
  AND category_cd = :category_cd
ORDER BY rep_id
