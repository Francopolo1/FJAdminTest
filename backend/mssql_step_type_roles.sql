-- ============================================================
-- workflow_step_type_roles lookup table for local MSSQL (FJADMINDBMODEL)
-- Run in SSMS against FJADMINDBMODEL.
-- Idempotent: guarded by IF NOT EXISTS.
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'workflow_step_type_roles')
BEGIN
    CREATE TABLE workflow_step_type_roles (
        step_type        NVARCHAR(50)  NOT NULL PRIMARY KEY,
        label            NVARCHAR(100) NOT NULL,
        responsible_role NVARCHAR(30)  NULL,
        description      NVARCHAR(MAX) NULL
    );

    PRINT 'Created workflow_step_type_roles';
END
ELSE
    PRINT 'workflow_step_type_roles already exists — skipped';
GO

-- ── Seed values ──────────────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM workflow_step_type_roles WHERE step_type = 'Manual')
    INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
    VALUES ('Manual', 'Manual', 'inspector', 'Inspectors complete manual field steps.');

IF NOT EXISTS (SELECT 1 FROM workflow_step_type_roles WHERE step_type = 'Decision')
    INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
    VALUES ('Decision', 'Decision', 'supervisor', 'Supervisors approve or reject decisions.');

IF NOT EXISTS (SELECT 1 FROM workflow_step_type_roles WHERE step_type = 'ComplianceCheck')
    INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
    VALUES ('ComplianceCheck', 'Compliance Check', NULL,
            'Automated: assesses fines from violations. Auto-advances via the Auto trigger.');

IF NOT EXISTS (SELECT 1 FROM workflow_step_type_roles WHERE step_type = 'Automated')
    INSERT INTO workflow_step_type_roles (step_type, label, responsible_role, description)
    VALUES ('Automated', 'Automated', NULL,
            'Generic automated step. Auto-advances via the Auto trigger.');
GO
