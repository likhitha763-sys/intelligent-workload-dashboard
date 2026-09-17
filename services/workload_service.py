from datetime import date, datetime, timedelta
from models import db, Subject, Task, Assignment, Exam

def calculate_deadline_pressure(deadline, today=None):
    """Calculates deadline pressure category based on deadline proximity."""
    if today is None:
        today = date.today()
    if not deadline:
        return 'Low'
    
    days = (deadline - today).days
    if days < 0:
        return 'Critical (Overdue)'
    elif days <= 1:
        return 'Critical'
    elif days <= 3:
        return 'High'
    elif days <= 7:
        return 'Moderate'
    else:
        return 'Low'


def calculate_item_urgency_score(item_type, item, today=None):
    """Calculates a numerical urgency score for sorting pending tasks and assignments."""
    if today is None:
        today = date.today()

    priority_map = {'High': 1.5, 'Medium': 1.0, 'Low': 0.7}
    difficulty_map = {'Hard': 1.5, 'Medium': 1.0, 'Easy': 0.7}

    p_mult = priority_map.get(getattr(item, 'priority', 'Medium'), 1.0)
    d_mult = difficulty_map.get(getattr(item, 'difficulty', 'Medium'), 1.0)
    est_hours = getattr(item, 'estimated_hours', 1.0) or 1.0

    deadline = item.deadline
    if deadline:
        days = (deadline - today).days
        if days < 0:
            prox_score = 40 + min(abs(days) * 5, 25)  # Overdue penalty
        elif days == 0:
            prox_score = 35
        elif days == 1:
            prox_score = 28
        elif days <= 3:
            prox_score = 20
        elif days <= 7:
            prox_score = 12
        else:
            prox_score = 5
    else:
        prox_score = 3

    urgency = prox_score + (p_mult * 12) + (d_mult * 10) + min(est_hours * 2.5, 15)
    return round(urgency, 2)


def calculate_overall_workload(user_id, today=None):
    """Calculates overall student workload score (0-100) and status level."""
    if today is None:
        today = date.today()

    pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    pending_assignments = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()
    upcoming_exams = Exam.query.filter(Exam.user_id == user_id, Exam.exam_date >= today).all()

    raw_score = 0.0

    # Task weights
    for task in pending_tasks:
        p_mult = {'High': 1.5, 'Medium': 1.0, 'Low': 0.7}.get(task.priority, 1.0)
        d_mult = {'Hard': 1.4, 'Medium': 1.0, 'Easy': 0.7}.get(task.difficulty, 1.0)
        hours = task.estimated_hours or 1.0
        
        prox = 1.0
        if task.deadline:
            days = (task.deadline - today).days
            if days < 0:
                prox = 2.5
                raw_score += 10.0 # Overdue penalty
            elif days <= 1:
                prox = 2.0
            elif days <= 3:
                prox = 1.5
            elif days <= 7:
                prox = 1.2

        raw_score += hours * p_mult * d_mult * prox * 3.5

    # Assignment weights
    for ass in pending_assignments:
        d_mult = {'Hard': 1.5, 'Medium': 1.0, 'Easy': 0.7}.get(ass.difficulty, 1.0)
        hours = ass.estimated_hours or 2.0
        
        prox = 1.0
        if ass.deadline:
            days = (ass.deadline - today).days
            if days < 0:
                prox = 2.5
                raw_score += 10.0 # Overdue penalty
            elif days <= 1:
                prox = 2.0
            elif days <= 3:
                prox = 1.5
            elif days <= 7:
                prox = 1.2

        raw_score += hours * d_mult * prox * 4.0

    # Exam weights
    for exam in upcoming_exams:
        days = (exam.exam_date - today).days
        prep_def = (100 - (exam.prep_percentage or 0)) / 100.0
        exam_prox = 2.5 if days <= 2 else (1.8 if days <= 7 else 1.1)
        raw_score += 12.0 * prep_def * exam_prox

    # Normalize to 0 - 100 range
    score = min(100, round(raw_score))

    if score >= 85:
        category = 'CRITICAL'
        badge_class = 'danger'
    elif score >= 70:
        category = 'HIGH'
        badge_class = 'warning text-dark'
    elif score >= 40:
        category = 'MODERATE'
        badge_class = 'primary'
    else:
        category = 'LOW'
        badge_class = 'success'

    return {
        'score': score,
        'category': category,
        'badge_class': badge_class,
        'pending_tasks_count': len(pending_tasks),
        'pending_assignments_count': len(pending_assignments),
        'upcoming_exams_count': len(upcoming_exams)
    }


