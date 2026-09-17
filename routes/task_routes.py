from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Task, Subject

task_bp = Blueprint('tasks', __name__)

def parse_date(date_str):
    """Helper to parse YYYY-MM-DD string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

@task_bp.route('/tasks', methods=['GET'])
@login_required
def list_tasks():
    """Lists all tasks for current authenticated student."""
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.deadline.asc()).all()
    subjects = Subject.query.filter_by(user_id=current_user.id).order_by(Subject.name.asc()).all()
    return render_template('tasks.html', tasks=tasks, subjects=subjects, today=date.today())


@task_bp.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    """Adds a new task for current student."""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    subject_id = request.form.get('subject_id', type=int)
    deadline = parse_date(request.form.get('deadline'))
    priority = request.form.get('priority', 'Medium')
    difficulty = request.form.get('difficulty', 'Medium')
    estimated_hours = request.form.get('estimated_hours', type=float, default=1.0)
    status = request.form.get('status', 'Not Started')

    if not title:
        flash('Task title is required.', 'danger')
        return redirect(url_for('tasks.list_tasks'))

    if estimated_hours is None or estimated_hours <= 0:
        flash('Estimated completion hours must be a positive number greater than 0.', 'danger')
        return redirect(url_for('tasks.list_tasks'))

    # Verify subject belongs to user if provided
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None

    new_task = Task(
        user_id=current_user.id,
        subject_id=subject_id,
        title=title,
        description=description,
        deadline=deadline,
        priority=priority,
        difficulty=difficulty,
        estimated_hours=estimated_hours,
        status=status
    )
    db.session.add(new_task)
    db.session.commit()

    flash(f'Task "{title}" created successfully!', 'success')
    return redirect(url_for('tasks.list_tasks'))


@task_bp.route('/tasks/<int:task_id>/edit', methods=['POST'])
@login_required
def edit_task(task_id):
    """Edits an existing task owned by the student."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    title = request.form.get('title', '').strip()
    estimated_hours = request.form.get('estimated_hours', type=float, default=1.0)

    if not title:
        flash('Task title is required.', 'danger')
        return redirect(url_for('tasks.list_tasks'))

    if estimated_hours is None or estimated_hours <= 0:
        flash('Estimated completion hours must be a positive number greater than 0.', 'danger')
        return redirect(url_for('tasks.list_tasks'))

    subject_id = request.form.get('subject_id', type=int)
    if subject_id:
        subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first()
        if not subject:
            subject_id = None
    else:
        subject_id = None

    task.title = title
    task.description = request.form.get('description', '').strip()
    task.subject_id = subject_id
    task.deadline = parse_date(request.form.get('deadline'))
    task.priority = request.form.get('priority', 'Medium')
    task.difficulty = request.form.get('difficulty', 'Medium')
    task.estimated_hours = estimated_hours
    task.status = request.form.get('status', 'Not Started')

    db.session.commit()
    flash(f'Task "{title}" updated successfully!', 'success')
    return redirect(url_for('tasks.list_tasks'))


@task_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Toggles task status between Completed and Not Started."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if task.status == 'Completed':
        task.status = 'In Progress'
        flash(f'Task "{task.title}" marked as In Progress.', 'info')
    else:
        task.status = 'Completed'
        flash(f'Task "{task.title}" marked as Completed!', 'success')

    db.session.commit()
    return redirect(request.referrer or url_for('tasks.list_tasks'))


@task_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Deletes a task owned by current student."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    title = task.title
    db.session.delete(task)
    db.session.commit()

    flash(f'Task "{title}" deleted.', 'success')
    return redirect(url_for('tasks.list_tasks'))
