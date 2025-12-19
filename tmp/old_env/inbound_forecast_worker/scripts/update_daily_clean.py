import pandas as pd
import shutil
import os

def parse_jp_date(date_str):
    # "2024/05/01(水)" -> "2024/05/01"
    return date_str.split('(')[0]

def main():
    daily_clean_path = 'data/input/01_daily_clean.csv'
    detail_path = 'data/input/20240501-20250422.csv'
    backup_path = 'data/input/01_daily_clean.csv.bak_update'

    # Backup
    if not os.path.exists(backup_path):
        shutil.copy(daily_clean_path, backup_path)
        print(f"Backed up {daily_clean_path} to {backup_path}")

    # Load existing daily clean
    print(f"Loading {daily_clean_path}...")
    df_daily = pd.read_csv(daily_clean_path)
    df_daily['date'] = pd.to_datetime(df_daily['date'])
    
    # Filter out data from 2024-05-01 onwards (to be replaced)
    cutoff_date = pd.Timestamp('2024-05-01')
    df_daily_old = df_daily[df_daily['date'] < cutoff_date].copy()
    print(f"Old data count (before {cutoff_date.date()}): {len(df_daily_old)}")

    # Load new detail data
    print(f"Loading {detail_path}...")
    # encoding might be shift_jis or utf-8. The file content showed Japanese characters.
    # Let's try utf-8 first, then shift_jis if it fails.
    try:
        df_detail = pd.read_csv(detail_path, encoding='utf-8')
    except UnicodeDecodeError:
        df_detail = pd.read_csv(detail_path, encoding='shift_jis')

    # Parse dates
    df_detail['date_str'] = df_detail['伝票日付'].apply(parse_jp_date)
    df_detail['date'] = pd.to_datetime(df_detail['date_str'])

    # Filter up to 2025-10-31
    end_date = pd.Timestamp('2025-10-31')
    df_detail = df_detail[df_detail['date'] <= end_date]
    
    # Aggregate
    # Sum '正味重量' by date
    # Note: '正味重量' might contain commas or be strings?
    # Handle '(10)' as -10
    def clean_weight(x):
        if pd.isna(x):
            return 0.0
        s = str(x).replace(',', '').strip()
        if s.startswith('(') and s.endswith(')'):
            try:
                return -float(s[1:-1])
            except ValueError:
                return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0

    df_detail['正味重量'] = df_detail['正味重量'].apply(clean_weight)
    
    df_agg = df_detail.groupby('date')['正味重量'].sum().reset_index()
    df_agg.columns = ['date', 'weight_t'] # Match column names of 01_daily_clean.csv

    print(f"New aggregated data count (2024-05-01 to {end_date.date()}): {len(df_agg)}")

    # Combine
    df_combined = pd.concat([df_daily_old, df_agg], axis=0)
    df_combined = df_combined.sort_values('date').reset_index(drop=True)

    # Format date column back to YYYY/M/D or YYYY/MM/DD?
    # The original file had "2021/3/1".
    # Let's use standard YYYY/MM/DD for consistency, or try to match.
    # pandas to_csv default is YYYY-MM-DD.
    # Let's stick to YYYY/MM/DD as it seems common in this workspace.
    df_combined['date'] = df_combined['date'].dt.strftime('%Y/%-m/%-d')

    # Save
    print(f"Saving to {daily_clean_path}...")
    df_combined.to_csv(daily_clean_path, index=False)
    print("Done.")

    # Verify tail
    print("Tail of new file:")
    print(df_combined.tail())

if __name__ == "__main__":
    main()
