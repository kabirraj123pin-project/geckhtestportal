"""
File: app/__init__.py
This is the "Application Factory" - the Flask app is created here.
Keeping app creation in one place makes the app easier to organize (MVC pattern).
"""

from flask import Flask
from flask_mysqldb import MySQL
from flask_mail import Mail
from flask_wtf import CSRFProtect
from config.config import Config

# MySQL object - used throughout the app
mysql = MySQL()

# Mail object - used to send OTP emails for password reset
mail = Mail()

# CSRF protection - blocks forged form submissions from other sites
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect MySQL to the app
    mysql.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # ---- Register Blueprints (Routes) ----
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.teacher import teacher_bp
    from app.routes.student import student_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(notifications_bp)

    # ---- Make notification data available to every template automatically ----
    # (so the bell icon in the top bar always has fresh data, without every
    #  single route having to fetch and pass it manually)
    @app.context_processor
    def inject_notifications():
        from flask import session
        from app.models.notification import Notification
        from app.models.settings import Settings
        from app.models.user import User

        context = {'college_settings': Settings.get()}

        if 'user_id' in session:
            context['nav_unread_count'] = Notification.get_unread_count(session['user_id'])
            context['nav_recent_notifications'] = Notification.get_recent(session['user_id'], limit=5)
            current_user = User.find_by_id(session['user_id'])
            context['nav_profile_photo'] = current_user['profile_photo'] if current_user else None
        else:
            context['nav_unread_count'] = 0
            context['nav_recent_notifications'] = []
            context['nav_profile_photo'] = None

        return context

    return app
