-- Create bonuses table
CREATE TABLE IF NOT EXISTS bonuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    points_required INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_bonuses_partner_id ON bonuses(partner_id);
CREATE INDEX IF NOT EXISTS idx_bonuses_is_active ON bonuses(is_active);

-- Add trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_bonuses_updated_at
AFTER UPDATE ON bonuses
BEGIN
    UPDATE bonuses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
