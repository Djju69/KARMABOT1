-- Add loyalty points transactions table
CREATE TABLE IF NOT EXISTS loyalty_points_tx (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    rule_code VARCHAR(32) NOT NULL,  -- checkin/geocheckin/etc
    points INTEGER NOT NULL,         -- can be negative
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,                  -- for future use (e.g., order ID)
    CONSTRAINT points_not_zero CHECK (points != 0)
);

-- Index for fast balance calculation
CREATE INDEX IF NOT EXISTS idx_loyalty_points_tx_user_ts 
ON loyalty_points_tx(user_id, created_at);

-- Add comment for the table
COMMENT ON TABLE loyalty_points_tx IS 'Stores loyalty points transactions for all users';

-- Add comments for columns
COMMENT ON COLUMN loyalty_points_tx.rule_code IS 'Activity type that triggered the transaction (e.g., checkin, geocheckin)';
COMMENT ON COLUMN loyalty_points_tx.points IS 'Positive for adding points, negative for spending';
COMMENT ON COLUMN loyalty_points_tx.metadata IS 'Additional transaction context (coordinates, listing ID, etc.)';

-- Add function to get current balance (can be used in views or other functions)
CREATE OR REPLACE FUNCTION get_user_balance(p_user_id BIGINT) 
RETURNS INTEGER AS $$
    SELECT COALESCE(SUM(points), 0)::INTEGER 
    FROM loyalty_points_tx 
    WHERE user_id = p_user_id;
$$ LANGUAGE SQL STABLE;
