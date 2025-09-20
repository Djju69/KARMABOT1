-- Migration: Create QR codes table
-- Description: Table for storing QR codes used for discount redemption
-- Date: 2025-01-27

CREATE TABLE IF NOT EXISTS qr_codes (
    id SERIAL PRIMARY KEY,
    qr_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    discount_type VARCHAR(50) NOT NULL,
    discount_value INTEGER NOT NULL,
    description TEXT,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_at TIMESTAMP,
    used_by_partner_id INTEGER REFERENCES partners_v2(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_qr_codes_qr_id ON qr_codes(qr_id);
CREATE INDEX IF NOT EXISTS idx_qr_codes_user_id ON qr_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_qr_codes_expires_at ON qr_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_qr_codes_is_used ON qr_codes(is_used);
CREATE INDEX IF NOT EXISTS idx_qr_codes_used_by_partner ON qr_codes(used_by_partner_id);

-- Create composite index for active QR codes
CREATE INDEX IF NOT EXISTS idx_qr_codes_active ON qr_codes(user_id, is_used, expires_at);

-- Add comment to table
COMMENT ON TABLE qr_codes IS 'QR codes for discount redemption system';
COMMENT ON COLUMN qr_codes.qr_id IS 'Unique QR code identifier (UUID)';
COMMENT ON COLUMN qr_codes.discount_type IS 'Type of discount: loyalty_points, percentage, fixed_amount';
COMMENT ON COLUMN qr_codes.discount_value IS 'Value of the discount';
COMMENT ON COLUMN qr_codes.expires_at IS 'When the QR code expires';
COMMENT ON COLUMN qr_codes.is_used IS 'Whether the QR code has been used';
COMMENT ON COLUMN qr_codes.used_by_partner_id IS 'Partner who redeemed the QR code';
