#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Block Unit Price Interactive - Test Script
リファクタリング後のモジュールをテスト
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../../.."))

def test_imports():
    """モジュールのインポートをテスト"""
    print("=" * 60)
    print("Testing module imports...")
    print("=" * 60)
    
    try:
        from app.backend.ledger_api.app.st_app.logic.manage.block_unit_price_interactive_utils import (
            make_session_id,
            clean_vendor_name,
            canonical_sort_labels,
            ensure_datetime_col,
        )
        print("✓ Utils module imported successfully")
        
        # Test make_session_id
        session_id = make_session_id()
        print(f"  - Session ID: {session_id}")
        assert session_id.startswith("bup-"), "Session ID should start with 'bup-'"
        
        # Test clean_vendor_name
        cleaned = clean_vendor_name("テスト業者（123）")
        print(f"  - Cleaned vendor name: {cleaned}")
        assert cleaned == "テスト業者", f"Expected 'テスト業者', got '{cleaned}'"
        
        # Test canonical_sort_labels
        labels = ["エコライン", "オネスト ウイング", "シェノンビ"]
        sorted_labels = canonical_sort_labels(labels)
        print(f"  - Sorted labels: {sorted_labels}")
        
        print("✓ Utils functions work correctly\n")
        
    except Exception as e:
        print(f"✗ Error importing utils: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from app.backend.ledger_api.app.st_app.logic.manage.block_unit_price_interactive_initial import (
            execute_initial_step,
            compute_options_and_initial,
        )
        print("✓ Initial module imported successfully\n")
        
    except Exception as e:
        print(f"✗ Error importing initial: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from app.backend.ledger_api.app.st_app.logic.manage.block_unit_price_interactive_finalize import (
            execute_finalize_step,
            execute_finalize_with_optional_selections,
        )
        print("✓ Finalize module imported successfully\n")
        
    except Exception as e:
        print(f"✗ Error importing finalize: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from app.backend.ledger_api.app.st_app.logic.manage.block_unit_price_interactive_main import (
            BlockUnitPriceInteractive,
        )
        print("✓ Main module imported successfully")
        
        # Test initialization
        interactive = BlockUnitPriceInteractive()
        print(f"  - Instance created: {type(interactive).__name__}")
        print(f"  - Report key: {interactive.report_key}")
        
        print("✓ Main class instantiated correctly\n")
        
    except Exception as e:
        print(f"✗ Error importing main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_structure():
    """モジュール構造をテスト"""
    print("=" * 60)
    print("Testing module structure...")
    print("=" * 60)
    
    try:
        from app.backend.ledger_api.app.st_app.logic.manage.block_unit_price_interactive_main import (
            BlockUnitPriceInteractive,
        )
        
        interactive = BlockUnitPriceInteractive()
        
        # Check methods
        methods = [
            "initial_step",
            "finalize_step",
            "finalize_with_optional_selections",
            "get_step_handlers",
            "_resolve_and_apply_selections",
            "_handle_select_transport",
            "_create_selection_summary",
        ]
        
        for method in methods:
            if hasattr(interactive, method):
                print(f"✓ Method '{method}' exists")
            else:
                print(f"✗ Method '{method}' is missing")
                return False
        
        print("\n✓ All required methods exist\n")
        
    except Exception as e:
        print(f"✗ Error testing structure: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """メインテスト関数"""
    print("\n" + "=" * 60)
    print("Block Unit Price Interactive - Refactoring Test")
    print("=" * 60 + "\n")
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
        print("\n⚠️  Import tests failed")
    else:
        print("✅ Import tests passed")
    
    # Test structure
    if not test_structure():
        success = False
        print("\n⚠️  Structure tests failed")
    else:
        print("✅ Structure tests passed")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
