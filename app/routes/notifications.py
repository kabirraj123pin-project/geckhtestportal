"""
File: app/routes/notifications.py
View all notifications, and mark them as read.
Works the same way for Admin, Teacher, and Student — the sidebar just
changes based on their role.
"""

from flask import Blueprint, render_template, redirect, url_for, session
from app.models.notification import Notification
from app.routes.dashboard import login_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required()
def list_notifications():
    user_id = session.get('user_id')
    notifications = Notification.get_all(user_id)
    return render_template('notifications/list.html', notifications=notifications)


@notifications_bp.route('/<int:notification_id>/read')
@login_required()
def mark_read(notification_id):
    Notification.mark_as_read(notification_id, session.get('user_id'))
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/mark-all-read')
@login_required()
def mark_all_read():
    Notification.mark_all_as_read(session.get('user_id'))
    return redirect(url_for('notifications.list_notifications'))
