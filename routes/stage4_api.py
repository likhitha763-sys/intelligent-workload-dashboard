from datetime import date
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Attendance, StudyPreference, Task, Assignment, Exam
from services.planner_service import get_or_create_preferences, generate_intelligent_study_plan
from services.ai_insights_service import generate_categorized_ai_insights
from services.attendance_service import get_subject_attendance_summary
from services.workload_service import calculate_overall_workload, get_subject_workload_breakdown

stage4_api_bp = Blueprint('stage4_api', __name__, url_prefix='/api')

# 1. PLANNER API
@stage4_api_bp.route('/planner', methods=['GET'])
@login_required
def get_planner_api():
    schedule = generate_intelligent_study_plan(current_user.id)
    return jsonify({'status': 'success', 'data': schedule})

@stage4_api_bp.route('/planner/generate', methods=['POST'])
@login_required
def generate_planner_api():
    schedule = generate_intelligent_study_plan(current_user.id)
    return jsonify({'status': 'success', 'message': 'Plan generated', 'data': schedule})

# 2. INSIGHTS API
@stage4_api_bp.route('/insights', methods=['GET'])
@login_required
def get_insights_api():
    insights = generate_categorized_ai_insights(current_user.id)
    return jsonify({'status': 'success', 'data': insights})

# 3. CALENDAR API
@stage4_api_bp.route('/calendar', methods=['GET'])
@login_required
def get_calendar_api():
    today = date.today()
    tasks = Task.query.filter(Task.user_id == current_user.id).all()
    assignments = Assignment.query.filter(Assignment.user_id == current_user.id).all()
    exams = Exam.query.filter(Exam.user_id == current_user.id).all()

    events = []
    for t in tasks:
        if t.deadline:
            events.append({'type': 'Task', 'title': t.title, 'date': t.deadline.strftime('%Y-%m-%d'), 'status': t.status})
    for a in assignments:
        if a.deadline:
            events.append({'type': 'Assignment', 'title': a.title, 'date': a.deadline.strftime('%Y-%m-%d'), 'status': a.status})
    for e in exams:
        events.append({'type': 'Exam', 'title': f"Exam ({e.subject.name if e.subject else 'General'})", 'date': e.exam_date.strftime('%Y-%m-%d'), 'status': f"{e.prep_percentage}% prepared"})

    return jsonify({'status': 'success', 'count': len(events), 'data': events})

# 4. ATTENDANCE API
@stage4_api_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance_api():
    if request.method == 'POST':
        data = request.get_json() or {}
        subject_id = data.get('subject_id')
        total = data.get('total_classes', 0)
        attended = data.get('attended_classes', 0)
        
        att = Attendance.query.filter_by(user_id=current_user.id, subject_id=subject_id).first()
        if not att:
            att = Attendance(user_id=current_user.id, subject_id=subject_id)
            db.session.add(att)
            
        att.total_classes = max(0, total)
        att.attended_classes = max(0, attended)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Attendance saved'})

    records = get_subject_attendance_summary(current_user.id)
    return jsonify({'status': 'success', 'data': records})

@stage4_api_bp.route('/attendance/<int:att_id>', methods=['PUT', 'DELETE'])
@login_required
def attendance_detail_api(att_id):
    att = Attendance.query.filter_by(id=att_id, user_id=current_user.id).first_or_404()
    if request.method == 'DELETE':
        att.total_classes = 0
        att.attended_classes = 0
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Attendance reset'})
    
    data = request.get_json() or {}
    att.total_classes = max(0, data.get('total_classes', att.total_classes))
    att.attended_classes = max(0, data.get('attended_classes', att.attended_classes))
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Attendance updated'})

# 5. ANALYTICS API
@stage4_api_bp.route('/analytics', methods=['GET'])
@login_required
def get_analytics_api():
    workload = calculate_overall_workload(current_user.id)
    subject_data = get_subject_workload_breakdown(current_user.id)
    return jsonify({'status': 'success', 'workload': workload, 'subjects': subject_data})

# 6. PROFILE API
@stage4_api_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile_api():
    if request.method == 'PUT':
        data = request.get_json() or {}
        current_user.student_id_no = data.get('student_id_no', current_user.student_id_no)
        current_user.college = data.get('college', current_user.college)
        current_user.department = data.get('department', current_user.department)
        current_user.year = data.get('year', current_user.year)
        current_user.semester = data.get('semester', current_user.semester)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Profile updated'})

    return jsonify({
        'status': 'success',
        'data': {
            'username': current_user.username,
            'email': current_user.email,
            'student_id_no': current_user.student_id_no,
            'college': current_user.college,
            'department': current_user.department,
            'year': current_user.year,
            'semester': current_user.semester
        }
    })

# 7. SETTINGS API
@stage4_api_bp.route('/settings', methods=['GET', 'PUT'])
@login_required
def settings_api():
    pref = get_or_create_preferences(current_user.id)
    if request.method == 'PUT':
        data = request.get_json() or {}
        pref.available_hours_per_day = data.get('available_hours_per_day', pref.available_hours_per_day)
        pref.preferred_start_time = data.get('preferred_start_time', pref.preferred_start_time)
        pref.preferred_end_time = data.get('preferred_end_time', pref.preferred_end_time)
        pref.break_duration_mins = data.get('break_duration_mins', pref.break_duration_mins)
        pref.theme = data.get('theme', pref.theme)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Settings saved'})

    return jsonify({
        'status': 'success',
        'data': {
            'available_hours_per_day': pref.available_hours_per_day,
            'preferred_start_time': pref.preferred_start_time,
            'preferred_end_time': pref.preferred_end_time,
            'break_duration_mins': pref.break_duration_mins,
            'theme': pref.theme
        }
    })
