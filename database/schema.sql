-- ============================================
-- College Exam Portal - Database Schema
-- File: database/schema.sql
-- ============================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS college_exam_portal;
USE college_exam_portal;

-- ============================================
-- Table: users
-- (Admin, Teacher, and Student logins are all handled by this table)
-- The "role" column determines what type of user this is
-- ============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    phone VARCHAR(15),
    registration_number VARCHAR(50) NULL,   -- students log in with this instead of email
    date_of_birth DATE NULL,
    gender ENUM('male', 'female', 'other') NULL,
    address TEXT NULL,
    department_id INT NULL,
    semester INT NULL,
    profile_photo VARCHAR(255) DEFAULT NULL,
    profile_photo_data LONGBLOB NULL,       -- actual image bytes (persists across restarts)
    profile_photo_mimetype VARCHAR(50) NULL,
    is_active TINYINT(1) DEFAULT 1,       -- must be approved by admin to become active
    reset_otp VARCHAR(6) NULL,            -- one-time password for "Forgot Password"
    reset_otp_expires DATETIME NULL,      -- when that OTP stops being valid
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_registration_number (registration_number)
);

-- ============================================
-- Table: departments
-- ============================================
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Now that departments exists, link a student's department_id to it
ALTER TABLE users
    ADD CONSTRAINT fk_user_department FOREIGN KEY (department_id)
        REFERENCES departments(id) ON DELETE SET NULL;

-- ============================================
-- Table: subjects
-- ============================================
CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    department_id INT,
    teacher_id INT,                        -- which teacher this subject is assigned to
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================
-- Table: tests
-- ============================================
CREATE TABLE tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    subject_id INT,
    teacher_id INT,
    duration_minutes INT DEFAULT 30,
    total_marks INT DEFAULT 0,
    negative_marking DECIMAL(3,2) DEFAULT 0.00,
    status ENUM('draft', 'published', 'completed', 'cancelled') DEFAULT 'draft',
    start_time DATETIME,
    end_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Table: questions
-- ============================================
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'numerical') DEFAULT 'single_choice',
    marks INT DEFAULT 1,
    image_path VARCHAR(255) DEFAULT NULL,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

-- ============================================
-- Table: options
-- (Stores MCQ answer options)
-- ============================================
CREATE TABLE options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text VARCHAR(500) NOT NULL,
    is_correct TINYINT(1) DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- ============================================
-- Table: student_answers
-- ============================================
CREATE TABLE student_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    test_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option_id INT,
    answer_text TEXT,                       -- used for fill-in-blank / numerical answers,
                                             -- and for comma-separated option IDs on multiple_choice questions
    marked_for_review TINYINT(1) DEFAULT 0,
    is_correct TINYINT(1) DEFAULT NULL,
    UNIQUE KEY unique_student_question (student_id, test_id, question_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- ============================================
-- Table: test_attempts
-- Tracks when a student started a test (needed to Resume Test and
-- to calculate remaining time correctly)
-- ============================================
CREATE TABLE test_attempts (
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
-- Table: results
-- ============================================
CREATE TABLE results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    test_id INT NOT NULL,
    score DECIMAL(6,2) DEFAULT 0,
    total_marks INT DEFAULT 0,
    percentage DECIMAL(5,2) DEFAULT 0,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_result (student_id, test_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
);

-- ============================================
-- Table: notifications
-- ============================================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- Table: college_settings
-- Single-row table holding the college name and logo shown site-wide
-- ============================================
CREATE TABLE college_settings (
    id INT PRIMARY KEY DEFAULT 1,
    college_name VARCHAR(200) DEFAULT 'College Exam Portal',
    logo_path VARCHAR(255) DEFAULT NULL,
    logo_data LONGBLOB NULL,               -- actual image bytes (persists across restarts)
    logo_mimetype VARCHAR(50) NULL
);

INSERT INTO college_settings (id, college_name) VALUES (1, 'College Exam Portal');
