from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Subject

subject_bp = Blueprint('subjects', __name__)

@subject_bp.route('/subjects', methods=['GET'])
@login_required
def list_subjects():
    """Lists all subjects belonging to the authenticated student."""
    subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name.asc()).all()
    return render_template('subjects.html', subjects=subjects)


@subject_bp.route('/subjects/add', methods=['POST'])
@login_required
def add_subject():
    """Adds a new subject for the authenticated student with validation."""
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    semester = request.form.get('semester', '').strip()
    faculty_name = request.form.get('faculty_name', '').strip()
    credits_val = request.form.get('credits', type=int, default=3)

    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('subjects.list_subjects'))

    if credits_val is None or credits_val < 1 or credits_val > 10:
        flash('Credits must be an integer between 1 and 10.', 'danger')
        return redirect(url_for('subjects.list_subjects'))

    new_subject = Subject(
        user_id=current_user.id,
        name=name,
        code=code or None,
        semester=semester or None,
        faculty_name=faculty_name,
        credits=credits_val
    )
    db.session.add(new_subject)
    db.session.commit()

    flash(f'Subject "{name}" added successfully!', 'success')
    return redirect(url_for('subjects.list_subjects'))


@subject_bp.route('/subjects/<int:subject_id>/edit', methods=['POST'])
@login_required
def edit_subject(subject_id):
    """Edits an existing subject owned by the authenticated student."""
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()

    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    semester = request.form.get('semester', '').strip()
    faculty_name = request.form.get('faculty_name', '').strip()
    credits_val = request.form.get('credits', type=int, default=3)

    if not name:
        flash('Subject name is required.', 'danger')
        return redirect(url_for('subjects.list_subjects'))

    if credits_val is None or credits_val < 1 or credits_val > 10:
        flash('Credits must be an integer between 1 and 10.', 'danger')
        return redirect(url_for('subjects.list_subjects'))

    subject.name = name
    subject.code = code or None
    subject.semester = semester or None
    subject.faculty_name = faculty_name
    subject.credits = credits_val
    db.session.commit()

    flash(f'Subject "{name}" updated successfully!', 'success')
    return redirect(url_for('subjects.list_subjects'))


@subject_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
def delete_subject(subject_id):
    """Deletes a subject owned by the authenticated student."""
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    
    subject_name = subject.name
    db.session.delete(subject)
    db.session.commit()

    flash(f'Subject "{subject_name}" deleted successfully.', 'success')
    return redirect(url_for('subjects.list_subjects'))
