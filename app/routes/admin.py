"""
File: app/routes/admin.py
Everything the Admin can do to manage Teacher and Student accounts:
List, Add, Edit, Delete, and Activate/Deactivate.
"""

import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from werkzeug.security import generate_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.subject import Subject
from app.models.notification import Notification
from app.models.report import Report
from app.models.settings import Settings
from app.utils import read_image_for_db
from app.routes.dashboard import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# =====================================================
# TEACHERS
# =====================================================

@admin_bp.route('/teachers')
@login_required(role='admin')
def teacher_list():
    """Show a table of all teachers"""
    teachers = User.get_all_by_role('teacher')
    return render_template('admin/user_list.html',
                            users=teachers,
                            role='teacher',
                            title='Manage Teachers')


@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required(role='admin')
def teacher_add():
    return _add_user(role='teacher')


@admin_bp.route('/teachers/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def teacher_edit(user_id):
    return _edit_user(user_id, role='teacher')


@admin_bp.route('/teachers/delete/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def teacher_delete(user_id):
    return _delete_user(user_id, role='teacher')


@admin_bp.route('/teachers/pending')
@login_required(role='admin')
def teacher_pending():
    """Teachers who self-registered and are waiting for approval"""
    pending = User.get_pending_users('teacher')
    return render_template('admin/teacher_pending.html', pending=pending)


@admin_bp.route('/teachers/approve/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def teacher_approve(user_id):
    user = User.find_by_id(user_id)
    if not user or user['role'] != 'teacher':
        flash('Teacher not found.', 'danger')
        return redirect(url_for('admin.teacher_pending'))

    User.approve_user(user_id)
    Notification.create(user_id, 'Account Approved',
                         'Your teacher account has been approved. You can now log in.')
    flash(f"{user['full_name']}'s account has been approved.", 'success')
    return redirect(url_for('admin.teacher_pending'))


@admin_bp.route('/teachers/reject/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def teacher_reject(user_id):
    user = User.find_by_id(user_id)
    if not user or user['role'] != 'teacher':
        flash('Teacher not found.', 'danger')
    else:
        User.delete_user(user_id)
        flash(f"{user['full_name']}'s registration was rejected and removed.", 'info')
    return redirect(url_for('admin.teacher_pending'))


# =====================================================
# STUDENTS
# =====================================================

@admin_bp.route('/students')
@login_required(role='admin')
def student_list():
    """Show a table of all students"""
    students = User.get_all_by_role('student')
    return render_template('admin/user_list.html',
                            users=students,
                            role='student',
                            title='Manage Students')


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required(role='admin')
def student_add():
    return _add_user(role='student')


@admin_bp.route('/students/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def student_edit(user_id):
    return _edit_user(user_id, role='student')


@admin_bp.route('/students/delete/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def student_delete(user_id):
    return _delete_user(user_id, role='student')


@admin_bp.route('/students/pending')
@login_required(role='admin')
def student_pending():
    """Students who self-registered and are waiting for approval"""
    pending = User.get_pending_users('student')
    return render_template('admin/student_pending.html', pending=pending)


@admin_bp.route('/students/approve/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def student_approve(user_id):
    user = User.find_by_id(user_id)
    if not user or user['role'] != 'student':
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.student_pending'))

    User.approve_user(user_id)
    Notification.create(user_id, 'Account Approved',
                         'Your student account has been approved. You can now log in.')
    flash(f"{user['full_name']}'s account has been approved.", 'success')
    return redirect(url_for('admin.student_pending'))


@admin_bp.route('/students/reject/<int:user_id>', methods=['POST'])
@login_required(role='admin')
def student_reject(user_id):
    user = User.find_by_id(user_id)
    if not user or user['role'] != 'student':
        flash('Student not found.', 'danger')
    else:
        User.delete_user(user_id)
        flash(f"{user['full_name']}'s registration was rejected and removed.", 'info')
    return redirect(url_for('admin.student_pending'))


# =====================================================
# Shared helper functions
# (Both Teacher and Student forms use the exact same logic,
#  so we avoid duplicating code by sharing these functions.)
# =====================================================

def _add_user(role):
    departments = Department.get_all() if role == 'student' else []

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        registration_number = request.form.get('registration_number', '').strip() or None
        department_id = request.form.get('department_id') or None
        semester = request.form.get('semester') or None

        # ---- Validation ----
        if not full_name or not email or not password:
            flash('Name, email, and password are required.', 'danger')
            return render_template('admin/user_form.html', role=role, user=None, departments=departments)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('admin/user_form.html', role=role, user=None, departments=departments)

        if User.find_by_email(email):
            flash('This email is already registered.', 'danger')
            return render_template('admin/user_form.html', role=role, user=None, departments=departments)

        if role == 'student' and registration_number and User.registration_number_exists(registration_number):
            flash('This Registration Number is already in use.', 'danger')
            return render_template('admin/user_form.html', role=role, user=None, departments=departments)

        # ---- Create the account ----
        password_hash = generate_password_hash(password)
        User.create_user_by_admin(full_name, email, password_hash, role, phone,
                                   registration_number, department_id, semester)

        flash(f'{role.capitalize()} account created successfully.', 'success')
        return redirect(url_for(f'admin.{role}_list'))

    # GET request -> show a blank form
    return render_template('admin/user_form.html', role=role, user=None, departments=departments)


def _edit_user(user_id, role):
    user = User.find_by_id(user_id)
    if not user or user['role'] != role:
        flash('User not found.', 'danger')
        return redirect(url_for(f'admin.{role}_list'))

    departments = Department.get_all() if role == 'student' else []

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        new_password = request.form.get('password', '').strip()

        registration_number = request.form.get('registration_number', '').strip() or None
        department_id = request.form.get('department_id') or None
        semester = request.form.get('semester') or None

        # ---- Validation ----
        if not full_name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('admin/user_form.html', role=role, user=user, departments=departments)

        if User.email_exists_for_other_user(email, user_id):
            flash('Another account is already using this email.', 'danger')
            return render_template('admin/user_form.html', role=role, user=user, departments=departments)

        if (role == 'student' and registration_number and
                User.registration_number_exists(registration_number, exclude_user_id=user_id)):
            flash('Another account is already using this Registration Number.', 'danger')
            return render_template('admin/user_form.html', role=role, user=user, departments=departments)

        # ---- Update basic details ----
        User.update_user(user_id, full_name, email, phone, is_active)

        if role == 'student':
            User.update_academic_info(user_id, registration_number=registration_number,
                                       date_of_birth=user.get('date_of_birth'), gender=user.get('gender'),
                                       address=user.get('address'), department_id=department_id,
                                       semester=semester)

        # ---- Only change the password if the admin actually typed a new one ----
        if new_password:
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return render_template('admin/user_form.html', role=role, user=user, departments=departments)
            User.update_password(user_id, generate_password_hash(new_password))
            Notification.create(user_id, 'Password Changed',
                                 'Your password was changed by an administrator.')

        flash(f'{role.capitalize()} account updated successfully.', 'success')
        return redirect(url_for(f'admin.{role}_list'))

    # GET request -> show the form pre-filled with existing data
    return render_template('admin/user_form.html', role=role, user=user, departments=departments)


def _delete_user(user_id, role):
    user = User.find_by_id(user_id)
    if not user or user['role'] != role:
        flash('User not found.', 'danger')
    else:
        User.delete_user(user_id)
        flash(f'{role.capitalize()} account deleted.', 'info')
    return redirect(url_for(f'admin.{role}_list'))


# =====================================================
# DEPARTMENTS
# =====================================================

@admin_bp.route('/departments')
@login_required(role='admin')
def department_list():
    departments = Department.get_all()
    return render_template('admin/department_list.html', departments=departments)


@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@login_required(role='admin')
def department_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            flash('Department name is required.', 'danger')
            return render_template('admin/department_form.html', department=None)

        if Department.name_exists(name):
            flash('A department with this name already exists.', 'danger')
            return render_template('admin/department_form.html', department=None)

        Department.create(name)
        flash('Department created successfully.', 'success')
        return redirect(url_for('admin.department_list'))

    return render_template('admin/department_form.html', department=None)


@admin_bp.route('/departments/edit/<int:department_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def department_edit(department_id):
    department = Department.get_by_id(department_id)
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('admin.department_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            flash('Department name is required.', 'danger')
            return render_template('admin/department_form.html', department=department)

        if Department.name_exists(name, exclude_id=department_id):
            flash('Another department already uses this name.', 'danger')
            return render_template('admin/department_form.html', department=department)

        Department.update(department_id, name)
        flash('Department updated successfully.', 'success')
        return redirect(url_for('admin.department_list'))

    return render_template('admin/department_form.html', department=department)


@admin_bp.route('/departments/delete/<int:department_id>', methods=['POST'])
@login_required(role='admin')
def department_delete(department_id):
    Department.delete(department_id)
    flash('Department deleted. Any subjects in it are now unassigned.', 'info')
    return redirect(url_for('admin.department_list'))


# =====================================================
# SUBJECTS
# =====================================================

@admin_bp.route('/subjects')
@login_required(role='admin')
def subject_list():
    subjects = Subject.get_all_with_details()
    return render_template('admin/subject_list.html', subjects=subjects)


@admin_bp.route('/subjects/add', methods=['GET', 'POST'])
@login_required(role='admin')
def subject_add():
    departments = Department.get_all()
    teachers = User.get_all_by_role('teacher')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department_id = request.form.get('department_id') or None
        teacher_id = request.form.get('teacher_id') or None

        if not name:
            flash('Subject name is required.', 'danger')
            return render_template('admin/subject_form.html', subject=None,
                                    departments=departments, teachers=teachers)

        Subject.create(name, department_id, teacher_id)
        flash('Subject created successfully.', 'success')
        return redirect(url_for('admin.subject_list'))

    return render_template('admin/subject_form.html', subject=None,
                            departments=departments, teachers=teachers)


@admin_bp.route('/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def subject_edit(subject_id):
    subject = Subject.get_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin.subject_list'))

    departments = Department.get_all()
    teachers = User.get_all_by_role('teacher')

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department_id = request.form.get('department_id') or None
        teacher_id = request.form.get('teacher_id') or None

        if not name:
            flash('Subject name is required.', 'danger')
            return render_template('admin/subject_form.html', subject=subject,
                                    departments=departments, teachers=teachers)

        Subject.update(subject_id, name, department_id, teacher_id)
        flash('Subject updated successfully.', 'success')
        return redirect(url_for('admin.subject_list'))

    return render_template('admin/subject_form.html', subject=subject,
                            departments=departments, teachers=teachers)


@admin_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required(role='admin')
def subject_delete(subject_id):
    Subject.delete(subject_id)
    flash('Subject deleted (any tests under it were removed too).', 'info')
    return redirect(url_for('admin.subject_list'))


# =====================================================
# REPORTS
# =====================================================

def _get_filters_from_request():
    """Read filter values from the query string (?date_from=...&subject_id=...)"""
    return {
        'date_from': request.args.get('date_from') or None,
        'date_to': request.args.get('date_to') or None,
        'department_id': request.args.get('department_id') or None,
        'subject_id': request.args.get('subject_id') or None,
        'teacher_id': request.args.get('teacher_id') or None,
    }


@admin_bp.route('/reports')
@login_required(role='admin')
def reports():
    filters = _get_filters_from_request()

    summary = Report.get_summary(filters)
    results = Report.get_results(filters)
    subject_summary = Report.get_subject_wise_summary(filters)
    teacher_summary = Report.get_teacher_wise_summary(filters)

    return render_template('admin/reports.html',
                            filters=filters,
                            active_filters={k: v for k, v in filters.items() if v},
                            summary=summary,
                            results=results,
                            subject_summary=subject_summary,
                            teacher_summary=teacher_summary,
                            departments=Department.get_all(),
                            subjects=Subject.get_all(),
                            teachers=User.get_all_by_role('teacher'))


@admin_bp.route('/reports/export')
@login_required(role='admin')
def reports_export():
    """Download the detailed report as a CSV file (opens directly in Excel)"""
    filters = _get_filters_from_request()
    results = Report.get_results(filters)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student', 'Test', 'Subject', 'Teacher', 'Score', 'Total Marks', 'Percentage', 'Submitted At'])

    for row in results:
        writer.writerow([
            row['student_name'], row['test_title'], row['subject_name'] or 'General',
            row['teacher_name'] or '—', row['score'], row['total_marks'],
            row['percentage'], row['submitted_at']
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=admin_report.csv'
    return response


# =====================================================
# COLLEGE SETTINGS (name + logo, shown site-wide)
# =====================================================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required(role='admin')
def settings():
    current_settings = Settings.get()

    if request.method == 'POST':
        college_name = request.form.get('college_name', '').strip() or 'College Exam Portal'
        logo_file = request.files.get('logo')

        try:
            logo_data, logo_mimetype = read_image_for_db(logo_file)
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('admin/settings.html', settings=current_settings)

        Settings.update(college_name, logo_data, logo_mimetype)
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', settings=current_settings)
