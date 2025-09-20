-- Migration: Enhanced moderation system
-- Description: Create comprehensive moderation tables and indexes
-- Date: 2025-01-27

-- Create moderation_logs table if not exists
CREATE TABLE IF NOT EXISTS moderation_logs (
    id SERIAL PRIMARY KEY,
    moderator_id INTEGER NOT NULL REFERENCES partners_v2(id) ON DELETE CASCADE,
    card_id INTEGER NOT NULL REFERENCES cards_v2(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'approve', 'reject', 'feature', 'archive', 'edit'
    comment TEXT,
    reason_code VARCHAR(50), -- 'incomplete', 'inappropriate', 'bad_photo', 'wrong_category', 'custom'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create moderation_queue table for better queue management
CREATE TABLE IF NOT EXISTS moderation_queue (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards_v2(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0, -- Higher number = higher priority
    assigned_to INTEGER REFERENCES partners_v2(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_review', 'completed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    UNIQUE(card_id)
);

-- Create moderation_rules table for automated moderation
CREATE TABLE IF NOT EXISTS moderation_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL UNIQUE,
    rule_type VARCHAR(50) NOT NULL, -- 'auto_approve', 'auto_reject', 'flag_for_review'
    conditions JSONB NOT NULL, -- JSON conditions for rule matching
    action VARCHAR(50) NOT NULL, -- Action to take when rule matches
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create moderation_statistics table for analytics
CREATE TABLE IF NOT EXISTS moderation_statistics (
    id SERIAL PRIMARY KEY,
    moderator_id INTEGER REFERENCES partners_v2(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    cards_reviewed INTEGER DEFAULT 0,
    cards_approved INTEGER DEFAULT 0,
    cards_rejected INTEGER DEFAULT 0,
    cards_featured INTEGER DEFAULT 0,
    avg_review_time_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(moderator_id, date)
);

-- Add moderation-related columns to cards_v2 if not exist
DO $$ 
BEGIN
    -- Add is_featured column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'cards_v2' AND column_name = 'is_featured') THEN
        ALTER TABLE cards_v2 ADD COLUMN is_featured BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- Add priority_level column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'cards_v2' AND column_name = 'priority_level') THEN
        ALTER TABLE cards_v2 ADD COLUMN priority_level INTEGER DEFAULT 0;
    END IF;
    
    -- Add moderation_notes column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'cards_v2' AND column_name = 'moderation_notes') THEN
        ALTER TABLE cards_v2 ADD COLUMN moderation_notes TEXT;
    END IF;
    
    -- Add auto_moderation_status column if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'cards_v2' AND column_name = 'auto_moderation_status') THEN
        ALTER TABLE cards_v2 ADD COLUMN auto_moderation_status VARCHAR(20) DEFAULT 'pending';
    END IF;
END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_moderation_logs_moderator_id ON moderation_logs(moderator_id);
CREATE INDEX IF NOT EXISTS idx_moderation_logs_card_id ON moderation_logs(card_id);
CREATE INDEX IF NOT EXISTS idx_moderation_logs_action ON moderation_logs(action);
CREATE INDEX IF NOT EXISTS idx_moderation_logs_created_at ON moderation_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_moderation_queue_card_id ON moderation_queue(card_id);
CREATE INDEX IF NOT EXISTS idx_moderation_queue_assigned_to ON moderation_queue(assigned_to);
CREATE INDEX IF NOT EXISTS idx_moderation_queue_status ON moderation_queue(status);
CREATE INDEX IF NOT EXISTS idx_moderation_queue_priority ON moderation_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_moderation_queue_created_at ON moderation_queue(created_at);

CREATE INDEX IF NOT EXISTS idx_moderation_rules_rule_type ON moderation_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_moderation_rules_is_active ON moderation_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_moderation_statistics_moderator_id ON moderation_statistics(moderator_id);
CREATE INDEX IF NOT EXISTS idx_moderation_statistics_date ON moderation_statistics(date);

-- Add indexes for cards_v2 moderation columns
CREATE INDEX IF NOT EXISTS idx_cards_v2_is_featured ON cards_v2(is_featured);
CREATE INDEX IF NOT EXISTS idx_cards_v2_priority_level ON cards_v2(priority_level DESC);
CREATE INDEX IF NOT EXISTS idx_cards_v2_auto_moderation_status ON cards_v2(auto_moderation_status);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cards_v2_status_featured ON cards_v2(status, is_featured);
CREATE INDEX IF NOT EXISTS idx_cards_v2_status_priority ON cards_v2(status, priority_level DESC);
CREATE INDEX IF NOT EXISTS idx_moderation_queue_status_priority ON moderation_queue(status, priority DESC);

-- Insert default moderation rules
INSERT INTO moderation_rules (rule_name, rule_type, conditions, action, is_active) VALUES
('Auto Approve Verified Partners', 'auto_approve', 
 '{"partner_verified": true, "has_photo": true, "description_length": {"min": 50}}', 
 'approve', true),
('Flag Incomplete Cards', 'flag_for_review', 
 '{"has_photo": false, "description_length": {"max": 20}}', 
 'flag', true),
('Auto Reject Spam', 'auto_reject', 
 '{"title_contains": ["spam", "реклама", "купить"], "description_length": {"max": 10}}', 
 'reject', true),
('Flag Suspicious Content', 'flag_for_review', 
 '{"title_contains": ["бесплатно", "халява"], "partner_verified": false}', 
 'flag', true)
ON CONFLICT (rule_name) DO NOTHING;

-- Create function to update moderation statistics
CREATE OR REPLACE FUNCTION update_moderation_stats(
    p_moderator_id INTEGER,
    p_action VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO moderation_statistics (moderator_id, date, cards_reviewed, cards_approved, cards_rejected, cards_featured)
    VALUES (
        p_moderator_id, 
        CURRENT_DATE, 
        1, 
        CASE WHEN p_action = 'approve' THEN 1 ELSE 0 END,
        CASE WHEN p_action = 'reject' THEN 1 ELSE 0 END,
        CASE WHEN p_action = 'feature' THEN 1 ELSE 0 END
    )
    ON CONFLICT (moderator_id, date) 
    DO UPDATE SET
        cards_reviewed = moderation_statistics.cards_reviewed + 1,
        cards_approved = moderation_statistics.cards_approved + CASE WHEN p_action = 'approve' THEN 1 ELSE 0 END,
        cards_rejected = moderation_statistics.cards_rejected + CASE WHEN p_action = 'reject' THEN 1 ELSE 0 END,
        cards_featured = moderation_statistics.cards_featured + CASE WHEN p_action = 'feature' THEN 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create function to auto-assign moderation queue
CREATE OR REPLACE FUNCTION auto_assign_moderation_queue() RETURNS VOID AS $$
DECLARE
    unassigned_count INTEGER;
    moderator_count INTEGER;
    cards_per_moderator INTEGER;
BEGIN
    -- Get count of unassigned cards
    SELECT COUNT(*) INTO unassigned_count 
    FROM moderation_queue 
    WHERE assigned_to IS NULL AND status = 'pending';
    
    -- Get count of active moderators
    SELECT COUNT(*) INTO moderator_count 
    FROM partners_v2 
    WHERE is_moderator = TRUE AND is_active = TRUE;
    
    -- If we have moderators and unassigned cards
    IF moderator_count > 0 AND unassigned_count > 0 THEN
        cards_per_moderator := unassigned_count / moderator_count;
        
        -- Assign cards to moderators
        UPDATE moderation_queue 
        SET assigned_to = (
            SELECT p.id 
            FROM partners_v2 p 
            WHERE p.is_moderator = TRUE 
            AND p.is_active = TRUE 
            ORDER BY RANDOM() 
            LIMIT 1
        )
        WHERE assigned_to IS NULL 
        AND status = 'pending'
        AND id IN (
            SELECT mq.id 
            FROM moderation_queue mq 
            ORDER BY mq.priority DESC, mq.created_at ASC 
            LIMIT cards_per_moderator
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically add new cards to moderation queue
CREATE OR REPLACE FUNCTION add_to_moderation_queue() RETURNS TRIGGER AS $$
BEGIN
    -- Only add to queue if status is pending and not already in queue
    IF NEW.status = 'pending' AND NOT EXISTS (
        SELECT 1 FROM moderation_queue WHERE card_id = NEW.id
    ) THEN
        INSERT INTO moderation_queue (card_id, priority, status)
        VALUES (NEW.id, 0, 'pending');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for cards_v2
DROP TRIGGER IF EXISTS trigger_add_to_moderation_queue ON cards_v2;
CREATE TRIGGER trigger_add_to_moderation_queue
    AFTER INSERT OR UPDATE ON cards_v2
    FOR EACH ROW
    EXECUTE FUNCTION add_to_moderation_queue();

-- Add comments to tables
COMMENT ON TABLE moderation_logs IS 'Log of all moderation actions taken by moderators';
COMMENT ON TABLE moderation_queue IS 'Queue management for cards awaiting moderation';
COMMENT ON TABLE moderation_rules IS 'Automated moderation rules and conditions';
COMMENT ON TABLE moderation_statistics IS 'Daily statistics for moderators performance';

COMMENT ON COLUMN moderation_logs.action IS 'Type of moderation action: approve, reject, feature, archive, edit';
COMMENT ON COLUMN moderation_logs.reason_code IS 'Standardized reason code for rejections';
COMMENT ON COLUMN moderation_queue.priority IS 'Higher number = higher priority for review';
COMMENT ON COLUMN moderation_queue.assigned_to IS 'Moderator assigned to review this card';
COMMENT ON COLUMN moderation_rules.conditions IS 'JSON conditions for rule matching';
COMMENT ON COLUMN moderation_statistics.avg_review_time_seconds IS 'Average time spent reviewing cards';
