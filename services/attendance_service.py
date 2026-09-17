import math
from models import db, Attendance, Subject

def get_subject_attendance_summary(user_id):
    """Calculates attendance percentages, statuses, and target class recommendations for current student."""
    subjects = Subject.query.filter_by(user_id=user_id).all()
    records = []

    for sub in subjects:
        att = Attendance.query.filter_by(user_id=user_id, subject_id=sub.id).first()
        if not att:
            # Create zero-state record if none exists
            att = Attendance(user_id=user_id, subject_id=sub.id, total_classes=0, attended_classes=0)
            db.session.add(att)
            db.session.commit()

        total = att.total_classes or 0
        attended = att.attended_classes or 0
        missed = max(0, total - attended)
        pct = att.percentage
        status = att.status

        # Calculate target recommendation
        if total == 0:
            rec_text = "No classes recorded yet for this subject."
        elif pct < 75.0:
            # Needed consecutive classes X such that (attended + X) / (total + X) >= 0.75 => X >= 3*total - 4*attended
            needed = math.ceil(3 * total - 4 * attended)
            needed = max(1, needed)
            rec_text = f"Attend the next {needed} consecutive class(es) to reach 75% attendance."
        else:
            # Buffer classes Y student can miss: (attended) / (total + Y) >= 0.75 => Y <= (4*attended - 3*total) / 3
            can_miss = math.floor((4 * attended - 3 * total) / 3.0)
            can_miss = max(0, can_miss)
            if can_miss > 0:
                rec_text = f"You are in safe standing. You can miss up to {can_miss} class(es) while maintaining >= 75%."
            else:
                rec_text = "You are currently at 75%. Attend the next class to maintain safe standing."

        records.append({
            'id': att.id,
            'subject_id': sub.id,
            'subject_name': sub.name,
            'faculty_name': sub.faculty_name or 'N/A',
            'total_classes': total,
            'attended_classes': attended,
            'missed_classes': missed,
            'percentage': pct,
            'status': status,
            'badge_class': 'success' if status == 'SAFE' else ('warning text-dark' if status == 'WARNING' else 'danger'),
            'recommendation': rec_text
        })

    return records
