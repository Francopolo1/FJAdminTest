-- Add next_visit_date and visit_month_seed columns to program_facilities
-- Run this directly in the Railway PostgreSQL database

ALTER TABLE program_facilities
    ADD COLUMN IF NOT EXISTS next_visit_date timestamp NULL,
    ADD COLUMN IF NOT EXISTS visit_month_seed smallint NULL,
    ADD COLUMN IF NOT EXISTS season_start varchar(5) NULL,
    ADD COLUMN IF NOT EXISTS season_end varchar(5) NULL;
