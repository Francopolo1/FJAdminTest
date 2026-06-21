-- ============================================================
-- Add seasonality columns to program_facilities (FJADMINDBMODEL)
-- Season dates stored as 'MM-DD' strings for simplicity
-- If both season_start and season_end are populated, activity_flag
-- auto-adjusts based on current date (A=active in season, I=inactive out of season)
-- Does not override C (closed) status
-- ============================================================

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('program_facilities') AND name = 'season_start')
BEGIN
    ALTER TABLE program_facilities
    ADD season_start NVARCHAR(5) NULL;
    PRINT 'Added season_start column to program_facilities';
END
ELSE
    PRINT 'season_start already exists';

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('program_facilities') AND name = 'season_end')
BEGIN
    ALTER TABLE program_facilities
    ADD season_end NVARCHAR(5) NULL;
    PRINT 'Added season_end column to program_facilities';
END
ELSE
    PRINT 'season_end already exists';

GO

-- ── Example data ──────────────────────────────────────────────────────────────
-- Uncomment to set a facility as seasonal (May 1 - Sept 30)
-- UPDATE program_facilities
-- SET season_start = '05-01', season_end = '09-30'
-- WHERE [description] = 'Example Summer Camp';
-- GO
