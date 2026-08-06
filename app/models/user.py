"""
File: app/models/user.py
All database operations related to the User live here.
(Login lookup, registration, find user, etc.)
"""

from app import mysql


class User:

    @staticmethod
    def find_by_email(email):
        """Look up a user by email (used during login)"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        """Look up a user by ID (used for session checks)"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user

    @staticmethod
    def create_user(full_name, email, password_hash, role, is_active=1, phone=None,
                     registration_number=None, date_of_birth=None, gender=None,
                     address=None, department_id=None, semester=None):
        """Insert a new user into the database.
        is_active=0 is used when a Teacher or Student self-registers, so an
        Admin has to approve them before they can log in."""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO users
                   (full_name, email, password_hash, role, is_active, phone,
                    registration_number, date_of_birth, gender, address, department_id, semester)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (full_name, email, password_hash, role, is_active, phone,
             registration_number, date_of_birth, gender, address, department_id, semester)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def create_user_by_admin(full_name, email, password_hash, role, phone=None,
                              registration_number=None, department_id=None, semester=None):
        """
        Admin creates a Teacher/Student directly.
        is_active is set to 1 immediately since the admin is creating it themself
        (no separate approval step needed, unlike self-registration).
        """
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO users
                   (full_name, email, password_hash, role, phone,
                    registration_number, department_id, semester, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)""",
            (full_name, email, password_hash, role, phone,
             registration_number, department_id, semester)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_all_by_role(role):
        """Return every user with the given role (teacher/student), newest first"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE role = %s ORDER BY created_at DESC", (role,)
        )
        users = cursor.fetchall()
        cursor.close()
        return users

    @staticmethod
    def count_by_role(role):
        """Return how many users exist for a given role (used on the dashboard)"""
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = %s", (role,))
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    @staticmethod
    def update_user(user_id, full_name, email, phone, is_active):
        """Update a user's basic editable fields (does not touch the password
        or academic details — see update_academic_info for those)"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """UPDATE users
               SET full_name = %s, email = %s, phone = %s, is_active = %s
               WHERE id = %s""",
            (full_name, email, phone, is_active, user_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def update_academic_info(user_id, registration_number=None, date_of_birth=None,
                              gender=None, address=None, department_id=None, semester=None):
        """Update a student's personal + academic details.
        Kept separate from update_user so that routes which don't manage these
        fields (like a simple name/email edit) can never accidentally wipe them out."""
        cursor = mysql.connection.cursor()
        cursor.execute(
            """UPDATE users
               SET registration_number = %s, date_of_birth = %s, gender = %s,
                   address = %s, department_id = %s, semester = %s
               WHERE id = %s""",
            (registration_number, date_of_birth, gender, address, department_id, semester, user_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def update_password(user_id, password_hash):
        """Update only the password hash for a user"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def delete_user(user_id):
        """Permanently delete a user"""
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def find_by_registration_number(registration_number):
        """Used during Student login — students sign in with this instead of email"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE registration_number = %s", (registration_number,)
        )
        user = cursor.fetchone()
        cursor.close()
        return user

    @staticmethod
    def registration_number_exists(registration_number, exclude_user_id=None):
        cursor = mysql.connection.cursor()
        if exclude_user_id:
            cursor.execute(
                "SELECT id FROM users WHERE registration_number = %s AND id != %s",
                (registration_number, exclude_user_id)
            )
        else:
            cursor.execute(
                "SELECT id FROM users WHERE registration_number = %s", (registration_number,)
            )
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    @staticmethod
    def get_pending_users(role):
        """Teachers OR Students who self-registered and are waiting for admin approval"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE role = %s AND is_active = 0 ORDER BY created_at DESC",
            (role,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def count_pending_users(role):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) AS total FROM users WHERE role = %s AND is_active = 0", (role,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result['total'] if result else 0

    @staticmethod
    def approve_user(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET is_active = 1 WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def update_profile_photo(user_id, photo_data, mimetype):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE users SET profile_photo_data = %s, profile_photo_mimetype = %s WHERE id = %s",
            (photo_data, mimetype, user_id)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def email_exists_for_other_user(email, exclude_user_id):
        """Check if another user (not this one) already has this email — used during edit"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s", (email, exclude_user_id)
        )
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    @staticmethod
    def save_reset_otp(email, otp, expires_at):
        """Save a freshly generated OTP against this user's account, with an expiry time"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE users SET reset_otp = %s, reset_otp_expires = %s WHERE email = %s",
            (otp, expires_at, email)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def verify_reset_otp(email, otp):
        """
        Check whether the OTP the user typed matches what we saved, and hasn't expired yet.
        Returns the user row if valid, otherwise None.
        """
        cursor = mysql.connection.cursor()
        cursor.execute(
            """SELECT * FROM users
               WHERE email = %s AND reset_otp = %s AND reset_otp_expires >= NOW()""",
            (email, otp)
        )
        user = cursor.fetchone()
        cursor.close()
        return user

    @staticmethod
    def clear_reset_otp(user_id):
        """Wipe the OTP once it's been used (or replaced by a newer one)"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE users SET reset_otp = NULL, reset_otp_expires = NULL WHERE id = %s",
            (user_id,)
        )
        mysql.connection.commit()
        cursor.close()
