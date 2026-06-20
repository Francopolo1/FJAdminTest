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

-- ── FK: program_facilities.risk_assessment → risk_assessment_levels ───────────
-- Composite FK on (risk_assessment, program_facility_type_id) so each facility's
-- risk code is validated against the levels defined for its specific program type.
-- Added WITH NOCHECK so existing rows (which may predate risk_assessment_levels
-- data) are not validated; new inserts/updates are enforced going forward.
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'fk_pf_risk_assessment' AND parent_object_id = OBJECT_ID('program_facilities')
)
BEGIN
    ALTER TABLE program_facilities
    WITH NOCHECK
    ADD CONSTRAINT fk_pf_risk_assessment
        FOREIGN KEY (risk_assessment, program_facility_type_id)
        REFERENCES risk_assessment_levels (code, program_facility_type_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

    PRINT 'Added FK fk_pf_risk_assessment on program_facilities';
END
ELSE
    PRINT 'fk_pf_risk_assessment already exists — skipped';
GO
