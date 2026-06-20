-- ============================================================
-- activity_flags lookup table for local MSSQL (FJADMINDBMODEL)
-- Run in SSMS against FJADMINDBMODEL.
-- Idempotent: all statements guarded by IF NOT EXISTS / IF NOT EXISTS row.
-- ============================================================

-- ── Create table ─────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'activity_flags')
BEGIN
    CREATE TABLE activity_flags (
        code        NVARCHAR(1)   NOT NULL PRIMARY KEY,
        label       NVARCHAR(50)  NOT NULL,
        description NVARCHAR(MAX) NULL
    );

    PRINT 'Created activity_flags';
END
ELSE
    PRINT 'activity_flags already exists — skipped';
GO

-- ── Seed values ──────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM activity_flags WHERE code = 'A')
    INSERT INTO activity_flags (code, label, description)
    VALUES ('A', 'Active', 'Facility is currently active and subject to visits.');

IF NOT EXISTS (SELECT 1 FROM activity_flags WHERE code = 'I')
    INSERT INTO activity_flags (code, label, description)
    VALUES ('I', 'Inactive', 'Facility is temporarily inactive.');

IF NOT EXISTS (SELECT 1 FROM activity_flags WHERE code = 'C')
    INSERT INTO activity_flags (code, label, description)
    VALUES ('C', 'Closed', 'Facility is permanently closed.');
GO

-- ── FK: program_facilities.activity_flag → activity_flags.code ───────────────
-- WITH NOCHECK skips existing row validation; new inserts/updates are enforced.
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'fk_pf_activity_flag'
      AND parent_object_id = OBJECT_ID('program_facilities')
)
BEGIN
    ALTER TABLE program_facilities
    WITH NOCHECK
    ADD CONSTRAINT fk_pf_activity_flag
        FOREIGN KEY (activity_flag)
        REFERENCES activity_flags (code)
        ON UPDATE CASCADE
        ON DELETE SET NULL;

    PRINT 'Added FK fk_pf_activity_flag on program_facilities';
END
ELSE
    PRINT 'fk_pf_activity_flag already exists — skipped';
GO
