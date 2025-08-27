-- Create qr_issues table for storing QR code information
CREATE TABLE IF NOT EXISTS qr_issues (
    id BIGSERIAL PRIMARY KEY,
    jti VARCHAR(64) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    listing_id BIGINT,
    points INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'issued' CHECK (status IN ('issued', 'redeemed', 'expired')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exp_at TIMESTAMPTZ,
    redeemed_at TIMESTAMPTZ,
    redeemed_by_partner_id BIGINT,
    
    -- Indexes
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_listing FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE SET NULL,
    CONSTRAINT fk_redeemed_by FOREIGN KEY (redeemed_by_partner_id) REFERENCES partners(id) ON DELETE SET NULL
);

-- Add indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_qr_issues_jti ON qr_issues(jti);
CREATE INDEX IF NOT EXISTS idx_qr_issues_user_id ON qr_issues(user_id);
CREATE INDEX IF NOT EXISTS idx_qr_issues_status ON qr_issues(status);
CREATE INDEX IF NOT EXISTS idx_qr_issues_exp_at ON qr_issues(exp_at) WHERE status = 'issued';

-- Add comments
COMMENT ON TABLE qr_issues IS 'Stores information about issued QR codes for discounts and points spending';
COMMENT ON COLUMN qr_issues.jti IS 'Unique identifier for the QR code';
COMMENT ON COLUMN qr_issues.user_id IS 'User who generated the QR code';
COMMENT ON COLUMN qr_issues.listing_id IS 'For discount QR codes - the listing this QR is for';
COMMENT ON COLUMN qr_issues.points IS 'For points QR codes - number of points to spend';
COMMENT ON COLUMN qr_issues.status IS 'Current status of the QR code';
COMMENT ON COLUMN qr_issues.exp_at IS 'Expiration time for the QR code';
COMMENT ON COLUMN qr_issues.redeemed_at IS 'When the QR code was redeemed';
COMMENT ON COLUMN qr_issues.redeemed_by_partner_id IS 'Which partner redeemed this QR code';

-- Add function to clean up expired QR codes
CREATE OR REPLACE FUNCTION clean_expired_qr_codes()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE qr_issues 
    SET status = 'expired' 
    WHERE status = 'issued' 
    AND exp_at < NOW();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to clean up expired QR codes on insert/update
DROP TRIGGER IF EXISTS trigger_clean_expired_qr_codes ON qr_issues;
CREATE TRIGGER trigger_clean_expired_qr_codes
AFTER INSERT OR UPDATE ON qr_issues
EXECUTE FUNCTION clean_expired_qr_codes();
