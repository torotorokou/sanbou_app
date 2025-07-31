"""
Excel出力ユーティリティのテスト・使用例

このスクリプトは、excel_utils.pyの機能をテストするためのサンプルコードです。
"""

import pandas as pd
from pathlib import Path
import sys
import os

# パスを追加してexcel_utilsをインポート
sys.path.append(str(Path(__file__).parent))
from excel_utils import (
    df_to_excel,
    simple_df_to_excel,
    formatted_df_to_excel,
    template_df_to_excel,
)


def test_simple_export():
    """シンプルなExcel出力のテスト"""
    print("=== シンプルなExcel出力テスト ===")

    # サンプルデータ作成
    df = pd.DataFrame(
        {
            "商品名": ["りんご", "バナナ", "オレンジ"],
            "価格": [100, 80, 120],
            "数量": [10, 15, 8],
            "合計": [1000, 1200, 960],
        }
    )

    print("データ:")
    print(df)

    try:
        # Excel出力
        excel_data = simple_df_to_excel(df, "商品一覧")
        print(f"✅ シンプルExcel出力成功: {len(excel_data)} bytes")

        # ファイルに保存してテスト
        output_path = Path("test_simple.xlsx")
        with open(output_path, "wb") as f:
            f.write(excel_data)
        print(f"✅ ファイル保存成功: {output_path}")

    except Exception as e:
        print(f"❌ エラー: {e}")


def test_formatted_export():
    """フォーマット付きExcel出力のテスト"""
    print("\n=== フォーマット付きExcel出力テスト ===")

    # 特定の列名でサンプルデータ作成
    df = pd.DataFrame(
        {
            "大項目": ["材料費", "労務費", "経費"],
            "中項目": ["鉄骨", "作業員", "運搬費"],
            "単価": [1500.50, 2000.00, 800.75],
            "台数": [5, 3, 2],
            "合計金額": [7502.5, 6000.0, 1601.5],
        }
    )

    print("データ:")
    print(df)

    try:
        # フォーマット付きExcel出力
        excel_data = formatted_df_to_excel(df, "コスト一覧")
        print(f"✅ フォーマット付きExcel出力成功: {len(excel_data)} bytes")

        # ファイルに保存してテスト
        output_path = Path("test_formatted.xlsx")
        with open(output_path, "wb") as f:
            f.write(excel_data)
        print(f"✅ ファイル保存成功: {output_path}")

    except Exception as e:
        print(f"❌ エラー: {e}")


def test_template_export():
    """テンプレートベースExcel出力のテスト"""
    print("\n=== テンプレートベースExcel出力テスト ===")

    # テンプレート用のDataFrame（セル・値形式）
    df = pd.DataFrame(
        {
            "セル": ["A1", "B1", "A2", "B2", "A3"],
            "値": ["項目", "金額", "材料費", 1500, "合計"],
        }
    )

    print("テンプレートデータ:")
    print(df)

    # 簡単なテンプレートファイルを作成
    template_path = Path("test_template.xlsx")
    try:
        # 簡単なテンプレートを作成
        template_df = pd.DataFrame([["", ""], ["", ""], ["", ""]])
        with pd.ExcelWriter(template_path, engine="openpyxl") as writer:
            template_df.to_excel(writer, index=False, header=False)

        # テンプレートベース出力
        excel_data = template_df_to_excel(df, template_path, "帳票")
        print(f"✅ テンプレートベースExcel出力成功: {len(excel_data)} bytes")

        # ファイルに保存してテスト
        output_path = Path("test_template_output.xlsx")
        with open(output_path, "wb") as f:
            f.write(excel_data)
        print(f"✅ ファイル保存成功: {output_path}")

    except Exception as e:
        print(f"❌ エラー: {e}")


def test_unified_function():
    """統合関数のテスト"""
    print("\n=== 統合関数テスト ===")

    df = pd.DataFrame(
        {"項目": ["売上", "経費", "利益"], "金額": [100000, 30000, 70000]}
    )

    print("データ:")
    print(df)

    try:
        # 1. シンプル出力
        simple_data = df_to_excel(df, "データ", use_formatting=False)
        print(f"✅ 統合関数（シンプル）: {len(simple_data)} bytes")

        # 2. フォーマット付き出力
        formatted_data = df_to_excel(df, "データ", use_formatting=True)
        print(f"✅ 統合関数（フォーマット付き）: {len(formatted_data)} bytes")

        # ファイル保存
        with open("test_unified_simple.xlsx", "wb") as f:
            f.write(simple_data)
        with open("test_unified_formatted.xlsx", "wb") as f:
            f.write(formatted_data)
        print("✅ 統合関数テスト完了")

    except Exception as e:
        print(f"❌ エラー: {e}")


def cleanup_test_files():
    """テストファイルのクリーンアップ"""
    test_files = [
        "test_simple.xlsx",
        "test_formatted.xlsx",
        "test_template.xlsx",
        "test_template_output.xlsx",
        "test_unified_simple.xlsx",
        "test_unified_formatted.xlsx",
    ]

    print(f"\n=== テストファイルクリーンアップ ===")
    for file in test_files:
        path = Path(file)
        if path.exists():
            path.unlink()
            print(f"🗑️ 削除: {file}")


if __name__ == "__main__":
    print("Excel出力ユーティリティ テスト開始")
    print("=" * 50)

    try:
        test_simple_export()
        test_formatted_export()
        test_template_export()
        test_unified_function()

        print("\n" + "=" * 50)
        print("✅ 全テスト完了！")

        # クリーンアップするかユーザーに確認
        response = input("\nテストファイルを削除しますか？ (y/N): ")
        if response.lower() in ["y", "yes"]:
            cleanup_test_files()
        else:
            print("テストファイルを保持します。")

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
