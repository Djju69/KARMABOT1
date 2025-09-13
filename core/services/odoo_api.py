from __future__ import annotations

import os
import json
import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp


logger = logging.getLogger(__name__)


class OdooKarmasystemAPI:
    """
    Minimal async client for Odoo KARMASYSTEM REST API.

    Notes:
    - Base URL is taken from ODOO_BASE_URL (or provided explicitly)
    - All requests have sane timeouts and log failures
    - This client does not change UI; handlers may call these methods
    """

    def __init__(self, base_url: Optional[str] = None, *, session: Optional[aiohttp.ClientSession] = None) -> None:
        url = (base_url or os.getenv("ODOO_BASE_URL", "")).strip()
        self._base = url.rstrip("/") if url else ""
        self._api = f"{self._base}/api/karmasystem" if self._base else ""
        self._session: Optional[aiohttp.ClientSession] = session

    @property
    def is_configured(self) -> bool:
        return bool(self._api)

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session
        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # --- Helpers ---
    async def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured:
            logger.warning("Odoo API is not configured (ODOO_BASE_URL is empty)")
            return {"success": False, "error": "odoo_not_configured"}
        sess = await self._ensure_session()
        url = f"{self._api}{path}"
        try:
            async with sess.post(url, json=payload) as resp:
                txt = await resp.text()
                if resp.status >= 400:
                    logger.error("Odoo POST %s failed: %s %s", url, resp.status, txt)
                    return {"success": False, "error": f"http_{resp.status}", "body": txt}
                try:
                    return json.loads(txt)
                except Exception:
                    logger.error("Odoo POST %s returned non-JSON: %s", url, txt)
                    return {"success": False, "error": "invalid_json", "body": txt}
        except asyncio.TimeoutError:
            logger.error("Odoo POST %s timeout", url)
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.exception("Odoo POST %s exception: %s", url, e)
            return {"success": False, "error": str(e)}

    async def _get_json(self, path: str) -> Dict[str, Any]:
        if not self.is_configured:
            logger.warning("Odoo API is not configured (ODOO_BASE_URL is empty)")
            return {"success": False, "error": "odoo_not_configured"}
        sess = await self._ensure_session()
        url = f"{self._api}{path}"
        try:
            async with sess.get(url) as resp:
                txt = await resp.text()
                if resp.status >= 400:
                    logger.error("Odoo GET %s failed: %s %s", url, resp.status, txt)
                    return {"success": False, "error": f"http_{resp.status}", "body": txt}
                try:
                    return json.loads(txt)
                except Exception:
                    logger.error("Odoo GET %s returned non-JSON: %s", url, txt)
                    return {"success": False, "error": "invalid_json", "body": txt}
        except asyncio.TimeoutError:
            logger.error("Odoo GET %s timeout", url)
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.exception("Odoo GET %s exception: %s", url, e)
            return {"success": False, "error": str(e)}

    # --- Public API ---
    async def register_partner(
        self,
        *,
        telegram_chat_id: str,
        telegram_username: Optional[str],
        business_name: str,
        business_category: str,
        phone: str,
        **extra: Any,
    ) -> Dict[str, Any]:
        payload = {
            "telegram_chat_id": str(telegram_chat_id),
            "telegram_username": telegram_username,
            "business_name": business_name,
            "business_category": business_category,
            "phone": phone,
            **extra,
        }
        return await self._post_json("/partner/register", payload)

    async def register_loyalty_user(
        self,
        *,
        telegram_user_id: str,
        telegram_username: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "telegram_user_id": str(telegram_user_id),
            "telegram_username": telegram_username,
            "phone": phone,
        }
        return await self._post_json("/loyalty/user/register", payload)

    async def process_transaction(
        self,
        *,
        partner_id: int,
        customer_telegram_id: str,
        amount: float,
        points_to_use: int = 0,
    ) -> Dict[str, Any]:
        payload = {
            "partner_id": int(partner_id),
            "customer_telegram_id": str(customer_telegram_id),
            "amount": float(amount),
            "points_to_use": int(points_to_use),
        }
        return await self._post_json("/transaction/process", payload)

    async def get_cards_by_category(self, *, category: str) -> Dict[str, Any]:
        return await self._get_json(f"/cards/category/{category}")

    async def get_user_points(self, *, telegram_user_id: str) -> Dict[str, Any]:
        return await self._get_json(f"/user/{telegram_user_id}/points")


# Singleton instance for app-wide reuse
odoo_api = OdooKarmasystemAPI()


__all__ = ["OdooKarmasystemAPI", "odoo_api"]


