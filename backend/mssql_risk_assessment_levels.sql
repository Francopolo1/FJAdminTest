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
