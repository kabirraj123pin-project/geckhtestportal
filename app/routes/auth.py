"""
File: app/routes/auth.py
Login, Register, Logout - all authentication logic lives here.
"""

import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from app import mail
from app.models.user import User
from app.models.department import Department
from app.utils import now_ist

auth_bp = Blueprint('auth', __name__)

# Basic in-memory login attempt limiter (use Redis in production)
failed_attempts = {}
MAX_ATTEMPTS = 5


@auth_bp.route('/', methods=['GET'])
def home():
    """Root URL -> redirect to login page"""
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Admins/Teachers sign in with email; Students sign in with their
        # registration number — this one field accepts either.
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        # ---- Check login attempt limit ----
        attempts = failed_attempts.get(identifier, 0)
        if attempts >= MAX_ATTEMPTS:
            flash('Too many failed attempts. Please try again in 15 minutes.', 'danger')
            return render_template('auth/login.html')

        # ---- Look up user by email first, then by registration number ----
        user = User.find_by_email(identifier) or User.find_by_registration_number(identifier)

        if user and check_password_hash(user['password_hash'], password):
            # Correct password - login successful
            failed_attempts[identifier] = 0

            if not user['is_active']:
                flash('Your account has not been approved by the admin yet.', 'warning')
                return render_template('auth/login.html')

            # ---- Save user data in the session ----
            session.permanent = True
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['full_name'] = user['full_name']

            flash(f'Welcome back, {user["full_name"]}!', 'success')

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('dashboard.admin_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('dashboard.teacher_dashboard'))
            else:
                return redirect(url_for('dashboard.student_dashboard'))
        else:
            # Wrong password - increment attempt count
            failed_attempts[identifier] = attempts + 1
            flash('Invalid credentials. Please check and try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    New students/teachers can register here.
    Both roles need admin approval before they can log in.
    Students additionally provide a Registration Number (used to log in
    instead of email) plus personal and academic details.
    """
    departments = Department.get_all()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        phone = request.form.get('phone', '').strip()

        # ---- Basic validation (applies to both roles) ----
        if not full_name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('auth/register.html', departments=departments)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', departments=departments)

        if User.find_by_email(email):
            flash('This email is already registered.', 'danger')
            return render_template('auth/register.html', departments=departments)

        registration_number = None
        date_of_birth = None
        gender = None
        address = None
        department_id = None
        semester = None

        if role == 'student':
            registration_number = request.form.get('registration_number', '').strip()
            date_of_birth = request.form.get('date_of_birth') or None
            gender = request.form.get('gender') or None
            address = request.form.get('address', '').strip() or None
            department_id = request.form.get('department_id') or None
            semester = request.form.get('semester') or None

            # ---- Student-specific validation ----
            if not registration_number:
                flash('Registration Number is required for students.', 'danger')
                return render_template('auth/register.html', departments=departments)

            if User.registration_number_exists(registration_number):
                flash('This Registration Number is already in use.', 'danger')
                return render_template('auth/register.html', departments=departments)

        # ---- Hash the password (never store plain text) ----
        password_hash = generate_password_hash(password)

        # Both roles need an admin to approve them before they can log in.
        User.create_user(full_name, email, password_hash, role, is_active=0, phone=phone,
                          registration_number=registration_number, date_of_birth=date_of_birth,
                          gender=gender, address=address, department_id=department_id,
                          semester=semester)

        flash('Registration successful! Your account is pending admin approval — '
              'you will be able to log in once approved.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', departments=departments)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


# =====================================================
# FORGOT PASSWORD (OTP-based reset)
# =====================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.find_by_email(email)

        # For security, we show the same message whether or not the email exists
        # (this stops people from using this form to check who has an account)
        generic_message = 'If that email is registered, an OTP has been sent to it.'

        if not user:
            flash(generic_message, 'info')
            return render_template('auth/forgot_password.html')

        # ---- Generate a 6-digit OTP that expires in 10 minutes ----
        otp = str(random.randint(100000, 999999))
        expires_at = now_ist() + timedelta(minutes=10)
        User.save_reset_otp(email, otp, expires_at)

        email_sent = _send_otp_email(email, otp)

        if email_sent:
            flash(generic_message, 'success')
        else:
            # Email isn't configured yet (no SMTP credentials in .env) — rather than
            # blocking the student/teacher/admin from testing this feature, show the
            # OTP directly on screen. Once real email is configured, this won't show.
            flash(f'Email is not configured yet, so here is your OTP for testing: {otp}', 'warning')

        return redirect(url_for('auth.reset_password', email=email))

    return render_template('auth/forgot_password.html')


def _send_otp_email(to_email, otp):
    """Try to send the OTP by email. Returns True on success, False if it fails
    (e.g. MAIL_USERNAME/MAIL_PASSWORD haven't been set up in .env yet)."""
    try:
        message = Message(
            subject='Your Password Reset OTP - College Exam Portal',
            recipients=[to_email],
            body=f'Your OTP to reset your password is: {otp}\n\nThis code expires in 10 minutes.'
        )
        mail.send(message)
        return True
    except Exception as error:
        print(f'[Email not sent — this is expected until you configure .env] {error}')
        return False


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email', '') or request.form.get('email', '')

    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', email=email)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', email=email)

        user = User.verify_reset_otp(email, otp)
        if not user:
            flash('That OTP is invalid or has expired. Please request a new one.', 'danger')
            return render_template('auth/reset_password.html', email=email)

        User.update_password(user['id'], generate_password_hash(new_password))
        User.clear_reset_otp(user['id'])

        flash('Password reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', email=email)
