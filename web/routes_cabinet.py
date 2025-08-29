from typing import Optional, List, Dict, Any
import os
import sqlite3
import logging

from fastapi import APIRouter, HTTPException, Header, Depends, Path, UploadFile, File, Form, Cookie, Response, Query

from pydantic import BaseModel, Field

from core.services.webapp_auth import check_jwt
import json, base64
from core.security.jwt_service import verify_partner, verify_admin
from core.settings import settings
from core.services.partners import is_partner
from core.services.cards import card_service
from core.services.cache import get_cache_service

router = APIRouter()
logger = logging.getLogger("auth")

# Define auth dependency BEFORE any route uses Depends(get_current_claims)
def get_current_claims(
    authorization: Optional[str] = Header(default=None),
    x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token"),
    partner_jwt: Optional[str] = Cookie(default=None),
    authToken: Optional[str] = Cookie(default=None),
    jwt: Optional[str] = Cookie(default=None),
    token_q: Optional[str] = Query(default=None, alias="token"),
) -> Dict[str, Any]:
    allow_partner = os.getenv("ALLOW_PARTNER_FOR_CABINET") == "1"
    # 0) Extract token from Authorization or alternative sources
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        try:
            token = authorization.split(" ", 1)[1]
        except Exception:
            token = None
    if not token:
        alt = token_q or x_auth_token or partner_jwt or authToken or jwt
        if alt:
            token = alt
    try:
        logger.info(
            "auth.extract",
            extra={
                "has_auth_header": bool(authorization),
                "has_x_auth": bool(x_auth_token),
                "has_cookie_partner_jwt": bool(partner_jwt),
                "has_cookie_authToken": bool(authToken),
                "has_cookie_jwt": bool(jwt),
                "has_query_token": bool(token_q),
            },
        )
    except Exception:
        pass
    if not token:
        # Dev bypass (optional)
        if getattr(settings, 'environment', None) == "development" and allow_partner:
            return {"sub": "1", "role": "partner", "src": "tg_webapp"}
        try:
            logger.warning("auth.missing_token")
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="missing bearer token")

    # 1) Try WebApp token (JWT_SECRET domain)
    claims = check_jwt(token)
    if claims:
        # Accept any valid JWT regardless of 'src' to avoid false 401 for WebApp tokens
        try:
            logger.info("auth.ok.webapp", extra={"sub": str(claims.get("sub")), "role": str(claims.get("role"))})
        except Exception:
            pass
        return claims

    # 2) Fallback: try partner/admin token verification
    partner_claims = verify_partner(token)
    if partner_claims:
        try:
            logger.info("auth.ok.partner", extra={"sub": str(partner_claims.get("sub")), "role": str(partner_claims.get("role"))})
        except Exception:
            pass
        return partner_claims
    admin_claims = verify_admin(token)
    if admin_claims:
        try:
            logger.info("auth.ok.admin", extra={"sub": str(admin_claims.get("sub")), "role": str(admin_claims.get("role"))})
        except Exception:
            pass
        return admin_claims
    # Strict: do not accept unsigned payloads
    # Any further fallbacks are disabled for production safety.

    # Dev bypass on invalid token
    if settings.environment == "development" and allow_partner:
        return {"sub": "1", "role": "partner", "src": "tg_webapp"}

    # Otherwise invalid
    try:
        logger.warning("auth.invalid_token")
    except Exception:
        pass
    raise HTTPException(status_code=401, detail="invalid token")


class Profile(BaseModel):
    user_id: int
    lang: str
    source: str = "tg_webapp"
    role: str = "user"  # user | partner


class OrderItem(BaseModel):
    id: str
    title: str
    status: str


class OrdersResponse(BaseModel):
    items: List[OrderItem]


# --- Partner Cards (MVP over SQLite migrations) ---
class Card(BaseModel):
    id: int
    category_id: int
    subcategory_id: Optional[int] = None
    city_id: Optional[int] = None
    area_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    google_maps_url: Optional[str] = None
    discount_text: Optional[str] = None
    status: str
    priority_level: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CardCreate(BaseModel):
    category_id: int
    subcategory_id: Optional[int] = Field(default=None)
    city_id: Optional[int] = Field(default=None)
    area_id: Optional[int] = Field(default=None)
    title: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    google_maps_url: Optional[str] = Field(default=None, max_length=500)
    discount_text: Optional[str] = Field(default=None, max_length=200)


