"""
File: config/config.py
Central place for all Flask app settings.
Values are loaded from the .env file so secrets never live in the code.
"""

import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Config:
    # Secret key - required to keep Flask sessions secure
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

    # MySQL Database settings
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'college_exam_portal')
    MYSQL_CURSORCLASS = 'DictCursor'   # query results come back as dictionaries

    # Cloud MySQL providers (like Aiven) require an encrypted connection.
    # Two ways to enable it:
    #   MYSQL_SSL_CA=path/to/cert.pem   -> encrypted AND verified against that CA
    #   MYSQL_USE_SSL=true              -> just encrypted, no certificate verification
    #                                      (matches what worked locally with --ssl-mode=REQUIRED)
    _ssl_ca = os.getenv('MYSQL_SSL_CA')
    _use_ssl = os.getenv('MYSQL_USE_SSL', 'false').lower() == 'true'
    if _ssl_ca:
        MYSQL_CUSTOM_OPTIONS = {'ssl': {'ca': _ssl_ca}}
    elif _use_ssl:
        MYSQL_CUSTOM_OPTIONS = {'ssl': {}}

    # Session settings (security)
    PERMANENT_SESSION_LIFETIME = 1800   # session expires after 30 minutes

    # File upload settings
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024   # 5 MB max upload size

    # Email settings (for Forgot Password OTP emails)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')
