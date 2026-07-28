"""
File: create_admin.py
Creates the first Admin account (with a hashed password).
Run with: python create_admin.py
"""

from app import create_app, mysql
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    full_name = "Super Admin"
    email = "admin@college.com"
    password = "Admin@123"       # change this after your first login
    role = "admin"

    password_hash = generate_password_hash(password)

    cursor = mysql.connection.cursor()

    # Check if the admin account already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing = cursor.fetchone()

    if existing:
        print("Admin account already exists.")
    else:
        cursor.execute(
            """INSERT INTO users (full_name, email, password_hash, role, is_active)
               VALUES (%s, %s, %s, %s, 1)""",
            (full_name, email, password_hash, role)
        )
        mysql.connection.commit()
        print("Admin account created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")

    cursor.close()