class CardUpdate(BaseModel):
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = Field(default=None)
    city_id: Optional[int] = Field(default=None)
    area_id: Optional[int] = Field(default=None)
    title: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    google_maps_url: Optional[str] = Field(default=None, max_length=500)
    discount_text: Optional[str] = Field(default=None, max_length=200)


class CardsResponse(BaseModel):
    items: List[Card]


# --- Card binding (plastic card UID) ---
class BindCardRequest(BaseModel):
    uid: str = Field(..., min_length=8, max_length=64, description="UID from card QR (typically 12 digits)")

class BindCardResponse(BaseModel):
    ok: bool
    last4: str | None = None
    reason: str | None = None  # invalid | taken | blocked


@router.post("/card/bind", response_model=BindCardResponse)
async def bind_card_api(payload: BindCardRequest, claims: Dict[str, Any] = Depends(get_current_claims)):
    """Bind a plastic card UID to current authenticated user (by Telegram user id in token)."""
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    uid = (payload.uid or "").strip()
    # Basic normalization: keep only digits if mostly digit-based UIDs
    if uid:
        import re as _re
        m = _re.findall(r"\d+", uid)
        if m and len("".join(m)) >= 8:
            uid = "".join(m)
    res = card_service.bind_card(tg_user_id, uid)
    if not res.ok:
        return BindCardResponse(ok=False, last4=None, reason=(res.reason or "invalid"))
    return BindCardResponse(ok=True, last4=res.last4, reason=None)


class RedeemRequest(BaseModel):
    uid: str = Field(..., min_length=8, max_length=64, description="UID from QR or plastic card")
    amount: Optional[int] = Field(default=None, description="Optional amount/points to redeem")


class RedeemResponse(BaseModel):
    ok: bool
    reason: Optional[str] = None  # not_implemented | invalid | blocked | already_redeemed | expired | limit


