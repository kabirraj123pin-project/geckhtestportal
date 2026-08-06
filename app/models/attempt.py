"""
File: app/models/attempt.py
Tracks a student's attempt at a test — when they started, and whether
they've submitted. This is what makes "Resume Test" possible: if a
student refreshes the page or closes the browser, we know exactly
when they started and can calculate how much time is left.
"""

from app import mysql
from app.utils import now_ist


class TestAttempt:

    @staticmethod
    def get_or_create(student_id, test_id):
        """
        If the student already has an attempt for this test, return it
        (this is what lets them "resume"). Otherwise start a new one.
        """
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM test_attempts WHERE student_id = %s AND test_id = %s",
            (student_id, test_id)
        )
        attempt = cursor.fetchone()

        if not attempt:
            cursor.execute(
                """INSERT INTO test_attempts (student_id, test_id, start_time, status)
                   VALUES (%s, %s, NOW(), 'in_progress')""",
                (student_id, test_id)
            )
            mysql.connection.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM test_attempts WHERE id = %s", (new_id,))
            attempt = cursor.fetchone()

        cursor.close()
        return attempt

    @staticmethod
    def get_by_student_test(student_id, test_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM test_attempts WHERE student_id = %s AND test_id = %s",
            (student_id, test_id)
        )
        attempt = cursor.fetchone()
        cursor.close()
        return attempt

    @staticmethod
    def mark_submitted(attempt_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE test_attempts SET status = 'submitted', submitted_at = NOW() WHERE id = %s",
            (attempt_id,)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_remaining_seconds(attempt, duration_minutes):
        """How many seconds does the student have left on the timer?"""
        elapsed = (now_ist() - attempt['start_time']).total_seconds()
        remaining = (duration_minutes * 60) - elapsed
        return max(0, int(remaining))
