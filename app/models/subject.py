"""
File: app/models/subject.py
Database operations for Subjects.
"""

from app import mysql


class Subject:

    @staticmethod
    def create(name, department_id, teacher_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO subjects (name, department_id, teacher_id)
               VALUES (%s, %s, %s)""",
            (name, department_id, teacher_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_all():
        """Return every subject, used to populate simple dropdowns"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM subjects ORDER BY name ASC")
        subjects = cursor.fetchall()
        cursor.close()
        return subjects

    @staticmethod
    def get_all_with_details():
        """Return every subject along with its department name and assigned teacher name
        (used on the admin Subjects list page)"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT subjects.*, departments.name AS department_name, users.full_name AS teacher_name
               FROM subjects
               LEFT JOIN departments ON subjects.department_id = departments.id
               LEFT JOIN users ON subjects.teacher_id = users.id
               ORDER BY subjects.name ASC"""
        )
        subjects = cursor.fetchall()
        cursor.close()
        return subjects

    @staticmethod
    def get_by_id(subject_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
        subject = cursor.fetchone()
        cursor.close()
        return subject

    @staticmethod
    def update(subject_id, name, department_id, teacher_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            """UPDATE subjects SET name = %s, department_id = %s, teacher_id = %s
               WHERE id = %s""",
            (name, department_id, teacher_id, subject_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def delete(subject_id):
        """Deleting a subject also deletes any tests linked to it (ON DELETE CASCADE)"""
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def count_all():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM subjects")
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0
