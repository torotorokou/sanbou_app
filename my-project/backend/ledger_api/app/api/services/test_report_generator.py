"""
BaseReportGeneratorクラスのテスト・使用例

このスクリプトは、ReportGeneratorクラスの機能をテストするためのサンプルコードです。
"""

import os
import sys
import pandas as pd
import tempfile
from pathlib import Path

# パスを追加してreport_generatorをインポート
sys.path.append("/backend")
from app.api.services.report_generator import get_report_generator


def test_report_generator():
    """レポート生成機能の統合テスト"""
    print("=== BaseReportGenerator 統合テスト ===")

    # 一時出力ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"一時ディレクトリ: {temp_dir}")

        # サンプルDataFrameを作成（CSVファイルの代わり）
        sample_files = {
            "shipment": pd.DataFrame(
                {
                    "伝票番号": ["S001", "S002", "S003"],
                    "商品名": ["商品A", "商品B", "商品C"],
                    "数量": [10, 20, 15],
                    "単価": [1000, 1500, 800],
                }
            ),
            "yard": pd.DataFrame(
                {
                    "ヤードID": ["Y001", "Y002"],
                    "保管商品": ["商品A", "商品B"],
                    "在庫数": [50, 30],
                }
            ),
        }

        print("サンプルデータ:")
        for key, df in sample_files.items():
            print(f"  {key}: {len(df)}行")
            print(f"    列: {list(df.columns)}")

        # 各レポートタイプをテスト
        report_types = [
            "balance_sheet",  # サンプル実装済み
            "average_sheet",  # サンプル実装済み
            "block_unit_price",  # サンプル実装済み
            "management_sheet",  # サンプル実装済み
            "balance_management_table",  # サンプル実装済み
        ]

        for report_key in report_types:
            test_single_report(report_key, temp_dir, sample_files)


def test_single_report(report_key: str, output_dir: str, files: dict):
    """単一レポートのテスト"""
    print(f"\n--- {report_key} テスト開始 ---")

    try:
        # 1. レポート生成器を取得
        generator = get_report_generator(report_key, output_dir, files)
        print(f"✅ Generator作成成功: {generator.__class__.__name__}")

        # 2. メイン処理実行
        result_df = generator.main_process()
        print(f"✅ メイン処理成功: {len(result_df)}行のデータ生成")
        print(f"   列: {list(result_df.columns)}")
        print("   データサンプル:")
        print(result_df.head(3).to_string(index=False))

        # 3. PDF生成
        pdf_name = f"{report_key}_test.pdf"
        generated_pdf = generator.generate_pdf(pdf_name)
        pdf_path = os.path.join(output_dir, generated_pdf)
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ PDF生成成功: {generated_pdf} ({file_size} bytes)")
        else:
            print(f"❌ PDF生成失敗: {pdf_path}")

        # 4. Excel生成
        excel_name = f"{report_key}_test.xlsx"
        generated_excel = generator.generate_excel(excel_name)
        excel_path = os.path.join(output_dir, generated_excel)
        if os.path.exists(excel_path):
            file_size = os.path.getsize(excel_path)
            print(f"✅ Excel生成成功: {generated_excel} ({file_size} bytes)")

            # Excelファイルの内容確認
            try:
                test_df = pd.read_excel(excel_path)
                print(f"   Excel内容確認: {len(test_df)}行読み込み成功")
            except Exception as e:
                print(f"   Excel内容確認エラー: {e}")
        else:
            print(f"❌ Excel生成失敗: {excel_path}")

        print(f"✅ {report_key} テスト完了")

    except Exception as e:
        print(f"❌ {report_key} テストエラー: {e}")
        import traceback

        traceback.print_exc()


def test_factory_report():
    """Factory Report の特別テスト（実装がある場合）"""
    print("\n=== Factory Report 特別テスト ===")

    # factory_report_main_processが存在するかチェック
    try:
        from app.api.services.manage_report_processors.factory_report.main import (
            factory_report_main_process,
        )

        print("✅ factory_report_main_process インポート成功")

        # テストデータでFactory Reportを試す
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_files = {
                "shipment": pd.DataFrame(
                    {"商品コード": ["A001", "A002"], "数量": [10, 20]}
                )
            }

            try:
                generator = get_report_generator(
                    "factory_report", temp_dir, sample_files
                )
                result_df = generator.main_process()
                print(f"✅ Factory Report実行成功: {len(result_df)}行")

                # Excel生成テスト
                excel_name = generator.generate_excel("factory_report.xlsx")
                excel_path = os.path.join(temp_dir, excel_name)
                if os.path.exists(excel_path):
                    print(
                        f"✅ Factory Report Excel生成成功: {os.path.getsize(excel_path)} bytes"
                    )

            except Exception as e:
                print(f"⚠️ Factory Report実行エラー（期待される）: {e}")

    except ImportError as e:
        print(f"⚠️ Factory Report モジュールが見つかりません（期待される）: {e}")


def demo_usage():
    """使用方法のデモ"""
    print("\n=== 使用方法デモ ===")

    demo_code = """
# エンドポイントでの使用例
@router.post("/report/manage")
async def generate_pdf(report_key: str, files: dict):
    # 1. レポート生成器を取得
    generator = get_report_generator(report_key, output_dir, df_formatted)
    
    # 2. 前処理（ファイルチェック）
    generator.preprocess(report_key)
    
    # 3. メイン処理（帳票データ生成）
    result_df = generator.main_process()
    
    # 4. PDF生成
    pdf_name = generator.generate_pdf("report.pdf")
    
    # 5. Excel生成（先ほど作成した高品質Excel機能を使用）
    excel_name = generator.generate_excel("report.xlsx")
    
    # 6. レスポンス返却
    return {
        "pdf_url": f"/static/{pdf_name}",
        "excel_url": f"/static/{excel_name}"
    }
    """

    print("📝 エンドポイントでの使用方法:")
    print(demo_code)


if __name__ == "__main__":
    print("BaseReportGenerator テスト開始")
    print("=" * 50)

    try:
        test_report_generator()
        test_factory_report()
        demo_usage()

        print("\n" + "=" * 50)
        print("✅ 全テスト完了！")
        print("\n📚 主要なポイント:")
        print("1. BaseReportGeneratorは共通的なPDF/Excel生成機能を提供")
        print("2. 各サブクラスはmain_process()でデータ生成ロジックを実装")
        print("3. 生成されたDataFrameは高品質Excel機能で出力される")
        print("4. エンドポイントから簡単に使用できる設計")

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
