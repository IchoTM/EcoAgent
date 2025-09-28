#!/usr/bin/env python3
"""
EcoAgent - AI Sustainability Assistant
Flask Application
"""

import asyncio
from datetime import datetime
from functools import wraps
from urllib.parse import urlencode
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
from agent.agent_core import EcoAgent, SustainabilityRequest
from auth import Auth, AuthError
from database import ConsumptionData, User, get_session

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure secret key

# Initialize Auth0 client
auth_client = Auth()
# Ensure we have the correct domain from environment variables
if not auth_client.domain or 'auth0.com' not in auth_client.domain:
    raise ValueError("Invalid Auth0 domain configuration")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_user_stats(consumption_data):
    if not consumption_data:
        return {
            'carbon_footprint': 0,
            'energy_usage': 0,
            'water_usage': 0,
            'miles_traveled': 0,
            'avg_us_carbon': 16,  # Average US carbon footprint in tons per year
            'avg_us_energy': 877,  # Average US household monthly kWh usage
            'avg_us_water': 8800,  # Average US household monthly water usage in gallons
            'avg_us_miles': 1200  # Average US household monthly miles traveled
        }
    
    # Calculate averages from the last 30 days of data
    recent_data = sorted(consumption_data, key=lambda x: x.timestamp, reverse=True)[:30]
    
    # Calculate carbon footprint (simplified calculation)
    carbon = sum([(
        d.electricity * 0.0004 +  # kWh to tons CO2
        d.gas * 0.005 +  # therms to tons CO2
        d.car_miles * 0.0004 +  # miles to tons CO2
        d.public_transport * 0.0002  # miles to tons CO2
    ) for d in recent_data]) / len(recent_data) * 12  # Annualized
    
    energy = sum([d.electricity for d in recent_data]) / len(recent_data)
    water = sum([d.water for d in recent_data]) / len(recent_data)
    
    # Calculate total miles (car + public transport)
    miles = sum([(d.car_miles + d.public_transport) for d in recent_data]) / len(recent_data)
    
    return {
        'carbon_footprint': round(carbon, 1),
        'energy_usage': round(energy, 0),
        'water_usage': round(water, 0),
        'miles_traveled': round(miles, 0),
        'avg_us_carbon': 16,  # Average US carbon footprint in tons per year
        'avg_us_energy': 877,  # Average US household monthly kWh usage
        'avg_us_water': 8800,  # Average US household monthly water usage in gallons
        'avg_us_miles': 1200  # Average US household monthly miles traveled
    }

@app.route('/')
def home():
    # Clear any existing session data when arriving at home page
    if 'user' in session:
        session.clear()
    return render_template('login.html')

@app.route('/analytics')
@login_required
def analytics():
    db = get_session()
    try:
        user = db.query(User).filter_by(auth0_id=session['user']['id']).first()
        if not user:
            return redirect(url_for('login'))
        
        consumption_data = db.query(ConsumptionData).filter_by(user_id=user.id).all()
        stats = calculate_user_stats(consumption_data)
        
        return render_template('analytics.html', 
                             user_energy=stats['energy_usage'],
                             user_water=stats['water_usage'],
                             user_miles=stats['miles_traveled'],
                             user_carbon=stats['carbon_footprint'] * 2000)  # Convert tons to pounds
    finally:
        db.close()

@app.route('/dashboard')
@login_required
def dashboard():
    db_session = get_session()
    user_id = session['user']['id']
    consumption_data = db_session.query(ConsumptionData).filter_by(user_id=user_id).all()
    
    # Calculate user statistics
    stats = calculate_user_stats(consumption_data)
    
    # Create charts
    energy_fig = create_energy_chart(consumption_data)
    transport_fig = create_transport_chart(consumption_data)
    
    # Convert charts to JSON for rendering
    charts = {
        'energy': json.dumps(energy_fig, cls=plotly.utils.PlotlyJSONEncoder),
        'transport': json.dumps(transport_fig, cls=plotly.utils.PlotlyJSONEncoder)
    }
    
    return render_template('index.html', charts=charts, stats=stats)

@app.route('/auth')
def auth():
    """Redirect to Auth0 login page"""
    return redirect(auth_client.get_auth_url())

