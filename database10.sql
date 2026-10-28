-- Database Migration: Weekly Report Email Settings
-- Date: 2026-10-27
-- Description: Add configuration for automated weekly timesheet report emails

-- Add new app_settings entries for report email configuration
INSERT INTO app_settings (key, value) VALUES ('report_email_enabled', 'false')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('report_email_recipients', '[]')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('report_email_day', 'fri')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('report_email_time', '17:00')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('report_email_timezone', 'UTC')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('report_email_last_sent', '')
ON CONFLICT (key) DO NOTHING;

-- Create table for report email delivery history
CREATE TABLE IF NOT EXISTS report_email_history (
    id SERIAL PRIMARY KEY,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recipient_emails TEXT NOT NULL,
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,
    status INTEGER NOT NULL DEFAULT 0,  -- 0=pending, 1=sent, -1=failed
    error_message TEXT,
    trigger_type VARCHAR(20) NOT NULL DEFAULT 'manual',  -- 'manual' or 'scheduled'
    sent_by VARCHAR(100),  -- employee_id or 'system' for scheduled
    email_subject TEXT,
    total_employees INTEGER,
    total_entries INTEGER,
    total_projects INTEGER,
    total_days DECIMAL(10,2)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_report_email_history_sent_at ON report_email_history(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_email_history_status ON report_email_history(status);

COMMENT ON TABLE report_email_history IS 'Tracks weekly timesheet report email delivery history';
COMMENT ON COLUMN report_email_history.status IS '0=pending, 1=sent, -1=failed';
COMMENT ON COLUMN report_email_history.trigger_type IS 'manual=user clicked button, scheduled=cron job';
