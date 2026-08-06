"""
File: app/utils.py
Small shared helpers used across multiple routes.
"""

import os
import io
import re
import base64
import uuid
import qrcode
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

IST_OFFSET = timedelta(hours=5, minutes=30)


def now_ist():
    """
    Current time as a naive datetime representing India Standard Time.

    Why this exists: the database session is set to IST (see config.py),
    so NOW() in SQL queries returns IST. But Python's own datetime.now()
    depends on the server's system timezone (often UTC on cloud hosts like
    Render), which would silently be 5 hours 30 minutes off from what's
    stored/compared in the database. Using this everywhere Python needs
    "now" for something that's saved to or compared against the database
    keeps both sides consistent.
    """
    return datetime.utcnow() + IST_OFFSET

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE_MB = 5


def save_uploaded_image(file_storage, subfolder):
    """
    Save an uploaded image file (profile photo, college logo, etc.) under
    app/static/uploads/<subfolder>/ with a random filename.

    NOTE: on hosts with an ephemeral filesystem (like Render's free tier),
    files saved here get wiped on every restart/redeploy. Use
    read_image_for_db() instead for anything that needs to survive that —
    this function is kept for local development only.

    Returns None if no file was actually chosen.
    Raises ValueError if the file type isn't an allowed image format.
    """
    if not file_storage or file_storage.filename == '':
        return None

    extension = file_storage.filename.rsplit('.', 1)[-1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('Invalid file type. Allowed: ' + ', '.join(ALLOWED_IMAGE_EXTENSIONS))

    # Random filename avoids collisions and keeps things simple/secure
    filename = secure_filename(f'{uuid.uuid4().hex}.{extension}')

    folder_path = os.path.join('app', 'static', 'uploads', subfolder)
    os.makedirs(folder_path, exist_ok=True)

    file_storage.save(os.path.join(folder_path, filename))

    # This is the path used with url_for('static', filename=...)
    return f'uploads/{subfolder}/{filename}'


def read_image_for_db(file_storage):
    """
    Read an uploaded image file into raw bytes so it can be stored directly
    in the database (as a LONGBLOB) instead of on disk. This is what makes
    the college logo and profile photos survive restarts/redeploys on hosts
    like Render, whose local filesystem gets wiped every time.

    Returns (image_bytes, mimetype) — both None if no file was chosen.
    Raises ValueError if the file type isn't an allowed image format.
    """
    if not file_storage or file_storage.filename == '':
        return None, None

    extension = file_storage.filename.rsplit('.', 1)[-1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError('Invalid file type. Allowed: ' + ', '.join(ALLOWED_IMAGE_EXTENSIONS))

    mimetype = file_storage.mimetype or f'image/{extension}'
    image_bytes = file_storage.read()
    return image_bytes, mimetype


def generate_qr_code_base64(data):
    """
    Turn any text (e.g. a result summary or student ID info) into a QR code image,
    returned as a base64 string ready to drop straight into an <img> tag —
    no need to save a file to disk for this.
    """
    qr_image = qrcode.make(data)
    buffer = io.BytesIO()
    qr_image.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def natural_sort_key(value):
    """
    Sort key that puts registration numbers in true numeric/alphabetical order,
    whether they're plain numbers ("1", "2", "10") or mixed ("2024CS1001").
    Without this, plain string sorting would wrongly put "10" before "2".
    """
    value = value or ''
    return [int(chunk) if chunk.isdigit() else chunk.lower()
            for chunk in re.split(r'(\d+)', value)]
