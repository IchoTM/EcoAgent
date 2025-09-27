#!/usr/bin/env python3
"""
EcoAgent - AI Sustainability Assistant
Main application entry point
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from agent.agent_core import EcoAgent, SustainabilityRequest
from auth import init_auth, require_auth
from database import ConsumptionData, get_session

# Configure page
st.set_page_config(
    page_title="EcoAgent - Your AI Sustainability Assistant",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
        /* Main content styling */
        .main {
            padding: 2rem;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        
        /* Card styling */
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 600 !important;
            color: #1f77b4 !important;
        }
        
        /* Header styling */
        h1, h2, h3 {
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #2c3e50;
            padding: 2rem;
        }
        section[data-testid="stSidebar"] .stRadio label {
            color: #ffffff !important;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: all 0.3s;
            cursor: pointer;
        }
        section[data-testid="stSidebar"] .stRadio input:checked + label {
            background-color: #1f77b4;
        }
        section[data-testid="stSidebar"] h1 {
            color: white !important;
            padding: 1rem 0;
        }
        
        /* Main content adjustments */
        .main > div {
            padding-top: 1rem !important;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #1f77b4;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
            transition: background-color 0.3s;
        }
        .stButton button:hover {
            background-color: #2c3e50;
        }
        
        /* Chart styling */
        div[data-testid="stPlotlyChart"] {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Container styling */
        div[data-testid="stContainer"] {
            background-color: #2c2c2c;
            border-radius: 10px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            color: #ffffff;
        }
        
        /* Success/Info/Warning message styling */
        div[data-testid="stSuccessMessage"] {
            background-color: rgba(40, 167, 69, 0.2) !important;
            border-left: 5px solid #28a745;
            color: #ffffff !important;
        }
        div[data-testid="stInfoMessage"] {
            background-color: rgba(23, 162, 184, 0.2) !important;
            border-left: 5px solid #17a2b8;
            color: #ffffff !important;
        }
        div[data-testid="stWarningMessage"] {
            background-color: rgba(255, 193, 7, 0.2) !important;
            border-left: 5px solid #ffc107;
            color: #ffffff !important;
        }
        
        /* Table styling */
        div[data-testid="stTable"] {
            background-color: #2c2c2c;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            color: #ffffff;
        }
        
        /* Chart styling improvements */
        div[data-testid="stPlotlyChart"] {
            background-color: #2c2c2c !important;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            margin: 1rem auto !important;
            max-width: 100% !important;
        }
        div[data-testid="stPlotlyChart"] > div {
            margin: 0 auto !important;
        }
        
        /* Improved button styling */
        .stButton button {
            background-color: #1f77b4 !important;
            color: white !important;
            border-radius: 5px !important;
            padding: 0.5rem 1.5rem !important;
            border: none !important;
            transition: all 0.3s !important;
            font-weight: 500 !important;
        }
        .stButton button:hover {
            background-color: #2c3e50 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        
        /* Dark mode text inputs */
        .stTextInput input {
            background-color: #363636 !important;
            color: #ffffff !important;
            border: 1px solid #4a4a4a !important;
        }
        
        /* Dark mode number inputs */
        .stNumberInput input {
            background-color: #363636 !important;
            color: #ffffff !important;
            border: 1px solid #4a4a4a !important;
        }
    </style>
""", unsafe_allow_html=True)

