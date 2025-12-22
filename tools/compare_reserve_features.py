#!/usr/bin/env python3
"""
CSV特徴量とDB特徴量を突合して差分を確認
"""
import pandas as pd
import numpy as np
from pathlib import Path

def main():
    print("=== CSV vs DB 3特徴量の突合 ===\n")
    
    # データ読み込み
    csv_path = Path("tmp/compare_out/csv_features.csv")
    db_path = Path("tmp/compare_out/db_features.csv")
    
    if not csv_path.exists() or not db_path.exists():
        print("ERROR: 特徴量ファイルが見つかりません")
        print(f"  CSV: {csv_path} (exists: {csv_path.exists()})")
        print(f"  DB: {db_path} (exists: {db_path.exists()})")
        exit(1)
    
    df_csv = pd.read_csv(csv_path)
    df_db = pd.read_csv(db_path)
    
    # date列をdatetimeに変換
    df_csv['date'] = pd.to_datetime(df_csv['date'])
    df_db['date'] = pd.to_datetime(df_db['date'])
    
    print(f"CSV行数: {len(df_csv)}, DB行数: {len(df_db)}")
    
    # Inner join
    merged = pd.merge(df_csv, df_db, on='date', suffixes=('_csv', '_db'))
    print(f"結合後行数: {len(merged)}\n")
    
    # 差分計算
    merged['diff_total'] = merged['total_customer_count_db'] - merged['total_customer_count_csv']
    merged['diff_fixed'] = merged['fixed_customer_count_db'] - merged['fixed_customer_count_csv']
    merged['diff_ratio'] = merged['fixed_customer_ratio_db'] - merged['fixed_customer_ratio_csv']
    
    # 一致率計算
    exact_match_total = (merged['diff_total'] == 0).sum()
    exact_match_fixed = (merged['diff_fixed'] == 0).sum()
    exact_match_ratio = (merged['diff_ratio'].abs() < 1e-6).sum()  # 浮動小数点誤差考慮
    
    total_days = len(merged)
    
    print("=" * 80)
    print("【一致率】")
    print("=" * 80)
    print(f"total_customer_count: {exact_match_total}/{total_days} ({exact_match_total/total_days*100:.2f}%)")
    print(f"fixed_customer_count: {exact_match_fixed}/{total_days} ({exact_match_fixed/total_days*100:.2f}%)")
    print(f"fixed_customer_ratio: {exact_match_ratio}/{total_days} ({exact_match_ratio/total_days*100:.2f}%)")
    print()
    
    # 差分統計
    print("=" * 80)
    print("【差分統計（DB - CSV）】")
    print("=" * 80)
    print("\ntotal_customer_count:")
    print(f"  平均差異: {merged['diff_total'].mean():.4f}")
    print(f"  最大差異: {merged['diff_total'].abs().max():.0f}")
    print(f"  標準偏差: {merged['diff_total'].std():.4f}")
    
    print("\nfixed_customer_count:")
    print(f"  平均差異: {merged['diff_fixed'].mean():.4f}")
    print(f"  最大差異: {merged['diff_fixed'].abs().max():.0f}")
    print(f"  標準偏差: {merged['diff_fixed'].std():.4f}")
    
    print("\nfixed_customer_ratio:")
    print(f"  平均差異: {merged['diff_ratio'].mean():.6f}")
    print(f"  最大差異: {merged['diff_ratio'].abs().max():.6f}")
    print(f"  標準偏差: {merged['diff_ratio'].std():.6f}")
    print()
    
    # 差分が大きい日（トップ10）
    print("=" * 80)
    print("【差異トップ10日（total_customer_count）】")
    print("=" * 80)
    top_diff = merged.nlargest(10, 'diff_total', keep='all')[
        ['date', 'total_customer_count_csv', 'total_customer_count_db', 'diff_total']
    ]
    print(top_diff.to_string(index=False))
    print()
    
    print("=" * 80)
    print("【差異トップ10日（fixed_customer_count）】")
    print("=" * 80)
    top_diff_fixed = merged.nlargest(10, 'diff_fixed', keep='all')[
        ['date', 'fixed_customer_count_csv', 'fixed_customer_count_db', 'diff_fixed']
    ]
    print(top_diff_fixed.to_string(index=False))
    print()
    
    # 原因診断
    print("=" * 80)
    print("【原因診断】")
    print("=" * 80)
    
    if exact_match_total == total_days and exact_match_fixed == total_days:
        print("✅ CSV と DB の total_customer_count / fixed_customer_count が完全一致")
        print("   → 定義が同じ、データも同じ")
    elif merged['diff_total'].abs().max() < 5:
        print("⚠️ 軽微な差異（±5未満）")
        print("   → customer_cd の欠損や重複の可能性")
        print("   → 同一企業が同日複数行存在する可能性")
    else:
        print("❌ 大きな差異あり")
        print("   → 定義が異なる可能性")
        print("   → データソースが異なる可能性")
    
    if exact_match_ratio / total_days < 0.95:
        print("\n⚠️ fixed_customer_ratio の不一致が多い")
        print("   → 計算精度の違い（丸め誤差）")
        print("   → 分子/分母の定義が異なる")
    else:
        print("\n✅ fixed_customer_ratio もほぼ一致（丸め誤差の範囲内）")
    
    print()
    
    # サンプル確認（2025-10-31）
    print("=" * 80)
    print("【具体例: 2025-10-31】")
    print("=" * 80)
    sample = merged[merged['date'] == '2025-10-31']
    if len(sample) > 0:
        row = sample.iloc[0]
        print(f"CSV:")
        print(f"  total_customer_count: {row['total_customer_count_csv']}")
        print(f"  fixed_customer_count: {row['fixed_customer_count_csv']}")
        print(f"  fixed_customer_ratio: {row['fixed_customer_ratio_csv']:.6f}")
        print(f"DB:")
        print(f"  total_customer_count: {row['total_customer_count_db']}")
        print(f"  fixed_customer_count: {row['fixed_customer_count_db']}")
        print(f"  fixed_customer_ratio: {row['fixed_customer_ratio_db']:.6f}")
        print(f"差分:")
        print(f"  total: {row['diff_total']:.0f}")
        print(f"  fixed: {row['diff_fixed']:.0f}")
        print(f"  ratio: {row['diff_ratio']:.6f}")
    
    print("\n" + "=" * 80)
    print("【結論】")
    print("=" * 80)
    if exact_match_total == total_days and exact_match_fixed == total_days and exact_match_ratio / total_days > 0.99:
        print("✅ CSV と DB の3特徴量は完全に一致（または丸め誤差の範囲内）")
        print("   → 定義が同じ、実測値も同じ")
        print("   → stg.reserve_customer_daily が CSV の1企業1行と同じ粒度")
    else:
        print("❌ CSV と DB の3特徴量に差異あり")
        print("   → 原因の詳細調査が必要")
    
    # レポート出力用にCSV保存
    comparison_path = Path("tmp/compare_out/feature_comparison.csv")
    merged.to_csv(comparison_path, index=False)
    print(f"\n📊 詳細比較データ: {comparison_path}")

if __name__ == "__main__":
    main()
