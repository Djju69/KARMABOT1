-- Migration: create partner_cards table
-- Idempotent: safe to run multiple times
CREATE TABLE IF NOT EXISTS partner_cards (
    id BIGSERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful index to check partner status quickly
CREATE INDEX IF NOT EXISTS idx_partner_cards_tg_user_id ON partner_cards (tg_user_id);
CREATE INDEX IF NOT EXISTS idx_partner_cards_status ON partner_cards (status);

-- Optionally ensure tg_user_id uniqueness if one card per user is required
-- CREATE UNIQUE INDEX IF NOT EXISTS uq_partner_cards_tg_user_id ON partner_cards (tg_user_id);