def get_top_recommendation(user_id, today=None):
    """Calculates top urgent task/assignment for 'What Should I Do Now?' widget."""
    if today is None:
        today = date.today()

    pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    pending_assignments = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()

    items = []
    for t in pending_tasks:
        score = calculate_item_urgency_score('Task', t, today)
        items.append({'type': 'Task', 'object': t, 'score': score})

    for a in pending_assignments:
        score = calculate_item_urgency_score('Assignment', a, today)
        items.append({'type': 'Assignment', 'object': a, 'score': score})

    if not items:
        return None

    # Sort descending by urgency score
    items.sort(key=lambda x: x['score'], reverse=True)
    top_item = items[0]
    obj = top_item['object']

    # Generate human-readable reason
    reasons = []
    if obj.deadline:
        days = (obj.deadline - today).days
        if days < 0:
            reasons.append(f"Overdue by {abs(days)} day(s)")
        elif days == 0:
            reasons.append("Due Today")
        elif days == 1:
            reasons.append("Due Tomorrow")
        else:
            reasons.append(f"Due in {days} days")
    
    if hasattr(obj, 'priority') and obj.priority == 'High':
        reasons.append("High Priority")
    if obj.difficulty == 'Hard':
        reasons.append("Hard Difficulty")
    if obj.estimated_hours:
        reasons.append(f"{obj.estimated_hours} hrs estimated")

    reason_str = " + ".join(reasons) if reasons else "Highest calculated urgency score"

    return {
        'id': obj.id,
        'type': top_item['type'],
        'title': obj.title,
        'subject_name': obj.subject.name if obj.subject else 'General',
        'deadline': obj.deadline.strftime('%Y-%m-%d') if obj.deadline else 'None',
        'estimated_hours': getattr(obj, 'estimated_hours', 1.0),
        'reason': reason_str,
        'score': top_item['score']
    }


def generate_smart_daily_plan(user_id, today=None):
    """Generates a realistic time-slotted daily study schedule for top urgent work."""
    if today is None:
        today = date.today()

    pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    pending_assignments = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()

    items = []
    for t in pending_tasks:
        items.append({'title': t.title, 'subject': t.subject.name if t.subject else 'General', 'hours': t.estimated_hours or 1.0, 'score': calculate_item_urgency_score('Task', t, today)})
    for a in pending_assignments:
        items.append({'title': a.title, 'subject': a.subject.name if a.subject else 'General', 'hours': a.estimated_hours or 2.0, 'score': calculate_item_urgency_score('Assignment', a, today)})

    items.sort(key=lambda x: x['score'], reverse=True)

    schedule = []
    current_time = datetime.strptime('09:00', '%H:%M')

    for item in items[:4]:  # Top 4 items max for a single day
        duration_minutes = int(item['hours'] * 60)
        # Cap slot duration at 2 hours max per session
        duration_minutes = min(duration_minutes, 120)
        
        end_time = current_time + timedelta(minutes=duration_minutes)
        slot_str = f"{current_time.strftime('%H:%M')} – {end_time.strftime('%H:%M')}"
        
        schedule.append({
            'time_slot': slot_str,
            'title': item['title'],
            'subject': item['subject'],
            'hours': item['hours']
        })
        
        # Add 30 min break
        current_time = end_time + timedelta(minutes=30)

    return schedule


