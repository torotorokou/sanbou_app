"""Unit Tests for SalesTree UseCases"""
import pytest
from datetime import date

from app.core.usecases.sales_tree.fetch_summary_uc import FetchSalesTreeSummaryUseCase
from app.core.usecases.sales_tree.fetch_daily_series_uc import FetchSalesTreeDailySeriesUseCase
from app.core.domain.sales_tree import (
    SummaryRequest, 
    DailySeriesRequest, 
    SummaryRow, 
    DailyPoint, 
    MetricEntry
)


class FakeSalesTreeQuery:
    """Fake implementation of ISalesTreeQuery for testing"""
    
    def __init__(self, summary_data=None, daily_data=None):
        self._summary_data = summary_data or []
        self._daily_data = daily_data or []
    
    def fetch_summary(self, req: SummaryRequest) -> list[SummaryRow]:
        """Return preset summary data"""
        return self._summary_data
    
    def fetch_daily_series(self, req: DailySeriesRequest) -> list[DailyPoint]:
        """Return preset daily series data"""
        return self._daily_data


class TestFetchSalesTreeSummaryUseCase:
    """Test FetchSalesTreeSummaryUseCase with Fake Port"""
    
    def test_fetch_summary_with_customer_mode(self):
        """Test fetching summary in customer mode"""
        # Arrange
        test_data = [
            SummaryRow(
                rep_id=101,
                rep_name="山田太郎",
                metrics=[
                    MetricEntry(
                        id="C001",
                        name="株式会社ABC",
                        amount=1500000,
                        qty=5000,
                        line_count=50,
                        slip_count=25,
                        count=25,
                        unit_price=300,
                    ),
                    MetricEntry(
                        id="C002",
                        name="株式会社XYZ",
                        amount=800000,
                        qty=2000,
                        line_count=20,
                        slip_count=10,
                        count=10,
                        unit_price=400,
                    ),
                ],
            ),
        ]
        fake_port = FakeSalesTreeQuery(summary_data=test_data)
        uc = FetchSalesTreeSummaryUseCase(query=fake_port)
        
        req = SummaryRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            mode="customer",
            rep_ids=[101],
            top_n=20,
            sort_by="amount",
            order="desc",
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 1
        assert result[0].rep_id == 101
        assert len(result[0].metrics) == 2
        assert result[0].metrics[0].name == "株式会社ABC"
        assert result[0].metrics[0].amount == 1500000
        assert result[0].metrics[1].name == "株式会社XYZ"
    
    def test_fetch_summary_with_item_mode(self):
        """Test fetching summary in item mode"""
        # Arrange
        test_data = [
            SummaryRow(
                rep_id=102,
                rep_name="佐藤花子",
                metrics=[
                    MetricEntry(
                        id="I001",
                        name="鉄くず",
                        amount=2000000,
                        qty=10000,
                        line_count=100,
                        slip_count=50,
                        count=100,  # 品目軸ではline_count
                        unit_price=200,
                    ),
                ],
            ),
        ]
        fake_port = FakeSalesTreeQuery(summary_data=test_data)
        uc = FetchSalesTreeSummaryUseCase(query=fake_port)
        
        req = SummaryRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            mode="item",
            rep_ids=[102],
            top_n=10,
            sort_by="qty",
            order="desc",
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 1
        assert result[0].metrics[0].name == "鉄くず"
        assert result[0].metrics[0].qty == 10000
    
    def test_fetch_summary_with_empty_result(self):
        """Test fetching summary with no data"""
        # Arrange
        fake_port = FakeSalesTreeQuery(summary_data=[])
        uc = FetchSalesTreeSummaryUseCase(query=fake_port)
        
        req = SummaryRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            mode="customer",
            rep_ids=[999],
            top_n=20,
            sort_by="amount",
            order="desc",
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert result == []
    
    def test_fetch_summary_with_multiple_reps(self):
        """Test fetching summary with multiple sales reps"""
        # Arrange
        test_data = [
            SummaryRow(
                rep_id=101,
                rep_name="山田太郎",
                metrics=[
                    MetricEntry(
                        id="C001",
                        name="株式会社ABC",
                        amount=1000000,
                        qty=3000,
                        line_count=30,
                        slip_count=15,
                        count=15,
                        unit_price=333,
                    ),
                ],
            ),
            SummaryRow(
                rep_id=102,
                rep_name="佐藤花子",
                metrics=[
                    MetricEntry(
                        id="C001",
                        name="株式会社ABC",
                        amount=500000,
                        qty=1500,
                        line_count=16,
                        slip_count=8,
                        count=8,
                        unit_price=333,
                    ),
                ],
            ),
        ]
        fake_port = FakeSalesTreeQuery(summary_data=test_data)
        uc = FetchSalesTreeSummaryUseCase(query=fake_port)
        
        req = SummaryRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            mode="customer",
            rep_ids=[101, 102],
            top_n=20,
            sort_by="amount",
            order="desc",
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 2
        assert result[0].rep_id == 101
        assert result[1].rep_id == 102


