-- ============================================
-- Migration: Student Features
-- File: database/migration_2_student_features.sql
--
-- Run this AFTER your original schema.sql, on your EXISTING database.
-- It adds what's needed for: Resume Test, Mark for Review, Auto-Save,
-- Instant Result, and Rank calculation.
-- ============================================

USE college_exam_portal;

-- ============================================
-- Table: test_attempts
-- Tracks when a student started a test, so we know:
--   1) How much time is left if they refresh/come back (Resume Test)
--   2) Whether they've already submitted (so they can't attempt twice)
-- ============================================
CREATE TABLE IF NOT EXISTS test_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    test_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    status ENUM('in_progress', 'submitted') DEFAULT 'in_progress',
    submitted_at DATETIME NULL,
    UNIQUE KEY unique_attempt (student_id, test_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

-- ============================================
-- student_answers: add "marked for review" flag,
-- and a unique key so we can save-or-update an answer in one query (autosave)
--
-- NOTE: if you see "Duplicate column" or "Duplicate key" errors when running
-- this, it just means that particular change was already applied — safe to
-- ignore and move on to the next statement.
-- ============================================
ALTER TABLE student_answers
    ADD COLUMN marked_for_review TINYINT(1) DEFAULT 0;

ALTER TABLE student_answers
    ADD UNIQUE KEY unique_student_question (student_id, test_id, question_id);

-- ============================================
-- results: only one result per student per test
-- (needed so re-evaluating doesn't create duplicate rows)
-- ============================================
ALTER TABLE results
    ADD UNIQUE KEY unique_result (student_id, test_id);
