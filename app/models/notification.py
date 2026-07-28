"""
File: app/models/notification.py
In-app notifications: test published, result published, password changed, etc.
Shown as a bell icon dropdown on every dashboard.
"""

from app import mysql


class Notification:

    @staticmethod
    def create(user_id, title, message):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
            (user_id, title, message)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def create_for_many(user_ids, title, message):
        """Send the same notification to a whole list of users at once
        (e.g. every student, when a teacher publishes a new test)"""
        if not user_ids:
            return
        cursor = mysql.connection.cursor()
        values = [(uid, title, message) for uid in user_ids]
        cursor.executemany(
            "INSERT INTO notifications (user_id, title, message) VALUES (%s, %s, %s)",
            values
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_unread_count(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    @staticmethod
    def get_recent(user_id, limit=5):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_all(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """user_id check ensures a student can't mark someone else's notification as read"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, user_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def mark_all_as_read(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        mysql.connection.commit()
        cursor.close()