class TestFetchDailySeriesUseCase:
    """Test FetchSalesTreeDailySeriesUseCase with Fake Port"""
    
    def test_fetch_daily_series_with_data(self):
        """Test fetching daily series with data"""
        # Arrange
        test_data = [
            DailyPoint(
                date=date(2025, 11, 1),
                amount=100000,
                qty=500,
                line_count=10,
                slip_count=5,
                count=5,
            ),
            DailyPoint(
                date=date(2025, 11, 2),
                amount=150000,
                qty=600,
                line_count=12,
                slip_count=6,
                count=6,
            ),
            DailyPoint(
                date=date(2025, 11, 3),
                amount=120000,
                qty=550,
                line_count=11,
                slip_count=5,
                count=5,
            ),
        ]
        fake_port = FakeSalesTreeQuery(daily_data=test_data)
        uc = FetchSalesTreeDailySeriesUseCase(query=fake_port)
        
        req = DailySeriesRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 3),
            rep_ids=[101],
            customer_ids=None,
            item_ids=None,
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 3
        assert result[0].date == date(2025, 11, 1)
        assert result[0].amount == 100000
        assert result[1].amount == 150000
        assert result[2].amount == 120000
    
    def test_fetch_daily_series_with_filters(self):
        """Test fetching daily series with customer and item filters"""
        # Arrange
        test_data = [
            DailyPoint(
                date=date(2025, 11, 1),
                amount=80000,
                qty=400,
                line_count=8,
                slip_count=4,
                count=4,
            ),
        ]
        fake_port = FakeSalesTreeQuery(daily_data=test_data)
        uc = FetchSalesTreeDailySeriesUseCase(query=fake_port)
        
        req = DailySeriesRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            rep_id=101,
            customer_id="C001",
            item_id=1,
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 1
        assert result[0].qty == 400
    
    def test_fetch_daily_series_with_empty_result(self):
        """Test fetching daily series with no data"""
        # Arrange
        fake_port = FakeSalesTreeQuery(daily_data=[])
        uc = FetchSalesTreeDailySeriesUseCase(query=fake_port)
        
        req = DailySeriesRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 30),
            rep_id=999,
            customer_id=None,
            item_id=None,
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert result == []
    
    def test_fetch_daily_series_date_ordering(self):
        """Test that daily series maintains date ordering"""
        # Arrange
        test_data = [
            DailyPoint(date=date(2025, 11, 1), amount=100000, qty=500, line_count=10, slip_count=5, count=5),
            DailyPoint(date=date(2025, 11, 2), amount=110000, qty=510, line_count=10, slip_count=5, count=5),
            DailyPoint(date=date(2025, 11, 3), amount=120000, qty=520, line_count=12, slip_count=6, count=6),
        ]
        fake_port = FakeSalesTreeQuery(daily_data=test_data)
        uc = FetchSalesTreeDailySeriesUseCase(query=fake_port)
        
        req = DailySeriesRequest(
            date_from=date(2025, 11, 1),
            date_to=date(2025, 11, 3),
            rep_ids=[101],
            customer_ids=None,
            item_ids=None,
        )
        
        # Act
        result = uc.execute(req)
        
        # Assert
        assert len(result) == 3
        # Verify dates are in order
        for i in range(len(result) - 1):
            assert result[i].date < result[i + 1].date
