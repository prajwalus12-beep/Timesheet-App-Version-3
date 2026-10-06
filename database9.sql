-- ==========================================
-- Timesheet Application — Database Migration 9
-- Add Project Permissions & Mark as Exported
-- Run this in the Supabase SQL Editor
-- ==========================================

-- 1. Add allow_add_project column to employee table
ALTER TABLE employee 
ADD COLUMN IF NOT EXISTS allow_add_project BOOLEAN DEFAULT FALSE;

-- 2. Add is_exported column to add_project table
ALTER TABLE add_project 
ADD COLUMN IF NOT EXISTS is_exported BOOLEAN DEFAULT FALSE;

-- 3. Sync existing fmp_added records to is_exported
UPDATE add_project 
SET is_exported = TRUE 
WHERE fmp_added = TRUE;

-- 4. Create index for fast export status filtering
CREATE INDEX IF NOT EXISTS idx_add_project_is_exported 
ON add_project (is_exported);
