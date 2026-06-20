-- ============================================================
-- risk_assessment_levels table for local MSSQL (FJADMINDBMODEL)
-- Run in SSMS against FJADMINDBMODEL.
-- Idempotent: guarded by IF NOT EXISTS.
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'risk_assessment_levels')
BEGIN
    CREATE TABLE risk_assessment_levels (
        id                        INT              NOT NULL IDENTITY(1,1) PRIMARY KEY,
        code                      NVARCHAR(5)      NOT NULL,
        label                     NVARCHAR(50)     NOT NULL,
        visit_frequency_days      INT              NOT NULL
            CHECK (visit_frequency_days > 0),
        description               NVARCHAR(MAX)    NULL,
        program_facility_type_id  NVARCHAR(36)     NOT NULL
            REFERENCES program_facility_types(program_facility_type_id)
            ON DELETE CASCADE,

        CONSTRAINT uq_risk_code_per_pft
            UNIQUE (code, program_facility_type_id)
    );

    PRINT 'Created risk_assessment_levels';
END
ELSE
    PRINT 'risk_assessment_levels already exists — skipped';
GO

-- ── Drop old composite FK if it was added previously ─────────────────────────
IF EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'fk_pf_risk_assessment' AND parent_object_id = OBJECT_ID('program_facilities')
)
BEGIN
    ALTER TABLE program_facilities DROP CONSTRAINT fk_pf_risk_assessment;
    PRINT 'Dropped old composite FK fk_pf_risk_assessment';
END
GO

-- ── Drop old risk_assessment VARCHAR column if it exists ──────────────────────
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('program_facilities') AND name = 'risk_assessment'
)
BEGIN
    ALTER TABLE program_facilities DROP COLUMN risk_assessment;
    PRINT 'Dropped old risk_assessment column';
END
GO

-- ── Add risk_assessment_levels_id INT FK column ───────────────────────────────
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('program_facilities') AND name = 'risk_assessment_levels_id'
)
BEGIN
    ALTER TABLE program_facilities
    ADD risk_assessment_levels_id INT NULL
        REFERENCES risk_assessment_levels(id)
        ON DELETE SET NULL;

    PRINT 'Added risk_assessment_levels_id FK column on program_facilities';
END
ELSE
    PRINT 'risk_assessment_levels_id already exists — skipped';
GO
