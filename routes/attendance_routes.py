from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Attendance, Subject
from services.attendance_service import get_subject_attendance_summary

attendance_bp = Blueprint('attendance_module', __name__)

@attendance_bp.route('/attendance', methods=['GET'])
@login_required
def attendance_view():
    """Renders attendance tracker page with target class recommendations."""
    records = get_subject_attendance_summary(current_user.id)
    return render_template('attendance.html', records=records)


@attendance_bp.route('/attendance/update/<int:attendance_id>', methods=['POST'])
@login_required
def update_attendance(attendance_id):
    """Updates total and attended classes for a subject."""
    att = Attendance.query.filter_by(id=attendance_id, user_id=current_user.id).first_or_404()
    
    total = request.form.get('total_classes', type=int, default=0)
    attended = request.form.get('attended_classes', type=int, default=0)

    if attended > total:
        flash('Attended classes cannot exceed total classes.', 'danger')
        return redirect(url_for('attendance_module.attendance_view'))

    att.total_classes = max(0, total)
    att.attended_classes = max(0, attended)
    db.session.commit()

    flash(f'Attendance for "{att.subject.name}" updated successfully!', 'success')
    return redirect(url_for('attendance_module.attendance_view'))


@attendance_bp.route('/attendance/delete/<int:attendance_id>', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    """Resets attendance records for a subject."""
    att = Attendance.query.filter_by(id=attendance_id, user_id=current_user.id).first_or_404()
    att.total_classes = 0
    att.attended_classes = 0
    db.session.commit()

    flash('Attendance record reset.', 'info')
    return redirect(url_for('attendance_module.attendance_view'))
