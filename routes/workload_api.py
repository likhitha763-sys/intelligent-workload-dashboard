from datetime import date
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from services.workload_service import (
    calculate_overall_workload,
    calculate_item_urgency_score,
    get_top_recommendation,
    generate_smart_daily_plan,
    get_subject_workload_breakdown,
    generate_intelligent_recommendations
)
from models import Task, Assignment

workload_api_bp = Blueprint('workload_api', __name__, url_prefix='/api/workload')

@workload_api_bp.route('', methods=['GET'])
@login_required
def get_workload():
    """GET /api/workload - Overall workload score and metrics summary."""
    workload = calculate_overall_workload(current_user.id)
    return jsonify({
        'status': 'success',
        'data': workload
    })


@workload_api_bp.route('/priority', methods=['GET'])
@login_required
def get_priority_list():
    """GET /api/workload/priority - Prioritized pending items sorted by urgency."""
    today = date.today()
    pending_tasks = Task.query.filter(Task.user_id == current_user.id, Task.status != 'Completed').all()
    pending_assigns = Assignment.query.filter(Assignment.user_id == current_user.id, Assignment.status != 'Submitted').all()

    items = []
    for t in pending_tasks:
        score = calculate_item_urgency_score('Task', t, today)
        items.append({
            'id': t.id,
            'type': 'Task',
            'title': t.title,
            'subject': t.subject.name if t.subject else 'General',
            'deadline': t.deadline.strftime('%Y-%m-%d') if t.deadline else None,
            'priority': t.priority,
            'difficulty': t.difficulty,
            'estimated_hours': t.estimated_hours,
            'urgency_score': score
        })

    for a in pending_assigns:
        score = calculate_item_urgency_score('Assignment', a, today)
        items.append({
            'id': a.id,
            'type': 'Assignment',
            'title': a.title,
            'subject': a.subject.name if a.subject else 'General',
            'deadline': a.deadline.strftime('%Y-%m-%d') if a.deadline else None,
            'priority': 'High' if a.difficulty == 'Hard' else 'Medium',
            'difficulty': a.difficulty,
            'estimated_hours': a.estimated_hours,
            'urgency_score': score
        })

    items.sort(key=lambda x: x['urgency_score'], reverse=True)
    return jsonify({
        'status': 'success',
        'count': len(items),
        'data': items
    })


@workload_api_bp.route('/recommendation', methods=['GET'])
@login_required
def get_recommendation():
    """GET /api/workload/recommendation - Top priority item and dynamic advice."""
    top = get_top_recommendation(current_user.id)
    recs = generate_intelligent_recommendations(current_user.id)
    return jsonify({
        'status': 'success',
        'top_recommendation': top,
        'recommendations': recs
    })


@workload_api_bp.route('/daily-plan', methods=['GET'])
@login_required
def get_daily_plan():
    """GET /api/workload/daily-plan - Generated smart daily study schedule."""
    plan = generate_smart_daily_plan(current_user.id)
    return jsonify({
        'status': 'success',
        'count': len(plan),
        'data': plan
    })


@workload_api_bp.route('/subjects', methods=['GET'])
@login_required
def get_subject_workload():
    """GET /api/workload/subjects - Per-subject workload scores and statistics."""
    subjects_data = get_subject_workload_breakdown(current_user.id)
    return jsonify({
        'status': 'success',
        'count': len(subjects_data),
        'data': subjects_data
    })
