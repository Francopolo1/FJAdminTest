-- ============================================================
-- Enforcement app tables for local MSSQL (FJADMINDBMODEL)
-- Run in SSMS against FJADMINDBMODEL.
-- All statements are idempotent (IF NOT EXISTS guards).
-- ============================================================

-- ── enforcement_fine_cases ────────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_cases')
BEGIN
    CREATE TABLE enforcement_fine_cases (
        fine_case_id         UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        case_number          NVARCHAR(40)      NOT NULL UNIQUE,
        status               NVARCHAR(20)      NOT NULL,
        opened_date          DATE              NOT NULL,
        closed_date          DATE              NULL,
        notes                NVARCHAR(MAX)     NULL,
        created_at           DATETIME2         NOT NULL,
        updated_at           DATETIME2         NOT NULL,
        created_by_id        INT               NULL
            REFERENCES auth_user(id),
        program_facility_id  NVARCHAR(36)      NOT NULL
            REFERENCES program_facilities(program_facility_id)
    );
    PRINT 'Created enforcement_fine_cases';
END
ELSE
    PRINT 'enforcement_fine_cases already exists — skipped';
GO

-- ── enforcement_fine_invoices ─────────────────────────────────────────────────
-- (created before fine_assessments because assessments FK to invoices)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_invoices')
BEGIN
    CREATE TABLE enforcement_fine_invoices (
        fine_invoice_id  UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        invoice_number   NVARCHAR(40)      NOT NULL UNIQUE,
        invoice_date     DATE              NOT NULL,
        due_date         DATE              NOT NULL,
        total_amount     DECIMAL(12,2)     NOT NULL,
        paid_amount      DECIMAL(12,2)     NOT NULL,
        waived_amount    DECIMAL(12,2)     NOT NULL,
        status           NVARCHAR(20)      NOT NULL,
        notes            NVARCHAR(MAX)     NULL,
        created_at       DATETIME2         NOT NULL,
        updated_at       DATETIME2         NOT NULL,
        case_id          UNIQUEIDENTIFIER  NOT NULL
            REFERENCES enforcement_fine_cases(fine_case_id)
    );
    PRINT 'Created enforcement_fine_invoices';
END
ELSE
    PRINT 'enforcement_fine_invoices already exists — skipped';
GO

-- ── enforcement_fine_assessments ──────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_assessments')
BEGIN
    CREATE TABLE enforcement_fine_assessments (
        fine_assessment_id  UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        assessed_amount     DECIMAL(12,2)     NOT NULL,
        waived_amount       DECIMAL(12,2)     NOT NULL,
        status              NVARCHAR(20)      NOT NULL,
        notes               NVARCHAR(MAX)     NULL,
        assessed_at         DATETIME2         NULL,
        created_at          DATETIME2         NOT NULL,
        updated_at          DATETIME2         NOT NULL,
        assessed_by_id      INT               NULL
            REFERENCES auth_user(id),
        fine_tier_id        UNIQUEIDENTIFIER  NULL
            REFERENCES fine_tiers(fine_tier_id),
        violation_id        UNIQUEIDENTIFIER  NOT NULL
            REFERENCES compliance_violations(compliance_violation_id),
        case_id             UNIQUEIDENTIFIER  NOT NULL
            REFERENCES enforcement_fine_cases(fine_case_id),
        invoice_id          UNIQUEIDENTIFIER  NULL
            REFERENCES enforcement_fine_invoices(fine_invoice_id)
    );
    PRINT 'Created enforcement_fine_assessments';
END
ELSE
    PRINT 'enforcement_fine_assessments already exists — skipped';
GO

-- ── enforcement_payment_plans ─────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_payment_plans')
BEGIN
    CREATE TABLE enforcement_payment_plans (
        payment_plan_id         UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        plan_date               DATE              NOT NULL,
        total_amount            DECIMAL(12,2)     NOT NULL,
        number_of_installments  INT               NOT NULL,
        installment_amount      DECIMAL(12,2)     NOT NULL,
        frequency               NVARCHAR(20)      NOT NULL,
        first_due_date          DATE              NOT NULL,
        approved_date           DATE              NULL,
        status                  NVARCHAR(20)      NOT NULL,
        notes                   NVARCHAR(MAX)     NULL,
        created_at              DATETIME2         NOT NULL,
        updated_at              DATETIME2         NOT NULL,
        approved_by_id          INT               NULL
            REFERENCES auth_user(id),
        invoice_id              UNIQUEIDENTIFIER  NOT NULL UNIQUE
            REFERENCES enforcement_fine_invoices(fine_invoice_id)
    );
    PRINT 'Created enforcement_payment_plans';
END
ELSE
    PRINT 'enforcement_payment_plans already exists — skipped';
GO

