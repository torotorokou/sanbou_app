-- DBから3特徴量をエクスポート
-- stg.reserve_customer_dailyから直接集計（mart.v_reserve_daily_featuresと同じロジック）
SELECT 
    reserve_date AS date,
    COUNT(*) AS total_customer_count,
    COUNT(*) FILTER (WHERE is_fixed_customer) AS fixed_customer_count,
    CASE 
        WHEN COUNT(*) > 0 
        THEN ROUND(COUNT(*) FILTER (WHERE is_fixed_customer)::numeric / COUNT(*)::numeric, 6)
        ELSE 0::numeric
    END AS fixed_customer_ratio
FROM stg.reserve_customer_daily
WHERE reserve_date >= '2023-01-04' AND reserve_date <= '2025-10-31'
GROUP BY reserve_date
ORDER BY reserve_date;
