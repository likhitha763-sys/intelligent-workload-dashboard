from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, StudyPreference
from services.planner_service import get_or_create_preferences

profile_bp = Blueprint('profile_module', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_view():
    """Renders and handles student profile updates."""
    if request.method == 'POST':
        student_id_no = request.form.get('student_id_no', '').strip()
        college = request.form.get('college', '').strip()
        department = request.form.get('department', '').strip()
        year = request.form.get('year', '').strip()
        semester = request.form.get('semester', '').strip()

        current_user.student_id_no = student_id_no
        current_user.college = college
        current_user.department = department
        current_user.year = year
        current_user.semester = semester

        db.session.commit()
        flash('Student profile updated successfully!', 'success')
        return redirect(url_for('profile_module.profile_view'))

    return render_template('profile.html')


@profile_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    """Renders and handles account & study preference settings."""
    pref = get_or_create_preferences(current_user.id)

    if request.method == 'POST':
        pref.available_hours_per_day = request.form.get('available_hours_per_day', type=float, default=4.0)
        pref.preferred_start_time = request.form.get('preferred_start_time', '09:00').strip()
        pref.preferred_end_time = request.form.get('preferred_end_time', '21:00').strip()
        pref.break_duration_mins = request.form.get('break_duration_mins', type=int, default=15)
        pref.theme = request.form.get('theme', 'light')
        pref.notifications_enabled = 'notifications_enabled' in request.form

        db.session.commit()
        flash('Account settings and study preferences saved.', 'success')
        return redirect(url_for('profile_module.settings_view'))

    return render_template('settings.html', pref=pref)
