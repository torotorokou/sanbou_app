-- ターゲットカードメトリクス取得（月末累積）
--
-- 指定日の月内で最新日のレコードを取得し、
-- 月累積の実績・ターゲットデータを返します。
--
-- パラメータ:
--   :target_date - 対象日（この日の月内で検索）
--
-- テンプレート変数:
--   {schema_mart}            - mart スキーマ
--   {mv_target_card_per_day} - mart.mv_target_card_per_day MV

SELECT 
    month_target_ton,
    week_target_ton,
    day_target_ton,
    month_actual_ton,
    week_actual_ton,
    day_actual_ton_prev,
    ddate
FROM "{schema_mart}"."{mv_target_card_per_day}"
WHERE date_trunc('month', ddate) = date_trunc('month', CAST(:target_date AS DATE))
ORDER BY ddate DESC
LIMIT 1