@router.post("/api/qr/redeem", response_model=RedeemResponse)
async def qr_redeem(payload: RedeemRequest, claims: Dict[str, Any] = Depends(get_current_claims)):
    """Погашение QR-кода партнёром.
    Валидация и атомарное обновление статуса QR в таблице `qr_codes_v2`.

    Возвращает причины: invalid | already_redeemed | expired | forbidden
    """
    # 1) Аутентификация
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="unauthorized")

    role = str(claims.get("role") or "").lower()
    uid = (payload.uid or "").strip()
    if not uid:
        return RedeemResponse(ok=False, reason="invalid")

    # 2) Идентификация партнёра и проверка владения QR через карточку
    with _db_connect() as conn:
        try:
            partner_id = _ensure_partner(conn, tg_user_id)
        except Exception:
            # fallback: запрет, если не удалось определить партнёра
            raise HTTPException(status_code=403, detail="forbidden")

        # Найти QR и связанный card.partner_id
        row = conn.execute(
            """
            SELECT q.id AS qid, q.is_redeemed, q.expires_at, q.redeemed_at,
                   c.partner_id
            FROM qr_codes_v2 q
            JOIN cards_v2 c ON c.id = q.card_id
            WHERE q.qr_token = ?
            LIMIT 1
            """,
            (uid,),
        ).fetchone()

        if not row:
            # Нет такого QR
            logger.info("qr_redeem.invalid", extra={"uid": uid[:10]})
            return RedeemResponse(ok=False, reason="invalid")

        qr_id = int(row["qid"]) if "qid" in row.keys() else int(row[0])
        qr_is_redeemed = bool(row["is_redeemed"]) if "is_redeemed" in row.keys() else bool(row[1])
        qr_expires_at = row["expires_at"] if "expires_at" in row.keys() else row[2]
        owner_partner_id = int(row["partner_id"]) if "partner_id" in row.keys() else int(row[4])

        # 3) Проверка владения: либо владелец карточки, либо (супер)админ
        if role not in ("admin", "superadmin") and owner_partner_id != partner_id:
            # Не раскрываем, существует ли токен — 403
            raise HTTPException(status_code=403, detail="forbidden")

        # 4) Попытка атомарного погашения (idempotent через WHERE-условия)
        cur = conn.execute(
            """
            UPDATE qr_codes_v2
            SET is_redeemed = 1,
                redeemed_at = CURRENT_TIMESTAMP,
                redeemed_by = ?
            WHERE id = ?
              AND is_redeemed = 0
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (tg_user_id, qr_id),
        )
        updated = cur.fetchone()
        if updated:
            # Успех
            try:
                logger.info("qr_redeem.ok", extra={"qr_id": qr_id, "by": tg_user_id})
            except Exception:
                pass
            return RedeemResponse(ok=True, reason=None)

        # 5) Определить причину отказа
        # Перечитаем актуальный статус
        row2 = conn.execute(
            "SELECT is_redeemed, expires_at FROM qr_codes_v2 WHERE id = ?",
            (qr_id,),
        ).fetchone()
        if not row2:
            # Теоретически не должен исчезнуть из-под нас
            return RedeemResponse(ok=False, reason="invalid")
        is_red = bool(row2[0])
        exp = row2[1]
        if is_red:
            logger.info("qr_redeem.already_redeemed", extra={"qr_id": qr_id})
            return RedeemResponse(ok=False, reason="already_redeemed")
        # Если не погасился и не redeemed=true, значит просрочен условием WHERE
        logger.info("qr_redeem.expired", extra={"qr_id": qr_id, "exp": str(exp)})
        return RedeemResponse(ok=False, reason="expired")


# --- Categories for Partner UI ---
class CategoryItem(BaseModel):
    id: int
    name: str
    emoji: Optional[str] = None


@router.get("/partner/categories", response_model=List[CategoryItem])
async def partner_categories(claims: Dict[str, Any] = Depends(get_current_claims)):
    # Require auth but no special role; partner or webapp user
    _ = claims
    with _db_connect() as conn:
        rows = conn.execute(
            "SELECT id, name, emoji FROM categories_v2 WHERE is_active = 1 ORDER BY priority_level DESC, name"
        ).fetchall()
        return [CategoryItem(**dict(r)) for r in rows]


# --- Subcategories & Cities (MVP: static lists) ---
class SubcategoryItem(BaseModel):
    id: int
    name: str


class CityItem(BaseModel):
    id: int
    name: str


# Static subcategory sets (MVP)
_SUBCATS_RESTAURANTS: list[SubcategoryItem] = [
    SubcategoryItem(id=101, name="Европейская кухня"),
    SubcategoryItem(id=102, name="Азиатская кухня"),
    SubcategoryItem(id=103, name="Грузинская кухня"),
    SubcategoryItem(id=104, name="Итальянская кухня"),
]

_SUBCATS_TRANSPORT: list[SubcategoryItem] = [
    SubcategoryItem(id=201, name="Авто"),
    SubcategoryItem(id=202, name="Байки/скутеры"),
    SubcategoryItem(id=203, name="Велосипеды"),
]

_SUBCATS_EXCURSIONS: list[SubcategoryItem] = [
    SubcategoryItem(id=301, name="Групповые"),
    SubcategoryItem(id=302, name="Индивидуальные"),
]

_SUBCATS_SPA: list[SubcategoryItem] = [
    SubcategoryItem(id=401, name="Спа-салоны"),
    SubcategoryItem(id=402, name="Массаж"),
    SubcategoryItem(id=403, name="Бани/сауны"),
]

_CITIES: list[CityItem] = [
    # По умолчанию — Нячанг
    CityItem(id=1, name="Нячанг"),
    CityItem(id=2, name="Дананг"),
    CityItem(id=3, name="Хошимин"),
    CityItem(id=4, name="Фукуок"),
]


@router.get("/partner/subcategories", response_model=List[SubcategoryItem])
async def partner_subcategories(category_id: int, claims: Dict[str, Any] = Depends(get_current_claims)):
    _ = claims
    # Определим набор подкатегорий по названию категории из БД, чтобы избежать рассинхронизации ID
    with _db_connect() as conn:
        row = conn.execute("SELECT name FROM categories_v2 WHERE id = ? LIMIT 1", (int(category_id),)).fetchone()
        if not row:
            return []
        name = str(row["name"]).lower()
        # Простейшее сопоставление по ключевым словам
        if "рестора" in name or "каф" in name:
            return _SUBCATS_RESTAURANTS
        if "spa" in name or "спа" in name or "массаж" in name:
            return _SUBCATS_SPA
        if "экскурс" in name:
            return _SUBCATS_EXCURSIONS
        if "транспорт" in name or "аренда" in name or "байк" in name or "скутер" in name or "авто" in name:
            return _SUBCATS_TRANSPORT
    return []


@router.get("/partner/cities", response_model=List[CityItem])
async def partner_cities(claims: Dict[str, Any] = Depends(get_current_claims)):
    _ = claims
    return _CITIES


class AreaItem(BaseModel):
    id: int
    name: str

# Простая карта районов по городу (пока статическая)
_AREAS: dict[int, list[AreaItem]] = {
    1: [  # Нячанг
        AreaItem(id=1001, name="Центр"),
        AreaItem(id=1002, name="Север"),
        AreaItem(id=1003, name="Юг"),
    ],
    2: [  # Дананг — заглушка
        AreaItem(id=2001, name="Все районы (заглушка)"),
    ],
    3: [  # Хошимин — заглушка
        AreaItem(id=3001, name="Все районы (заглушка)"),
    ],
    4: [  # Фукуок — заглушка
        AreaItem(id=4001, name="Все районы (заглушка)"),
    ],
}


@router.get("/partner/areas", response_model=List[AreaItem])
async def partner_areas(city_id: int, claims: Dict[str, Any] = Depends(get_current_claims)):
    _ = claims
    return _AREAS.get(int(city_id), [])



def _ensure_db_bootstrap(conn: sqlite3.Connection) -> None:
    """Create minimal schema if missing to avoid 500 on fresh installs."""
    try:
        # partners_v2
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS partners_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER UNIQUE,
                display_name TEXT,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
            """
        )
        # categories_v2 (subset used by API)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                emoji TEXT,
                is_active INTEGER DEFAULT 1,
                priority_level INTEGER DEFAULT 0
            )
            """
        )
        # Seed default categories if empty
        try:
            row = conn.execute("SELECT COUNT(*) FROM categories_v2").fetchone()
            cnt = int(row[0]) if row else 0
            if cnt == 0:
                conn.executemany(
                    "INSERT INTO categories_v2 (name, emoji, is_active, priority_level) VALUES (?, ?, 1, ?)",
                    [
                        ("Рестораны", "🍽", 100),
                        ("SPA/Массаж", "💆", 90),
                        ("Транспорт/Аренда", "🚗", 80),
                        ("Отели", "🏨", 70),
                        ("Экскурсии", "🗺", 60),
                    ],
                )
        except Exception:
            # Non-fatal seed error
            pass
        # cards_v2 minimal set, optional columns are handled dynamically elsewhere
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cards_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                subcategory_id INTEGER,
                city_id INTEGER,
                area_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                contact TEXT,
                address TEXT,
                google_maps_url TEXT,
                discount_text TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                priority_level INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(partner_id) REFERENCES partners_v2(id)
            )
            """
        )
        conn.commit()
    except Exception:
        # Best-effort; avoid crashing on bootstrap
        pass


