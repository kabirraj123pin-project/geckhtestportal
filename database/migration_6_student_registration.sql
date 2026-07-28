-- ============================================
-- Migration: Student Registration Number + Academic Details
-- File: database/migration_6_student_registration.sql
--
-- Run this on your EXISTING database.
-- Adds registration number (used as the student login ID), plus
-- personal and academic details captured at registration.
--
-- NOTE: if you see "Duplicate column" or "Duplicate key" errors,
-- it just means that particular change was already applied — safe to ignore.
-- ============================================

USE college_exam_portal;

ALTER TABLE users
    ADD COLUMN registration_number VARCHAR(50) NULL,
    ADD COLUMN date_of_birth DATE NULL,
    ADD COLUMN gender ENUM('male', 'female', 'other') NULL,
    ADD COLUMN address TEXT NULL,
    ADD COLUMN department_id INT NULL,
    ADD COLUMN semester INT NULL;

ALTER TABLE users
    ADD UNIQUE KEY unique_registration_number (registration_number);

ALTER TABLE users
    ADD CONSTRAINT fk_user_department FOREIGN KEY (department_id)
        REFERENCES departments(id) ON DELETE SET NULL;
