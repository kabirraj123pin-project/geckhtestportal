"""
File: app/routes/dashboard.py
Each role (Admin / Teacher / Student) has its own dashboard route here.
"""

from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models.user import User
from app.models.test import Test
from app.models.subject import Subject
from app.models.result import Result

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(role=None):
    """
    Decorator that checks whether the user is logged in,
    and (if a role is given) whether they have the correct role.
    Avoids repeating the same check in every route.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                flash('You do not have permission to view this page.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@dashboard_bp.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    stats = {
        'total_students': User.count_by_role('student'),
        'total_teachers': User.count_by_role('teacher'),
        'total_subjects': Subject.count_all(),
        'total_tests': Test.count_all(),
        'pending_teachers': User.count_pending_users('teacher'),
        'pending_students': User.count_pending_users('student'),
    }
    return render_template('admin/dashboard.html', name=session.get('full_name'), stats=stats)


@dashboard_bp.route('/teacher/dashboard')
@login_required(role='teacher')
def teacher_dashboard():
    teacher_id = session.get('user_id')
    overview = Result.get_teacher_overview(teacher_id)
    stats = {
        'tests_created': Test.count_by_teacher(teacher_id),
        'students_attempted': overview['students_attempted'],
        'avg_percentage': overview['avg_percentage'],
    }
    return render_template('teacher/dashboard.html', name=session.get('full_name'), stats=stats)


@dashboard_bp.route('/student/dashboard')
@login_required(role='student')
def student_dashboard():
    student_id = session.get('user_id')
    stats = {
        'upcoming_tests': len(Test.get_upcoming()),
        'available_tests': len(Test.get_available_for_student(student_id)),
        'completed_tests': len(Test.get_completed_for_student(student_id)),
        'average_score': Result.get_average_percentage(student_id),
    }
    return render_template('student/dashboard.html', name=session.get('full_name'), stats=stats)
