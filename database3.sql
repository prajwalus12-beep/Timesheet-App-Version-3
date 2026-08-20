-- ==========================================
-- Timesheet Reminder Feature — Database Migration
-- Run this in the Supabase SQL Editor
-- ==========================================

-- 1. Application Settings Table (key-value store)
CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Auto-update updated_at on changes
CREATE OR REPLACE FUNCTION update_app_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_app_settings_updated_at ON app_settings;
CREATE TRIGGER trigger_app_settings_updated_at
BEFORE UPDATE ON app_settings
FOR EACH ROW
EXECUTE FUNCTION update_app_settings_updated_at();

-- Default settings
INSERT INTO app_settings (key, value) VALUES ('timesheet_reminder_enabled', 'false')
ON CONFLICT (key) DO NOTHING;

INSERT INTO app_settings (key, value) VALUES ('timesheet_reminder_time', '10:00')
ON CONFLICT (key) DO NOTHING;


-- 2. Timesheet Reminder Logs Table
CREATE TABLE IF NOT EXISTS timesheet_reminder_logs (
    id BIGSERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    employee_email VARCHAR(255) NOT NULL,
    week_start_date DATE NOT NULL,
    reminder_type VARCHAR(20) NOT NULL CHECK (reminder_type IN ('cron', 'manual')),
    missing_days JSONB,
    status SMALLINT NOT NULL DEFAULT 0 CHECK (status IN (1, 0, -1)),
    error_message TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast duplicate checks (employee + week)
CREATE INDEX IF NOT EXISTS idx_ts_reminder_logs_emp_week
ON timesheet_reminder_logs(employee_id, week_start_date);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_ts_reminder_logs_status
ON timesheet_reminder_logs(status);
