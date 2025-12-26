"""
Customer Churn Analysis - Integration Test

顧客離脱分析APIの統合テスト
"""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.usecases.customer_churn import AnalyzeCustomerChurnUseCase
from app.infra.adapters.customer_churn import CustomerChurnQueryAdapter


@pytest.mark.integration
def test_analyze_customer_churn_integration(db: Session):
    """
    顧客離脱分析の統合テスト

    前提条件:
    - mart.v_customer_sales_daily ビューが存在すること
    - テストデータが投入されていること
    """
    # Arrange
    adapter = CustomerChurnQueryAdapter(db)
    use_case = AnalyzeCustomerChurnUseCase(query_port=adapter)

    # 前期間: 2024年1-3月
    # 今期間: 2024年4-6月
    previous_start = date(2024, 1, 1)
    previous_end = date(2024, 3, 31)
    current_start = date(2024, 4, 1)
    current_end = date(2024, 6, 30)

    # Act
    lost_customers = use_case.execute(
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )

    # Assert
    assert isinstance(lost_customers, list)
    # テストデータに依存するため、件数の具体的な検証は環境次第
    # 基本的な構造の検証のみ行う
    if len(lost_customers) > 0:
        first_customer = lost_customers[0]
        assert hasattr(first_customer, "customer_id")
        assert hasattr(first_customer, "customer_name")
        assert hasattr(first_customer, "last_visit_date")
        assert hasattr(first_customer, "prev_visit_days")
        assert hasattr(first_customer, "prev_total_amount_yen")
        assert hasattr(first_customer, "prev_total_qty_kg")
        assert first_customer.prev_visit_days >= 0
        assert first_customer.prev_total_amount_yen >= 0
        assert first_customer.prev_total_qty_kg >= 0
        # last_visit_date は前期間内であること
        assert previous_start <= first_customer.last_visit_date <= previous_end


def test_analyze_customer_churn_validation():
    """
    顧客離脱分析のバリデーションテスト
    """
    from unittest.mock import Mock

    # Arrange
    mock_adapter = Mock()
    use_case = AnalyzeCustomerChurnUseCase(query_port=mock_adapter)

    # Act & Assert: current_start > current_end
    with pytest.raises(ValueError, match="current_start must be <= current_end"):
        use_case.execute(
            current_start=date(2024, 6, 30),
            current_end=date(2024, 4, 1),
            previous_start=date(2024, 1, 1),
            previous_end=date(2024, 3, 31),
        )

    # Act & Assert: previous_start > previous_end
    with pytest.raises(ValueError, match="previous_start must be <= previous_end"):
        use_case.execute(
            current_start=date(2024, 4, 1),
            current_end=date(2024, 6, 30),
            previous_start=date(2024, 3, 31),
            previous_end=date(2024, 1, 1),
        )
