-- ============================================
-- Migration: Forgot Password (OTP)
-- File: database/migration_3_forgot_password.sql
--
-- Run this on your EXISTING database.
-- Adds 2 columns to the users table to support OTP-based password reset.
--
-- NOTE: if you see a "Duplicate column" error, it just means this was
-- already applied — safe to ignore.
-- ============================================

USE college_exam_portal;

ALTER TABLE users
    ADD COLUMN reset_otp VARCHAR(6) NULL,
    ADD COLUMN reset_otp_expires DATETIME NULL;