def get_subject_workload_breakdown(user_id, today=None):
    """Calculates workload metrics separately for each subject of the authenticated student."""
    if today is None:
        today = date.today()

    subjects = Subject.query.filter_by(user_id=user_id).all()
    result = []

    for sub in subjects:
        p_tasks = Task.query.filter(Task.user_id == user_id, Task.subject_id == sub.id, Task.status != 'Completed').all()
        p_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.subject_id == sub.id, Assignment.status != 'Submitted').all()
        u_exams = Exam.query.filter(Exam.user_id == user_id, Exam.subject_id == sub.id, Exam.exam_date >= today).all()

        task_hours = sum(t.estimated_hours or 1.0 for t in p_tasks)
        assign_hours = sum(a.estimated_hours or 2.0 for a in p_assigns)
        total_hours = task_hours + assign_hours

        # Sub-workload score
        sub_raw = (len(p_tasks) * 10) + (len(p_assigns) * 15) + (len(u_exams) * 20) + (total_hours * 5)
        sub_score = min(100, round(sub_raw))

        result.append({
            'id': sub.id,
            'name': sub.name,
            'faculty_name': sub.faculty_name or 'N/A',
            'credits': sub.credits,
            'pending_tasks': len(p_tasks),
            'pending_assignments': len(p_assigns),
            'upcoming_exams': len(u_exams),
            'estimated_hours': round(total_hours, 1),
            'workload_score': sub_score
        })

    return result


def generate_intelligent_recommendations(user_id, today=None):
    """Generates data-driven dynamic recommendations based on database analysis."""
    if today is None:
        today = date.today()

    recs = []

    # 1. Urgent deadlines within 48 hours
    imminent_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed', Task.deadline <= (today + timedelta(days=2))).all()
    imminent_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted', Assignment.deadline <= (today + timedelta(days=2))).all()
    total_imm = len(imminent_tasks) + len(imminent_assigns)

    if total_imm > 0:
        recs.append({
            'icon': 'bi-exclamation-triangle-fill',
            'type': 'danger',
            'text': f"You have {total_imm} deadline(s) occurring within the next 48 hours. Prioritize these immediately."
        })

    # 2. Subject workload distribution check
    subjects = get_subject_workload_breakdown(user_id, today)
    if subjects:
        top_subject = max(subjects, key=lambda x: x['workload_score'])
        if top_subject['workload_score'] >= 50:
            recs.append({
                'icon': 'bi-journal-text',
                'type': 'warning',
                'text': f"Your workload for '{top_subject['name']}' is high ({top_subject['workload_score']}/100 with {top_subject['estimated_hours']} hrs estimated). Focus study sessions here."
            })

    # 3. Overall study capacity estimate
    all_pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    all_pending_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()
    total_est_hours = sum(t.estimated_hours or 1.0 for t in all_pending_tasks) + sum(a.estimated_hours or 2.0 for a in all_pending_assigns)

    if total_est_hours > 0:
        tasks_completable = min(len(all_pending_tasks), int(6.0 / 1.5)) # assuming ~6 study hours available daily
        recs.append({
            'icon': 'bi-clock-history',
            'type': 'info',
            'text': f"You have {round(total_est_hours, 1)} total estimated study hours remaining. You have enough capacity today to finish up to {max(1, tasks_completable)} pending item(s)."
        })

    # 4. Overdue work alert
    overdue_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed', Task.deadline < today).count()
    overdue_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted', Assignment.deadline < today).count()
    if overdue_tasks + overdue_assigns > 0:
        recs.append({
            'icon': 'bi-alarm-fill',
            'type': 'danger',
            'text': f"Warning: You have {overdue_tasks + overdue_assigns} overdue item(s). Complete overdue submissions first to avoid academic penalties."
        })

    if not recs:
        recs.append({
            'icon': 'bi-check-circle-fill',
            'type': 'success',
            'text': "Great job! Your academic workload is balanced and all deadlines are well under control."
        })

    return recs
