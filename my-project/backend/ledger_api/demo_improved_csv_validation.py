"""
改良されたCSVバリデーションアーキテクチャのデモンストレーション

新しい責任分離設計と従来設計の比較を通じて、
改良の効果を具体的に示すデモンストレーションファイルです。
"""

import io
from typing import Dict

import pandas as pd
from fastapi import UploadFile

# 新しい設計のクラス群
from backend_shared.src.csv_validator.pure_csv_validator import PureCSVValidator
from backend_shared.src.csv_validator.response_converter import (
    ValidationResponseConverter,
)


def create_mock_file(filename: str, content: str) -> UploadFile:
    """テスト用のモックファイルを作成"""
    return UploadFile(filename=filename, file=io.BytesIO(content.encode()))


def create_sample_dataframes() -> Dict[str, pd.DataFrame]:
    """サンプルデータフレームを作成"""
    return {
        "shipment": pd.DataFrame(
            {
                "出荷日": ["2024-01-01", "2024-01-02"],
                "商品名": ["商品A", "商品B"],
                "数量": [100, 200],
            }
        ),
        "yard": pd.DataFrame(
            {"ヤード名": ["ヤードA", "ヤードB"], "住所": ["住所A", "住所B"]}
        ),
    }


def create_sample_files() -> Dict[str, UploadFile]:
    """サンプルファイルを作成"""
    return {
        "shipment": create_mock_file(
            "shipment.csv", "出荷日,商品名,数量\n2024-01-01,商品A,100"
        ),
        "yard": create_mock_file("yard.csv", "ヤード名,住所\nヤードA,住所A"),
    }


def demo_new_architecture():
    """新しいアーキテクチャのデモンストレーション"""
    print("=== 新しいアーキテクチャのデモ ===")

    # サンプルデータ準備
    dfs = create_sample_dataframes()
    files = create_sample_files()
    required_columns = {
        "shipment": ["出荷日", "商品名", "数量"],
        "yard": ["ヤード名", "住所"],
    }

    # 1. 純粋なバリデーションロジック（APIレスポンスに依存しない）
    print("\n1. 純粋なバリデーション実行:")
    validator = PureCSVValidator(required_columns)
    validation_result = validator.validate_all(dfs, files)

    print(f"   バリデーション結果: {'成功' if validation_result.is_valid else '失敗'}")
    if not validation_result.is_valid:
        for error in validation_result.errors:
            print(f"   エラー: {error.error_type.value} - {error.message}")

    # 2. APIレスポンス変換（バリデーションロジックとは独立）
    print("\n2. APIレスポンス変換:")
    converter = ValidationResponseConverter()
    api_response = converter.convert_to_api_response(validation_result, files)

    if api_response:
        print(f"   レスポンスコード: {api_response.code}")
        print(f"   詳細: {api_response.detail}")
    else:
        print("   レスポンス: 成功（Noneが返却）")

    # 3. 単体テストが容易になることの実演
    print("\n3. 単体テストの容易さ:")
    print("   - バリデーションロジックのテスト（APIレスポンス不要）")
    print("   - レスポンス変換のテスト（バリデーションロジック不要）")
    print("   - 各責務が独立してテスト可能")


def demo_error_handling():
    """エラーハンドリングのデモンストレーション"""
    print("\n=== エラーハンドリングのデモ ===")

    # エラーケース：必須カラム不足
    dfs_with_error = {
        "shipment": pd.DataFrame(
            {
                "出荷日": ["2024-01-01"],
                # "商品名"カラムが不足
                "数量": [100],
            }
        ),
        "yard": pd.DataFrame({"ヤード名": ["ヤードA"], "住所": ["住所A"]}),
    }

    files = create_sample_files()
    required_columns = {
        "shipment": ["出荷日", "商品名", "数量"],
        "yard": ["ヤード名", "住所"],
    }

    # 新しいアーキテクチャでのエラーハンドリング
    validator = PureCSVValidator(required_columns)
    validation_result = validator.validate_all(dfs_with_error, files)

    print(f"バリデーション結果: {'成功' if validation_result.is_valid else '失敗'}")

    if not validation_result.is_valid:
        error = validation_result.errors[0]
        print(f"エラータイプ: {error.error_type.value}")
        print(f"エラーメッセージ: {error.message}")
        print(f"影響するCSVタイプ: {error.csv_type}")
        print(f"詳細情報: {error.details}")

        # APIレスポンスへの変換
        converter = ValidationResponseConverter()
        api_response = converter.convert_to_api_response(validation_result, files)
        if api_response:
            print(f"APIレスポンスコード: {api_response.code}")
            print(f"APIレスポンス詳細: {api_response.detail}")
        else:
            print("APIレスポンス: None（予期しない結果）")


def demo_architecture_benefits():
    """アーキテクチャ改善の利点を説明"""
    print("\n=== アーキテクチャ改善の利点 ===")

    print("\n1. 責任分離（Single Responsibility Principle）:")
    print("   - PureCSVValidator: 純粋なバリデーションロジックのみ")
    print("   - ValidationResponseConverter: レスポンス変換のみ")
    print("   - CsvValidatorService: 統合・調整のみ")

    print("\n2. テスタビリティの向上:")
    print("   - バリデーションロジックを APIレスポンス不要でテスト可能")
    print("   - レスポンス変換を バリデーションロジック不要でテスト可能")
    print("   - モック作成が容易")

    print("\n3. 保守性の向上:")
    print("   - バリデーションルール変更時：PureCSVValidatorのみ修正")
    print("   - レスポンス形式変更時：ValidationResponseConverterのみ修正")
    print("   - 変更の影響範囲が限定される")

    print("\n4. 再利用性の向上:")
    print("   - PureCSVValidatorは他のAPIタイプでも再利用可能")
    print("   - ValidationResponseConverterは他のバリデーション結果でも使用可能")

    print("\n5. 型安全性の向上:")
    print("   - ValidationResult型による明確なバリデーション結果表現")
    print("   - 各層での型安全なデータ交換")


if __name__ == "__main__":
    print("CSVバリデーションアーキテクチャ改善デモンストレーション")
    print("=" * 60)

    demo_new_architecture()
    demo_error_handling()
    demo_architecture_benefits()

    print("\n" + "=" * 60)
    print("デモンストレーション完了")
