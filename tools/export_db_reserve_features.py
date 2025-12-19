#!/usr/bin/env python3
"""
DBから3特徴量をエクスポート
"""
import os
import subprocess
import pandas as pd
from pathlib import Path

def main():
    sql = """
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
    ORDER BY reserve_date
    """
    
    print("=== DBから3特徴量をエクスポート ===")
    
    # docker composeコマンド実行
    cmd = [
        "docker", "compose", "-f", "docker/docker-compose.dev.yml", "-p", "local_dev",
        "exec", "-T", "db", "psql", "-U", "myuser", "-d", "sanbou_dev",
        "-c", sql, "--csv"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/koujiro/work_env/22.Work_React/sanbou_app")
    
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        exit(1)
    
    # CSVパース
    from io import StringIO
    df = pd.read_csv(StringIO(result.stdout))
    
    print(f"取得行数: {len(df)}")
    print(f"列: {df.columns.tolist()}")
    print()
    
    # date列をdatetimeに変換
    df['date'] = pd.to_datetime(df['date'])
    
    # 統計情報
    print("=== 取得した3特徴量の統計 ===")
    print(df[['total_customer_count', 'fixed_customer_count', 'fixed_customer_ratio']].describe())
    print()
    
    # サンプル表示
    print("=== サンプル（最初の10日）===")
    print(df.head(10))
    print()
    
    print("=== サンプル（最後の10日）===")
    print(df.tail(10))
    print()
    
    # 出力
    output_path = Path("tmp/compare_out/db_features.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"✅ 出力完了: {output_path}")
    print(f"   期間: {df['date'].min()} ～ {df['date'].max()}")
    print(f"   日数: {len(df)}")

if __name__ == "__main__":
    main()
