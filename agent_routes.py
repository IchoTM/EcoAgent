from app import app
from flask import jsonify, session
from database import User, get_session
from auth import login_required
from agent_web_interface import WebAgentInterface

@app.route('/api/insights')
@login_required
async def get_insights():
    """Get personalized insights from the agents"""
    user = session.get('user')
    if not user:
        return jsonify({"error": "User not authenticated"}), 401
    
    # Get user from database
    db_session = get_session()
    db_user = db_session.query(User).filter(User.auth0_id == user['sub']).first()
    if not db_user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        insights = await WebAgentInterface.get_user_insights(db_user.id)
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this near your other template routes
@app.context_processor
def inject_agent_state():
    """Inject agent state into all templates"""
    return {
        'agents_enabled': True,
        'has_insights': True
    }
