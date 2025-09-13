from __future__ import annotations

import os
import asyncio
import logging
from typing import Any, Dict, Optional

import xmlrpc.client


logger = logging.getLogger(__name__)


class OdooKarmasystemAPI:
    """
    Async-friendly XML-RPC client for Odoo.

    Reads configuration from env:
      - ODOO_BASE_URL (e.g., https://odoo-crm-production.up.railway.app)
      - ODOO_DB (e.g., 'postgres' or 'odoo')
      - ODOO_USERNAME (e.g., 'user@example.com')
      - ODOO_PASSWORD

    All methods are safe: they catch exceptions and return {success: False} on failure.
    """

    def __init__(self, base_url: Optional[str] = None, *, db: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None) -> None:
        self._base = (base_url or os.getenv("ODOO_BASE_URL", "")).rstrip("/")
        self._db = db or os.getenv("ODOO_DB") or "postgres"
        self._username = username or os.getenv("ODOO_USERNAME") or ""
        self._password = password or os.getenv("ODOO_PASSWORD") or ""
        self._uid: Optional[int] = None
        self._common: Optional[xmlrpc.client.ServerProxy] = None
        self._models: Optional[xmlrpc.client.ServerProxy] = None

    @property
    def is_configured(self) -> bool:
        return bool(self._base and self._db and self._username and self._password)

    # --- Internal helpers ---
    def _common_proxy(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self._base}/xmlrpc/2/common")

    def _models_proxy(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self._base}/xmlrpc/2/object")

    def _authenticate_blocking(self) -> int:
        common = self._common_proxy()
        uid = common.authenticate(self._db, self._username, self._password, {})
        if not uid:
            raise RuntimeError("Odoo authentication failed")
        self._common = common
        self._models = self._models_proxy()
        self._uid = int(uid)
        return self._uid

    async def _ensure_auth(self) -> bool:
        if not self.is_configured:
            logger.warning("Odoo XML-RPC not configured (check ODOO_* env vars)")
            return False
        if self._uid:
            return True
        try:
            await asyncio.to_thread(self._authenticate_blocking)
            return True
        except Exception as e:
            logger.error("Odoo auth error: %s", e)
            return False

    def _execute_kw_blocking(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        if not self._models or self._uid is None:
            raise RuntimeError("Odoo client not authenticated")
        return self._models.execute_kw(self._db, self._uid, self._password, model, method, list(args), kwargs)

    async def _execute_kw(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._execute_kw_blocking, model, method, *args, **kwargs)

    # --- Public API (safe) ---
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
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            vals = {
                'name': business_name or (telegram_username or f"tg:{telegram_chat_id}"),
                'phone': phone or '',
                'customer_rank': 1,
            }
            partner_id = await self._execute_kw('res.partner', 'create', vals)
            return {"success": True, "partner_id": partner_id}
        except Exception as e:
            logger.error("register_partner failed: %s", e)
            return {"success": False, "error": str(e)}

    async def register_loyalty_user(
        self,
        *,
        telegram_user_id: str,
        telegram_username: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            # Ensure a partner exists for the user
            name = telegram_username or f"tg:{telegram_user_id}"
            partner_vals = {'name': name, 'phone': phone or '', 'customer_rank': 1}
            partner_id = await self._execute_kw('res.partner', 'create', partner_vals)
            # Optionally write to a loyalty model if present
            try:
                loy_vals = {'telegram_id': str(telegram_user_id), 'phone': phone or '', 'points': 0, 'partner_id': partner_id}
                await self._execute_kw('karma.loyalty', 'create', loy_vals)
            except Exception:
                pass
            return {"success": True, "partner_id": partner_id}
        except Exception as e:
            logger.error("register_loyalty_user failed: %s", e)
            return {"success": False, "error": str(e)}

    async def process_transaction(
        self,
        *,
        partner_id: int,
        customer_telegram_id: str,
        amount: float,
        points_to_use: int = 0,
    ) -> Dict[str, Any]:
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            # If a dedicated model exists, create a transaction; otherwise, noop
            try:
                vals = {
                    'partner_id': int(partner_id),
                    'amount_vnd': float(amount),
                    'customer_telegram_id': str(customer_telegram_id),
                    'points_used': int(points_to_use),
                }
                txn_id = await self._execute_kw('karmasystem.transaction', 'create', vals)
                return {"success": True, "transaction_id": txn_id}
            except Exception:
                # Graceful fallback if model doesn't exist
                return {"success": False, "error": "model_missing"}
        except Exception as e:
            logger.error("process_transaction failed: %s", e)
            return {"success": False, "error": str(e)}

    async def get_cards_by_category(self, *, category: str) -> Dict[str, Any]:
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            # Attempt to read cards from a model if present
            try:
                domain = [["category", "=", category]]
                fields = ["id", "name", "description", "address", "phone", "average_check", "cashback_percent", "latitude", "longitude"]
                records = await self._execute_kw('karmasystem.partner.card', 'search_read', domain, {'fields': fields, 'limit': 100})
                return {"success": True, "cards": records}
            except Exception:
                return {"success": True, "cards": []}
        except Exception as e:
            logger.error("get_cards_by_category failed: %s", e)
            return {"success": False, "error": str(e)}

    async def get_user_points(self, *, telegram_user_id: str) -> Dict[str, Any]:
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            try:
                # Try modern field name
                domain = [["telegram_id", "=", str(telegram_user_id)]]
                fields = ["points"]
                recs = await self._execute_kw('karma.loyalty', 'search_read', domain, {'fields': fields, 'limit': 1})
                if recs:
                    pts = int(recs[0].get('points') or 0)
                    return {"success": True, "available_points": pts}
                # Try alternative field
                domain2 = [["telegram_user_id", "=", str(telegram_user_id)]]
                recs2 = await self._execute_kw('karma.loyalty', 'search_read', domain2, {'fields': fields, 'limit': 1})
                if recs2:
                    pts = int(recs2[0].get('points') or 0)
                    return {"success": True, "available_points": pts}
                return {"success": True, "available_points": 0}
            except Exception:
                return {"success": True, "available_points": 0}
        except Exception as e:
            logger.error("get_user_points failed: %s", e)
            return {"success": False, "error": str(e)}

    async def create_partner_card(
        self,
        *,
        partner_name: str,
        title: str,
        description: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        category: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        discount_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create partner card in Odoo if model exists. Returns {success, card_id or error}."""
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            try:
                # Ensure partner exists (by name or phone). Simplified: create if missing.
                pid = await self._execute_kw('res.partner', 'create', {
                    'name': partner_name or (title or 'KARMASYSTEM Partner'),
                    'phone': phone or '',
                    'customer_rank': 1,
                })
                vals = {
                    'name': title,
                    'description': description or '',
                    'address': address or '',
                    'phone': phone or '',
                    'category': category or '',
                    'google_maps_url': google_maps_url or '',
                    'discount_text': discount_text or '',
                    'partner_id': pid,
                }
                card_id = await self._execute_kw('karmasystem.partner.card', 'create', vals)
                return {"success": True, "card_id": card_id}
            except Exception:
                return {"success": False, "error": "model_missing"}
        except Exception as e:
            logger.error("create_partner_card failed: %s", e)
            return {"success": False, "error": str(e)}

    async def update_partner_card_status(
        self,
        *,
        card_id: int,
        status: str,
    ) -> Dict[str, Any]:
        """Update Odoo card status if model exists. Safe no-op if missing."""
        try:
            if not await self._ensure_auth():
                return {"success": False, "error": "not_configured"}
            try:
                await self._execute_kw('karmasystem.partner.card', 'write', [int(card_id)], {'status': status})
                return {"success": True}
            except Exception:
                return {"success": False, "error": "model_missing"}
        except Exception as e:
            logger.error("update_partner_card_status failed: %s", e)
            return {"success": False, "error": str(e)}


# Singleton instance for app-wide reuse
odoo_api = OdooKarmasystemAPI()


__all__ = ["OdooKarmasystemAPI", "odoo_api"]


