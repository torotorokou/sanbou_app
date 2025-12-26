"""
Health Check UseCase

各マイクロサービスのヘルスステータスをチェックし、統合されたステータスを返す。
"""

import asyncio
from datetime import datetime
from typing import Any

import httpx

from backend_shared.application.logging import get_module_logger

logger = get_module_logger(__name__)


class HealthCheckUseCase:
    """
    システム全体のヘルスチェックを実行するUseCase

    各マイクロサービスの状態を並行でチェックし、統合されたステータスを返す。
    """

    def __init__(
        self,
        ai_api_base: str,
        ledger_api_base: str,
        rag_api_base: str,
        manual_api_base: str,
        timeout: float = 2.0,
    ):
        """
        Args:
            ai_api_base: AI API のベースURL
            ledger_api_base: Ledger API のベースURL
            rag_api_base: RAG API のベースURL
            manual_api_base: Manual API のベースURL
            timeout: 各サービスへのリクエストタイムアウト（秒）
        """
        self.services = {
            "ai_api": ai_api_base.rstrip("/"),
            "ledger_api": ledger_api_base.rstrip("/"),
            "rag_api": rag_api_base.rstrip("/"),
            "manual_api": manual_api_base.rstrip("/"),
        }
        self.timeout = timeout

    async def _check_service(
        self, name: str, base_url: str, client: httpx.AsyncClient
    ) -> dict[str, Any]:
        """
        個別サービスのヘルスチェックを実行

        Args:
            name: サービス名
            base_url: サービスのベースURL
            client: HTTPクライアント

        Returns:
            サービスのステータス情報
        """
        try:
            # /health または / エンドポイントをチェック
            for endpoint in ["/health", "/"]:
                try:
                    response = await client.get(f"{base_url}{endpoint}")
                    if response.status_code == 200:
                        return {
                            "name": name,
                            "status": "healthy",
                            "url": base_url,
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "checked_at": datetime.now().isoformat(),
                        }
                except httpx.HTTPError:
                    continue

            # すべてのエンドポイントが失敗
            return {
                "name": name,
                "status": "unhealthy",
                "url": base_url,
                "error": "No valid health endpoint found",
                "checked_at": datetime.now().isoformat(),
            }

        except httpx.TimeoutException:
            logger.warning(
                f"Health check timeout for {name}",
                extra={"service": name, "url": base_url},
            )
            return {
                "name": name,
                "status": "timeout",
                "url": base_url,
                "error": "Request timeout",
                "checked_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(
                f"Health check error for {name}",
                extra={"service": name, "url": base_url, "error": str(e)},
                exc_info=True,
            )
            return {
                "name": name,
                "status": "error",
                "url": base_url,
                "error": str(e),
                "checked_at": datetime.now().isoformat(),
            }

    async def execute(self) -> dict[str, Any]:
        """
        すべてのサービスのヘルスチェックを並行実行

        Returns:
            統合されたヘルスステータス
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 並行実行
            tasks = [self._check_service(name, url, client) for name, url in self.services.items()]
            results = await asyncio.gather(*tasks, return_exceptions=False)

        # 結果を集計
        services_status = {}
        healthy_count = 0
        total_count = len(results)

        for result in results:
            service_name = result["name"]
            services_status[service_name] = result
            if result["status"] == "healthy":
                healthy_count += 1

        # 全体ステータスを決定
        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count == 0:
            overall_status = "critical"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": services_status,
            "checked_at": datetime.now().isoformat(),
        }