-- ── enforcement_payment_plan_installments ─────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_payment_plan_installments')
BEGIN
    CREATE TABLE enforcement_payment_plan_installments (
        installment_id      UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        installment_number  INT               NOT NULL,
        due_date            DATE              NOT NULL,
        amount              DECIMAL(12,2)     NOT NULL,
        status              NVARCHAR(20)      NOT NULL,
        plan_id             UNIQUEIDENTIFIER  NOT NULL
            REFERENCES enforcement_payment_plans(payment_plan_id),
        CONSTRAINT uq_plan_installment UNIQUE (plan_id, installment_number)
    );
    PRINT 'Created enforcement_payment_plan_installments';
END
ELSE
    PRINT 'enforcement_payment_plan_installments already exists — skipped';
GO

-- ── enforcement_fine_payments ─────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_payments')
BEGIN
    CREATE TABLE enforcement_fine_payments (
        payment_id        UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        payment_date      DATE              NOT NULL,
        amount            DECIMAL(12,2)     NOT NULL,
        payment_method    NVARCHAR(20)      NOT NULL,
        reference_number  NVARCHAR(100)     NULL,
        notes             NVARCHAR(MAX)     NULL,
        status            NVARCHAR(20)      NOT NULL,
        created_at        DATETIME2         NOT NULL,
        updated_at        DATETIME2         NOT NULL,
        invoice_id        UNIQUEIDENTIFIER  NOT NULL
            REFERENCES enforcement_fine_invoices(fine_invoice_id),
        received_by_id    INT               NULL
            REFERENCES auth_user(id),
        installment_id    UNIQUEIDENTIFIER  NULL
            REFERENCES enforcement_payment_plan_installments(installment_id)
    );
    PRINT 'Created enforcement_fine_payments';
END
ELSE
    PRINT 'enforcement_fine_payments already exists — skipped';
GO

-- ── enforcement_payment_receipts ──────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_payment_receipts')
BEGIN
    CREATE TABLE enforcement_payment_receipts (
        receipt_id      UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        receipt_number  NVARCHAR(40)      NOT NULL UNIQUE,
        issued_at       DATETIME2         NOT NULL,
        notes           NVARCHAR(MAX)     NULL,
        issued_by_id    INT               NULL
            REFERENCES auth_user(id),
        payment_id      UNIQUEIDENTIFIER  NOT NULL UNIQUE
            REFERENCES enforcement_fine_payments(payment_id)
    );
    PRINT 'Created enforcement_payment_receipts';
END
ELSE
    PRINT 'enforcement_payment_receipts already exists — skipped';
GO

-- ── enforcement_fine_appeals ──────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_appeals')
BEGIN
    CREATE TABLE enforcement_fine_appeals (
        appeal_id         UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        appeal_date       DATE              NOT NULL,
        grounds           NVARCHAR(MAX)     NOT NULL,
        status            NVARCHAR(20)      NOT NULL,
        hearing_date      DATE              NULL,
        decision_notes    NVARCHAR(MAX)     NULL,
        decision_date     DATE              NULL,
        adjusted_amount   DECIMAL(12,2)     NULL,
        created_at        DATETIME2         NOT NULL,
        updated_at        DATETIME2         NOT NULL,
        assessment_id     UNIQUEIDENTIFIER  NOT NULL
            REFERENCES enforcement_fine_assessments(fine_assessment_id),
        filed_by_id       INT               NULL
            REFERENCES auth_user(id),
        decided_by_id     INT               NULL
            REFERENCES auth_user(id)
    );
    PRINT 'Created enforcement_fine_appeals';
END
ELSE
    PRINT 'enforcement_fine_appeals already exists — skipped';
GO

-- ── enforcement_fine_waivers ──────────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'enforcement_fine_waivers')
BEGIN
    CREATE TABLE enforcement_fine_waivers (
        waiver_id          UNIQUEIDENTIFIER  NOT NULL PRIMARY KEY,
        waived_amount      DECIMAL(12,2)     NOT NULL,
        reason             NVARCHAR(MAX)     NOT NULL,
        authorization_date DATE              NOT NULL,
        notes              NVARCHAR(MAX)     NULL,
        created_at         DATETIME2         NOT NULL,
        assessment_id      UNIQUEIDENTIFIER  NULL
            REFERENCES enforcement_fine_assessments(fine_assessment_id),
        invoice_id         UNIQUEIDENTIFIER  NULL
            REFERENCES enforcement_fine_invoices(fine_invoice_id),
        authorized_by_id   INT               NULL
            REFERENCES auth_user(id),
        -- Enforce that exactly one of assessment_id / invoice_id is set
        CONSTRAINT chk_waiver_target CHECK (
            (assessment_id IS NOT NULL AND invoice_id IS NULL)
            OR
            (assessment_id IS NULL AND invoice_id IS NOT NULL)
        )
    );
    PRINT 'Created enforcement_fine_waivers';
END
ELSE
    PRINT 'enforcement_fine_waivers already exists — skipped';
GO

PRINT 'Done.';
