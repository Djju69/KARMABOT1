-- Migration: add archived_at to partner_cards and supporting indexes
-- Idempotent and safe to run multiple times
ALTER TABLE partner_cards
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- Optional index to speed up queries filtering non-archived
CREATE INDEX IF NOT EXISTS idx_partner_cards_archived_at ON partner_cards (archived_at);
