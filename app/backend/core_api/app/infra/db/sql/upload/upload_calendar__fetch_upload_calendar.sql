-- アップロードカレンダー集計
-- 全CSV種別（flash/final × receive/yard/shipment）のUNION ALL集計
-- 
-- パラメータ:
--   :start_date - 開始日
--   :end_date   - 終了日
--
-- テンプレート変数（Pythonでformat置換）:
--   {schema_log}                           - log スキーマ
--   {schema_stg}                           - stg スキーマ
--   {t_upload_file}                        - log.upload_file テーブル
--   {v_active_shogun_flash_receive}        - stg.v_active_shogun_flash_receive ビュー
--   {v_active_shogun_flash_yard}           - stg.v_active_shogun_flash_yard ビュー
--   {v_active_shogun_flash_shipment}       - stg.v_active_shogun_flash_shipment ビュー
--   {v_active_shogun_final_receive}        - stg.v_active_shogun_final_receive ビュー
--   {v_active_shogun_final_shipment}       - stg.v_active_shogun_final_shipment ビュー
--   {v_active_shogun_final_yard}           - stg.v_active_shogun_final_yard ビュー

WITH upload_data AS (
    -- 将軍速報版 受入（アクティブ行専用ビュー使用）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_flash_receive'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_flash_receive}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
    
    UNION ALL
    
    -- 将軍速報版 ヤード（アクティブ行専用ビュー使用）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_flash_yard'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_flash_yard}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
    
    UNION ALL
    
    -- 将軍速報版 出荷（アクティブ行専用ビュー使用）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_flash_shipment'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_flash_shipment}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
    
    UNION ALL
    
    -- 将軍最終版 受入（アクティブ行専用ビュー - is_deleted=false自動フィルタ）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_final_receive'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_final_receive}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
    
    UNION ALL
    
    -- 将軍最終版 出荷（アクティブ行専用ビュー - is_deleted=false自動フィルタ）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_final_shipment'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_final_shipment}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
    
    UNION ALL
    
    -- 将軍最終版 ヤード（アクティブ行専用ビュー - is_deleted=false自動フィルタ）
    SELECT 
        uf.id AS upload_file_id,
        s.slip_date AS data_date,
        'shogun_final_yard'::text AS csv_kind,
        COUNT(*) AS row_count
    FROM "{schema_log}"."{t_upload_file}" uf
    JOIN "{schema_stg}"."{v_active_shogun_final_yard}" s ON s.upload_file_id = uf.id
    WHERE uf.is_deleted = false
      AND s.slip_date IS NOT NULL
      AND s.slip_date >= :start_date
      AND s.slip_date <= :end_date
    GROUP BY uf.id, s.slip_date
)
SELECT 
    upload_file_id,
    data_date,
    csv_kind,
    row_count
FROM upload_data
ORDER BY data_date, csv_kind, upload_file_id
