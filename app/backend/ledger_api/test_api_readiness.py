#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API エンドポイントの動作確認スクリプト

st_app を削除する前に、すべての API エンドポイントが
正常に動作することを確認します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """必要なモジュールがインポートできることを確認"""
    print("=" * 80)
    print("🔍 モジュールインポートテスト")
    print("=" * 80)
    print()
    
    test_cases = [
        ("api.endpoints.block_unit_price_interactive", "block_unit_price_interactive エンドポイント"),
        ("api.endpoints.reports.average_sheet", "average_sheet エンドポイント"),
        ("api.endpoints.reports.balance_sheet", "balance_sheet エンドポイント"),
        ("api.endpoints.reports.factory_report", "factory_report エンドポイント"),
        ("api.endpoints.reports.management_sheet", "management_sheet エンドポイント"),
        ("api.endpoints.report_artifacts", "report_artifacts エンドポイント"),
        ("api.services.report.report_processing_service", "ReportProcessingService"),
        ("api.services.report.interactive_report_processing_service", "InteractiveReportProcessingService"),
        ("api.services.report.concrete_generators", "レポート生成器"),
        ("api.services.report.ledger.interactive", "インタラクティブレポート"),
        ("api.services.csv_formatter_service", "CSV フォーマッター"),
        ("api.services.csv_validator_facade", "CSV バリデーター"),
    ]
    
    success_count = 0
    failed_imports = []
    
    for module_path, description in test_cases:
        try:
            full_path = f"app.{module_path}"
            __import__(full_path)
            print(f"✅ {description:50s} OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {description:50s} FAILED")
            failed_imports.append((description, str(e)))
    
    print()
    print(f"結果: {success_count}/{len(test_cases)} 成功")
    
    if failed_imports:
        print()
        print("=" * 80)
        print("❌ 失敗したインポート:")
        print("=" * 80)
        for desc, error in failed_imports:
            print(f"\n{desc}:")
            print(f"  エラー: {error}")
        return False
    
    print()
    print("=" * 80)
    print("✅ すべてのモジュールが正常にインポートできました")
    print("=" * 80)
    return True


def test_class_instantiation():
    """主要クラスがインスタンス化できることを確認"""
    print()
    print("=" * 80)
    print("🔍 クラスインスタンス化テスト")
    print("=" * 80)
    print()
    
    test_cases = []
    success_count = 0
    failed_tests = []
    
    try:
        from app.api.services.report.concrete_generators import (
            AverageSheetGenerator,
            BalanceSheetGenerator,
            FactoryReportGenerator,
            ManagementSheetGenerator,
        )
        # 各生成器は report_key と files を必要とする
        test_cases.extend([
            (lambda: AverageSheetGenerator(report_key="average_sheet", files={}), "AverageSheetGenerator"),
            (lambda: BalanceSheetGenerator(report_key="balance_sheet", files={}), "BalanceSheetGenerator"),
            (lambda: FactoryReportGenerator(report_key="factory_report", files={}), "FactoryReportGenerator"),
            (lambda: ManagementSheetGenerator(report_key="management_sheet", files={}), "ManagementSheetGenerator"),
        ])
    except ImportError as e:
        print(f"⚠️  生成器のインポートに失敗: {e}")
    
    try:
        from app.api.services.report.ledger.interactive import BlockUnitPriceInteractive
        test_cases.append(
            (lambda: BlockUnitPriceInteractive(), "BlockUnitPriceInteractive")
        )
    except ImportError as e:
        print(f"⚠️  BlockUnitPriceInteractive のインポートに失敗: {e}")
    
    try:
        from app.api.services.report.report_processing_service import ReportProcessingService
        test_cases.append(
            (lambda: ReportProcessingService(), "ReportProcessingService")
        )
    except ImportError as e:
        print(f"⚠️  ReportProcessingService のインポートに失敗: {e}")
    
    try:
        from app.api.services.report.interactive_report_processing_service import InteractiveReportProcessingService
        test_cases.append(
            (lambda: InteractiveReportProcessingService(), "InteractiveReportProcessingService")
        )
    except ImportError as e:
        print(f"⚠️  InteractiveReportProcessingService のインポートに失敗: {e}")
    
    for instantiate_func, class_name in test_cases:
        try:
            _ = instantiate_func()  # インスタンス化のみ確認
            print(f"✅ {class_name:50s} OK")
            success_count += 1
        except Exception as e:
            print(f"❌ {class_name:50s} FAILED")
            failed_tests.append((class_name, str(e)))
    
    print()
    print(f"結果: {success_count}/{len(test_cases)} 成功")
    
    if failed_tests:
        print()
        print("=" * 80)
        print("❌ 失敗したインスタンス化:")
        print("=" * 80)
        for class_name, error in failed_tests:
            print(f"\n{class_name}:")
            print(f"  エラー: {error}")
        return False
    
    print()
    print("=" * 80)
    print("✅ すべてのクラスが正常にインスタンス化できました")
    print("=" * 80)
    return True


