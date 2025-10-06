"""
Manual API Client - Internal HTTP client for manual/documentation service.
"""
import os
import httpx
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

MANUAL_API_BASE = os.getenv("MANUAL_API_BASE", "http://manual_api:8000")
TIMEOUT = httpx.Timeout(connect=1.0, read=5.0, write=5.0, pool=1.0)


class ManualClient:
    """Client for Manual API internal HTTP calls."""

    def __init__(self, base_url: str = MANUAL_API_BASE):
        self.base_url = base_url.rstrip("/")

    async def list_manuals(self) -> List[Dict]:
        """
        List all available manuals.
        
        Returns:
            List of manual metadata dicts
            
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If Manual API returns error status
        """
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(f"Calling Manual API: {self.base_url}/list")
            response = await client.get(f"{self.base_url}/list")
            response.raise_for_status()
            data = response.json()
            manuals = data.get("manuals", [])
            logger.info("Manual API response received", extra={"count": len(manuals)})
            return manuals

    async def get_manual(self, manual_id: str) -> dict:
        """Get specific manual by ID."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            logger.info(f"Calling Manual API: {self.base_url}/manuals/{manual_id}")
            response = await client.get(f"{self.base_url}/manuals/{manual_id}")
            response.raise_for_status()
            return response.json()
