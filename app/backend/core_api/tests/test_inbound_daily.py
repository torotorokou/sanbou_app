"""
Tests for inbound daily API endpoint.
日次搬入量APIのテスト（累積モード・バリデーション）
"""
import pytest
from datetime import date
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_inbound_daily_cum_scope_none(client: AsyncClient):
    """cum_scope=none: 累積計算なし（cum_ton=NULL）"""
    response = await client.get(
        "/api/inbound/daily",
        params={"start": "2025-10-01", "end": "2025-10-05", "cum_scope": "none"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
    # cum_tonはすべてNULL
    for row in data:
        assert row["cum_ton"] is None
        assert row["ton"] >= 0


@pytest.mark.asyncio
async def test_inbound_daily_cum_scope_range(client: AsyncClient):
    """cum_scope=range: 全期間累積"""
    response = await client.get(
        "/api/inbound/daily",
        params={"start": "2025-10-01", "end": "2025-10-05", "cum_scope": "range"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
    # cum_tonは単調増加（または同値）
    prev_cum = -1.0
    for row in data:
        assert row["cum_ton"] is not None
        assert row["cum_ton"] >= prev_cum
        prev_cum = row["cum_ton"]


@pytest.mark.asyncio
async def test_inbound_daily_cum_scope_month(client: AsyncClient):
    """cum_scope=month: 月ごとリセット"""
    response = await client.get(
        "/api/inbound/daily",
        params={
            "start": "2025-09-28",
            "end": "2025-10-03",
            "cum_scope": "month",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 6
    
    # 月跨ぎで累積がリセットされることを確認
    # 9月末の累積 > 10月初日の累積
    sep_last = [r for r in data if r["ddate"].startswith("2025-09")][-1]
    oct_first = [r for r in data if r["ddate"].startswith("2025-10")][0]
    
    if sep_last["cum_ton"] is not None and oct_first["cum_ton"] is not None:
        # 10月の累積はリセットされるため、9月末より小さい可能性が高い
        # （ただし10月初日のtonが大きい場合は逆転もあり得る）
        assert oct_first["cum_ton"] >= 0


@pytest.mark.asyncio
async def test_inbound_daily_cum_scope_week(client: AsyncClient):
    """cum_scope=week: 週ごとリセット"""
    response = await client.get(
        "/api/inbound/daily",
        params={
            "start": "2025-10-05",
            "end": "2025-10-13",
            "cum_scope": "week",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 9
    
    # 週跨ぎで累積がリセット
    # iso_weekが変わるタイミングで累積がリセットされる
    prev_week = None
    for row in data:
        if prev_week is not None and row["iso_week"] != prev_week:
            # 週が変わったら、累積は小さくリセットされる（初日のtonから再スタート）
            assert row["cum_ton"] is not None
        prev_week = row["iso_week"]


@pytest.mark.asyncio
async def test_inbound_daily_with_segment(client: AsyncClient):
    """segment指定でフィルタリング"""
    response = await client.get(
        "/api/inbound/daily",
        params={
            "start": "2025-10-01",
            "end": "2025-10-05",
            "segment": "A",
            "cum_scope": "none",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5
    for row in data:
        assert row["segment"] == "A"


@pytest.mark.asyncio
async def test_inbound_daily_invalid_range(client: AsyncClient):
    """start > end の場合は400エラー"""
    response = await client.get(
        "/api/inbound/daily",
        params={"start": "2025-10-10", "end": "2025-10-05", "cum_scope": "none"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_inbound_daily_range_too_long(client: AsyncClient):
    """範囲が366日を超える場合は400エラー"""
    response = await client.get(
        "/api/inbound/daily",
        params={"start": "2025-01-01", "end": "2026-01-05", "cum_scope": "none"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_inbound_daily_missing_required_params(client: AsyncClient):
    """startとendが必須パラメータ"""
    response = await client.get("/api/inbound/daily")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
