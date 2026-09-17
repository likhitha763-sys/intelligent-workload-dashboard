import calendar
from datetime import date, datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import Task, Assignment, Exam, StudySession
from services.planner_service import generate_intelligent_study_plan

calendar_bp = Blueprint('calendar_module', __name__)

@calendar_bp.route('/calendar', methods=['GET'])
@login_required
def calendar_view():
    """Renders the monthly academic calendar displaying tasks, assignments, exams, and study sessions."""
    today = date.today()
    
    try:
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # Boundary handling for months
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Navigation months
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = calendar.month_name[month]
    month_cal = calendar.monthcalendar(year, month)

    # Query events for current user
    first_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last_date = date(year, month, last_day)

    tasks = Task.query.filter(Task.user_id == current_user.id, Task.deadline >= first_date, Task.deadline <= last_date).all()
    assignments = Assignment.query.filter(Assignment.user_id == current_user.id, Assignment.deadline >= first_date, Assignment.deadline <= last_date).all()
    exams = Exam.query.filter(Exam.user_id == current_user.id, Exam.exam_date >= first_date, Exam.exam_date <= last_date).all()

    # Map events by day number
    events_by_day = {}

    for t in tasks:
        day = t.deadline.day
        events_by_day.setdefault(day, []).append({
            'type': 'Task',
            'title': t.title,
            'subject': t.subject.name if t.subject else 'General',
            'badge': 'primary',
            'status': t.status,
            'priority': t.priority,
            'hours': t.estimated_hours
        })

    for a in assignments:
        day = a.deadline.day
        events_by_day.setdefault(day, []).append({
            'type': 'Assignment',
            'title': a.title,
            'subject': a.subject.name if a.subject else 'General',
            'badge': 'warning text-dark',
            'status': a.status,
            'priority': a.difficulty,
            'hours': a.estimated_hours
        })

    for e in exams:
        day = e.exam_date.day
        events_by_day.setdefault(day, []).append({
            'type': 'Exam',
            'title': f"Exam: {e.subject.name if e.subject else 'General'}",
            'subject': e.subject.name if e.subject else 'General',
            'badge': 'danger',
            'status': f"{e.prep_percentage}% Prepared",
            'priority': e.difficulty,
            'hours': e.exam_time or 'N/A'
        })

    return render_template(
        'calendar.html',
        year=year,
        month=month,
        month_name=month_name,
        month_cal=month_cal,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        events_by_day=events_by_day,
        today=today
    )