def test_no_st_app_imports():
    """app/api 内に st_app へのインポートがないことを確認"""
    print()
    print("=" * 80)
    print("🔍 st_app 依存チェック")
    print("=" * 80)
    print()
    
    api_dir = project_root / "app" / "api"
    if not api_dir.exists():
        print(f"❌ {api_dir} が見つかりません")
        return False
    
    st_app_imports = []
    
    for py_file in api_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'st_app' in content or 'from app.st_app' in content:
                # 詳細チェック
                for line_num, line in enumerate(content.splitlines(), 1):
                    if 'import' in line and 'st_app' in line:
                        relative_path = py_file.relative_to(project_root)
                        st_app_imports.append((str(relative_path), line_num, line.strip()))
        except Exception as e:
            print(f"⚠️  {py_file} の読み込みに失敗: {e}")
    
    if st_app_imports:
        print("❌ app/api 内に st_app へのインポートが見つかりました:")
        print()
        for file_path, line_num, line in st_app_imports:
            print(f"  📄 {file_path}:{line_num}")
            print(f"     {line}")
            print()
        return False
    
    print("✅ app/api 内に st_app への依存はありません")
    print()
    print("=" * 80)
    return True


def test_utility_functions():
    """ユーティリティ関数が正常に動作することを確認"""
    print()
    print("=" * 80)
    print("🔍 ユーティリティ関数テスト")
    print("=" * 80)
    print()
    
    success_count = 0
    failed_tests = []
    
    # logger のテスト
    try:
        from app.api.services.report.ledger.utils.logger import app_logger
        logger = app_logger()
        logger.info("Test log message")
        print("✅ logger                                                  OK")
        success_count += 1
    except Exception as e:
        print("❌ logger                                                  FAILED")
        failed_tests.append(("logger", str(e)))
    
    # config のテスト
    try:
        from app.api.services.report.ledger.utils.config import get_template_config
        config = get_template_config()
        assert isinstance(config, dict), "config は辞書である必要があります"
        print("✅ get_template_config                                    OK")
        success_count += 1
    except Exception as e:
        print("❌ get_template_config                                    FAILED")
        failed_tests.append(("get_template_config", str(e)))
    
    # MainPath のテスト
    try:
        from app.api.services.report.ledger.utils.main_path import MainPath
        _ = MainPath()  # インスタンス化のみ確認
        print("✅ MainPath                                               OK")
        success_count += 1
    except Exception as e:
        print("❌ MainPath                                               FAILED")
        failed_tests.append(("MainPath", str(e)))
    
    # date_tools のテスト
    try:
        from app.api.services.report.ledger.utils.date_tools import get_weekday_japanese
        from datetime import date
        weekday = get_weekday_japanese(date(2024, 1, 1))
        assert isinstance(weekday, str), "曜日は文字列である必要があります"
        print("✅ get_weekday_japanese                                   OK")
        success_count += 1
    except Exception as e:
        print("❌ get_weekday_japanese                                   FAILED")
        failed_tests.append(("get_weekday_japanese", str(e)))
    
    print()
    print(f"結果: {success_count}/4 成功")
    
    if failed_tests:
        print()
        print("=" * 80)
        print("❌ 失敗したテスト:")
        print("=" * 80)
        for func_name, error in failed_tests:
            print(f"\n{func_name}:")
            print(f"  エラー: {error}")
        return False
    
    print()
    print("=" * 80)
    print("✅ すべてのユーティリティ関数が正常に動作しました")
    print("=" * 80)
    return True


def main():
    """メイン関数"""
    print()
    print("=" * 80)
    print("🚀 API エンドポイント動作確認テスト")
    print("=" * 80)
    print()
    print("このスクリプトは、st_app を削除する前に")
    print("すべての API エンドポイントが正常に動作することを確認します。")
    print()
    
    # テストの実行
    results = []
    
    results.append(("モジュールインポート", test_imports()))
    results.append(("st_app 依存チェック", test_no_st_app_imports()))
    results.append(("クラスインスタンス化", test_class_instantiation()))
    results.append(("ユーティリティ関数", test_utility_functions()))
    
    # 結果のサマリー
    print()
    print("=" * 80)
    print("📊 テスト結果サマリー")
    print("=" * 80)
    print()
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:30s} {status}")
        if not result:
            all_passed = False
    
    print()
    print("=" * 80)
    
    if all_passed:
        print("✅ すべてのテストが成功しました！")
        print()
        print("st_app を安全に削除できます。")
        print()
        print("削除コマンド:")
        print("  cd /home/koujiro/work_env/22.Work_React/sanbou_app/app/backend/ledger_api")
        print("  mv app/st_app app/st_app.backup_$(date +%Y%m%d)")
        print()
        return 0
    else:
        print("❌ 一部のテストが失敗しました")
        print()
        print("上記のエラーを解決してから st_app を削除してください。")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
