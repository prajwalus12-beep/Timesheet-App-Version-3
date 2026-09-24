-- ==========================================
-- Timesheet Application — Database Migration 6
-- Employee Type Management
-- Run this in the Supabase SQL Editor
-- ==========================================

-- Add emp_type column to employee table
ALTER TABLE employee 
ADD COLUMN IF NOT EXISTS emp_type VARCHAR(50) DEFAULT 'Full-Time Employee';
