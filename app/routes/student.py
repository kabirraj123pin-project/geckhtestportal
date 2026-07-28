"""
File: app/routes/student.py
Everything a Student can do:
Browse tests, attempt a test (with timer/resume/autosave), submit,
view instant results with rank, review answers, track performance,
and manage their profile.
"""

import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.test import Test
from app.models.question import Question
from app.models.attempt import TestAttempt
from app.models.student_answer import StudentAnswer
from app.models.result import Result
from app.models.user import User
from app.models.notification import Notification
from app.utils import save_uploaded_image, generate_qr_code_base64
from app.routes.dashboard import login_required

student_bp = Blueprint('student', __name__, url_prefix='/student')


# =====================================================
# TEST LISTS (Available / Upcoming / Completed)
# =====================================================

@student_bp.route('/tests')
@login_required(role='student')
def test_list():
    student_id = session.get('user_id')
    available_tests = Test.get_available_for_student(student_id)
    upcoming_tests = Test.get_upcoming()
    completed_tests = Test.get_completed_for_student(student_id)

    return render_template('student/test_list.html',
                            available_tests=available_tests,
                            upcoming_tests=upcoming_tests,
                            completed_tests=completed_tests)


# =====================================================
# START / RESUME / ATTEMPT a Test
# =====================================================

@student_bp.route('/tests/<int:test_id>/start')
@login_required(role='student')
def test_start(test_id):
    student_id = session.get('user_id')

    # Already submitted? Send them straight to the result instead of letting them retake it.
    if Result.get_by_student_test(student_id, test_id):
        flash('You have already completed this test.', 'info')
        return redirect(url_for('student.test_result', test_id=test_id))

    # Creates a new attempt (records start time) or resumes the existing one
    TestAttempt.get_or_create(student_id, test_id)
    return redirect(url_for('student.test_attempt', test_id=test_id))


@student_bp.route('/tests/<int:test_id>/attempt')
@login_required(role='student')
def test_attempt(test_id):
    student_id = session.get('user_id')
    test = Test.get_by_id(test_id)

    if not test or test['status'] != 'published':
        flash('This test is not available.', 'danger')
        return redirect(url_for('student.test_list'))

    attempt = TestAttempt.get_by_student_test(student_id, test_id)
    if not attempt:
        # Safety net: if someone lands here directly without starting, start it now
        attempt = TestAttempt.get_or_create(student_id, test_id)

    if attempt['status'] == 'submitted':
        return redirect(url_for('student.test_result', test_id=test_id))

    remaining_seconds = TestAttempt.get_remaining_seconds(attempt, test['duration_minutes'])

    # Time already up (e.g. student closed the tab and came back too late) -> auto-submit now
    if remaining_seconds <= 0:
        return _finalize_submission(student_id, test_id, attempt)

    questions = Question.get_all_by_test(test_id)

    # Shuffle questions and their options — but using a seed based on the attempt ID,
    # so the order stays the SAME every time this student reloads/resumes this attempt.
    shuffler = random.Random(attempt['id'])
    shuffler.shuffle(questions)
    for question in questions:
        if question['question_type'] in ('single_choice', 'multiple_choice'):
            shuffler.shuffle(question['options'])

    existing_answers = StudentAnswer.get_all_for_attempt(student_id, test_id)

    return render_template('student/attempt.html',
                            test=test,
                            questions=questions,
                            existing_answers=existing_answers,
                            remaining_seconds=remaining_seconds)


@student_bp.route('/tests/<int:test_id>/save-answer', methods=['POST'])
@login_required(role='student')
def save_answer(test_id):
    """Called via JavaScript (fetch) every time the student picks/changes an answer — autosave"""
    student_id = session.get('user_id')
    data = request.get_json()

    question_id = data.get('question_id')
    selected_option_id = data.get('selected_option_id')
    answer_text = data.get('answer_text')
    marked_for_review = 1 if data.get('marked_for_review') else 0

    StudentAnswer.save_answer(student_id, test_id, question_id,
                               selected_option_id, answer_text, marked_for_review)

    return jsonify({'success': True})


@student_bp.route('/tests/<int:test_id>/submit', methods=['POST'])
@login_required(role='student')
def test_submit(test_id):
    student_id = session.get('user_id')
    attempt = TestAttempt.get_by_student_test(student_id, test_id)

    if not attempt:
        flash('No attempt found for this test.', 'danger')
        return redirect(url_for('student.test_list'))

    if attempt['status'] == 'submitted':
        return redirect(url_for('student.test_result', test_id=test_id))

    return _finalize_submission(student_id, test_id, attempt)


