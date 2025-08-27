import asyncio
import logging
from typing import Optional

try:
    import asyncpg  # type: ignore
except Exception:
    asyncpg = None

from ..settings import settings
from .cache import cache_service
from ..utils.telemetry import log_event

logger = logging.getLogger(__name__)


class PGNotifyListener:
    """LISTEN/NOTIFY consumer for cache invalidation.
    Non-breaking: if asyncpg or PG URL unavailable, runs as no-op with logs.
    """

    def __init__(self, dsn: str, channel: str = "cache_invalidation"):
        self._dsn = dsn
        self._channel = channel
        self._conn: Optional[any] = None
        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

    async def start(self):
        if not settings.features.listen_notify:
            logger.info("PGNotifyListener disabled by feature flag")
            return
        if not asyncpg or not self._dsn.startswith("postgresql+"):
            logger.warning("PGNotifyListener not started (no asyncpg or DSN not Postgres)")
            return
        try:
            self._conn = await asyncpg.connect(self._dsn.replace("+asyncpg", ""))
            await self._conn.add_listener(self._channel, self._on_notify)
            await self._conn.execute(f"LISTEN {self._channel};")
            logger.info(f"✅ PG LISTEN started on channel '{self._channel}'")
            self._task = asyncio.create_task(self._watchdog())
        except Exception as e:
            logger.warning(f"PGNotifyListener start failed: {e}")

    async def stop(self):
        self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2)
            except Exception:
                pass
        try:
            if self._conn:
                await self._conn.close()
        except Exception:
            pass

    async def _watchdog(self):
        # Keep connection alive, periodically ping
        while not self._stop.is_set():
            await asyncio.sleep(30)
            try:
                if self._conn:
                    await self._conn.execute("SELECT 1;")
            except Exception as e:
                logger.warning(f"PGNotifyListener ping failed: {e}")

    def _on_notify(self, connection, pid, channel, payload):
        # Expected payload: JSON with {type, city_id, category, partner_profile_id}
        logger.info(f"📣 PG NOTIFY: channel={channel} payload={payload}")
        # Safe parse and delete by mask
        try:
            import json
            data = json.loads(payload)
            # telemetry (fire-and-forget)
            try:
                import asyncio; asyncio.create_task(log_event("cache_invalidate_event_received", source="pg_notify", **{k: data.get(k) for k in ("type","city_id","category","category_id","partner_profile_id")}))
            except Exception:
                pass
            if data.get("type") == "catalog":
                city_id = data.get("city_id", "*")
                category = data.get("category") or data.get("category_id") or "*"
                mask = f"catalog:{city_id}:{category}:*"
                asyncio.create_task(cache_service.delete_by_mask(mask))
                try:
                    import asyncio; asyncio.create_task(log_event("cache_invalidate_delete_scheduled", type="catalog", mask=mask))
                except Exception:
                    pass
            elif data.get("type") == "partner_cab":
                partner_id = data.get("partner_profile_id", "*")
                category = data.get("category") or data.get("category_id") or "*"
                mask = f"partner_cab:{partner_id}:{category}:*"
                asyncio.create_task(cache_service.delete_by_mask(mask))
                try:
                    import asyncio; asyncio.create_task(log_event("cache_invalidate_delete_scheduled", type="partner_cab", mask=mask))
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"PGNotifyListener payload error: {e}")


pg_notify_listener = PGNotifyListener(settings.database.url)
