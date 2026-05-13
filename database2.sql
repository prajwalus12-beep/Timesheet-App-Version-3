


-- 6. Project Reports Table (with change tracking)
CREATE TABLE project_reports (
    id                     SERIAL PRIMARY KEY,

    -- Project Code
    project_code           VARCHAR(50) NOT NULL,
    project_code_updated   BOOLEAN NOT NULL DEFAULT FALSE,

    -- Project Name
    project_name           VARCHAR(255) NOT NULL,
    project_name_updated   BOOLEAN NOT NULL DEFAULT FALSE,

    -- Lead Engineer
    lead_engineer          VARCHAR(255) NOT NULL,
    lead_engineer_updated  BOOLEAN NOT NULL DEFAULT FALSE,

    -- Priority
    priority               VARCHAR(50) NOT NULL,
    priority_updated       BOOLEAN NOT NULL DEFAULT FALSE,

    -- Start Date
    start_date             DATE,
    start_date_updated     BOOLEAN NOT NULL DEFAULT FALSE,

    -- End Date
    end_date               DATE,
    end_date_updated       BOOLEAN NOT NULL DEFAULT FALSE,

    -- Status
    status                 VARCHAR(50) NOT NULL,
    status_updated         BOOLEAN NOT NULL DEFAULT FALSE,

    -- Phase
    phase                  VARCHAR(100) NOT NULL,
    phase_updated          BOOLEAN NOT NULL DEFAULT FALSE,

    -- Trello
    trello_link            TEXT,
    trello_link_updated    BOOLEAN NOT NULL DEFAULT FALSE,

    -- Prototype
    prototype_link         TEXT,
    prototype_link_updated BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);


-- ==========================================
-- STEP 3: AUTO-UPDATE TIMESTAMP TRIGGER
-- ==========================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_project_reports_updated_at
BEFORE UPDATE ON project_reports
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();


CREATE INDEX idx_project_reports_code      ON project_reports(project_code);

ALTER TABLE project_reports
ADD COLUMN slack_link TEXT,
ADD COLUMN slack_link_updated BOOLEAN NOT NULL DEFAULT FALSE;

-- ==========================================
-- ADD NEW CHECKBOX COLUMNS + ESTIMATED DAYS
-- ==========================================

ALTER TABLE project_reports
ADD COLUMN checkbox_bc SMALLINT,
ADD COLUMN checkbox_bc_updated BOOLEAN NOT NULL DEFAULT FALSE,

ADD COLUMN checkbox_trello SMALLINT,
ADD COLUMN checkbox_trello_updated BOOLEAN NOT NULL DEFAULT FALSE,

ADD COLUMN checkbox_wa SMALLINT,
ADD COLUMN checkbox_wa_updated BOOLEAN NOT NULL DEFAULT FALSE,

ADD COLUMN checkbox_ws SMALLINT,
ADD COLUMN checkbox_ws_updated BOOLEAN NOT NULL DEFAULT FALSE,

ADD COLUMN estimated_days INTEGER,
ADD COLUMN estimated_days_updated BOOLEAN NOT NULL DEFAULT FALSE;


-- ==========================================
-- OPTIONAL CHECK CONSTRAINTS
-- only allow NULL or 1
-- 1 = Unchecked
-- NULL = Checked / No Value
-- ==========================================

ALTER TABLE project_reports
ADD CONSTRAINT chk_checkbox_bc
CHECK (checkbox_bc IS NULL OR checkbox_bc = 1);

ALTER TABLE project_reports
ADD CONSTRAINT chk_checkbox_trello
CHECK (checkbox_trello IS NULL OR checkbox_trello = 1);

ALTER TABLE project_reports
ADD CONSTRAINT chk_checkbox_wa
CHECK (checkbox_wa IS NULL OR checkbox_wa = 1);

ALTER TABLE project_reports
ADD CONSTRAINT chk_checkbox_ws
CHECK (checkbox_ws IS NULL OR checkbox_ws = 1);