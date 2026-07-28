"""
File: app/models/department.py
Database operations for Departments.
"""

from app import mysql


class Department:

    @staticmethod
    def create(name):
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_all():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM departments ORDER BY name ASC")
        departments = cursor.fetchall()
        cursor.close()
        return departments

    @staticmethod
    def get_by_id(department_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM departments WHERE id = %s", (department_id,))
        department = cursor.fetchone()
        cursor.close()
        return department

    @staticmethod
    def update(department_id, name):
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE departments SET name = %s WHERE id = %s", (name, department_id))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def delete(department_id):
        """Deleting a department sets subject.department_id to NULL automatically
        (ON DELETE SET NULL in the schema) — subjects themselves are not deleted."""
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM departments WHERE id = %s", (department_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def name_exists(name, exclude_id=None):
        """Check for duplicate department names (case-insensitive)"""
        cursor = mysql.connection.cursor()
        if exclude_id:
            cursor.execute(
                "SELECT id FROM departments WHERE LOWER(name) = LOWER(%s) AND id != %s",
                (name, exclude_id)
            )
        else:
            cursor.execute("SELECT id FROM departments WHERE LOWER(name) = LOWER(%s)", (name,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None
