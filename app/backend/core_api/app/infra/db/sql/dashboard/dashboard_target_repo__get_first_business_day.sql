-- 月内最初の営業日取得
--
-- 指定月内の最初の営業日を取得します。
--
-- パラメータ:
--   :month_start - 月の初日
--   :month_end   - 月の末日
--
-- テンプレート変数:
--   {schema_mart}            - mart スキーマ
--   {mv_target_card_per_day} - mart.mv_target_card_per_day MV

SELECT ddate
FROM "{schema_mart}"."{mv_target_card_per_day}"
WHERE ddate BETWEEN CAST(:month_start AS DATE) AND CAST(:month_end AS DATE)
  AND is_business = true
ORDER BY ddate ASC
LIMIT 1
