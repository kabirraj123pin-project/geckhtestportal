"""
File: app/models/question.py
Database operations for Questions and their answer Options.
"""

from app import mysql


class Question:

    @staticmethod
    def create(test_id, question_text, question_type, marks):
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO questions (test_id, question_text, question_type, marks)
               VALUES (%s, %s, %s, %s)""",
            (test_id, question_text, question_type, marks)
        )
        mysql.connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id

    @staticmethod
    def get_all_by_test(test_id):
        """Return every question for a test, each with its list of options attached"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM questions WHERE test_id = %s ORDER BY id ASC", (test_id,)
        )
        # MySQLdb's fetchall() always returns a tuple (even with DictCursor rows) —
        # convert to a list so features like question shuffling can modify it in place.
        questions = list(cursor.fetchall())
        cursor.close()

        # Attach options to each question so templates can loop through them easily
        for question in questions:
            question['options'] = Option.get_all_by_question(question['id'])

        return questions

    @staticmethod
    def count_by_test(test_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM questions WHERE test_id = %s", (test_id,))
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    @staticmethod
    def delete(question_id):
        """Deleting a question also deletes its options automatically (ON DELETE CASCADE)"""
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_test_id_for_question(question_id):
        """Handy helper: find which test a question belongs to (used after deleting,
        so we know which test's total_marks to recalculate)"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT test_id FROM questions WHERE id = %s", (question_id,))
        result = cursor.fetchone()
        cursor.close()
        return result['test_id'] if result else None


class Option:

    @staticmethod
    def create(question_id, option_text, is_correct):
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO options (question_id, option_text, is_correct)
               VALUES (%s, %s, %s)""",
            (question_id, option_text, is_correct)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_all_by_question(question_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM options WHERE question_id = %s ORDER BY id ASC", (question_id,)
        )
        options = list(cursor.fetchall())
        cursor.close()
        return options
