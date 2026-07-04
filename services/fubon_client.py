"""
HTTP client for the standalone Fubon SDK service.

The Fubon SDK is expected to run on the already-authorized machine via
``fubon_service.py``.  This client keeps the main app decoupled from the SDK
installation and gives API routes a single integration point.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from loguru import logger


class FubonClient:
    """Small wrapper around the standalone Fubon service HTTP API."""

    def __init__(
        self,
        base_url: Optional[str],
        timeout: int = 10,
        service_token: Optional[str] = None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = timeout
        self.service_token = service_token

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> Dict[str, str]:
        if not self.service_token:
            return {}
        return {"X-Fubon-Service-Token": self.service_token}

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "success": False,
                "error": "FUBON_SERVICE_URL is not configured",
            }

        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            return {"success": True, "data": data}
        except requests.exceptions.RequestException as exc:
            logger.warning(f"Fubon service request failed: {url} ({exc})")
            return {"success": False, "error": str(exc), "service_url": self.base_url}
        except ValueError as exc:
            logger.warning(f"Fubon service returned non-JSON response: {url} ({exc})")
            return {"success": False, "error": "Fubon service returned non-JSON"}

    @staticmethod
    def normalize_stock_id(stock_id: str) -> str:
        return stock_id.replace(".TW", "").replace(".TWO", "").strip()

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def accounts(self) -> Dict[str, Any]:
        return self._request("GET", "/accounts")

    def quote(self, stock_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/quote/{self.normalize_stock_id(stock_id)}")

    def comprehensive(self, stock_id: str) -> Dict[str, Any]:
        return self._request(
            "GET", f"/comprehensive/{self.normalize_stock_id(stock_id)}"
        )

    def place_order(
        self,
        stock_id: str,
        action: str,
        quantity: int,
        price: float,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/order",
            params={
                "stock_id": self.normalize_stock_id(stock_id),
                "action": action,
                "quantity": quantity,
                "price": price,
                "dry_run": dry_run,
            },
        )
