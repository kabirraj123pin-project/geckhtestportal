"""
File: app/models/result.py
Stores final test results and calculates rank/performance history.
"""

from app import mysql


class Result:

    @staticmethod
    def save(student_id, test_id, score, total_marks, percentage):
        """Save the result, or overwrite it if one already exists for this attempt"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO results (student_id, test_id, score, total_marks, percentage)
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                   score = VALUES(score),
                   total_marks = VALUES(total_marks),
                   percentage = VALUES(percentage),
                   submitted_at = NOW()""",
            (student_id, test_id, score, total_marks, percentage)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_by_student_test(student_id, test_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM results WHERE student_id = %s AND test_id = %s",
            (student_id, test_id)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    @staticmethod
    def get_rank(test_id, student_id):
        """
        Return (rank, total_participants) for this student on this test.
        Uses MySQL's RANK() window function to rank everyone by score, highest first.
        """
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT student_id,
                      RANK() OVER (ORDER BY score DESC) AS student_rank,
                      COUNT(*) OVER () AS total_participants
               FROM results
               WHERE test_id = %s""",
            (test_id,)
        )
        rows = cursor.fetchall()
        cursor.close()

        for row in rows:
            if row['student_id'] == student_id:
                return row['student_rank'], row['total_participants']
        return None, None

    @staticmethod
    def get_all_by_student(student_id):
        """Every result for this student, oldest first — used for the performance graph"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT results.*, tests.title AS test_title
               FROM results
               JOIN tests ON results.test_id = tests.id
               WHERE results.student_id = %s
               ORDER BY results.submitted_at ASC""",
            (student_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        return results

    @staticmethod
    def get_average_percentage(student_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT AVG(percentage) AS avg_pct FROM results WHERE student_id = %s",
            (student_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return round(row['avg_pct'], 1) if row and row['avg_pct'] else 0

    # =====================================================
    # Teacher-facing queries
    # =====================================================

    @staticmethod
    def get_all_for_test(test_id):
        """Every student's result for a test, best score first — this IS the leaderboard"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT results.*, users.full_name AS student_name,
                      users.registration_number AS student_registration_number
               FROM results
               JOIN users ON results.student_id = users.id
               WHERE results.test_id = %s
               ORDER BY results.score DESC""",
            (test_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_stats_for_test(test_id, pass_percentage=40):
        """Total attempts, average score, and pass percentage for a test
        (a student "passes" if their percentage is at least `pass_percentage`)"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT COUNT(*) AS total_attempts,
                      AVG(percentage) AS avg_pct,
                      SUM(CASE WHEN percentage >= %s THEN 1 ELSE 0 END) AS pass_count
               FROM results WHERE test_id = %s""",
            (pass_percentage, test_id)
        )
        row = cursor.fetchone()
        cursor.close()

        total = row['total_attempts'] or 0
        pass_count = row['pass_count'] or 0

        return {
            'total_attempts': total,
            'average_percentage': round(row['avg_pct'], 1) if row['avg_pct'] else 0,
            'pass_count': pass_count,
            'pass_percentage': round((pass_count / total) * 100, 1) if total else 0,
        }

    @staticmethod
    def get_teacher_overview(teacher_id):
        """Across every test this teacher has created: how many unique students
        have attempted something, and what's the average pass rate (used on the
        teacher dashboard's summary cards)"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT COUNT(DISTINCT results.student_id) AS students_attempted,
                      AVG(results.percentage) AS avg_pct
               FROM results
               JOIN tests ON results.test_id = tests.id
               WHERE tests.teacher_id = %s""",
            (teacher_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        return {
            'students_attempted': row['students_attempted'] or 0,
            'avg_percentage': round(row['avg_pct'], 1) if row['avg_pct'] else 0,
        }
