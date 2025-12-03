"""
Health Check Router

システム全体およびCore API自体のヘルスチェックエンドポイントを提供する。
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.usecases.health_check_uc import HealthCheckUseCase
from app.config.di_providers import get_health_check_usecase

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Core API自体のヘルスチェック
    
    Returns:
        {"status": "ok"}
    """
    return {"status": "ok"}


@router.get("/health/services")
async def services_health_check(
    usecase: HealthCheckUseCase = Depends(get_health_check_usecase)
) -> Dict[str, Any]:
    """
    すべてのマイクロサービスのヘルスチェック
    
    各サービス（AI API, Ledger API, RAG API, Manual API）の状態を並行でチェックし、
    統合されたステータスを返す。
    
    Returns:
        {
            "status": "healthy" | "degraded" | "critical",
            "healthy_services": int,
            "total_services": int,
            "services": {
                "service_name": {
                    "status": "healthy" | "unhealthy" | "timeout" | "error",
                    "url": str,
                    "response_time_ms": float,  # healthyの場合のみ
                    "error": str,  # エラーの場合のみ
                    "checked_at": str
                }
            },
            "checked_at": str
        }
    """
    return await usecase.execute()
