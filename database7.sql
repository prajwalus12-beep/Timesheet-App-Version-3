-- ==========================================
-- Timesheet Application — Database Migration 7
-- Project Updates Notes Field
-- Run this in the Supabase SQL Editor
-- ==========================================

-- Add notes column to project_reports table
ALTER TABLE project_reports
ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT NULL;

-- Add notes_updated flag column (used to track manual edits in the UI)
ALTER TABLE project_reports
ADD COLUMN IF NOT EXISTS notes_updated BOOLEAN DEFAULT FALSE;
