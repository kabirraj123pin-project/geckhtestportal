"""
File: app/models/report.py
Powers the Admin Reports page: filterable results across the whole
system (by date range, department, subject, teacher), plus summary
stats and subject-wise / teacher-wise breakdowns.
"""

from app import mysql


# Shared FROM/JOIN clause used by every report query below —
# joins results to the student, the test, its subject/department, and its teacher.
_BASE_FROM = """
    FROM results
    JOIN users student ON results.student_id = student.id
    JOIN tests ON results.test_id = tests.id
    LEFT JOIN subjects ON tests.subject_id = subjects.id
    LEFT JOIN departments ON subjects.department_id = departments.id
    LEFT JOIN users teacher ON tests.teacher_id = teacher.id
"""


def _build_where(filters):
    """Turn a dict of optional filters into a SQL WHERE clause + matching params list"""
    clauses = ['1=1']
    params = []

    if filters.get('date_from'):
        clauses.append('results.submitted_at >= %s')
        params.append(filters['date_from'])

    if filters.get('date_to'):
        clauses.append('results.submitted_at <= %s')
        params.append(filters['date_to'] + ' 23:59:59')

    if filters.get('department_id'):
        clauses.append('departments.id = %s')
        params.append(filters['department_id'])

    if filters.get('subject_id'):
        clauses.append('subjects.id = %s')
        params.append(filters['subject_id'])

    if filters.get('teacher_id'):
        clauses.append('teacher.id = %s')
        params.append(filters['teacher_id'])

    return ' AND '.join(clauses), params


class Report:

    @staticmethod
    def get_results(filters):
        """The detailed, row-by-row report: every matching test attempt"""
        where_clause, params = _build_where(filters)
        cursor = mysql.connection.cursor()
        cursor.execute(
            f"""SELECT results.score, results.total_marks, results.percentage, results.submitted_at,
                       student.full_name AS student_name,
                       tests.title AS test_title,
                       subjects.name AS subject_name,
                       teacher.full_name AS teacher_name
                {_BASE_FROM}
                WHERE {where_clause}
                ORDER BY results.submitted_at DESC""",
            params
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    @staticmethod
    def get_summary(filters):
        """High-level numbers for the summary cards at the top of the report"""
        where_clause, params = _build_where(filters)
        cursor = mysql.connection.cursor()
        cursor.execute(
            f"""SELECT COUNT(DISTINCT tests.id) AS tests_conducted,
                       COUNT(results.id) AS total_attempts,
                       AVG(results.percentage) AS avg_percentage,
                       SUM(CASE WHEN results.percentage >= 40 THEN 1 ELSE 0 END) AS pass_count
                {_BASE_FROM}
                WHERE {where_clause}""",
            params
        )
        row = cursor.fetchone()
        cursor.close()

        total = row['total_attempts'] or 0
        pass_count = row['pass_count'] or 0

        return {
            'tests_conducted': row['tests_conducted'] or 0,
            'total_attempts': total,
            'average_percentage': round(row['avg_percentage'], 1) if row['avg_percentage'] else 0,
            'pass_percentage': round((pass_count / total) * 100, 1) if total else 0,
        }

    @staticmethod
    def get_subject_wise_summary(filters):
        where_clause, params = _build_where(filters)
        cursor = mysql.connection.cursor()
        cursor.execute(
            f"""SELECT COALESCE(subjects.name, 'General') AS subject_name,
                       COUNT(results.id) AS attempts,
                       AVG(results.percentage) AS avg_percentage
                {_BASE_FROM}
                WHERE {where_clause}
                GROUP BY subjects.id
                ORDER BY attempts DESC""",
            params
        )
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            row['avg_percentage'] = round(row['avg_percentage'], 1) if row['avg_percentage'] else 0
        return rows

    @staticmethod
    def get_teacher_wise_summary(filters):
        where_clause, params = _build_where(filters)
        cursor = mysql.connection.cursor()
        cursor.execute(
            f"""SELECT COALESCE(teacher.full_name, 'Unassigned') AS teacher_name,
                       COUNT(DISTINCT tests.id) AS tests_conducted,
                       COUNT(results.id) AS attempts,
                       AVG(results.percentage) AS avg_percentage
                {_BASE_FROM}
                WHERE {where_clause}
                GROUP BY teacher.id
                ORDER BY attempts DESC""",
            params
        )
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            row['avg_percentage'] = round(row['avg_percentage'], 1) if row['avg_percentage'] else 0
        return rows
