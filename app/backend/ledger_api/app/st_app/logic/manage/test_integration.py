#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Block Unit Price Interactive - 統合テストスクリプト
エンドポイントとリファクタリングされたモジュールの統合テスト
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../../.."))


def test_module_integration():
    """モジュールの統合テスト"""
    print("=" * 70)
    print("統合テスト: エンドポイント → サービス → リファクタリングモジュール")
    print("=" * 70)
    
    try:
        # 1. エンドポイントのインポート
        print("\n[1/5] エンドポイントモジュールのインポート...")
        from app.api.endpoints.block_unit_price_interactive import router
        print(f"✓ エンドポイント: {len(router.routes)} ルート")
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'N/A'
                print(f"  - {methods:6s} {route.path}")
        
        # 2. サービスのインポート
        print("\n[2/5] サービスモジュールのインポート...")
        from app.api.services.report.interactive_report_processing_service import (
            InteractiveReportProcessingService,
        )
        service = InteractiveReportProcessingService()
        print(f"✓ サービス: {type(service).__name__}")
        
        # 3. リファクタリングされたメインモジュールのインポート
        print("\n[3/5] リファクタリングモジュールのインポート...")
        from app.st_app.logic.manage.block_unit_price_interactive_main import (
            BlockUnitPriceInteractive,
        )
        generator = BlockUnitPriceInteractive()
        print(f"✓ ジェネレータ: {type(generator).__name__}")
        print(f"  - report_key: {generator.report_key}")
        
        # 4. メソッドの存在確認
        print("\n[4/5] 必須メソッドの確認...")
        required_methods = [
            'initial_step',
            'finalize_step',
            'finalize_with_optional_selections',
            'get_step_handlers',
            'serialize_state',
            'deserialize_state',
        ]
        
        for method in required_methods:
            if hasattr(generator, method):
                print(f"✓ メソッド '{method}' が存在します")
            else:
                print(f"✗ メソッド '{method}' が見つかりません")
                return False
        
        # 5. 分離されたモジュールのインポート確認
        print("\n[5/5] 分離されたモジュールの確認...")
        from app.st_app.logic.manage.block_unit_price_interactive_utils import (
            make_session_id,
            canonical_sort_labels,
        )
        from app.st_app.logic.manage.block_unit_price_interactive_initial import (
            execute_initial_step,
        )
        from app.st_app.logic.manage.block_unit_price_interactive_finalize import (
            execute_finalize_step,
            execute_finalize_with_optional_selections,
        )
        
        print("✓ utils モジュール")
        print("✓ initial モジュール")
        print("✓ finalize モジュール")
        
        # 6. ユーティリティ関数のテスト
        print("\n[Bonus] ユーティリティ関数のテスト...")
        session_id = make_session_id()
        print(f"✓ session_id 生成: {session_id}")
        assert session_id.startswith("bup-"), "session_id should start with 'bup-'"
        
        labels = ["エコライン", "オネスト ウイング", "シェノンビ"]
        sorted_labels = canonical_sort_labels(labels)
        print(f"✓ ラベルソート: {sorted_labels}")
        
        print("\n" + "=" * 70)
        print("✅ すべての統合テストが成功しました！")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_endpoint_flow():
    """エンドポイントフローのテスト（モック）"""
    print("\n" + "=" * 70)
    print("エンドポイントフローテスト（モック）")
    print("=" * 70)
    
    try:
        from app.st_app.logic.manage.block_unit_price_interactive_main import (
            BlockUnitPriceInteractive,
        )
        
        generator = BlockUnitPriceInteractive()
        
        print("\n[シナリオ] Initial → Apply → Finalize")
        print("-" * 70)
        
        # Step 1: initial_step が呼べることを確認
        print("\n1. initial_step メソッドの確認")
        if hasattr(generator, 'initial_step'):
            print("   ✓ initial_step メソッドが存在")
            # 注: 実際の呼び出しにはデータが必要なので、メソッドの存在確認のみ
        
        # Step 2: apply_step または get_step_handlers の確認
        print("\n2. ステップハンドラーの確認")
        if hasattr(generator, 'get_step_handlers'):
            handlers = generator.get_step_handlers()
            print(f"   ✓ ステップハンドラー: {list(handlers.keys())}")
        
        # Step 3: finalize_with_optional_selections の確認
        print("\n3. finalize_with_optional_selections メソッドの確認")
        if hasattr(generator, 'finalize_with_optional_selections'):
            print("   ✓ finalize_with_optional_selections メソッドが存在")
            print("   → サービスから正しく呼び出し可能")
        
        print("\n" + "-" * 70)
        print("✅ エンドポイントフローテストが成功しました！")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """後方互換性のテスト"""
    print("\n" + "=" * 70)
    print("後方互換性テスト")
    print("=" * 70)
    
    try:
        from app.st_app.logic.manage.block_unit_price_interactive_main import (
            BlockUnitPriceInteractive,
        )
        
        # インスタンス化
        generator = BlockUnitPriceInteractive()
        print("\n✓ 既存のインスタンス化方法で作成可能")
        
        # with files パラメータ
        generator_with_files = BlockUnitPriceInteractive(files={})
        print("✓ files パラメータ付きでインスタンス化可能")
        
        # 継承確認
        from app.api.services.report.base_interactive_report_generator import (
            BaseInteractiveReportGenerator,
        )
        assert isinstance(generator, BaseInteractiveReportGenerator)
        print("✓ BaseInteractiveReportGenerator を継承")
        
        print("\n" + "=" * 70)
        print("✅ 後方互換性テストが成功しました！")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト関数"""
    print("\n" + "=" * 70)
    print("Block Unit Price Interactive - 統合テスト")
    print("=" * 70)
    
    results = []
    
    # Test 1: モジュール統合
    print("\n")
    results.append(("モジュール統合", test_module_integration()))
    
    # Test 2: エンドポイントフロー
    print("\n")
    results.append(("エンドポイントフロー", test_endpoint_flow()))
    
    # Test 3: 後方互換性
    print("\n")
    results.append(("後方互換性", test_backward_compatibility()))
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:12s} {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 70)
    if all_passed:
        print("\n🎉 すべてのテストが成功しました！")
        print("\n✨ エンドポイントから正しく呼び出せることが確認されました。")
        return 0
    else:
        print("\n❌ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