def run_async(func):
    """Run an async function in a new event loop"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(func)
    finally:
        loop.close()

def init_session_state():
    """Initialize session state variables"""
    if 'fetchai_agent' not in st.session_state:
        st.session_state.fetchai_agent = None
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'agent_task' not in st.session_state:
        st.session_state.agent_task = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    if 'sustainability_results' not in st.session_state:
        st.session_state.sustainability_results = None
    if 'login_initialized' not in st.session_state:
        st.session_state.login_initialized = False
    if 'db_session' not in st.session_state:
        st.session_state.db_session = None
    if 'last_auth_code' not in st.session_state:
        st.session_state.last_auth_code = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

def init_agent():
    """Initialize the FetchAI agent"""
    if not st.session_state.agent_initialized:
        st.session_state.fetchai_agent = EcoAgent()
        st.session_state.fetchai_agent.start()
        st.session_state.agent_initialized = True

def show_home():
    # Create a welcoming hero section
    st.markdown("""
        <div style='text-align: center; padding: 3rem 0; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 2rem;'>
            <h1 style='color: #2c3e50; font-size: 3rem; margin-bottom: 1rem;'>Welcome to EcoAgent! 🌱</h1>
            <p style='color: #6c757d; font-size: 1.2rem; margin-bottom: 2rem;'>Your AI-powered sustainability companion</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; height: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #2c3e50; margin-bottom: 1rem;'>📊 Track Progress</h3>
                <p style='color: #6c757d;'>Monitor your sustainability metrics and environmental impact in real-time through our interactive dashboard.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; height: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #2c3e50; margin-bottom: 1rem;'>🤖 AI Insights</h3>
                <p style='color: #6c757d;'>Get personalized recommendations and insights from our advanced AI assistant to improve your eco-friendly habits.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div style='background-color: white; padding: 1.5rem; border-radius: 10px; height: 200px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #2c3e50; margin-bottom: 1rem;'>📈 Analytics</h3>
                <p style='color: #6c757d;'>Dive deep into your environmental data with detailed analytics and visualization tools.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Get Started section
    st.markdown("""
        <div style='margin-top: 3rem; padding: 2rem; background-color: white; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h2 style='color: #2c3e50; margin-bottom: 1.5rem;'>Get Started</h2>
            <ol style='color: #6c757d; font-size: 1.1rem; margin-left: 1.5rem;'>
                <li style='margin-bottom: 1rem;'>View your sustainability metrics on the <b>Dashboard</b></li>
                <li style='margin-bottom: 1rem;'>Input your consumption data in the <b>Data Input</b> section</li>
                <li style='margin-bottom: 1rem;'>Analyze your environmental impact in the <b>Analytics</b> tab</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.agent_initialized:
        st.success("🤖 AI agent is initialized and ready to assist you!")

def calculate_metrics(data):
    """Calculate sustainability metrics from input data"""
    if not data:
        return None
        
    # Simple calculations (we can make these more sophisticated later)
    carbon_footprint = (
        float(data["electricity"]) * 0.0005 +  # kWh to tons CO2
        float(data["gas"]) * 0.005 +          # therms to tons CO2
        float(data["car_miles"]) * 0.0004    # miles to tons CO2
    )
    
    # Energy score based on consumption relative to average household
    avg_electricity = 877  # kWh per month
    avg_gas = 82         # therms per month
    energy_ratio = (float(data["electricity"]) / avg_electricity + float(data["gas"]) / avg_gas) / 2
    energy_score = max(0, min(100, int(100 * (1 - energy_ratio))))
    
    # Water score based on consumption relative to average
    avg_water = 3000  # gallons per month
    water_ratio = float(data["water"]) / avg_water
    water_delta = avg_water - float(data["water"])
    
    return {
        "carbon_footprint": carbon_footprint,
        "energy_score": energy_score,
        "water_usage": float(data["water"]),
        "water_delta": water_delta
    }

def load_user_data():
    """Load user's consumption data from database"""
    session = get_session()
    data = (session.query(ConsumptionData)
            .filter_by(user_id=st.session_state.db_user_id)
            .order_by(ConsumptionData.timestamp.desc())
            .all())
    return data

def show_dashboard():
    # Header with background
    st.markdown("""
        <div style='background-color: #2c3e50; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0;'>Sustainability Dashboard</h1>
            <p style='color: #a8b9cc; margin-top: 0.5rem;'>Track your environmental impact in real-time</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load historical data
    historical_data = load_user_data()
    
    if historical_data:
        try:
            # Get latest data for metrics
            latest_data = historical_data[0]
            metrics = calculate_metrics({
                "electricity": latest_data.electricity,
                "gas": latest_data.gas,
                "water": latest_data.water,
                "car_miles": latest_data.car_miles,
                "public_transport": latest_data.public_transport,
                "diet": latest_data.diet,
                "household_size": latest_data.household_size
            })
            
            # Metric cards with enhanced styling
            st.markdown("""
                <style>
                    .metric-card {
                        background-color: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    .metric-value {
                        font-size: 2rem;
                        font-weight: bold;
                        color: #1f77b4;
                        margin: 1rem 0;
                    }
                    .metric-label {
                        color: #6c757d;
                        font-size: 1.1rem;
                        margin-bottom: 0.5rem;
                    }
                    .metric-delta {
                        font-size: 0.9rem;
                        padding: 0.3rem 0.8rem;
                        border-radius: 15px;
                    }
                    .metric-delta.positive {
                        background-color: #d4edda;
                        color: #155724;
                    }
                    .metric-delta.negative {
                        background-color: #f8d7da;
                        color: #721c24;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Carbon Footprint</div>
                        <div class="metric-value">{metrics['carbon_footprint']:.2f} tons</div>
                        <span class="metric-delta positive">-0.2 tons</span>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                delta_class = "positive" if metrics['energy_score'] > 50 else "negative"
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Energy Score</div>
                        <div class="metric-value">{metrics['energy_score']}/100</div>
                        <span class="metric-delta {delta_class}">{"↑5" if metrics['energy_score'] > 50 else "↓5"}</span>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                delta_class = "positive" if metrics['water_delta'] < 0 else "negative"
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Water Usage</div>
                        <div class="metric-value">{metrics['water_usage']:.1f}L/day</div>
                        <span class="metric-delta {delta_class}">{metrics['water_delta']:.0f}L</span>
                    </div>
                """, unsafe_allow_html=True)
                
            # Add visualization
            st.subheader("Resource Usage Breakdown")
            latest_data_dict = {
                "electricity": latest_data.electricity,
                "gas": latest_data.gas,
                "water": latest_data.water,
                "car_miles": latest_data.car_miles,
                "public_transport": latest_data.public_transport,
                "diet": latest_data.diet,
                "household_size": latest_data.household_size
            }
            fig = go.Figure()
            
            # Energy usage chart
            fig.add_trace(go.Bar(
                name="Electricity",
                y=["Energy"],
                x=[float(latest_data_dict["electricity"])],
                orientation='h',
                marker_color='#1f77b4'
            ))
            
            fig.add_trace(go.Bar(
                name="Gas",
                y=["Energy"],
                x=[float(latest_data_dict["gas"])],
                orientation='h',
                marker_color='#ff7f0e'
            ))
            
            fig.update_layout(
                barmode='stack',
                height=200,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=True,
                paper_bgcolor='#2c2c2c',
                plot_bgcolor='#2c2c2c',
                font=dict(color='#ffffff'),
                xaxis=dict(
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                ),
                yaxis=dict(
                    gridcolor='#404040',
                    zerolinecolor='#404040',
                ),
                legend=dict(
                    bgcolor='#2c2c2c',
                    font=dict(color='#ffffff')
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error calculating metrics: {str(e)}")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Carbon Footprint", value="-- tons", delta=None)
        with col2:
            st.metric(label="Energy Score", value="--/100", delta=None)
        with col3:
            st.metric(label="Water Usage", value="--L/day", delta=None)
        st.info("Enter your consumption data in the Data Input page to see your sustainability metrics.")

    # Add sustainability tips section
    st.subheader("Today's Eco Tips")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.info("🌿 Tip: Turn off lights in unoccupied rooms to save energy.")
        with col2:
            st.info("💧 Tip: Fix leaky faucets to save up to 3,000 gallons per year.")

def show_data_input():
    st.header("Enter Your Sustainability Data")
    
    with st.form("sustainability_data"):
        # Energy Usage
        st.subheader("Energy Consumption")
        col1, col2 = st.columns(2)
        with col1:
            electricity = st.number_input("Monthly Electricity Usage (kWh)", min_value=0.0)
        with col2:
            gas = st.number_input("Monthly Gas Usage (therms)", min_value=0.0)
        
        # Water Usage
        st.subheader("Water Consumption")
        col1, col2 = st.columns(2)
        with col1:
            water = st.number_input("Monthly Water Usage (gallons)", min_value=0.0)
        with col2:
            st.info("💧 Average US household uses about 3,000 gallons per month")
        
        # Transportation
        st.subheader("Transportation")
        col1, col2 = st.columns(2)
        with col1:
            car_miles = st.number_input("Monthly Car Miles", min_value=0.0)
        with col2:
            public_transport = st.number_input("Monthly Public Transport Miles", min_value=0.0)
        
        # Consumption
        st.subheader("Lifestyle")
        col1, col2 = st.columns(2)
        with col1:
            diet = st.selectbox(
                "Diet Type",
                ["Meat Daily", "Meat Weekly", "Vegetarian", "Vegan"]
            )
        with col2:
            household_size = st.number_input("Household Size", min_value=1, value=1)
        
        # Submit button
        submitted = st.form_submit_button("Calculate Impact")
        if submitted:
            try:
                # Use existing session from auth if available, or create new one
                session = getattr(st.session_state, 'db_session', None) or get_session()
                
                # Create the data dictionary
                data = {
                    "electricity": electricity,
                    "gas": gas,
                    "water": water,
                    "car_miles": car_miles,
                    "public_transport": public_transport,
                    "diet": diet,
                    "household_size": household_size,
                    "timestamp": str(datetime.now())
                }
                
                # Save to database
                consumption_data = ConsumptionData(
                    user_id=st.session_state.db_user_id,
                    **{k: v for k, v in data.items() if k != 'timestamp'}
                )
                session.add(consumption_data)
                session.commit()
                
                # Create request for agent
                request = SustainabilityRequest(
                    query_type="analyze",
                    user_id=st.session_state.user['auth0_id'],
                    data=data
                )
                
                # Store in session state (though we'll primarily use database for persistence)
                st.session_state.sustainability_results = data
                
                # Show immediate feedback
                st.success("Data submitted successfully!")
                st.markdown("### Quick Analysis")
                metrics = calculate_metrics(request.data)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Carbon Footprint", f"{metrics['carbon_footprint']:.2f} tons")
                with col2:
                    st.metric("Energy Score", f"{metrics['energy_score']}/100")
                
                st.balloons()
                
                # Add a link to the dashboard
                st.markdown("📊 [View detailed analysis on the Dashboard](/#Dashboard)")
                
            except Exception as e:
                st.error(f"Error submitting data: {str(e)}")

def show_chat():
    """Show the AI chat interface"""
    st.header("Chat with EcoAgent 🤖")
    
    # Initialize the chat messages if not already done
    if not st.session_state.chat_messages:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "👋 Hello! I'm your EcoAgent AI assistant. I'm here to help you understand your environmental impact and discover personalized ways to live more sustainably. What would you like to know about?"}
        ]
    
    # Create a clean chat interface
    chat_container = st.container()
    
    # Display chat messages with typing indicators
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.write(message["content"])
    
    # Get user input with a more engaging prompt
    prompt = st.chat_input("💭 Ask me about your sustainability impact...")
    if prompt:
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Show user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get user's latest data for context
        historical_data = load_user_data()
        latest_data = historical_data[0] if historical_data else None
        
        try:
            # Create the sustainability request
            request = SustainabilityRequest(
                query_type="chat",
                user_id=st.session_state.user['auth0_id'],
                message=prompt,
                data={
                    "latest_data": {
                        "electricity": latest_data.electricity if latest_data else None,
                        "gas": latest_data.gas if latest_data else None,
                        "water": latest_data.water if latest_data else None,
                        "car_miles": latest_data.car_miles if latest_data else None,
                        "public_transport": latest_data.public_transport if latest_data else None,
                        "diet": latest_data.diet if latest_data else None,
                        "household_size": latest_data.household_size if latest_data else None
                    } if latest_data else None
                }
            )
            
            # Show thinking message with dynamic loading states
            with st.chat_message("assistant", avatar="🤖"):
                thinking_placeholder = st.empty()
                
                # Show progressive thinking states
                for state in ["🤔 Analyzing your data...", 
                            "📊 Calculating metrics...",
                            "🌱 Generating eco-friendly insights..."]:
                    thinking_placeholder.write(state)
                    time.sleep(0.7)  # Brief pause between states
                
                # Process the request through the agent
                response = st.session_state.fetchai_agent.process_request(request)
                
                if response and response.status == "success" and response.message:
                    message = response.message
                else:
                    message = "I apologize, but I'm having trouble processing your request. Please try again."
                
                # Clear thinking indicator and show response with typing effect
                thinking_placeholder.empty()
                
                # Add assistant's response to chat history
                st.session_state.chat_messages.append({"role": "assistant", "content": message})
                st.write(message)
                
                # Add a subtle success sound effect
                st.balloons()
                    
        except Exception as e:
            st.error(f"Error processing chat: {str(e)}")

def show_analytics():
    st.header("Sustainability Analytics")
    
    # Load user data from database
    historical_data = load_user_data()
    
    if historical_data:
        # Get latest data
        latest_data = historical_data[0]
        data = {
            "electricity": latest_data.electricity,
            "gas": latest_data.gas,
            "water": latest_data.water,
            "car_miles": latest_data.car_miles,
            "public_transport": latest_data.public_transport,
            "diet": latest_data.diet,
            "household_size": latest_data.household_size
        }
        metrics = calculate_metrics(data)
        
        # Resource Usage Analysis
        st.subheader("Resource Usage Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Energy breakdown
            fig_energy = go.Figure()
            fig_energy.add_trace(go.Pie(
                labels=["Electricity", "Gas"],
                values=[float(data["electricity"]), float(data["gas"])],
                hole=.3
            ))
            fig_energy.update_layout(title="Energy Usage Distribution")
            st.plotly_chart(fig_energy)
        
        with col2:
            # Water usage comparison
            fig_water = go.Figure()
            fig_water.add_trace(go.Bar(
                x=["Your Usage", "Average"],
                y=[float(data["water"]), 3000],
                marker_color=["#1f77b4", "#2ca02c"]
            ))
            fig_water.update_layout(
                title="Monthly Water Usage (gallons)",
                showlegend=False
            )
            st.plotly_chart(fig_water)
        
        # Transportation Impact
        st.subheader("Transportation Impact")
        fig_transport = go.Figure()
        fig_transport.add_trace(go.Bar(
            x=["Car", "Public Transport"],
            y=[float(data["car_miles"]), float(data["public_transport"])],
            marker_color=["#ff7f0e", "#2ca02c"]
        ))
        fig_transport.update_layout(
            title="Monthly Travel Miles",
            showlegend=False
        )
        st.plotly_chart(fig_transport)
        
        # Recommendations based on data
        st.subheader("Personalized Recommendations")
        
        # Water recommendations
        if float(data["water"]) > 3000:
            st.warning("💧 Your water usage is above average. Consider:")
            st.markdown("""
            - Installing low-flow fixtures
            - Fixing any leaks
            - Collecting rainwater for gardening
            """)
        else:
            st.success("💧 Great job on water conservation!")
        
        # Show raw data in expander
        with st.expander("View Raw Data"):
            st.json(data)
            
    else:
        st.warning("No data available. Please submit your sustainability data first.")

def show_agent_testing():
    """Show the agent testing interface in the sidebar"""
    with st.sidebar:
        st.divider()
        with st.expander("Agent Testing"):
            query_type = st.selectbox(
                "Query Type",
                ["sustainability_check", "eco_tips", "carbon_footprint"]
            )
            
            if st.button("Send Query", key="send_query_btn"):
                try:
                    request = SustainabilityRequest(
                        query_type=query_type,
                        user_id=st.session_state.user['auth0_id'],
                        data={"timestamp": str(datetime.now())}
                    )
                    st.info("Query sent! Response handling coming soon...")
                except Exception as e:
                    st.error(f"Error sending query: {str(e)}")

@require_auth
def show_protected_content():
    """Show the main application content for authenticated users"""
    # Initialize agent if not already initialized
    if not st.session_state.agent_initialized:
        with st.spinner("Initializing AI agent..."):
            init_agent()
        st.success("AI agent initialized successfully!")
    
    # Navigation
    selected_page = st.sidebar.radio(
        "Navigation",
        ["Home", "Dashboard", "Data Input", "Analytics", "AI Chat"],
        key="nav"
    )
    
    # Agent status indicator
    st.sidebar.divider()
    if st.session_state.agent_initialized:
        st.sidebar.success("Agent Status: Running")
    else:
        st.sidebar.warning("Agent Status: Not Initialized")
    
    # Show selected page content
    st.title(f"EcoAgent - {selected_page}")
    
    if selected_page == "Home":
        show_home()
    elif selected_page == "Dashboard":
        show_dashboard()
    elif selected_page == "Data Input":
        show_data_input()
    elif selected_page == "Analytics":
        show_analytics()
    elif selected_page == "AI Chat":
        show_chat()
    
    # Show agent testing interface if agent is initialized
    if st.session_state.agent_initialized:
        show_agent_testing()

def main():
    # Initialize session and auth
    init_session_state()
    init_auth()
    
    # Sidebar title
    st.sidebar.title("🌱 EcoAgent")
    
    if "user" in st.session_state:
        show_protected_content()
    else:
        st.title("Welcome to EcoAgent! 🌱")
        st.write("Please log in to access your sustainability dashboard.")

if __name__ == "__main__":
    main()
