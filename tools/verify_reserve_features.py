#!/usr/bin/env python3
"""
CSVから3特徴量を生成
- total_customer_count: その日の予約企業数（行数）
- fixed_customer_count: その日の固定客企業数（固定客=Trueの行数）
- fixed_customer_ratio: fixed_customer_count / total_customer_count
"""
import pandas as pd
import sys
from pathlib import Path

def main():
    # 旧版CSVパス
    csv_path = Path("tmp/legacy_release/inbound_forecast_worker/data/input/yoyaku_data.csv")
    
    if not csv_path.exists():
        print(f"ERROR: CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"=== CSVから3特徴量を生成 ===")
    print(f"入力: {csv_path}")
    
    # CSV読み込み
    df = pd.read_csv(csv_path)
    print(f"総行数: {len(df):,}")
    print(f"列: {df.columns.tolist()}")
    print()
    
    # 予約日列のパース
    df['予約日'] = pd.to_datetime(df['予約日'], format='%Y/%m/%d', errors='coerce')
    
    # 固定客列を1/0に変換（True/False, "TRUE"/"FALSE", 1/0 すべて対応）
    df['固定客_binary'] = df['固定客'].astype(str).str.lower().isin(['true', '1', 'yes', '固定', '固定客']).astype(int)
    
    # 日次集計
    daily = df.groupby('予約日').agg(
        total_customer_count=('予約得意先名', 'size'),  # 企業数（行数）
        fixed_customer_count=('固定客_binary', 'sum')   # 固定客企業数（固定客=1の行数）
    ).reset_index()
    
    # 比率計算（0除算回避）
    daily['fixed_customer_ratio'] = (
        daily['fixed_customer_count'] / daily['total_customer_count'].replace(0, float('nan'))
    ).fillna(0.0)
    
    # 列名をDBと揃える
    daily = daily.rename(columns={'予約日': 'date'})
    
    # 統計情報
    print("=== 生成した3特徴量の統計 ===")
    print(daily[['total_customer_count', 'fixed_customer_count', 'fixed_customer_ratio']].describe())
    print()
    
    # サンプル表示
    print("=== サンプル（最初の10日）===")
    print(daily.head(10))
    print()
    
    print("=== サンプル（最後の10日）===")
    print(daily.tail(10))
    print()
    
    # 出力
    output_path = Path("tmp/compare_out/csv_features.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output_path, index=False)
    
    print(f"✅ 出力完了: {output_path}")
    print(f"   期間: {daily['date'].min()} ～ {daily['date'].max()}")
    print(f"   日数: {len(daily)}")

if __name__ == "__main__":
    main()