def _db_connect() -> sqlite3.Connection:
    # Reuse same path as migrations
    path = "core/database/data.db"
    # Ensure directory exists
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # Ensure minimal schema exists to prevent 500 on first run
    _ensure_db_bootstrap(conn)
    return conn


def _ensure_partner(conn: sqlite3.Connection, tg_user_id: int) -> int:
    # Returns partners_v2.id for given tg_user_id; creates a stub row if absent
    cur = conn.execute(
        "SELECT id FROM partners_v2 WHERE tg_user_id = ? LIMIT 1", (tg_user_id,)
    )
    row = cur.fetchone()
    if row:
        return int(row["id"])
    cur = conn.execute(
        "INSERT INTO partners_v2 (tg_user_id, display_name, is_active) VALUES (?, ?, 1)",
        (tg_user_id, None),
    )
    return int(cur.lastrowid)


def _table_has_columns(conn: sqlite3.Connection, table: str, cols: list[str]) -> set[str]:
    """Return subset of cols that exist in the given table."""
    try:
        info = conn.execute(f"PRAGMA table_info({table})").fetchall()
        have = {str(r[1]) for r in info}
        return {c for c in cols if c in have}
    except Exception:
        return set()


def _select_card_columns(conn: sqlite3.Connection) -> str:
    base = [
        "id", "category_id", "title", "description", "contact", "address",
        "google_maps_url", "discount_text", "status", "priority_level", "created_at", "updated_at",
    ]
    opt = _table_has_columns(conn, 'cards_v2', ['subcategory_id','city_id','area_id'])
    # Keep a stable order
    ordered = []
    if 'subcategory_id' in opt: ordered.append('subcategory_id')
    if 'city_id' in opt: ordered.append('city_id')
    if 'area_id' in opt: ordered.append('area_id')
    # Insert optional right after category_id
    cols = []
    for c in base:
        cols.append(c)
        if c == 'category_id':
            cols.extend(ordered)
    return ", ".join(cols)


