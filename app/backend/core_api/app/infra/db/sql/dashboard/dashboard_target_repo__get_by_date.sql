-- ターゲットカードデータ取得（特定日）
--
-- 指定日のターゲットと実績を取得します。
-- MATERIALIZED VIEW から高速取得。
--
-- パラメータ:
--   :target_date - 取得対象日
--
-- テンプレート変数:
--   {schema_mart}            - mart スキーマ
--   {mv_target_card_per_day} - mart.mv_target_card_per_day MV

SELECT 
    ddate,
    month_target_ton,
    week_target_ton,
    day_target_ton,
    month_actual_ton,
    week_actual_ton,
    day_actual_ton_prev,
    iso_year,
    iso_week,
    iso_dow,
    day_type,
    is_business
FROM "{schema_mart}"."{mv_target_card_per_day}"
WHERE ddate = CAST(:target_date AS DATE)
LIMIT 1