@app.route('/callback')
def callback():
    try:
        code = request.args.get('code')
        if not code:
            app.logger.error("No code in callback")
            return redirect(url_for('login'))
            
        token = auth_client.get_token(code)
        if not token or 'access_token' not in token:
            app.logger.error(f"Invalid token response: {token}")
            return redirect(url_for('login'))
            
        user_info = auth_client.get_user_profile(token['access_token'])
        app.logger.info(f"User info received: {user_info}")
        
        # Handle GitHub-specific auth
        is_github = user_info.get('sub', '').startswith('github|')
        
        # Store user info in session
        session['user'] = {
            'id': user_info.get('sub'),  # Use sub as primary identifier
            'email': user_info.get('email') or (f"{user_info.get('nickname')}@github.com" if is_github else None),
            'name': user_info.get('name') or user_info.get('nickname', ''),
            'picture': user_info.get('picture'),
            'access_token': token['access_token'],
            'provider': 'github' if is_github else 'other'
        }
        
        if not session['user']['id']:
            app.logger.error(f"Missing required user info (sub/id): {user_info}")
            return redirect(url_for('login'))
        
        try:
            # Get or create user in database
            db_session = get_session()
            user = db_session.query(User).filter_by(auth0_id=session['user']['id']).first()
            
            if not user:
                # For GitHub users, create a new user with GitHub-specific info
                user = User(
                    auth0_id=session['user']['id'],
                    email=session['user']['email'],
                    name=session['user']['name']
                )
                db_session.add(user)
                db_session.commit()
                app.logger.info(f"Created new user: {user.name} ({user.email})")
            else:
                # Update existing user's info
                user.name = session['user']['name']
                if not user.email and session['user']['email']:
                    user.email = session['user']['email']
                db_session.commit()
                app.logger.info(f"Updated existing user: {user.name} ({user.email})")
                
            session['user']['db_id'] = user.id  # Store database ID in session
            return redirect(url_for('dashboard'))
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}")
            return redirect(url_for('login'))
        
        session['user']['db_id'] = user.id  # Store database ID in session
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Auth error: {str(e)}")
        return redirect(url_for('login'))

@app.route('/data-entry')
@login_required
def data_entry():
    return render_template('data_entry.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    
    try:
        # Construct Auth0 logout URL
        params = {
            'returnTo': 'http://localhost:8501/',  # Include trailing slash
            'client_id': auth_client.client_id
        }
        logout_url = f"https://{auth_client.domain}/v2/logout?{urlencode(params)}"
        
        # Log the URL we're redirecting to (for debugging)
        app.logger.info(f"Redirecting to logout URL: {logout_url}")
        
        return redirect(logout_url)
    except Exception as e:
        # Log any errors
        app.logger.error(f"Logout error: {str(e)}")
        return redirect('/')

@app.route('/add_consumption', methods=['POST'])
@login_required
def add_consumption():
    data = request.json
    db_session = get_session()
    
    consumption = ConsumptionData(
        user_id=session['user']['id'],
        electricity=data['electricity'],
        gas=data['gas'],
        water=data['water'],
        car_miles=data['car_miles'],
        public_transport=data['public_transport'],
        household_size=data['household_size']
    )
    
    db_session.add(consumption)
    db_session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/analyze', methods=['POST'])
@login_required
async def analyze():
    data = request.json
    agent = EcoAgent()
    request_data = SustainabilityRequest(**data)
    analysis = await agent.analyze_sustainability(request_data)
    return jsonify(analysis)

def create_energy_chart(consumption_data):
    dates = [d.timestamp for d in consumption_data]
    electricity = [d.electricity for d in consumption_data]
    gas = [d.gas for d in consumption_data]
    water = [d.water for d in consumption_data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=electricity, name='Electricity'))
    fig.add_trace(go.Scatter(x=dates, y=gas, name='Gas'))
    fig.add_trace(go.Scatter(x=dates, y=water, name='Water'))
    
    fig.update_layout(
        title='Energy Consumption Over Time',
        xaxis_title='Date',
        yaxis_title='Consumption',
        template='plotly_dark'
    )
    
    return fig

def create_transport_chart(consumption_data):
    dates = [d.timestamp for d in consumption_data]
    car_miles = [d.car_miles for d in consumption_data]
    public_transport = [d.public_transport for d in consumption_data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=car_miles, name='Car Miles'))
    fig.add_trace(go.Scatter(x=dates, y=public_transport, name='Public Transport'))
    
    fig.update_layout(
        title='Transportation Usage Over Time',
        xaxis_title='Date',
        yaxis_title='Miles',
        template='plotly_dark'
    )
    
    return fig

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=8501, help='Port to run the application on')
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
