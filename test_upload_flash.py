#!/usr/bin/env python3
"""
将軍_速報版CSVアップロードテスト
"""
import requests
from pathlib import Path

# テスト用ファイル
csv_files = {
    'receive': '受入一覧_20251112_150252.csv',
    'shipment': '出荷一覧_202404_202510.csv',
    'yard': 'ヤード一覧_202404_202510.csv',
}

base_url = 'http://localhost:5173/core_api'
upload_endpoint = f'{base_url}/database/upload/syogun_csv_flash'

print("=" * 80)
print("将軍_速報版 CSVアップロードテスト")
print("=" * 80)

for csv_type, filename in csv_files.items():
    file_path = Path(filename)
    
    if not file_path.exists():
        print(f"❌ {csv_type}: ファイルが見つかりません: {filename}")
        continue
    
    print(f"\n📤 {csv_type}: {filename} をアップロード中...")
    
    # ファイルをShift-JISとして読み込み（将軍ソフトの出力形式）
    with open(file_path, 'rb') as f:
        files = {csv_type: (filename, f, 'text/csv')}
        
        try:
            response = requests.post(upload_endpoint, files=files, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {csv_type}: 成功")
                print(f"   - ステータス: {result.get('status')}")
                print(f"   - メッセージ: {result.get('message')}")
                if 'detail' in result:
                    detail = result['detail']
                    if isinstance(detail, dict):
                        for key, value in detail.items():
                            print(f"   - {key}: {value}")
            else:
                print(f"❌ {csv_type}: 失敗 (HTTP {response.status_code})")
                try:
                    error = response.json()
                    print(f"   エラー: {error}")
                except:
                    print(f"   エラー: {response.text[:500]}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ {csv_type}: 通信エラー - {e}")
        except Exception as e:
            print(f"❌ {csv_type}: 予期しないエラー - {e}")

print("\n" + "=" * 80)
print("テスト完了")
print("=" * 80)
