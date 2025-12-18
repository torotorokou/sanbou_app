#!/usr/bin/env python
"""
将軍データセット取得 統合テストスクリプト
6種類全てのデータセットから取得可能か確認
"""
from backend_shared.shogun import ShogunDatasetFetcher, ShogunDatasetKey, ShogunMasterNameMapper
from backend_shared.infra.db.url_builder import build_database_url_with_driver
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

print("=" * 70)
print("将軍データセット取得 統合テスト")
print("=" * 70)

# DB接続
engine = create_engine(build_database_url_with_driver(), pool_pre_ping=True)
session = Session(engine)

fetcher = ShogunDatasetFetcher(session)
mapper = ShogunMasterNameMapper()

datasets = [
    ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
    ShogunDatasetKey.SHOGUN_FINAL_SHIPMENT,
    ShogunDatasetKey.SHOGUN_FINAL_YARD,
    ShogunDatasetKey.SHOGUN_FLASH_RECEIVE,
    ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT,
    ShogunDatasetKey.SHOGUN_FLASH_YARD,
]

results = []

for dataset_key in datasets:
    try:
        label = mapper.get_dataset_label(dataset_key.value)
        data = fetcher.fetch(dataset_key, limit=3)
        view_name = dataset_key.get_view_name()
        
        row_count = len(data) if data else 0
        cols = list(data[0].keys())[:5] if data else []
        
        print(f"\n✅ {dataset_key.value}")
        print(f"   Label: {label}")
        print(f"   View:  stg.{view_name}")
        print(f"   Rows:  {row_count}")
        print(f"   Cols:  {', '.join(cols)}...")
        
        results.append(True)
    except Exception as e:
        print(f"\n❌ {dataset_key.value}")
        print(f"   Error: {e}")
        results.append(False)

session.close()

print("\n" + "=" * 70)
success = sum(results)
print(f"結果: {success}/{len(results)} 成功")

if success == len(results):
    print("✅ 全データセット取得成功！")
else:
    print(f"⚠️  {len(results) - success}件失敗")
