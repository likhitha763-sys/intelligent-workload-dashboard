from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Exam, Subject

exam_bp = Blueprint('exams', __name__)

def parse_date(date_str):
    """Helper to parse YYYY-MM-DD string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

@exam_bp.route('/exams', methods=['GET'])
@login_required
def list_exams():
    """Lists all exams for current authenticated student."""
    exams = Exam.query.filter_by(user_id=current_user.id).order_by(Exam.exam_date.asc()).all()
    subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name.asc()).all()
    return render_template('exams.html', exams=exams, subjects=subjects, today=date.today())


@exam_bp.route('/exams/add', methods=['POST'])
@login_required
def add_exam():
    """Adds a new exam schedule entry."""
    subject_id = request.form.get('subject_id', type=int)
    exam_date = parse_date(request.form.get('exam_date'))
    exam_time = request.form.get('exam_time', '').strip()
    difficulty = request.form.get('difficulty', 'Medium')
    syllabus = request.form.get('syllabus', '').strip()
    prep_percentage = request.form.get('prep_percentage', type=int, default=0)

    if not exam_date:
        flash('Exam date is required.', 'danger')
        return redirect(url_for('exams.list_exams'))

    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None

    # Keep prep_percentage within 0-100 bounds
    prep_percentage = max(0, min(100, prep_percentage))

    new_exam = Exam(
        user_id=current_user.id,
        subject_id=subject_id,
        exam_date=exam_date,
        exam_time=exam_time,
        difficulty=difficulty,
        syllabus=syllabus,
        prep_percentage=prep_percentage
    )
    db.session.add(new_exam)
    db.session.commit()

    flash('Exam schedule added successfully!', 'success')
    return redirect(url_for('exams.list_exams'))


@exam_bp.route('/exams/<int:exam_id>/edit', methods=['POST'])
@login_required
def edit_exam(exam_id):
    """Edits an existing exam schedule entry."""
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()

    exam_date = parse_date(request.form.get('exam_date'))
    if not exam_date:
        flash('Exam date is required.', 'danger')
        return redirect(url_for('exams.list_exams'))

    subject_id = request.form.get('subject_id', type=int)
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None
    else:
        subject_id = None

    prep_percentage = request.form.get('prep_percentage', type=int, default=0)
    prep_percentage = max(0, min(100, prep_percentage))

    exam.subject_id = subject_id
    exam.exam_date = exam_date
    exam.exam_time = request.form.get('exam_time', '').strip()
    exam.difficulty = request.form.get('difficulty', 'Medium')
    exam.syllabus = request.form.get('syllabus', '').strip()
    exam.prep_percentage = prep_percentage

    db.session.commit()
    flash('Exam schedule updated successfully!', 'success')
    return redirect(url_for('exams.list_exams'))


@exam_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    """Deletes an exam entry owned by current student."""
    exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first_or_404()
    db.session.delete(exam)
    db.session.commit()

    flash('Exam schedule entry deleted.', 'success')
    return redirect(url_for('exams.list_exams'))
