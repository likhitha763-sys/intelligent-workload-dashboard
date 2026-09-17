from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Subject, Task, Assignment, Exam
from services.workload_service import (
    calculate_overall_workload,
    get_top_recommendation,
    generate_smart_daily_plan,
    get_subject_workload_breakdown,
    calculate_deadline_pressure
)
from services.ai_insights_service import generate_categorized_ai_insights
from services.attendance_service import get_subject_attendance_summary

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    """Redirects to dashboard if authenticated, else to login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Renders comprehensive student dashboard with all Stage 4 academic workload components."""
    today = date.today()

    workload_data = calculate_overall_workload(current_user.id, today)
    top_rec = get_top_recommendation(current_user.id, today)
    daily_plan = generate_smart_daily_plan(current_user.id, today)
    subject_workloads = get_subject_workload_breakdown(current_user.id, today)
    ai_insights = generate_categorized_ai_insights(current_user.id, today)
    attendance_records = get_subject_attendance_summary(current_user.id)

    # Calculate weekly study hours estimate
    pending_tasks = Task.query.filter(Task.user_id == current_user.id, Task.status != 'Completed').all()
    pending_assigns = Assignment.query.filter(Assignment.user_id == current_user.id, Assignment.status != 'Submitted').all()
    weekly_study_hours = round(sum(t.estimated_hours or 1.0 for t in pending_tasks) + sum(a.estimated_hours or 2.0 for a in pending_assigns), 1)

    # Urgent deadlines
    urgent_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status != 'Completed',
        Task.deadline <= (today + timedelta(days=7))
    ).order_by(Task.deadline.asc()).all()

    urgent_assignments = Assignment.query.filter(
        Assignment.user_id == current_user.id,
        Assignment.status != 'Submitted',
        Assignment.deadline <= (today + timedelta(days=7))
    ).order_by(Assignment.deadline.asc()).all()

    urgent_deadlines = []
    for t in urgent_tasks:
        urgent_deadlines.append({
            'type': 'Task',
            'title': t.title,
            'subject': t.subject.name if t.subject else 'General',
            'deadline': t.deadline,
            'pressure': calculate_deadline_pressure(t.deadline, today)
        })
    for a in urgent_assignments:
        urgent_deadlines.append({
            'type': 'Assignment',
            'title': a.title,
            'subject': a.subject.name if a.subject else 'General',
            'deadline': a.deadline,
            'pressure': calculate_deadline_pressure(a.deadline, today)
        })

    urgent_deadlines.sort(key=lambda x: x['deadline'] if x['deadline'] else today)

    return render_template(
        'dashboard.html',
        today=today,
        workload=workload_data,
        top_recommendation=top_rec,
        daily_plan=daily_plan,
        subject_workloads=subject_workloads,
        ai_insights=ai_insights[:4],
        attendance_records=attendance_records[:4],
        weekly_study_hours=weekly_study_hours,
        urgent_deadlines=urgent_deadlines[:6]
    )
