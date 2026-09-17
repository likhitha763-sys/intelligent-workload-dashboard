from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.workload_service import calculate_overall_workload, get_subject_workload_breakdown
from models import Task, Assignment, Attendance, Subject

placeholder_bp = Blueprint('placeholder', __name__)

@placeholder_bp.route('/analytics')
@login_required
def analytics():
    """Renders comprehensive workload and study analytics page."""
    workload = calculate_overall_workload(current_user.id)
    subject_data = get_subject_workload_breakdown(current_user.id)
    
    # Task status distribution
    tasks_not_started = Task.query.filter_by(user_id=current_user.id, status='Not Started').count()
    tasks_in_progress = Task.query.filter_by(user_id=current_user.id, status='In Progress').count()
    tasks_completed = Task.query.filter_by(user_id=current_user.id, status='Completed').count()
    tasks_overdue = Task.query.filter_by(user_id=current_user.id, status='Overdue').count()

    # Assignment status distribution
    assign_not_started = Assignment.query.filter_by(user_id=current_user.id, status='Not Started').count()
    assign_in_progress = Assignment.query.filter_by(user_id=current_user.id, status='In Progress').count()
    assign_submitted = Assignment.query.filter_by(user_id=current_user.id, status='Submitted').count()
    assign_late = Assignment.query.filter_by(user_id=current_user.id, status='Late').count()

    # Attendance by subject
    attendances = Attendance.query.filter_by(user_id=current_user.id).all()
    att_labels = [att.subject.name for att in attendances] if attendances else []
    att_pcts = [att.percentage for att in attendances] if attendances else []

    return render_template(
        'analytics.html',
        workload=workload,
        subject_data=subject_data,
        task_stats=[tasks_not_started, tasks_in_progress, tasks_completed, tasks_overdue],
        assign_stats=[assign_not_started, assign_in_progress, assign_submitted, assign_late],
        att_labels=att_labels,
        att_pcts=att_pcts
    )
