"""
File: app/models/student_answer.py
Saves a student's answer for each question (autosave), and evaluates
the whole test once submitted.

Note on multiple-choice questions: since a student can pick more than
one correct option, we store their selected option IDs as a comma
separated string in `answer_text` (e.g. "12,15") rather than adding a
whole new table — keeps things simple while still working correctly.
"""

from app import mysql


class StudentAnswer:

    @staticmethod
    def save_answer(student_id, test_id, question_id, selected_option_id,
                     answer_text, marked_for_review):
        """
        Insert a new answer, or update it if the student already answered
        this question before (autosave calls this every time an answer changes).
        """
        cursor = mysql.connection.cursor()
        cursor.execute(
            """INSERT INTO student_answers
                   (student_id, test_id, question_id, selected_option_id, answer_text, marked_for_review)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                   selected_option_id = VALUES(selected_option_id),
                   answer_text = VALUES(answer_text),
                   marked_for_review = VALUES(marked_for_review)""",
            (student_id, test_id, question_id, selected_option_id, answer_text, marked_for_review)
        )
        mysql.connection.commit()
        cursor.close()

    @staticmethod
    def get_all_for_attempt(student_id, test_id):
        """Return a dict of {question_id: answer_row} for quick lookup while rendering the exam"""
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM student_answers WHERE student_id = %s AND test_id = %s",
            (student_id, test_id)
        )
        rows = cursor.fetchall()
        cursor.close()
        return {row['question_id']: row for row in rows}

    @staticmethod
    def evaluate_test(student_id, test_id, questions, negative_marking):
        """
        Compare the student's saved answers against the correct answers
        for every question, and return a full breakdown:
        score, total marks, correct/wrong/skipped counts, and per-question detail
        (used both to save the Result and to show the Review Answers screen).
        """
        answers = StudentAnswer.get_all_for_attempt(student_id, test_id)

        score = 0
        correct_count = 0
        wrong_count = 0
        skipped_count = 0
        breakdown = []

        for question in questions:
            answer = answers.get(question['id'])
            options = question['options']
            is_correct = False
            student_display_answer = None

            has_answer = answer and (answer['selected_option_id'] or
                                      (answer['answer_text'] and answer['answer_text'].strip()))

            if not has_answer:
                skipped_count += 1
                breakdown.append({**question, 'student_answer': None, 'is_correct': None})
                continue

            if question['question_type'] == 'single_choice' or question['question_type'] == 'true_false':
                correct_option = next((o for o in options if o['is_correct']), None)
                selected_id = answer['selected_option_id']
                is_correct = correct_option is not None and selected_id == correct_option['id']
                student_display_answer = next(
                    (o['option_text'] for o in options if o['id'] == selected_id), None
                )

            elif question['question_type'] == 'multiple_choice':
                correct_ids = {o['id'] for o in options if o['is_correct']}
                selected_ids = set()
                if answer['answer_text']:
                    selected_ids = {int(x) for x in answer['answer_text'].split(',') if x}
                is_correct = selected_ids == correct_ids and len(selected_ids) > 0
                student_display_answer = ', '.join(
                    o['option_text'] for o in options if o['id'] in selected_ids
                )

            elif question['question_type'] in ('fill_blank', 'numerical'):
                correct_option = next((o for o in options if o['is_correct']), None)
                student_text = (answer['answer_text'] or '').strip().lower()
                correct_text = (correct_option['option_text'] if correct_option else '').strip().lower()
                is_correct = bool(student_text) and student_text == correct_text
                student_display_answer = answer['answer_text']

            if is_correct:
                correct_count += 1
                score += question['marks']
            else:
                wrong_count += 1
                score -= float(negative_marking)

            breakdown.append({**question, 'student_answer': student_display_answer, 'is_correct': is_correct})

        # Score should never go negative overall
        score = max(0, score)

        return {
            'score': score,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'skipped_count': skipped_count,
            'breakdown': breakdown,
        }

    @staticmethod
    def _is_answer_correct(question, answer):
        """
        Shared logic: given one question and one student's saved answer,
        return True (correct), False (wrong), or None (skipped).
        Used both for grading a single student AND for the teacher's
        question-wise analysis across every student.
        """
        options = question['options']
        has_answer = answer and (answer['selected_option_id'] or
                                  (answer['answer_text'] and answer['answer_text'].strip()))
        if not has_answer:
            return None

        if question['question_type'] in ('single_choice', 'true_false'):
            correct_option = next((o for o in options if o['is_correct']), None)
            return correct_option is not None and answer['selected_option_id'] == correct_option['id']

        elif question['question_type'] == 'multiple_choice':
            correct_ids = {o['id'] for o in options if o['is_correct']}
            selected_ids = set()
            if answer['answer_text']:
                selected_ids = {int(x) for x in answer['answer_text'].split(',') if x}
            return selected_ids == correct_ids and len(selected_ids) > 0

        elif question['question_type'] in ('fill_blank', 'numerical'):
            correct_option = next((o for o in options if o['is_correct']), None)
            student_text = (answer['answer_text'] or '').strip().lower()
            correct_text = (correct_option['option_text'] if correct_option else '').strip().lower()
            return bool(student_text) and student_text == correct_text

        return False

    @staticmethod
    def get_question_wise_stats(test_id, questions):
        """
        For every question in the test, count how many students (across ALL
        submitted attempts) got it correct / wrong / skipped. This is what
        powers the teacher's "Question Wise Analysis" report — it shows
        which questions were too easy, too hard, or confusing.
        """
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT student_id FROM results WHERE test_id = %s", (test_id,))
        student_ids = [row['student_id'] for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM student_answers WHERE test_id = %s", (test_id,))
        all_answers = cursor.fetchall()
        cursor.close()

        # Quick lookup: (student_id, question_id) -> answer row
        answer_map = {(row['student_id'], row['question_id']): row for row in all_answers}

        stats = []
        for question in questions:
            correct = wrong = skipped = 0
            for student_id in student_ids:
                answer = answer_map.get((student_id, question['id']))
                outcome = StudentAnswer._is_answer_correct(question, answer)
                if outcome is None:
                    skipped += 1
                elif outcome:
                    correct += 1
                else:
                    wrong += 1

            total = len(student_ids)
            stats.append({
                'question_text': question['question_text'],
                'question_type': question['question_type'],
                'marks': question['marks'],
                'correct': correct,
                'wrong': wrong,
                'skipped': skipped,
                'correct_pct': round((correct / total) * 100, 1) if total else 0,
            })

        return stats
