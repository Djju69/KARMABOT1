# Dev seed for QR redeem E2E testing
# Creates partner tg_user_id=1, a card, and one QR token for that card.

from core.database.db_v2 import db_v2

# Ensure partner tg_user_id=1 exists
partner = db_v2.get_or_create_partner(1, "Dev Partner")

# Ensure at least one category exists and pick first
with db_v2.get_connection() as conn:
    row = conn.execute("SELECT id FROM categories_v2 ORDER BY id LIMIT 1").fetchone()
    if not row:
        raise SystemExit("No categories_v2 found. Run app once to apply migrations.")
    cat_id = int(row[0])

# Create a card for this partner
card_id = db_v2.admin_add_card(
    partner_tg_id=1,
    category_slug=db_v2.get_category_by_slug("restaurants").slug if db_v2.get_category_by_slug("restaurants") else "restaurants",
    title="Dev Test Card",
    description="Test",
    status="approved",
)

if not card_id:
    # Fallback: create with direct insert using existing category id
    from core.database.db_v2 import Card
    c = Card(
        id=None,
        partner_id=partner.id,
        category_id=cat_id,
        title="Dev Test Card",
        description="Test",
        status="approved",
    )
    card_id = db_v2.create_card(c)

# Create a QR code
QR_TOKEN = "TESTQR123"
with db_v2.get_connection() as conn:
    # Try insert or ignore if exists
    conn.execute(
        """
        INSERT OR IGNORE INTO qr_codes_v2 (card_id, qr_token, is_redeemed)
        VALUES (?, ?, 0)
        """,
        (card_id, QR_TOKEN),
    )
    # Fetch ID for visibility
    row = conn.execute("SELECT id, is_redeemed FROM qr_codes_v2 WHERE qr_token = ?", (QR_TOKEN,)).fetchone()
    print({"card_id": card_id, "qr_id": int(row[0]), "is_redeemed": int(row[1]), "qr_token": QR_TOKEN})