def _finalize_submission(student_id, test_id, attempt):
    """Shared logic: evaluate every answer, save the Result, mark the attempt submitted."""
    test = Test.get_by_id(test_id)
    questions = Question.get_all_by_test(test_id)

    evaluation = StudentAnswer.evaluate_test(student_id, test_id, questions, test['negative_marking'])

    percentage = round((evaluation['score'] / test['total_marks']) * 100, 1) if test['total_marks'] else 0

    Result.save(student_id, test_id, evaluation['score'], test['total_marks'], percentage)
    TestAttempt.mark_submitted(attempt['id'])

    Notification.create(
        student_id,
        'Result Published',
        f"Your result for '{test['title']}' is ready: {evaluation['score']}/{test['total_marks']} ({percentage}%)."
    )

    flash('Test submitted! Here is your result.', 'success')
    return redirect(url_for('student.test_result', test_id=test_id))


# =====================================================
# RESULT + REVIEW ANSWERS
# =====================================================

@student_bp.route('/tests/<int:test_id>/result')
@login_required(role='student')
def test_result(test_id):
    student_id = session.get('user_id')
    test = Test.get_by_id(test_id)
    result = Result.get_by_student_test(student_id, test_id)

    if not result:
        flash('You have not attempted this test yet.', 'warning')
        return redirect(url_for('student.test_list'))

    rank, total_participants = Result.get_rank(test_id, student_id)

    questions = Question.get_all_by_test(test_id)
    evaluation = StudentAnswer.evaluate_test(student_id, test_id, questions, test['negative_marking'])

    student = User.find_by_id(student_id)
    qr_data = (f"Result Verification\n"
               f"Student: {student['full_name']}\n"
               f"Test: {test['title']}\n"
               f"Score: {result['score']}/{result['total_marks']} ({result['percentage']}%)\n"
               f"Date: {result['submitted_at'].strftime('%d %b %Y')}")
    qr_code_base64 = generate_qr_code_base64(qr_data)

    return render_template('student/result.html',
                            test=test,
                            result=result,
                            rank=rank,
                            total_participants=total_participants,
                            breakdown=evaluation['breakdown'],
                            correct_count=evaluation['correct_count'],
                            qr_code_base64=qr_code_base64,
                            wrong_count=evaluation['wrong_count'],
                            skipped_count=evaluation['skipped_count'])


# =====================================================
# PERFORMANCE ANALYTICS
# =====================================================

@student_bp.route('/performance')
@login_required(role='student')
def performance():
    student_id = session.get('user_id')
    results = Result.get_all_by_student(student_id)
    average_percentage = Result.get_average_percentage(student_id)

    return render_template('student/performance.html',
                            results=results,
                            average_percentage=average_percentage)


# =====================================================
# PROFILE + CHANGE PASSWORD
# =====================================================

@student_bp.route('/id-card')
@login_required(role='student')
def id_card():
    student_id = session.get('user_id')
    student = User.find_by_id(student_id)

    qr_data = (f"Student ID Card\nName: {student['full_name']}\nEmail: {student['email']}\n"
               f"Registration Number: {student['registration_number'] or 'N/A'}")
    qr_code_base64 = generate_qr_code_base64(qr_data)

    return render_template('student/id_card.html', student=student, qr_code_base64=qr_code_base64)


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required(role='student')
def profile():
    student_id = session.get('user_id')
    user = User.find_by_id(student_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not full_name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('student/profile.html', user=user)

        if User.email_exists_for_other_user(email, student_id):
            flash('Another account is already using this email.', 'danger')
            return render_template('student/profile.html', user=user)

        # ---- Profile photo (optional — only updated if a new file was chosen) ----
        try:
            photo_path = save_uploaded_image(request.files.get('profile_photo'), 'profiles')
            if photo_path:
                User.update_profile_photo(student_id, photo_path)
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template('student/profile.html', user=user)

        User.update_user(student_id, full_name, email, phone, user['is_active'])
        session['full_name'] = full_name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', user=user)


@student_bp.route('/change-password', methods=['GET', 'POST'])
@login_required(role='student')
def change_password():
    student_id = session.get('user_id')

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        user = User.find_by_id(student_id)

        if not check_password_hash(user['password_hash'], current_password):
            flash('Your current password is incorrect.', 'danger')
            return render_template('student/change_password.html')

        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'danger')
            return render_template('student/change_password.html')

        if new_password != confirm_password:
            flash('New password and confirmation do not match.', 'danger')
            return render_template('student/change_password.html')

        User.update_password(student_id, generate_password_hash(new_password))
        Notification.create(student_id, 'Password Changed',
                             'Your password was changed successfully. If this wasn\'t you, contact the admin immediately.')
        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard.student_dashboard'))

    return render_template('student/change_password.html')
