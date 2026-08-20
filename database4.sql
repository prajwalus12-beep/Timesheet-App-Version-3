-- ==========================================
-- Timesheet Application — Database Migration 4
-- Employee Status feature
-- Run this in the Supabase SQL Editor
-- ==========================================

-- 1. Add status column to employee table
ALTER TABLE employee 
ADD COLUMN IF NOT EXISTS status SMALLINT NOT NULL DEFAULT 1;

-- 2. Ensure existing employees are marked as Active
UPDATE employee 
SET status = 1 
WHERE status IS NULL;