@router.get("/profile", response_model=Profile)
async def profile(claims: Dict[str, Any] = Depends(get_current_claims)):
    # Minimal read-only profile from JWT claims and defaults
    try:
        user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    # Language could be taken from DB/profile service later; return default for MVP
    lang = settings.default_lang or "ru"
    # Determine role:
    # 1) Respect explicit roles from token (admin/superadmin/partner)
    role = str(claims.get("role") or "").lower()
    if role in ("admin", "superadmin", "partner"):
        pass  # keep as is
    else:
        # 2) Detect partner via SQLite (partners_v2) to avoid false downgrade to 'user'
        try:
            with _db_connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM partners_v2 WHERE tg_user_id = ? LIMIT 1",
                    (user_id,),
                ).fetchone()
                if row:
                    role = "partner"
                else:
                    # Fallback to legacy detector (e.g., Postgres-backed)
                    try:
                        role = "partner" if await is_partner(user_id) else "user"
                    except Exception:
                        role = "user"
        except Exception:
            # Final fallback: legacy is_partner or user
            try:
                role = "partner" if await is_partner(user_id) else "user"
            except Exception:
                role = "user"
    return Profile(user_id=user_id, lang=lang, source=str(claims.get("src", "")), role=role)


@router.get("/orders", response_model=OrdersResponse)
async def orders(limit: int = 10, claims: Dict[str, Any] = Depends(get_current_claims)):
    # MVP: return empty or mock list until DB integration is finalized
    _ = claims  # reserved for future filtering by user_id
    limit = max(1, min(limit, 50))
    items: List[OrderItem] = []
    # Example mock (commented). Uncomment if you want visible demo data.
    # items = [
    #     OrderItem(id="ord_1", title="Демонстрационный заказ", status="completed"),
    # ]
    return OrdersResponse(items=items[:limit])


@router.get("/partner/cards", response_model=CardsResponse)
async def partner_cards(
    status: Optional[str] = None,
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    after_id: Optional[int] = None,
    limit: int = 20,
    claims: Dict[str, Any] = Depends(get_current_claims),
):
    """List cards owned by current partner (by tg_user_id)."""
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    limit = max(1, min(limit, 100))
    with _db_connect() as conn:
        role = str(claims.get("role") or "").lower()
        args: list = []
        if role in ("admin", "superadmin"):
            # Admins can see all cards
            where = "WHERE 1=1"
        else:
            partner_id = _ensure_partner(conn, tg_user_id)
            where = "WHERE partner_id = ?"
            args.append(partner_id)
        if status:
            where += " AND status = ?"
            args.append(status)
        if q:
            where += " AND title LIKE ?"
            args.append(f"%{q}%")
        if category_id:
            where += " AND category_id = ?"
            args.append(int(category_id))
        if after_id:
            where += " AND id < ?"
            args.append(after_id)
        cols = _select_card_columns(conn)
        # Consistent keyset pagination: use id for both cursor and ordering
        sql = f"SELECT {cols} FROM cards_v2 {where} ORDER BY id DESC LIMIT ?"
        args.append(limit)
        rows = conn.execute(sql, tuple(args)).fetchall()
        items = [Card(**dict(r)) for r in rows]
        return CardsResponse(items=items)


