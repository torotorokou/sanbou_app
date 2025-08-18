"""
改良されたCSVバリデーションアーキテクチャのユニットテスト例

新しい責任分離設計により、各コンポーネントが独立してテストできることを実証します。
従来の設計と比較して、テストの複雑さが大幅に軽減されることを示します。
"""

import io
import unittest

import pandas as pd
from fastapi import UploadFile

from backend_shared.src.csv_validator.pure_csv_validator import PureCSVValidator
from backend_shared.src.csv_validator.response_converter import (
    ValidationResponseConverter,
)
from backend_shared.src.csv_validator.validation_result import (
    ValidationError,
    ValidationErrorType,
    ValidationResult,
)


class TestPureCSVValidator(unittest.TestCase):
    """
    純粋なバリデーションロジックのテスト

    APIレスポンスに依存しないため、シンプルでフォーカスされたテストが可能
    """

    def setUp(self):
        """テストセットアップ"""
        self.required_columns = {
            "shipment": ["出荷日", "商品名", "数量"],
            "yard": ["ヤード名", "住所"],
        }
        self.validator = PureCSVValidator(self.required_columns)

    def test_validate_required_columns_success(self):
        """必須カラムチェック成功テスト"""
        # 正常なDataFrame
        dfs = {
            "shipment": pd.DataFrame(
                {"出荷日": ["2024-01-01"], "商品名": ["商品A"], "数量": [100]}
            ),
            "yard": pd.DataFrame({"ヤード名": ["ヤードA"], "住所": ["住所A"]}),
        }

        files = {
            "shipment": UploadFile(filename="shipment.csv", file=io.BytesIO()),
            "yard": UploadFile(filename="yard.csv", file=io.BytesIO()),
        }

        result = self.validator.validate_required_columns(dfs, files)

        # アサーション
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_validate_required_columns_failure(self):
        """必須カラムチェック失敗テスト"""
        # 不正なDataFrame（商品名カラムが不足）
        dfs = {
            "shipment": pd.DataFrame(
                {
                    "出荷日": ["2024-01-01"],
                    # "商品名"カラムが不足
                    "数量": [100],
                }
            ),
            "yard": pd.DataFrame({"ヤード名": ["ヤードA"], "住所": ["住所A"]}),
        }

        files = {
            "shipment": UploadFile(filename="shipment.csv", file=io.BytesIO()),
            "yard": UploadFile(filename="yard.csv", file=io.BytesIO()),
        }

        result = self.validator.validate_required_columns(dfs, files)

        # アサーション
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(
            result.errors[0].error_type, ValidationErrorType.MISSING_COLUMNS
        )
        self.assertEqual(result.errors[0].csv_type, "shipment")
        if result.errors[0].details:
            self.assertIn("商品名", result.errors[0].details["missing_columns"])

    def test_validate_denpyou_date_exists_failure(self):
        """伝票日付存在チェック失敗テスト"""
        # 伝票日付カラムが不足したDataFrame
        dfs = {
            "shipment": pd.DataFrame(
                {
                    "出荷日": ["2024-01-01"],
                    "商品名": ["商品A"],
                    "数量": [100],
                    # "伝票日付"カラムが不足
                }
            )
        }

        files = {"shipment": UploadFile(filename="shipment.csv", file=io.BytesIO())}

        result = self.validator.validate_denpyou_date_exists(dfs, files)

        # アサーション
        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.errors[0].error_type, ValidationErrorType.MISSING_DATE_FIELD
        )


class TestValidationResponseConverter(unittest.TestCase):
    """
    レスポンス変換ロジックのテスト

    バリデーションロジックに依存しないため、純粋にレスポンス変換のみをテスト可能
    """

    def setUp(self):
        """テストセットアップ"""
        self.converter = ValidationResponseConverter()

    def test_convert_success_result(self):
        """成功結果の変換テスト"""
        success_result = ValidationResult.success()

        api_response = self.converter.convert_to_api_response(success_result)

        # アサーション
        self.assertIsNone(api_response)

    def test_convert_missing_columns_error(self):
        """カラム不足エラーの変換テスト"""
        error = ValidationError(
            error_type=ValidationErrorType.MISSING_COLUMNS,
            csv_type="shipment",
            message="テストエラー",
            details={
                "filename": "test.csv",
                "missing_columns": ["商品名"],
                "available_columns": ["出荷日", "数量"],
            },
        )
        failure_result = ValidationResult.single_error(error)

        files = {"shipment": UploadFile(filename="test.csv", file=io.BytesIO())}

        api_response = self.converter.convert_to_api_response(failure_result, files)

        # アサーション
        self.assertIsNotNone(api_response)
        if api_response:
            self.assertEqual(api_response.code, "MISSING_COLUMNS")
            self.assertIn("商品名", api_response.detail)

    def test_convert_date_mismatch_error(self):
        """日付不一致エラーの変換テスト"""
        error = ValidationError(
            error_type=ValidationErrorType.DATE_MISMATCH,
            message="伝票日付が一致しません",
            details={
                "dates_info": {"shipment": ["2024-01-01"], "yard": ["2024-01-02"]}
            },
        )
        failure_result = ValidationResult.single_error(error)

        api_response = self.converter.convert_to_api_response(failure_result)

        # アサーション
        self.assertIsNotNone(api_response)
        if api_response:
            self.assertEqual(api_response.code, "DATE_MISMATCH")
            self.assertEqual(api_response.detail, "伝票日付が一致しません。")


class TestArchitectureBenefits(unittest.TestCase):
    """
    アーキテクチャ改善による利点を実証するテスト
    """

    def test_independent_testing(self):
        """独立したテストが可能であることを実証"""
        # 1. バリデーションロジック単体のテスト（APIレスポンス不要）
        validator = PureCSVValidator({"test": ["col1", "col2"]})
        dfs = {"test": pd.DataFrame({"col1": [1], "col2": [2]})}
        files = {"test": UploadFile(filename="test.csv", file=io.BytesIO())}

        validation_result = validator.validate_required_columns(dfs, files)
        self.assertTrue(validation_result.is_valid)

        # 2. レスポンス変換単体のテスト（実際のバリデーション不要）
        converter = ValidationResponseConverter()
        mock_error = ValidationError(
            error_type=ValidationErrorType.MISSING_COLUMNS,
            csv_type="test",
            message="Mock error",
            details={
                "missing_columns": ["col3"],
                "available_columns": ["col1", "col2"],
            },
        )
        mock_result = ValidationResult.single_error(mock_error)

        api_response = converter.convert_to_api_response(mock_result, files)
        self.assertIsNotNone(api_response)
        if api_response:
            self.assertEqual(api_response.code, "MISSING_COLUMNS")

    def test_easy_mocking(self):
        """モック作成の容易さを実証"""
        # 純粋なValidationResultオブジェクトは簡単にモック可能
        mock_success = ValidationResult.success()
        mock_failure = ValidationResult.single_error(
            ValidationError(
                error_type=ValidationErrorType.DATE_MISMATCH,
                message="Mock date mismatch",
            )
        )

        converter = ValidationResponseConverter()

        # 成功ケース
        success_response = converter.convert_to_api_response(mock_success)
        self.assertIsNone(success_response)

        # 失敗ケース
        failure_response = converter.convert_to_api_response(mock_failure)
        self.assertIsNotNone(failure_response)
        if failure_response:
            self.assertEqual(failure_response.code, "DATE_MISMATCH")


if __name__ == "__main__":
    print("改良されたCSVバリデーションアーキテクチャのユニットテスト")
    print("=" * 60)

    # テスト実行
    unittest.main(verbosity=2)
