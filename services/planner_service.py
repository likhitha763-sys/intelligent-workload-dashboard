from datetime import date, datetime, timedelta
from models import db, Task, Assignment, Exam, StudyPreference, StudySession

def get_or_create_preferences(user_id):
    """Retrieves existing study preferences or creates default preferences for student."""
    pref = StudyPreference.query.filter_by(user_id=user_id).first()
    if not pref:
        pref = StudyPreference(user_id=user_id)
        db.session.add(pref)
        db.session.commit()
    return pref


def calculate_planner_rank(item_type, item, today):
    """
    Computes priority rank score according to Stage 4 requirements:
    1. Overdue work (Rank weight 1000+)
    2. Deadlines within 24 hours (Rank weight 800+)
    3. High-priority work (Rank weight 600+)
    4. Upcoming exams (Rank weight 400+)
    5. Difficult tasks (Rank weight 200+)
    6. Lower-priority work (Rank weight 50+)
    """
    rank = 0

    if item_type == 'Exam':
        days = (item.exam_date - today).days
        prep_def = (100 - (item.prep_percentage or 0))
        rank = 400 + (30 - min(days, 30)) * 10 + prep_def
        return rank

    deadline = item.deadline
    if deadline:
        days = (deadline - today).days
        if days < 0:
            rank += 1000 + abs(days) * 20  # 1. Overdue work
        elif days == 0 or days == 1:
            rank += 800 + (1 - days) * 50  # 2. Deadlines within 24h
        elif days <= 3:
            rank += 500
        elif days <= 7:
            rank += 300
        else:
            rank += 100
    else:
        rank += 50

    # 3. High-priority work
    priority = getattr(item, 'priority', 'Medium')
    if priority == 'High':
        rank += 150
    elif priority == 'Medium':
        rank += 75

    # 5. Difficult tasks
    difficulty = getattr(item, 'difficulty', 'Medium')
    if difficulty == 'Hard':
        rank += 100
    elif difficulty == 'Medium':
        rank += 50

    return rank


def generate_intelligent_study_plan(user_id, today=None):
    """
    Generates a realistic daily study schedule based on student's actual preferences,
    prioritizing overdue work, imminent deadlines, high priority, upcoming exams, and difficulty.
    """
    if today is None:
        today = date.today()

    pref = get_or_create_preferences(user_id)
    available_hours = pref.available_hours_per_day or 4.0
    start_time_str = pref.preferred_start_time or '09:00'
    break_mins = pref.break_duration_mins or 15

    # Query uncompleted work
    pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    pending_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()
    upcoming_exams = Exam.query.filter(Exam.user_id == user_id, Exam.exam_date >= today, Exam.exam_date <= (today + timedelta(days=7))).all()

    candidates = []

    for t in pending_tasks:
        rank = calculate_planner_rank('Task', t, today)
        candidates.append({
            'type': 'Task',
            'object': t,
            'title': t.title,
            'subject': t.subject.name if t.subject else 'General',
            'hours': t.estimated_hours or 1.0,
            'rank': rank,
            'reason': f"Task ({t.priority} Priority, {t.difficulty} Difficulty)"
        })

    for a in pending_assigns:
        rank = calculate_planner_rank('Assignment', a, today)
        candidates.append({
            'type': 'Assignment',
            'object': a,
            'title': a.title,
            'subject': a.subject.name if a.subject else 'General',
            'hours': a.estimated_hours or 2.0,
            'rank': rank,
            'reason': f"Assignment ({a.difficulty} Difficulty)"
        })

    for e in upcoming_exams:
        rank = calculate_planner_rank('Exam', e, today)
        sub_name = e.subject.name if e.subject else 'General'
        candidates.append({
            'type': 'Exam',
            'object': e,
            'title': f"Exam Prep: {sub_name}",
            'subject': sub_name,
            'hours': 1.5,
            'rank': rank,
            'reason': f"Exam on {e.exam_date} ({e.prep_percentage}% prepared)"
        })

    # Sort candidates descending by rank
    candidates.sort(key=lambda x: x['rank'], reverse=True)

    # Schedule items into available daily hours
    schedule = []
    accumulated_minutes = 0
    max_minutes = int(available_hours * 60)

    try:
        curr_time = datetime.strptime(start_time_str, '%H:%M')
    except ValueError:
        curr_time = datetime.strptime('09:00', '%H:%M')

    for item in candidates:
        if accumulated_minutes >= max_minutes:
            break

        duration_mins = int(item['hours'] * 60)
        # Cap single slot at remaining budget or 120 mins max per session
        duration_mins = min(duration_mins, max_minutes - accumulated_minutes, 120)

        if duration_mins < 15:
            continue

        end_time = curr_time + timedelta(minutes=duration_mins)
        slot_str = f"{curr_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

        schedule.append({
            'time_slot': slot_str,
            'title': item['title'],
            'subject': item['subject'],
            'type': item['type'],
            'hours': round(duration_mins / 60.0, 1),
            'reason': item['reason']
        })

        accumulated_minutes += duration_mins
        curr_time = end_time + timedelta(minutes=break_mins)

    return schedule
