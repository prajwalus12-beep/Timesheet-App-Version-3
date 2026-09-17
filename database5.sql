-- ==========================================
-- Timesheet Application — Database Migration 5
-- Holiday Management Feature
-- Run this in the Supabase SQL Editor
-- ==========================================

-- 1. Create holidays table
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL,
    updated_by VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL,
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Unique index ensuring only one active holiday per calendar date
CREATE UNIQUE INDEX IF NOT EXISTS uq_holidays_active_date 
ON holidays (holiday_date) 
WHERE deleted_at IS NULL;

-- Performance index for range searches
CREATE INDEX IF NOT EXISTS idx_holidays_date 
ON holidays (holiday_date);

-- Auto-update updated_at on modification
CREATE OR REPLACE FUNCTION update_holidays_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_holidays_updated_at ON holidays;
CREATE TRIGGER trigger_holidays_updated_at
BEFORE UPDATE ON holidays
FOR EACH ROW
EXECUTE FUNCTION update_holidays_timestamp();


-- 2. Create employee_holiday_exclusions table
-- Records employee self-service overrides when an employee works on a holiday
CREATE TABLE IF NOT EXISTS employee_holiday_exclusions (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL REFERENCES employee(employee_id) ON DELETE CASCADE,
    holiday_id INT NOT NULL REFERENCES holidays(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL
);

-- Ensure an employee cannot have duplicate exclusion records for the same holiday
CREATE UNIQUE INDEX IF NOT EXISTS uq_emp_holiday_exclusion 
ON employee_holiday_exclusions (employee_id, holiday_id);

-- Performance index for fast joining/filtering during timesheet queries
CREATE INDEX IF NOT EXISTS idx_exclusions_emp_holiday 
ON employee_holiday_exclusions (employee_id, holiday_id);
