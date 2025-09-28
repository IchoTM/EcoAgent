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
        
        # Check if the session has expired (24 hours)
        last_login = session.get('last_login', 0)
        if datetime.now().timestamp() - last_login > 24 * 60 * 60:
            session.clear()
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login')
def login():
    # Check if we've recently hit a rate limit
    last_error_time = session.get('rate_limit_hit')
    if last_error_time:
        # If it's been less than 60 seconds since the last rate limit
        if datetime.now().timestamp() - last_error_time < 60:
            return render_template('error.html',
                title="Rate Limit Active",
                message="Please wait before trying to log in again.",
                retry_after=int(60 - (datetime.now().timestamp() - last_error_time)))
        else:
            # Clear the rate limit flag if it's been long enough
            session.pop('rate_limit_hit', None)

    try:
        callback_url = url_for('callback', _external=True)
        return auth_client.authorize_redirect(callback_url)
    except Exception as e:
        app.logger.error(f"Error initiating login: {str(e)}")
        if 'Too Many Requests' in str(e):
            session['rate_limit_hit'] = datetime.now().timestamp()
            return render_template('error.html',
                title="Rate Limit Exceeded",
                message="Too many login attempts. Please wait a moment before trying again.",
                retry_after=60)
        return render_template('error.html',
            title="Login Error",
            message="An error occurred while trying to log in. Please try again later.")

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
    
    # Debug: Print raw data
    print("\nDEBUG: Raw consumption data for last 30 days:")
    for d in recent_data:
        print(f"Date: {d.timestamp}")
        print(f"  Electricity: {d.electricity} kWh")
        print(f"  Gas: {d.gas} therms")
        print(f"  Car: {d.car_miles} miles")
        print(f"  Public Transit: {d.public_transport} miles")

    # Calculate individual contributions to monthly carbon footprint
    electricity_carbon = sum([d.electricity * 0.85 for d in recent_data]) / len(recent_data)
    gas_carbon = sum([d.gas * 11.7 for d in recent_data]) / len(recent_data)
    car_carbon = sum([d.car_miles * 0.89 for d in recent_data]) / len(recent_data)
    transit_carbon = sum([d.public_transport * 0.14 for d in recent_data]) / len(recent_data)
    
    # Debug: Print intermediate calculations
    print("\nDEBUG: Monthly Carbon Calculations (lbs CO2):")
    print(f"Electricity: {electricity_carbon:.2f} lbs CO2/month")
    print(f"Gas: {gas_carbon:.2f} lbs CO2/month")
    print(f"Car: {car_carbon:.2f} lbs CO2/month")
    print(f"Transit: {transit_carbon:.2f} lbs CO2/month")
    
    # Sum up monthly carbon in pounds
    monthly_carbon_lbs = electricity_carbon + gas_carbon + car_carbon + transit_carbon
    print(f"\nTotal monthly: {monthly_carbon_lbs:.2f} lbs CO2")
    
    # Convert to annual tons
    carbon = (monthly_carbon_lbs * 12) / 2000
    print(f"Annual total: {carbon:.2f} tons CO2/year")
    print(f"US average: 16 tons CO2/year")
    
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
    # Only show login page if user is not logged in
    if 'user' not in session:
        return render_template('login.html')
    return redirect(url_for('dashboard'))

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
        
        # Convert annual tons to monthly pounds for display
        monthly_pounds = (stats['carbon_footprint'] * 2000) / 12  # First convert to pounds, then to monthly
        
        return render_template('analytics.html', 
                             user_energy=stats['energy_usage'],
                             user_water=stats['water_usage'],
                             user_miles=stats['miles_traveled'],
                             user_carbon=monthly_pounds)
    finally:
        db.close()

@app.route('/dashboard')
@login_required
def dashboard():
    db_session = get_session()
    try:
        if 'user' not in session:
            app.logger.error("No user in session")
            return redirect(url_for('login'))
            
        # Debug log to see the user info structure
        app.logger.debug(f"User info in session: {session['user']}")
        
        # Get the user's Auth0 sub (unique identifier)
        auth0_id = session['user'].get('sub')
        if not auth0_id:
            app.logger.error("No sub field in user info")
            return redirect(url_for('login'))
            
        # First get the user's database ID using their auth0_id
        user = db_session.query(User).filter_by(auth0_id=auth0_id).first()
        
        # If user doesn't exist, create a new user
        if not user:
            app.logger.info(f"Creating new user for auth0_id: {auth0_id}")
            email = session['user'].get('email', '')
            if not email and session['user'].get('nickname'):
                email = f"{session['user']['nickname']}@github.com"
            user = User(
                auth0_id=auth0_id,
                email=email,
                name=session['user'].get('name', session['user'].get('nickname', 'Unknown'))
            )
            db_session.add(user)
            db_session.commit()
            
        app.logger.info(f"Loading dashboard for user {user.id} ({user.email})")
        
        try:
            # Get all consumption data for the user using their database ID
            consumption_data = db_session.query(ConsumptionData).filter_by(user_id=user.id).all()
            app.logger.info(f"Found {len(consumption_data)} consumption records")
            
            # Calculate user statistics
            stats = calculate_user_stats(consumption_data)
            
            return render_template('index.html', stats=stats)
            
        except Exception as e:
            app.logger.error(f"Error calculating statistics: {str(e)}")
            # Return empty statistics if there's an error
            empty_stats = {
                'carbon_footprint': 0,
                'energy_usage': 0,
                'water_usage': 0,
                'avg_us_carbon': 16,
                'avg_us_energy': 877,
                'avg_us_water': 8800
            }
            return render_template('index.html', stats=empty_stats)
        
    except Exception as e:
        app.logger.error(f"Error loading dashboard: {str(e)}")
        return redirect(url_for('login'))
    finally:
        db_session.close()

