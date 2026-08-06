-- ============================================
-- Migration: Store Images in Database (not disk)
-- File: database/migration_7_images_in_db.sql
--
-- Run this on your EXISTING database.
--
-- Why: hosts like Render wipe the local disk on every restart/redeploy,
-- so uploaded files (college logo, profile photos) were disappearing.
-- Storing the image bytes directly in MySQL fixes this permanently,
-- since the database persists.
-- ============================================

USE college_exam_portal;

ALTER TABLE college_settings
    ADD COLUMN logo_data LONGBLOB NULL,
    ADD COLUMN logo_mimetype VARCHAR(50) NULL;

ALTER TABLE users
    ADD COLUMN profile_photo_data LONGBLOB NULL,
    ADD COLUMN profile_photo_mimetype VARCHAR(50) NULL;
