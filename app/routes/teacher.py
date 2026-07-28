"""
File: app/routes/teacher.py
Everything a Teacher can do with Tests:
Create, Edit, Delete, Add Questions, Delete Questions, Publish/Cancel.
"""

import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from app.models.test import Test
from app.models.question import Question, Option
from app.models.subject import Subject
from app.models.result import Result
from app.models.student_answer import StudentAnswer
from app.models.notification import Notification
from app.models.user import User
from app.utils import natural_sort_key
from app.routes.dashboard import login_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


# =====================================================
# TEST LIST
# =====================================================

@teacher_bp.route('/tests')
@login_required(role='teacher')
def test_list():
    teacher_id = session.get('user_id')
    tests = Test.get_all_by_teacher(teacher_id)
    return render_template('teacher/test_list.html', tests=tests)


# =====================================================
# CREATE / EDIT TEST (basic details)
# =====================================================

@teacher_bp.route('/tests/create', methods=['GET', 'POST'])
@login_required(role='teacher')
def test_create():
    subjects = Subject.get_all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject_id = request.form.get('subject_id') or None
        duration_minutes = request.form.get('duration_minutes', '30')
        negative_marking = request.form.get('negative_marking', '0')
        start_time = request.form.get('start_time') or None
        end_time = request.form.get('end_time') or None

        if not title:
            flash('Test title is required.', 'danger')
            return render_template('teacher/test_form.html', subjects=subjects, test=None)

        teacher_id = session.get('user_id')
        test_id = Test.create(title, subject_id, teacher_id, duration_minutes,
                               negative_marking, start_time, end_time)

        flash('Test created! Now add some questions to it.', 'success')
        return redirect(url_for('teacher.test_questions', test_id=test_id))

    return render_template('teacher/test_form.html', subjects=subjects, test=None)


