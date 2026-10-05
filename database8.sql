-- ==========================================
-- Timesheet Application — Database Migration 8
-- Add Project Feature
-- Run this in the Supabase SQL Editor
-- ==========================================

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: add_project
-- Independent table for tracking new projects to be added to FMP.
-- Mirrors column naming from project_reports for consistency.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS add_project (
    -- Primary Key
    id                          BIGSERIAL PRIMARY KEY,

    -- ── Project Core Fields ──────────────────────────────────────────────────
    project_code                VARCHAR(50),
    project_name                VARCHAR(255) NOT NULL,
    priority                    VARCHAR(50),
    status                      VARCHAR(50) DEFAULT 'Not started',
    lead_engineer               VARCHAR(255),
    phase                       VARCHAR(100),

    -- ── Links ────────────────────────────────────────────────────────────────
    trello_link                 TEXT,
    prototype_link              TEXT,
    slack_link                  TEXT,

    -- ── Estimates ────────────────────────────────────────────────────────────
    estimated_days              INTEGER,
    actual_days                 DOUBLE PRECISION,

    -- ── Dates ────────────────────────────────────────────────────────────────
    start_date                  DATE,
    end_date                    DATE,

    -- ── Checkboxes (NULL=checked, 1=unchecked — same as project_reports) ─────
    checkbox_bc                 SMALLINT CHECK (checkbox_bc IS NULL OR checkbox_bc = 1),
    checkbox_trello             SMALLINT CHECK (checkbox_trello IS NULL OR checkbox_trello = 1),
    checkbox_wa                 SMALLINT CHECK (checkbox_wa IS NULL OR checkbox_wa = 1),
    checkbox_ws                 SMALLINT CHECK (checkbox_ws IS NULL OR checkbox_ws = 1),

    -- ── Notes ────────────────────────────────────────────────────────────────
    notes                       TEXT,

    -- ── Audit: Created ───────────────────────────────────────────────────────
    created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by_id               VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL,
    created_by_name             VARCHAR(255),

    -- ── Audit: Last Updated ──────────────────────────────────────────────────
    updated_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by_id               VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL,
    updated_by_name             VARCHAR(255),

    -- ── FMP Import Tracking ──────────────────────────────────────────────────
    fmp_added                   BOOLEAN NOT NULL DEFAULT FALSE,
    fmp_added_at                TIMESTAMP WITH TIME ZONE,
    fmp_added_by_id             VARCHAR(50) REFERENCES employee(employee_id) ON DELETE SET NULL,
    fmp_added_by_name           VARCHAR(255)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- AUTO-UPDATE updated_at TRIGGER
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_add_project_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_add_project_updated_at ON add_project;
CREATE TRIGGER trigger_add_project_updated_at
BEFORE UPDATE ON add_project
FOR EACH ROW
EXECUTE FUNCTION update_add_project_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_add_project_created_at
    ON add_project (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_add_project_fmp_added
    ON add_project (fmp_added);

CREATE INDEX IF NOT EXISTS idx_add_project_project_code
    ON add_project (project_code)
    WHERE project_code IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_add_project_lead_engineer
    ON add_project (lead_engineer)
    WHERE lead_engineer IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_add_project_status
    ON add_project (status);
