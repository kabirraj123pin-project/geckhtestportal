-- ============================================
-- Migration: College Settings + Profile Photos
-- File: database/migration_5_settings_and_photos.sql
--
-- Run this on your EXISTING database.
-- Adds a settings table (college name/logo) — profile_photo already
-- existed on the users table from the very first schema.sql.
-- ============================================

USE college_exam_portal;

CREATE TABLE IF NOT EXISTS college_settings (
    id INT PRIMARY KEY DEFAULT 1,
    college_name VARCHAR(200) DEFAULT 'College Exam Portal',
    logo_path VARCHAR(255) DEFAULT NULL
);

INSERT IGNORE INTO college_settings (id, college_name) VALUES (1, 'College Exam Portal');