@app.route('/auth')
def auth():
    """Redirect to Auth0 login page"""
    return redirect(auth_client.get_auth_url())

@app.route('/callback')
def callback():
    try:
        # Get the authorization code from the URL parameters
        code = request.args.get('code')
        if not code:
            app.logger.error("No code in callback")
            return render_template('error.html', 
                title="Authentication Error",
                message="No authorization code received. Please try logging in again.")

        error = request.args.get('error')
        error_description = request.args.get('error_description')
        if error:
            app.logger.error(f"Auth0 error: {error} - {error_description}")
            return render_template('error.html',
                title="Authentication Error",
                message=error_description or "An error occurred during authentication.")
        
        # Exchange the code for tokens
        try:
            token = auth_client.get_token(code)
        except Exception as e:
            if 'Too Many Requests' in str(e):
                return render_template('error.html',
                    title="Rate Limit Exceeded",
                    message="Too many login attempts. Please wait a moment before trying again.",
                    retry_after=60)
            raise

        # Get user information using the access token
        try:
            userinfo = auth_client.get_userinfo(token)
        except Exception as e:
            if 'Too Many Requests' in str(e):
                return render_template('error.html',
                    title="Rate Limit Exceeded",
                    message="Too many login attempts. Please wait a moment before trying again.",
                    retry_after=60)
            raise

        # Clear any existing session data
        session.clear()
        
        # Store user information in session
        session['user'] = userinfo
        session['last_login'] = datetime.now().timestamp()
        
        # Redirect to dashboard
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        app.logger.error(f"Error in callback: {str(e)}")
        return render_template('error.html',
            title="Authentication Error",
            message="An unexpected error occurred during authentication. Please try again later.")
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

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/delete-user-data', methods=['POST'])
@login_required
def delete_user_data():
    db_session = get_session()
    try:
        # Get user by auth0_id
        auth0_id = session['user']['id']
        user = db_session.query(User).filter_by(auth0_id=auth0_id).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Store IDs for logging
        user_id = user.id
        user_email = user.email  # Store for logging
        
        try:
            # 1. Delete all consumption data first (in a separate transaction)
            with get_session() as data_session:
                data_session.query(ConsumptionData).filter_by(user_id=user_id).delete(synchronize_session=False)
                data_session.commit()
                app.logger.info(f"Deleted all consumption data for user {user_id}")
            
            # 2. Delete from Auth0
            try:
                auth_client.delete_auth0_user(auth0_id)
                app.logger.info(f"Auth0 account deleted - Auth0 ID: {auth0_id}")
            except AuthError as e:
                app.logger.error(f"Failed to delete Auth0 account: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to delete account. Please contact support.'
                }), 500
            
            # 3. Double-check and force-delete any remaining consumption data
            remaining_data = db_session.query(ConsumptionData).filter_by(user_id=user_id).all()
            if remaining_data:
                app.logger.warning(f"Found {len(remaining_data)} remaining consumption records - force deleting")
                for record in remaining_data:
                    db_session.delete(record)
            
            # 4. Delete the user record itself
            db_session.delete(user)
            
            # 5. Commit the final changes
            db_session.commit()
            
            # 6. Verify complete deletion
            verify_session = get_session()
            try:
                remaining_user = verify_session.query(User).filter_by(auth0_id=auth0_id).first()
                remaining_data = verify_session.query(ConsumptionData).filter_by(user_id=user_id).first()
                
                if remaining_user or remaining_data:
                    app.logger.error(f"Data deletion verification failed! User: {bool(remaining_user)}, Data: {bool(remaining_data)}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to verify complete data deletion.'
                    }), 500
            finally:
                verify_session.close()
            
            # 7. Log the successful complete deletion
            app.logger.info(
                f"Complete user deletion verified - "
                f"Database ID: {user_id}, Auth0 ID: {auth0_id}, "
                f"Email: {user_email} - All data confirmed deleted"
            )
            
            # 8. Clear the session
            session.clear()
            
            return jsonify({
                'status': 'success',
                'message': 'Account and all associated data permanently deleted'
            })
            
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Error during user deletion process: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'An error occurred during deletion. Please contact support.'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error in delete_user_data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Server error occurred'
        }), 500
        
    finally:
        db_session.close()

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
    if 'user' not in session:
        app.logger.error("No user in session")
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

    app.logger.info(f"Received consumption data request for user: {session['user']['id']}")
    
    db_session = get_session()
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")
        
        if not data:
            app.logger.error("No data in request")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Get the user's database ID using their auth0_id
        user = db_session.query(User).filter_by(auth0_id=session['user']['id']).first()
        if not user:
            app.logger.error(f"User not found in database: {session['user']['id']}")
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        app.logger.info(f"Found user in database: {user.id} ({user.email})")
            
        # Validate and convert input data
        try:
            # First validate all data is present
            required_fields = ['electricity', 'gas', 'water', 'car_miles', 'public_transport', 'household_size']
            for field in required_fields:
                if field not in data:
                    raise KeyError(f"Missing required field: {field}")
                    
            # Create consumption record
            consumption = ConsumptionData(
                user_id=user.id,
                electricity=float(data['electricity']),
                gas=float(data['gas']),
                water=float(data['water']),
                car_miles=float(data['car_miles']),
                public_transport=float(data['public_transport']),
                household_size=int(data['household_size'])
            )
            
            app.logger.info(f"Created consumption record: {consumption.__dict__}")
            
        except (KeyError, ValueError) as e:
            app.logger.error(f"Data validation error: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Invalid data: {str(e)}'}), 400
        
        # Add and commit in separate try block to catch database errors
        try:
            db_session.add(consumption)
            db_session.flush()  # Check for database errors before commit
            app.logger.info(f"Added consumption record with ID: {consumption.id}")
            
            db_session.commit()
            app.logger.info(f"Successfully committed consumption data for user {user.id}")
            
            # Verify the data was saved
            saved_data = db_session.query(ConsumptionData).filter_by(id=consumption.id).first()
            if not saved_data:
                raise Exception("Data verification failed - record not found after commit")
                
            return jsonify({
                'status': 'success',
                'message': 'Data saved successfully',
                'data': {
                    'id': consumption.id,
                    'timestamp': consumption.timestamp.isoformat()
                }
            })
            
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Database error: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Database error: Failed to save data'}), 500
        
    except Exception as e:
        app.logger.error(f"Unexpected error in add_consumption: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Server error occurred'}), 500
        
    finally:
        db_session.close()

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.json
    agent = EcoAgent()
    request_data = SustainabilityRequest(
        query_type=data.get('query_type', 'chat'),
        user_id=session['user']['id'],
        message=data.get('message'),
        data=data.get('data')
    )
    # Use synchronous process_request instead of async analyze_sustainability
    response = agent.process_request(request_data)
    return jsonify({
        'status': response.status,
        'message': response.message if response.message else None,
        'error': response.error if response.error else None,
        'data': response.data if response.data else None
    })

def create_energy_chart(consumption_data):
    # Sort data by timestamp
    sorted_data = sorted(consumption_data, key=lambda x: x.timestamp)
    
    dates = [d.timestamp for d in sorted_data]
    electricity = [d.electricity for d in sorted_data]
    gas = [d.gas for d in sorted_data]
    water = [d.water for d in sorted_data]
    
    fig = go.Figure()
    
    # Add traces with improved styling
    fig.add_trace(go.Scatter(
        x=dates, 
        y=electricity, 
        name='Electricity (kWh)',
        mode='lines+markers',
        line=dict(width=2, color='#2ecc71'),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, 
        y=gas, 
        name='Gas (therms)',
        mode='lines+markers',
        line=dict(width=2, color='#e74c3c'),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, 
        y=water, 
        name='Water (gallons)',
        mode='lines+markers',
        line=dict(width=2, color='#3498db'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title={
            'text': 'Energy & Water Consumption Over Time',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Date',
        yaxis_title='Consumption',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_transport_chart(consumption_data):
    # Sort data by timestamp
    sorted_data = sorted(consumption_data, key=lambda x: x.timestamp)
    
    dates = [d.timestamp for d in sorted_data]
    car_miles = [d.car_miles for d in sorted_data]
    public_transport = [d.public_transport for d in sorted_data]
    
    fig = go.Figure()
    
    # Add traces with improved styling
    fig.add_trace(go.Scatter(
        x=dates, 
        y=car_miles, 
        name='Car Miles',
        mode='lines+markers',
        line=dict(width=2, color='#e67e22'),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, 
        y=public_transport, 
        name='Public Transit Miles',
        mode='lines+markers',
        line=dict(width=2, color='#9b59b6'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title={
            'text': 'Transportation Usage Over Time',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Date',
        yaxis_title='Miles',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

@app.route('/chat')
@login_required
def chat():
    """Render the chat interface"""
    return render_template('chat.html')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--port', type=int, default=8501, help='Port to run the application on')
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
