from datetime import date, timedelta
from models import Task, Assignment, Exam, Subject, Attendance
from services.workload_service import calculate_overall_workload, get_subject_workload_breakdown

def generate_categorized_ai_insights(user_id, today=None):
    """
    Analyzes actual student database records to generate intelligent, non-random insights
    across 5 explicit categories: URGENT, IMPORTANT, WARNING, SUGGESTION, ACHIEVEMENT.
    """
    if today is None:
        today = date.today()

    insights = []

    # Query database data
    pending_tasks = Task.query.filter(Task.user_id == user_id, Task.status != 'Completed').all()
    completed_tasks_count = Task.query.filter(Task.user_id == user_id, Task.status == 'Completed').count()
    
    pending_assigns = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status != 'Submitted').all()
    submitted_assigns_count = Assignment.query.filter(Assignment.user_id == user_id, Assignment.status == 'Submitted').count()

    upcoming_exams = Exam.query.filter(Exam.user_id == user_id, Exam.exam_date >= today).all()
    attendances = Attendance.query.filter_by(user_id=user_id).all()
    workload = calculate_overall_workload(user_id, today)
    subject_workloads = get_subject_workload_breakdown(user_id, today)

    # 1. URGENT CATEGORY (Overdue or Due within 48 Hours)
    imminent_count = 0
    for t in pending_tasks:
        if t.deadline:
            days = (t.deadline - today).days
            if days < 0:
                insights.append({
                    'category': 'URGENT',
                    'badge_class': 'danger',
                    'icon': 'bi-alarm-fill',
                    'text': f'Overdue Task: "{t.title}" was due on {t.deadline}. Complete it now to avoid penalty.'
                })
            elif days <= 2:
                imminent_count += 1

    for a in pending_assigns:
        if a.deadline:
            days = (a.deadline - today).days
            if days < 0:
                insights.append({
                    'category': 'URGENT',
                    'badge_class': 'danger',
                    'icon': 'bi-exclamation-triangle-fill',
                    'text': f'Overdue Assignment: "{a.title}" was due on {a.deadline}. Submit as soon as possible.'
                })
            elif days <= 2:
                imminent_count += 1

    if imminent_count > 0:
        insights.append({
            'category': 'URGENT',
            'badge_class': 'danger',
            'icon': 'bi-clock-fill',
            'text': f'You have {imminent_count} deadline(s) occurring within the next 48 hours.'
        })

    # 2. IMPORTANT CATEGORY (Workload Level & Exam Preparation)
    if workload['score'] >= 70:
        insights.append({
            'category': 'IMPORTANT',
            'badge_class': 'warning text-dark',
            'icon': 'bi-speedometer2',
            'text': f'Your overall workload has reached {workload["score"]}/100 ({workload["category"]}). Focus on high-priority items first.'
        })

    for e in upcoming_exams:
        days = (e.exam_date - today).days
        sub_name = e.subject.name if e.subject else 'General'
        if e.prep_percentage < 50:
            insights.append({
                'category': 'IMPORTANT',
                'badge_class': 'warning text-dark',
                'icon': 'bi-pencil-square',
                'text': f'Exam Preparation Deficit: Your prep for "{sub_name}" (on {e.exam_date}) is at {e.prep_percentage}%. Consider starting revision today.'
            })

    if subject_workloads:
        top_sub = max(subject_workloads, key=lambda x: x['workload_score'])
        if top_sub['workload_score'] >= 40:
            insights.append({
                'category': 'IMPORTANT',
                'badge_class': 'warning text-dark',
                'icon': 'bi-journal-bookmark-fill',
                'text': f'"{top_sub["name"]}" has your highest academic workload score ({top_sub["workload_score"]}/100).'
            })

    # 3. WARNING CATEGORY (Attendance alerts & stress warnings)
    for att in attendances:
        if att.status == 'CRITICAL':
            insights.append({
                'category': 'WARNING',
                'badge_class': 'danger',
                'icon': 'bi-person-x-fill',
                'text': f'Attendance Warning: Your attendance in "{att.subject.name}" is {att.percentage}% (CRITICAL). Attend upcoming classes immediately.'
            })
        elif att.status == 'WARNING':
            insights.append({
                'category': 'WARNING',
                'badge_class': 'warning text-dark',
                'icon': 'bi-person-exclamation',
                'text': f'Attendance Caution: Your attendance in "{att.subject.name}" is {att.percentage}% (below 75% target).'
            })

    # 4. SUGGESTION CATEGORY (Study Capacity & Time Management)
    total_est_hours = sum(t.estimated_hours or 1.0 for t in pending_tasks) + sum(a.estimated_hours or 2.0 for a in pending_assigns)
    if total_est_hours > 0:
        insights.append({
            'category': 'SUGGESTION',
            'badge_class': 'info text-dark',
            'icon': 'bi-lightbulb-fill',
            'text': f'You have approximately {round(total_est_hours, 1)} hours of total academic study work remaining.'
        })

    if len(pending_tasks) > 3:
        insights.append({
            'category': 'SUGGESTION',
            'badge_class': 'info text-dark',
            'icon': 'bi-check2-all',
            'text': 'Consider tackling short 1-hour tasks first to build momentum and reduce task count.'
        })

    # 5. ACHIEVEMENT CATEGORY (Positive Feedback)
    total_completed = completed_tasks_count + submitted_assigns_count
    if total_completed > 0:
        insights.append({
            'category': 'ACHIEVEMENT',
            'badge_class': 'success',
            'icon': 'bi-trophy-fill',
            'text': f'Great progress! You have completed {completed_tasks_count} task(s) and submitted {submitted_assigns_count} assignment(s) so far.'
        })
    else:
        insights.append({
            'category': 'ACHIEVEMENT',
            'badge_class': 'secondary',
            'icon': 'bi-star',
            'text': 'Complete your first task or assignment to unlock academic achievement milestones!'
        })

    return insights
