#!/usr/bin/env python3
"""
Integration Test: ServiceBasedPredictionExecutor

ServiceBasedPredictionExecutorの動作確認テスト。
既存機能が損なわれていないか検証する。
"""
import sys
import os
from pathlib import Path
from datetime import date, datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "app"))

from app.config.di_providers import get_prediction_executor
from app.core.domain.prediction import DailyForecastRequest

def test_service_executor():
    """ServiceBasedPredictionExecutorのテスト"""
    print("=" * 60)
    print("ServiceBasedPredictionExecutor Integration Test")
    print("=" * 60)
    
    # 環境変数を設定（serviceモード）
    os.environ["EXECUTOR_TYPE"] = "service"
    os.environ["MODEL_BUNDLE_PATH"] = "/backend/data/output/final_fast_balanced/model_bundle.joblib"
    os.environ["OUTPUT_DIR"] = "/backend/output"
    os.environ["ENABLE_DB_SAVE"] = "false"  # テストではDB保存を無効化
    
    try:
        # 1. Executorを取得
        print("\n[1/4] Getting prediction executor...")
        executor = get_prediction_executor()
        print(f"✅ Executor type: {type(executor).__name__}")
        print(f"   Model bundle: {executor.model_bundle_path}")
        print(f"   Output dir: {executor.output_dir}")
        
        # 2. リクエストを作成
        print("\n[2/4] Creating forecast request...")
        request = DailyForecastRequest(
            target_date=date.today()
        )
        print(f"✅ Request created: target_date={request.target_date}")
        
        # 3. 予測を実行
        print("\n[3/4] Executing daily forecast...")
        output = executor.execute_daily_forecast(request)
        print(f"✅ Forecast completed")
        print(f"   CSV path: {output.csv_path}")
        
        # 4. 結果を検証
        print("\n[4/4] Verifying output...")
        csv_path = Path(output.csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Output CSV not found: {csv_path}")
        
        # CSVのサイズを確認
        file_size = csv_path.stat().st_size
        print(f"✅ CSV file exists: {csv_path}")
        print(f"   File size: {file_size:,} bytes")
        
        # CSVの内容を簡易確認
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"   Columns: {list(df.columns)}")
        
        if len(df) > 0:
            print(f"\n   First row:")
            for col in df.columns:
                print(f"     {col}: {df[col].iloc[0]}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


def test_script_executor():
    """ScriptBasedPredictionExecutor（既存）のテスト"""
    print("\n\n" + "=" * 60)
    print("ScriptBasedPredictionExecutor Integration Test (Legacy)")
    print("=" * 60)
    
    # 環境変数を設定（scriptモード）
    os.environ["EXECUTOR_TYPE"] = "script"
    os.environ["SCRIPTS_DIR"] = "/backend/app/infra/scripts"
    os.environ["ENABLE_DB_SAVE"] = "false"
    
    try:
        # 1. Executorを取得
        print("\n[1/4] Getting prediction executor...")
        executor = get_prediction_executor()
        print(f"✅ Executor type: {type(executor).__name__}")
        
        # 2. リクエストを作成
        print("\n[2/4] Creating forecast request...")
        request = DailyForecastRequest(
            target_date=date.today()
        )
        print(f"✅ Request created: target_date={request.target_date}")
        
        # 3. 予測を実行
        print("\n[3/4] Executing daily forecast...")
        output = executor.execute_daily_forecast(request)
        print(f"✅ Forecast completed")
        print(f"   CSV path: {output.csv_path}")
        
        # 4. 結果を検証
        print("\n[4/4] Verifying output...")
        csv_path = Path(output.csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Output CSV not found: {csv_path}")
        
        file_size = csv_path.stat().st_size
        print(f"✅ CSV file exists: {csv_path}")
        print(f"   File size: {file_size:,} bytes")
        
        print("\n" + "=" * 60)
        print("✅ LEGACY EXECUTOR STILL WORKS")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ LEGACY TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Starting Integration Tests\n")
    
    # ServiceBasedPredictionExecutorのテスト
    service_ok = test_service_executor()
    
    # ScriptBasedPredictionExecutor（既存）のテスト
    script_ok = test_script_executor()
    
    # 結果サマリー
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"ServiceBasedPredictionExecutor: {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"ScriptBasedPredictionExecutor:  {'✅ PASS' if script_ok else '❌ FAIL'}")
    print("=" * 60)
    
    # 終了コード
    if service_ok and script_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
