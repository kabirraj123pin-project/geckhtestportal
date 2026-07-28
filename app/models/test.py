"""
File: app/models/test.py
All database operations related to Tests.
"""

from app import mysql


class Test:

    @staticmethod
    def create(title, subject_id, teacher_id, duration_minutes, negative_marking,
               start_time, end_time):
        """Create a new test in 'draft' status. Questions get added afterwards."""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO tests
               (title, subject_id, teacher_id, duration_minutes, negative_marking,
                start_time, end_time, status, total_marks)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', 0)""",
            (title, subject_id, teacher_id, duration_minutes, negative_marking,
             start_time, end_time)
        )
        mysql.connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id

    @staticmethod
    def update(test_id, title, subject_id, duration_minutes, negative_marking,
               start_time, end_time):
        cursor = mysql.connection.cursor()
        cursor.execute(
            """UPDATE tests
               SET title = %s, subject_id = %s, duration_minutes = %s,
                   negative_marking = %s, start_time = %s, end_time = %s
               WHERE id = %s""",
            (title, subject_id, duration_minutes, negative_marking,
             start_time, end_time, test_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_by_id(test_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM tests WHERE id = %s", (test_id,))
        test = cursor.fetchone()
        cursor.close()
        return test

    @staticmethod
    def get_all_by_teacher(teacher_id):
        """Return every test created by this teacher, along with its subject name"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT tests.*, subjects.name AS subject_name
               FROM tests
               LEFT JOIN subjects ON tests.subject_id = subjects.id
               WHERE tests.teacher_id = %s
               ORDER BY tests.created_at DESC""",
            (teacher_id,)
        )
        tests = cursor.fetchall()
        cursor.close()
        return tests

    @staticmethod
    def count_by_teacher(teacher_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM tests WHERE teacher_id = %s", (teacher_id,))
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    @staticmethod
    def count_all():
        """Total tests across every teacher — used on the admin dashboard"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM tests")
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    # =====================================================
    # Student-facing queries
    # =====================================================

    @staticmethod
    def get_available_for_student(student_id):
        """Published tests that are open right now and not yet completed by this student"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT tests.*, subjects.name AS subject_name
               FROM tests
               LEFT JOIN subjects ON tests.subject_id = subjects.id
               WHERE tests.status = 'published'
                 AND (tests.start_time IS NULL OR tests.start_time <= NOW())
                 AND (tests.end_time IS NULL OR tests.end_time >= NOW())
                 AND tests.id NOT IN (
                     SELECT test_id FROM results WHERE student_id = %s
                 )
               ORDER BY tests.created_at DESC""",
            (student_id,)
        )
        tests = cursor.fetchall()
        cursor.close()
        return tests

    @staticmethod
    def get_upcoming():
        """Published tests scheduled to start in the future"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT tests.*, subjects.name AS subject_name
               FROM tests
               LEFT JOIN subjects ON tests.subject_id = subjects.id
               WHERE tests.status = 'published'
                 AND tests.start_time IS NOT NULL
                 AND tests.start_time > NOW()
               ORDER BY tests.start_time ASC"""
        )
        tests = cursor.fetchall()
        cursor.close()
        return tests

    @staticmethod
    def get_completed_for_student(student_id):
        """Tests this student has already submitted, with their score attached"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT tests.*, subjects.name AS subject_name,
                      results.score, results.total_marks, results.percentage, results.submitted_at
               FROM results
               JOIN tests ON results.test_id = tests.id
               LEFT JOIN subjects ON tests.subject_id = subjects.id
               WHERE results.student_id = %s
               ORDER BY results.submitted_at DESC""",
            (student_id,)
        )
        tests = cursor.fetchall()
        cursor.close()
        return tests

    @staticmethod
    def set_status(test_id, status):
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE tests SET status = %s WHERE id = %s", (status, test_id))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def delete(test_id):
        """Deleting a test also deletes its questions/options/answers automatically
        because the database schema uses ON DELETE CASCADE."""
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM tests WHERE id = %s", (test_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def recalculate_total_marks(test_id):
        """Re-sum the marks of every question in this test and save it on the test row.
        Call this every time a question is added or removed."""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(marks), 0) AS total FROM questions WHERE test_id = %s",
            (test_id,)
        )
        total = cursor.fetchone()['total']
        cursor.execute("UPDATE tests SET total_marks = %s WHERE id = %s", (total, test_id))
        mysql.connection.commit()
        cursor.close()
