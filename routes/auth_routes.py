import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles student registration securely with SQLite database persistence."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Basic input validations
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        try:
            # Case-insensitive check for duplicate username
            if User.query.filter(db.func.lower(User.username) == username.lower()).first():
                flash('Username is already taken.', 'danger')
                return render_template('auth/register.html')

            # Case-insensitive check for duplicate email
            if User.query.filter(db.func.lower(User.email) == email).first():
                flash('Email address is already registered.', 'danger')
                return render_template('auth/register.html')

            # Create new student user with Werkzeug hashed password
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            db_path = db.engine.url
            logger.info(f"[REGISTER SUCCESS] DB: {db_path} | User ID: {new_user.id} | Username: '{username}' | Email: '{email}'")

            flash('Registration successful! Please log in to continue.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during user registration: {e}", exc_info=True)
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles student login with case-insensitive username/email matching."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')

        if not username_or_email or not password:
            flash('Please enter both username/email and password.', 'danger')
            return render_template('auth/login.html')

        try:
            query_str = username_or_email.lower()
            
            # Case-insensitive lookup against both username and email fields
            user = User.query.filter(
                (db.func.lower(User.username) == query_str) | 
                (db.func.lower(User.email) == query_str)
            ).first()

            pwd_match = user.check_password(password) if user else False
            db_path = db.engine.url
            logger.info(f"[LOGIN ATTEMPT] DB: {db_path} | Identifier: '{username_or_email}' | QueryStr: '{query_str}' | User Found: {bool(user)} | Pwd Match: {pwd_match}")

            if user and pwd_match:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page or url_for('dashboard.dashboard'))
            else:
                flash('Invalid username/email or password.', 'danger')

        except Exception as e:
            logger.error(f"Error during user login: {e}", exc_info=True)
            flash('A database error occurred during login. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logs out the current student and clears Flask session."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
