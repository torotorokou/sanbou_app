"""
将軍データセット取得 統合テスト

実際のDBに接続して6種類全てのデータ取得を確認
"""
import sys
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# backend_shared をインポート可能にする
sys.path.insert(0, '/backend/backend_shared/src')

from backend_shared.db.shogun import (
    ShogunDatasetFetcher,
    ShogunDatasetKey,
    ShogunMasterNameMapper,
)
from backend_shared.db.url_builder import build_database_url_with_driver


def test_all_datasets():
    """6種類全てのデータセットから取得可能かテスト"""
    
    print("=" * 70)
    print("将軍データセット取得 統合テスト")
    print("=" * 70)
    
    # DB接続
    database_url = build_database_url_with_driver()
    print(f"\n✓ DB接続URL構築完了")
    
    engine = create_engine(database_url, pool_pre_ping=True)
    print(f"✓ Engine作成完了")
    
    results = {}
    
    with Session(engine) as session:
        fetcher = ShogunDatasetFetcher(session)
        mapper = ShogunMasterNameMapper()
        
        print(f"\n✓ ShogunDatasetFetcher初期化完了")
        print(f"✓ ShogunMasterNameMapper初期化完了")
        
        # 6種類全てテスト
        datasets = [
            ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
            ShogunDatasetKey.SHOGUN_FINAL_SHIPMENT,
            ShogunDatasetKey.SHOGUN_FINAL_YARD,
            ShogunDatasetKey.SHOGUN_FLASH_RECEIVE,
            ShogunDatasetKey.SHOGUN_FLASH_SHIPMENT,
            ShogunDatasetKey.SHOGUN_FLASH_YARD,
        ]
        
        print("\n" + "=" * 70)
        print("データ取得テスト（各データセット limit=5）")
        print("=" * 70)
        
        for dataset_key in datasets:
            try:
                # 日本語ラベル取得
                label = mapper.get_dataset_label(dataset_key.value)
                
                # データ取得（最新5件）
                data = fetcher.fetch(
                    dataset_key,
                    limit=5
                )
                
                # view名取得
                view_name = dataset_key.get_view_name()
                
                # 結果表示
                status = "✅ SUCCESS" if data is not None else "⚠️  NO DATA"
                row_count = len(data) if data else 0
                
                print(f"\n{status}")
                print(f"  Dataset: {dataset_key.value}")
                print(f"  Label:   {label}")
                print(f"  View:    stg.{view_name}")
                print(f"  Rows:    {row_count}")
                
                if data and len(data) > 0:
                    # 最初の1件のカラム名を表示
                    columns = list(data[0].keys())
                    print(f"  Columns: {len(columns)} カラム")
                    print(f"  Sample:  {', '.join(columns[:5])}...")
                
                results[dataset_key.value] = {
                    "success": True,
                    "row_count": row_count,
                    "label": label,
                    "view_name": view_name,
                }
                
            except Exception as e:
                print(f"\n❌ FAILED")
                print(f"  Dataset: {dataset_key.value}")
                print(f"  Error:   {str(e)}")
                results[dataset_key.value] = {
                    "success": False,
                    "error": str(e),
                }
    
    # 総合結果
    print("\n" + "=" * 70)
    print("総合結果")
    print("=" * 70)
    
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)
    
    print(f"\n成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ 全データセットから取得成功！")
        return True
    else:
        print(f"\n⚠️  {total_count - success_count}件のデータセットで取得失敗")
        return False


def test_date_filter():
    """日付フィルタのテスト"""
    
    print("\n" + "=" * 70)
    print("日付フィルタテスト")
    print("=" * 70)
    
    database_url = build_database_url_with_driver()
    engine = create_engine(database_url, pool_pre_ping=True)
    
    with Session(engine) as session:
        fetcher = ShogunDatasetFetcher(session)
        
        # 過去30日間のデータ取得
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n期間: {start_date} ～ {end_date}")
        
        try:
            data = fetcher.fetch(
                ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
                start_date=start_date,
                end_date=end_date,
                limit=10
            )
            
            print(f"✅ 取得成功: {len(data)}件")
            
            if data:
                # 日付が範囲内かチェック
                for row in data[:3]:
                    slip_date = row.get("slip_date")
                    if slip_date:
                        in_range = start_date <= slip_date <= end_date
                        status = "✅" if in_range else "❌"
                        print(f"  {status} slip_date: {slip_date}")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False


def test_convenience_methods():
    """便利メソッドのテスト"""
    
    print("\n" + "=" * 70)
    print("便利メソッドテスト")
    print("=" * 70)
    
    database_url = build_database_url_with_driver()
    engine = create_engine(database_url, pool_pre_ping=True)
    
    methods = [
        ("get_final_receive", lambda f: f.get_final_receive(limit=1)),
        ("get_final_shipment", lambda f: f.get_final_shipment(limit=1)),
        ("get_final_yard", lambda f: f.get_final_yard(limit=1)),
        ("get_flash_receive", lambda f: f.get_flash_receive(limit=1)),
        ("get_flash_shipment", lambda f: f.get_flash_shipment(limit=1)),
        ("get_flash_yard", lambda f: f.get_flash_yard(limit=1)),
    ]
    
    with Session(engine) as session:
        fetcher = ShogunDatasetFetcher(session)
        
        success = 0
        for method_name, method_func in methods:
            try:
                data = method_func(fetcher)
                row_count = len(data) if data else 0
                print(f"  ✅ {method_name:25s} => {row_count}件")
                success += 1
            except Exception as e:
                print(f"  ❌ {method_name:25s} => エラー: {e}")
        
        print(f"\n成功: {success}/{len(methods)}")
        return success == len(methods)


def test_dataframe_output():
    """DataFrame出力のテスト"""
    
    print("\n" + "=" * 70)
    print("DataFrame出力テスト")
    print("=" * 70)
    
    database_url = build_database_url_with_driver()
    engine = create_engine(database_url, pool_pre_ping=True)
    
    with Session(engine) as session:
        fetcher = ShogunDatasetFetcher(session)
        
        try:
            df = fetcher.fetch_df(
                ShogunDatasetKey.SHOGUN_FINAL_RECEIVE,
                limit=5
            )
            
            print(f"  ✅ DataFrame取得成功")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {len(df.columns)}カラム")
            print(f"  Sample columns: {', '.join(df.columns[:5].tolist())}...")
            
            return True
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return False


if __name__ == "__main__":
    print("\n🚀 統合テスト開始\n")
    
    results = []
    
    # テスト1: 全データセット取得
    results.append(("全データセット取得", test_all_datasets()))
    
    # テスト2: 日付フィルタ
    results.append(("日付フィルタ", test_date_filter()))
    
    # テスト3: 便利メソッド
    results.append(("便利メソッド", test_convenience_methods()))
    
    # テスト4: DataFrame出力
    results.append(("DataFrame出力", test_dataframe_output()))
    
    # 最終結果
    print("\n" + "=" * 70)
    print("最終結果")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} {test_name}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n✅ 全テストPASS！")
        print("✅ v_active_*から6種類全てのデータ取得が確認できました")
        sys.exit(0)
    else:
        print("\n⚠️  一部テスト失敗")
        sys.exit(1)
