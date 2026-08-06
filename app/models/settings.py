"""
File: app/models/settings.py
Site-wide settings: college name and logo, shown in the header everywhere.
This is a "single row" table — there's only ever one settings record (id=1).
"""

from app import mysql


class Settings:

    @staticmethod
    def get():
        """Return the settings row, creating a default one if it somehow doesn't exist yet"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM college_settings WHERE id = 1")
        settings = cursor.fetchone()

        if not settings:
            cursor.execute(
                "INSERT INTO college_settings (id, college_name) VALUES (1, 'College Exam Portal')"
            )
            mysql.connection.commit()
            cursor.execute("SELECT * FROM college_settings WHERE id = 1")
            settings = cursor.fetchone()

        cursor.close()
        return settings

    @staticmethod
    def update(college_name, logo_data=None, logo_mimetype=None):
        """Update the college name, and the logo only if a new one was uploaded"""
        cursor = mysql.connection.cursor()
        if logo_data:
            cursor.execute(
                """UPDATE college_settings
                   SET college_name = %s, logo_data = %s, logo_mimetype = %s
                   WHERE id = 1""",
                (college_name, logo_data, logo_mimetype)
            )
        else:
            cursor.execute(
                "UPDATE college_settings SET college_name = %s WHERE id = 1",
                (college_name,)
            )
        mysql.connection.commit()
        cursor.close()
