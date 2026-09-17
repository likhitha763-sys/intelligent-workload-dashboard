from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Assignment, Subject

assignment_bp = Blueprint('assignments', __name__)

def parse_date(date_str):
    """Helper to parse YYYY-MM-DD string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

@assignment_bp.route('/assignments', methods=['GET'])
@login_required
def list_assignments():
    """Lists all assignments for current authenticated student."""
    assignments = Assignment.query.filter_by(user_id=current_user.id).order_by(Assignment.deadline.asc()).all()
    subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name.asc()).all()
    return render_template('assignments.html', assignments=assignments, subjects=subjects, today=date.today())


@assignment_bp.route('/assignments/add', methods=['POST'])
@login_required
def add_assignment():
    """Adds a new assignment for current student."""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    subject_id = request.form.get('subject_id', type=int)
    deadline = parse_date(request.form.get('deadline'))
    difficulty = request.form.get('difficulty', 'Medium')
    estimated_hours = request.form.get('estimated_hours', type=float, default=2.0)
    status = request.form.get('status', 'Not Started')

    if not title:
        flash('Assignment title is required.', 'danger')
        return redirect(url_for('assignments.list_assignments'))

    if estimated_hours is None or estimated_hours <= 0:
        flash('Estimated completion hours must be a positive number greater than 0.', 'danger')
        return redirect(url_for('assignments.list_assignments'))

    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None

    new_assignment = Assignment(
        user_id=current_user.id,
        subject_id=subject_id,
        title=title,
        description=description,
        deadline=deadline,
        difficulty=difficulty,
        estimated_hours=estimated_hours,
        status=status
    )
    db.session.add(new_assignment)
    db.session.commit()

    flash(f'Assignment "{title}" added successfully!', 'success')
    return redirect(url_for('assignments.list_assignments'))


@assignment_bp.route('/assignments/<int:assignment_id>/edit', methods=['POST'])
@login_required
def edit_assignment(assignment_id):
    """Edits an existing assignment owned by current student."""
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()

    title = request.form.get('title', '').strip()
    estimated_hours = request.form.get('estimated_hours', type=float, default=2.0)

    if not title:
        flash('Assignment title is required.', 'danger')
        return redirect(url_for('assignments.list_assignments'))

    if estimated_hours is None or estimated_hours <= 0:
        flash('Estimated completion hours must be a positive number greater than 0.', 'danger')
        return redirect(url_for('assignments.list_assignments'))

    subject_id = request.form.get('subject_id', type=int)
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None
    else:
        subject_id = None

    assignment.title = title
    assignment.description = request.form.get('description', '').strip()
    assignment.subject_id = subject_id
    assignment.deadline = parse_date(request.form.get('deadline'))
    assignment.difficulty = request.form.get('difficulty', 'Medium')
    assignment.estimated_hours = estimated_hours
    assignment.status = request.form.get('status', 'Not Started')

    db.session.commit()
    flash(f'Assignment "{title}" updated successfully!', 'success')
    return redirect(url_for('assignments.list_assignments'))


@assignment_bp.route('/assignments/<int:assignment_id>/status', methods=['POST'])
@login_required
def update_status(assignment_id):
    """Updates status for an assignment."""
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()
    new_status = request.form.get('status')
    if new_status in ['Not Started', 'In Progress', 'Submitted', 'Late']:
        assignment.status = new_status
        db.session.commit()
        flash(f'Status for "{assignment.title}" updated to {new_status}.', 'success')
    return redirect(url_for('assignments.list_assignments'))


@assignment_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    """Deletes an assignment owned by current student."""
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first_or_404()
    title = assignment.title
    db.session.delete(assignment)
    db.session.commit()

    flash(f'Assignment "{title}" deleted.', 'success')
    return redirect(url_for('assignments.list_assignments'))
