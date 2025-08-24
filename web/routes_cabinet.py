from typing import Optional, List, Dict, Any
import os
import sqlite3

from fastapi import APIRouter, HTTPException, Header, Depends, Path, UploadFile, File, Form, Cookie, Response, Query

from pydantic import BaseModel, Field

from core.services.webapp_auth import check_jwt
from core.security.jwt_service import verify_partner
from core.settings import settings
from core.services.partners import is_partner

router = APIRouter()

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
    # Dev bypass: allow running UI without real token
    if (not authorization or not authorization.lower().startswith("bearer ")):
        # Try alternative sources: Query, Header, Cookies (in that order)
        alt = token_q or x_auth_token or partner_jwt or authToken or jwt
        if alt:
            authorization = f"Bearer {alt}"
        
        if settings.environment == "development" and allow_partner:
            return {"sub": "1", "role": "partner", "src": "tg_webapp"}
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]

    # 1) Try WebApp token (JWT_SECRET domain)
    claims = check_jwt(token)
    if claims:
        # Require WebApp source unless in development
        src = str(claims.get("src", ""))
        if src != "tg_webapp" and settings.environment != "development":
            # If flagged, attempt partner verification as fallback
            if allow_partner:
                partner_claims = verify_partner(token)
                if partner_claims:
                    return partner_claims
            raise HTTPException(status_code=401, detail="invalid token source")
        return claims

    # 2) Fallback: allow partner tokens if enabled
    if allow_partner:
        partner_claims = verify_partner(token)
        if partner_claims:
            return partner_claims

    # Dev bypass on invalid token
    if settings.environment == "development" and allow_partner:
        return {"sub": "1", "role": "partner", "src": "tg_webapp"}

    # Otherwise invalid
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



def _db_connect() -> sqlite3.Connection:
    # Reuse same path as migrations
    path = "core/database/data.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
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
    # 1) Partner JWTs usually carry role=partner
    role = str(claims.get("role") or "").lower()
    if role != "partner":
        # 2) For WebApp users, auto-switch to partner if they have a partner card (MVP via ENV allowlist)
        try:
            if await is_partner(user_id):
                role = "partner"
            else:
                role = "user"
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
        partner_id = _ensure_partner(conn, tg_user_id)
        args: list[Any] = [partner_id]
        where = "WHERE partner_id = ?"
        if status:
            where += " AND status = ?"
            args.append(status)
        if q:
            where += " AND title LIKE ?"
            args.append(f"%{q}%")
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
        return Card(**dict(row))
