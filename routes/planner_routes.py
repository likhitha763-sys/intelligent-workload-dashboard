from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from services.planner_service import get_or_create_preferences, generate_intelligent_study_plan

planner_bp = Blueprint('planner', __name__)

@planner_bp.route('/study-planner', methods=['GET'])
@login_required
def study_planner():
    """Renders the Intelligent Study Planner page with custom preferences and schedule."""
    pref = get_or_create_preferences(current_user.id)
    schedule = generate_intelligent_study_plan(current_user.id)
    return render_template('study_planner.html', pref=pref, schedule=schedule)


@planner_bp.route('/study-planner/generate', methods=['POST'])
@login_required
def generate_plan():
    """Saves updated study preferences and generates an updated schedule."""
    pref = get_or_create_preferences(current_user.id)
    
    pref.available_hours_per_day = request.form.get('available_hours_per_day', type=float, default=4.0)
    pref.preferred_start_time = request.form.get('preferred_start_time', '09:00').strip()
    pref.preferred_end_time = request.form.get('preferred_end_time', '21:00').strip()
    pref.break_duration_mins = request.form.get('break_duration_mins', type=int, default=15)
    
    db.session.commit()
    flash('Study Planner schedule generated based on your academic workload!', 'success')
    return redirect(url_for('planner.study_planner'))