@teacher_bp.route('/tests/<int:test_id>/edit', methods=['GET', 'POST'])
@login_required(role='teacher')
def test_edit(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    subjects = Subject.get_all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject_id = request.form.get('subject_id') or None
        duration_minutes = request.form.get('duration_minutes', '30')
        negative_marking = request.form.get('negative_marking', '0')
        start_time = request.form.get('start_time') or None
        end_time = request.form.get('end_time') or None

        if not title:
            flash('Test title is required.', 'danger')
            return render_template('teacher/test_form.html', subjects=subjects, test=test)

        Test.update(test_id, title, subject_id, duration_minutes,
                    negative_marking, start_time, end_time)
        flash('Test details updated.', 'success')
        return redirect(url_for('teacher.test_list'))

    return render_template('teacher/test_form.html', subjects=subjects, test=test)


@teacher_bp.route('/tests/<int:test_id>/delete', methods=['POST'])
@login_required(role='teacher')
def test_delete(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
    else:
        Test.delete(test_id)
        flash('Test deleted.', 'info')
    return redirect(url_for('teacher.test_list'))


@teacher_bp.route('/tests/<int:test_id>/publish', methods=['POST'])
@login_required(role='teacher')
def test_publish(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    question_count = Question.count_by_test(test_id)
    if question_count == 0:
        flash('You must add at least one question before publishing.', 'warning')
        return redirect(url_for('teacher.test_questions', test_id=test_id))

    Test.set_status(test_id, 'published')

    # Let every student know a new test is available (or scheduled, if it has a start time)
    student_ids = [s['id'] for s in User.get_all_by_role('student')]
    if test['start_time']:
        message = f"'{test['title']}' is scheduled to start on {test['start_time'].strftime('%d %b %Y, %I:%M %p')}."
    else:
        message = f"'{test['title']}' is now available to attempt."
    Notification.create_for_many(student_ids, 'New Test Published', message)

    flash('Test published! Students will now be able to see it.', 'success')
    return redirect(url_for('teacher.test_list'))


@teacher_bp.route('/tests/<int:test_id>/cancel', methods=['POST'])
@login_required(role='teacher')
def test_cancel(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
    else:
        Test.set_status(test_id, 'cancelled')
        flash('Test cancelled.', 'info')
    return redirect(url_for('teacher.test_list'))


# =====================================================
# QUESTIONS (inside a test)
# =====================================================

@teacher_bp.route('/tests/<int:test_id>/questions')
@login_required(role='teacher')
def test_questions(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    questions = Question.get_all_by_test(test_id)
    return render_template('teacher/test_questions.html', test=test, questions=questions)


@teacher_bp.route('/tests/<int:test_id>/questions/add', methods=['POST'])
@login_required(role='teacher')
def question_add(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    question_text = request.form.get('question_text', '').strip()
    question_type = request.form.get('question_type', 'single_choice')
    marks = request.form.get('marks', '1')

    if not question_text:
        flash('Question text cannot be empty.', 'danger')
        return redirect(url_for('teacher.test_questions', test_id=test_id))

    try:
        marks = int(marks)
    except ValueError:
        marks = 1

    question_id = Question.create(test_id, question_text, question_type, marks)

    # ---- Handle answer options based on question type ----
    if question_type in ('single_choice', 'multiple_choice'):
        option_texts = request.form.getlist('option_text[]')
        correct_indexes = set(request.form.getlist('correct_options'))

        for index, option_text in enumerate(option_texts):
            option_text = option_text.strip()
            if option_text:  # skip empty option rows
                is_correct = 1 if str(index) in correct_indexes else 0
                Option.create(question_id, option_text, is_correct)

    elif question_type == 'true_false':
        correct_answer = request.form.get('correct_option')  # 'true' or 'false'
        Option.create(question_id, 'True', 1 if correct_answer == 'true' else 0)
        Option.create(question_id, 'False', 1 if correct_answer == 'false' else 0)

    elif question_type in ('fill_blank', 'numerical'):
        answer_text = request.form.get('answer_text', '').strip()
        if answer_text:
            Option.create(question_id, answer_text, 1)

    # Keep the test's total_marks in sync with its questions
    Test.recalculate_total_marks(test_id)

    flash('Question added.', 'success')
    return redirect(url_for('teacher.test_questions', test_id=test_id))


@teacher_bp.route('/tests/<int:test_id>/questions/<int:question_id>/delete', methods=['POST'])
@login_required(role='teacher')
def question_delete(test_id, question_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    Question.delete(question_id)
    Test.recalculate_total_marks(test_id)

    flash('Question removed.', 'info')
    return redirect(url_for('teacher.test_questions', test_id=test_id))


# =====================================================
# RESULTS, LEADERBOARD & QUESTION ANALYSIS
# =====================================================

@teacher_bp.route('/tests/<int:test_id>/results')
@login_required(role='teacher')
def test_results(test_id):
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    leaderboard = Result.get_all_for_test(test_id)
    stats = Result.get_stats_for_test(test_id)

    questions = Question.get_all_by_test(test_id)
    question_stats = StudentAnswer.get_question_wise_stats(test_id, questions)

    return render_template('teacher/test_results.html',
                            test=test, leaderboard=leaderboard,
                            stats=stats, question_stats=question_stats)


@teacher_bp.route('/tests/<int:test_id>/results/export')
@login_required(role='teacher')
def test_results_export(test_id):
    """Download the leaderboard as a CSV file (opens directly in Excel)"""
    test = Test.get_by_id(test_id)
    if not test or test['teacher_id'] != session.get('user_id'):
        flash('Test not found.', 'danger')
        return redirect(url_for('teacher.test_list'))

    leaderboard = Result.get_all_for_test(test_id)

    # Sort by registration number for the export, so it's easy to look up a
    # specific student's result — the on-screen leaderboard stays score-sorted.
    # natural_sort_key ensures true ascending order (1, 2, 3, 10) even if
    # registration numbers are plain numbers or mixed text+numbers.
    leaderboard_by_reg_no = sorted(
        leaderboard, key=lambda r: natural_sort_key(r['student_registration_number'])
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Registration Number', 'Student Name', 'Score', 'Total Marks', 'Percentage', 'Submitted At'])

    for row in leaderboard_by_reg_no:
        writer.writerow([
            row['student_registration_number'] or '—', row['student_name'], row['score'],
            row['total_marks'], row['percentage'], row['submitted_at']
        ])

    response = Response(output.getvalue(), mimetype='text/csv')
    safe_title = test['title'].replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename=results_{safe_title}.csv'
    return response
