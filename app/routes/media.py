"""
File: app/routes/media.py
Serves images that are stored directly in the database (college logo,
profile photos) — instead of as files on disk. This is what makes them
survive server restarts/redeploys on hosts with an ephemeral filesystem
(like Render's free tier).
"""

from flask import Blueprint, Response, abort
from app.models.settings import Settings
from app.models.user import User

media_bp = Blueprint('media', __name__)


@media_bp.route('/media/logo')
def logo():
    settings = Settings.get()
    if not settings or not settings.get('logo_data'):
        abort(404)
    return Response(settings['logo_data'], mimetype=settings['logo_mimetype'] or 'image/png')


@media_bp.route('/media/profile-photo/<int:user_id>')
def profile_photo(user_id):
    user = User.find_by_id(user_id)
    if not user or not user.get('profile_photo_data'):
        abort(404)
    return Response(user['profile_photo_data'], mimetype=user['profile_photo_mimetype'] or 'image/jpeg')
