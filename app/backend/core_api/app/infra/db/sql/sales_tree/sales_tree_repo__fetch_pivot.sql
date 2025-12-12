-- Sales Tree ピボット集計（ページング対応）
--
-- ソース軸とターゲット軸でクロス集計（ページネーション付き）
--
-- パラメータ:
--   :date_from   - 開始日
--   :date_to     - 終了日
--   :category_cd - カテゴリコード (1=処分費, 3=有価物)
--   :limit       - 内部LIMIT（ランキング用）
--   :page_size   - ページサイズ
--   :offset      - オフセット
--
-- 動的置換:
--   {schema_mart}              - mart スキーマ
--   {v_sales_tree_detail_base} - mart.v_sales_tree_detail_base ビュー
--   {target_id_col}            - ターゲット軸IDカラム
--   {target_name_col}          - ターゲット軸名カラム
--   {where_sql}                - 動的WHERE句
--   {sort_col}                 - ソート列
--   {order_dir}                - ソート方向

WITH aggregated AS (
    SELECT
        {target_id_col} AS target_id,
        {target_name_col} AS target_name,
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
    line_count,
    slip_count,
    unit_price
FROM ranked
WHERE rn <= :limit
ORDER BY rn
LIMIT :page_size OFFSET :offset