@router.post("/partner/cards", response_model=Card)
async def partner_cards_create(payload: CardCreate, claims: Dict[str, Any] = Depends(get_current_claims)):
    """Create a new card in 'draft' status for current partner."""
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        opt_cols = _table_has_columns(conn, 'cards_v2', ['subcategory_id','city_id','area_id'])
        ordered_opt: list[str] = []
        if 'subcategory_id' in opt_cols:
            ordered_opt.append('subcategory_id')
        if 'city_id' in opt_cols:
            ordered_opt.append('city_id')
        if 'area_id' in opt_cols:
            ordered_opt.append('area_id')
        cols = ['partner_id','category_id','title','description','contact','address','google_maps_url','discount_text'] + ordered_opt
        vals = [
            partner_id,
            payload.category_id,
            payload.title,
            payload.description,
            payload.contact,
            payload.address,
            payload.google_maps_url,
            payload.discount_text,
        ]
        for c in ordered_opt:
            if c == 'subcategory_id':
                vals.append(payload.subcategory_id)
            elif c == 'city_id':
                vals.append(payload.city_id)
            elif c == 'area_id':
                vals.append(payload.area_id)
        placeholders = ", ".join(["?"] * len(vals))
        sql = f"INSERT INTO cards_v2 ({', '.join(cols)}, status) VALUES ({placeholders}, 'pending')"
        cur = conn.execute(sql, tuple(vals))
        card_id = int(cur.lastrowid)
        cols = _select_card_columns(conn)
        row = conn.execute(f"SELECT {cols} FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        # Best-effort: invalidate /auth/me cache for this user to reflect listings
        try:
            await cache_service.invalidate_authme(tg_user_id, reason="listings")
        except Exception:
            pass
        return Card(**dict(row))

# --- Catch-all for HEAD/OPTIONS inside this router to prevent 405 on preflights/HEAD probes
@router.api_route("/{_any:path}", methods=["HEAD", "OPTIONS"])
async def _cabinet_head_options(_any: str):
    return Response(status_code=204)


@router.patch("/partner/cards/{card_id}", response_model=Card)
async def partner_cards_update(
    payload: CardUpdate,
    card_id: int = Path(..., ge=1),
    claims: Dict[str, Any] = Depends(get_current_claims),
):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        # Ensure ownership
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        # Build dynamic update
        fields: list[str] = []
        params: list[Any] = []
        # Always-allowed
        for k in ["category_id","title","description","contact","address","google_maps_url","discount_text"]:
            v = getattr(payload, k)
            if v is not None:
                fields.append(f"{k} = ?")
                params.append(v)
        # Optional columns if exist in table
        opt_cols = _table_has_columns(conn, 'cards_v2', ['subcategory_id','city_id','area_id'])
        for k in ["subcategory_id","city_id","area_id"]:
            if k in opt_cols:
                v = getattr(payload, k)
                if v is not None:
                    fields.append(f"{k} = ?")
                    params.append(v)
        # Sensitive changes -> send to moderation (pending)
        if payload.category_id is not None:
            fields.append("status = 'pending'")
        # If subcategory/city/area changed — also pending (optional)
        if any(getattr(payload, k) is not None for k in ("subcategory_id","city_id","area_id")):
            fields.append("status = 'pending'")
        if not fields:
            # No changes; return current
            cols = _select_card_columns(conn)
            row = conn.execute(f"SELECT {cols} FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="card not found")
            return Card(**dict(row))
        params.append(card_id)
        conn.execute(f"UPDATE cards_v2 SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", tuple(params))
        cols = _select_card_columns(conn)
        row = conn.execute(f"SELECT {cols} FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        # Invalidate /auth/me cache to reflect updated listings
        try:
            await cache_service.invalidate_authme(tg_user_id, reason="listings")
        except Exception:
            pass
        return Card(**dict(row))

@router.post("/partner/cards/{card_id}/hide", response_model=Card)
async def partner_cards_hide(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        conn.execute(
            "UPDATE cards_v2 SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (card_id,),
        )
        cols = _select_card_columns(conn)
        row = conn.execute(
            f"SELECT {cols} FROM cards_v2 WHERE id = ?",
            (card_id,),
        ).fetchone()
        # Invalidate /auth/me cache to reflect archived listings
        try:
            await cache_service.invalidate_authme(tg_user_id, reason="archive")
        except Exception:
            pass
        return Card(**dict(row))


# ----------------------
# Photo gallery (card_images) and moderated delete flow
# ----------------------

def _ensure_card_images_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            position INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
        )
        """
    )


def _ensure_delete_requests_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_delete_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            partner_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending | approved | rejected
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            decided_at DATETIME,
            decided_by TEXT
        )
        """
    )


class CardImage(BaseModel):
    id: int
    card_id: int
    url: str
    position: int = 0
    created_at: Optional[str] = None


@router.get("/partner/cards/{card_id}/images", response_model=List[CardImage])
async def partner_card_images(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        _ensure_card_images_table(conn)
        rows = conn.execute(
            "SELECT id, card_id, url, position, created_at FROM card_images WHERE card_id = ? ORDER BY position, id",
            (card_id,),
        ).fetchall()
        return [CardImage(**dict(r)) for r in rows]


@router.post("/partner/cards/{card_id}/images", response_model=List[CardImage])
async def partner_card_images_upload(
    card_id: int = Path(..., ge=1),
    files: List[UploadFile] = File(..., description="Изображения"),
    claims: Dict[str, Any] = Depends(get_current_claims),
):
    import pathlib
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        _ensure_card_images_table(conn)
        # Prepare directory under web/static/uploads/cards/{card_id}
        base_dir = pathlib.Path("web/static/uploads/cards") / str(card_id)
        base_dir.mkdir(parents=True, exist_ok=True)
        saved: list[CardImage] = []
        # Determine next position
        cur_pos_row = conn.execute("SELECT COALESCE(MAX(position), 0) AS p FROM card_images WHERE card_id = ?", (card_id,)).fetchone()
        next_pos = int(cur_pos_row["p"] or 0)
        for f in files:
            if not f.filename:
                continue
            # Basic extension check
            name = f.filename
            ext = name.split(".")[-1].lower()
            if ext not in ("jpg","jpeg","png","webp","gif"):
                raise HTTPException(status_code=400, detail=f"unsupported file type: .{ext}")
            next_pos += 1
            safe_name = f"{next_pos:03d}_" + name.replace(" ", "_")
            dest_path = base_dir / safe_name
            content = await f.read()
            with open(dest_path, "wb") as out:
                out.write(content)
            url = f"/static/uploads/cards/{card_id}/{safe_name}"
            cur = conn.execute(
                "INSERT INTO card_images (card_id, url, position) VALUES (?, ?, ?)",
                (card_id, url, next_pos),
            )
            img_id = int(cur.lastrowid)
            row = conn.execute(
                "SELECT id, card_id, url, position, created_at FROM card_images WHERE id = ?",
                (img_id,),
            ).fetchone()
            saved.append(CardImage(**dict(row)))
        return saved


@router.delete("/partner/cards/{card_id}/images/{image_id}")
async def partner_card_image_delete(
    card_id: int = Path(..., ge=1),
    image_id: int = Path(..., ge=1),
    claims: Dict[str, Any] = Depends(get_current_claims),
):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        _ensure_card_images_table(conn)
        row = conn.execute("SELECT id, url FROM card_images WHERE id = ? AND card_id = ?", (image_id, card_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="image not found")
        conn.execute("DELETE FROM card_images WHERE id = ?", (image_id,))
        return {"ok": True}


class DeleteRequest(BaseModel):
    id: int
    card_id: int
    partner_id: int
    status: str
    reason: Optional[str] = None
    created_at: Optional[str] = None
    decided_at: Optional[str] = None
    decided_by: Optional[str] = None


class DeleteRequestCreate(BaseModel):
    reason: Optional[str] = None


@router.post("/partner/cards/{card_id}/delete_request", response_model=DeleteRequest)
async def partner_card_delete_request(
    card_id: int = Path(..., ge=1),
    payload: DeleteRequestCreate = None,
    claims: Dict[str, Any] = Depends(get_current_claims),
):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        _ensure_delete_requests_table(conn)
        cur = conn.execute(
            "INSERT INTO card_delete_requests (card_id, partner_id, status, reason) VALUES (?, ?, 'pending', ?)",
            (card_id, partner_id, (payload.reason if payload else None)),
        )
        req_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM card_delete_requests WHERE id = ?", (req_id,)).fetchone()
        return DeleteRequest(**dict(row))


# Admin moderation endpoints (simple role check by claims.role == 'admin' or 'superadmin')
def _require_admin(claims: Dict[str, Any]):
    role = str(claims.get("role") or "").lower()
    if role not in ("admin", "superadmin", "superадмин", "суперадмин"):
        raise HTTPException(status_code=403, detail="admin only")


@router.post("/admin/cards/{card_id}/delete_request/approve")
async def admin_approve_delete(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    _require_admin(claims)
    with _db_connect() as conn:
        _ensure_delete_requests_table(conn)
        # Mark latest pending request approved and delete card
        req = conn.execute(
            "SELECT id FROM card_delete_requests WHERE card_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (card_id,),
        ).fetchone()
        if not req:
            raise HTTPException(status_code=404, detail="pending request not found")
        conn.execute(
            "UPDATE card_delete_requests SET status = 'approved', decided_at = CURRENT_TIMESTAMP, decided_by = ? WHERE id = ?",
            (str(claims.get("sub")), int(req["id"])),
        )
        # Soft delete: set status = 'deleted'
        conn.execute("UPDATE cards_v2 SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (card_id,))
        return {"ok": True}


@router.post("/admin/cards/{card_id}/delete_request/reject")
async def admin_reject_delete(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    _require_admin(claims)
    with _db_connect() as conn:
        _ensure_delete_requests_table(conn)
        req = conn.execute(
            "SELECT id FROM card_delete_requests WHERE card_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1",
            (card_id,),
        ).fetchone()
        if not req:
            raise HTTPException(status_code=404, detail="pending request not found")
        conn.execute(
            "UPDATE card_delete_requests SET status = 'rejected', decided_at = CURRENT_TIMESTAMP, decided_by = ? WHERE id = ?",
            (str(claims.get("sub")), int(req["id"])),
        )
        return {"ok": True}


@router.post("/admin/cards/{card_id}/block")
async def admin_block_card(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    _require_admin(claims)
    with _db_connect() as conn:
        conn.execute("UPDATE cards_v2 SET status = 'blocked', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (card_id,))
        # Also invalidate partner's /auth/me cache using linked tg_user_id
        try:
            owner = conn.execute("SELECT partner_id FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
            if owner:
                pid = int(owner["partner_id"])
                row = conn.execute("SELECT tg_user_id FROM partners_v2 WHERE id = ?", (pid,)).fetchone()
                if row and row["tg_user_id"] is not None:
                    await cache_service.invalidate_authme(int(row["tg_user_id"]), reason="block")
        except Exception:
            pass
        return {"ok": True}


@router.post("/partner/cards/{card_id}/unhide", response_model=Card)
async def partner_cards_unhide(card_id: int = Path(..., ge=1), claims: Dict[str, Any] = Depends(get_current_claims)):
    try:
        tg_user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    with _db_connect() as conn:
        partner_id = _ensure_partner(conn, tg_user_id)
        owner = conn.execute("SELECT partner_id, status FROM cards_v2 WHERE id = ?", (card_id,)).fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="card not found")
        if int(owner["partner_id"]) != partner_id:
            raise HTTPException(status_code=403, detail="forbidden")
        # Unhide: return to approved (published) state; moderation may re-check later if needed
        conn.execute(
            "UPDATE cards_v2 SET status = 'approved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (card_id,),
        )
        cols = _select_card_columns(conn)
        row = conn.execute(
            f"SELECT {cols} FROM cards_v2 WHERE id = ?",
            (card_id,),
        ).fetchone()
        # Invalidate /auth/me cache to reflect listings becoming visible
        try:
            await cache_service.invalidate_authme(tg_user_id, reason="listings")
        except Exception:
            pass
        return Card(**dict(row))
