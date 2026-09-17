from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.ai_insights_service import generate_categorized_ai_insights

ai_insights_bp = Blueprint('ai_insights', __name__)

@ai_insights_bp.route('/ai-insights', methods=['GET'])
@login_required
def insights_page():
    """Renders the AI Insights page displaying real database-driven academic analysis."""
    insights = generate_categorized_ai_insights(current_user.id)
    return render_template('ai_insights.html', insights=insights)
