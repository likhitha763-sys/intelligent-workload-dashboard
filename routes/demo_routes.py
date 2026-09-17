from flask import Blueprint, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from services.demo_seeder import seed_engineering_demo_data

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/demo-data/seed', methods=['POST'])
@login_required
def seed_demo_data():
    """Triggers seeding of realistic engineering demo data for project evaluation."""
    seed_engineering_demo_data(current_user.id)
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success', 'message': 'Demo data loaded successfully!'})
        
    flash('Engineering Demo Data loaded successfully! Real workload metrics updated.', 'success')
    return redirect(url_for('dashboard.dashboard'))
