"""
Ledger API Client - 元帳サービス内部HTTPクライアント

元帳サービスと通信し、各種レポート生成、財務計算、
ブロック単価計算などの機能を利用。

機能:
  - 各種レポート生成(財務表、工場レポート等)
  - ブロック単価計算
  - 分析データ取得

タイムアウト設定:
  - connect: 1.0s
  - read: 5.0s (レポート生成は時間がかかる場合がある)
  - write: 5.0s
  - pool: 1.0s

使用例:
    client = LedgerClient()
    report = await client.generate_report(
        "balance_sheet",
        {"start_date": "2025-01-01", "end_date": "2025-01-31"}
    )
"""

import os

import httpx

from backend_shared.application.logging import create_log_context, get_module_logger

logger = get_module_logger(__name__)

LEDGER_API_BASE = os.getenv("LEDGER_API_BASE", "http://ledger_api:8000")
TIMEOUT = httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=1.0)


class LedgerClient:
    """Client for Ledger API internal HTTP calls."""

    def __init__(self, base_url: str = LEDGER_API_BASE):
        self.base_url = base_url.rstrip("/")

    async def generate_report(self, report_type: str, params: dict) -> dict:
        """
        Request report generation from Ledger API.

        Args:
            report_type: Type of report (e.g., 'balance_sheet', 'factory_report')
            params: Report parameters (date range, filters, etc.)

        Returns:
            dict with report metadata or job ID

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If Ledger API returns error status
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(
                "Calling Ledger API",
                extra=create_log_context(
                    operation="call_ledger_api",
                    url=f"{self.base_url}/reports/{report_type}",
                    params=params,
                ),
            )
            response = await client.post(
                f"{self.base_url}/reports/{report_type}",
                json=params,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(
                "Ledger API response received", extra={"report_type": report_type}
            )
            return data

    async def get_health(self) -> dict:
        """Check Ledger API health status."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
