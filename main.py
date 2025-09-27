#!/usr/bin/env python3
"""
EcoAgent - AI Sustainability Assistant
Main application entry point
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from agent_core import EcoAgent, SustainabilityRequest
from auth import init_auth, require_auth
from database import ConsumptionData, get_session

# Configure page
st.set_page_config(
    page_title="EcoAgent - Your AI Sustainability Assistant",
    page_icon="🌱",
    layout="wide"
)

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

def init_agent():
    """Initialize the FetchAI agent"""
    if not st.session_state.agent_initialized:
        st.session_state.fetchai_agent = EcoAgent()
        st.session_state.fetchai_agent.start()
        st.session_state.agent_initialized = True

def show_home():
    st.write("Welcome to EcoAgent! 🌱")
    
    # Show welcome content
    st.markdown("""
    ### Get Started
    1. View your sustainability metrics on the **Dashboard**
    2. Input your consumption data in the **Data Input** section
    3. Analyze your environmental impact in the **Analytics** tab
    
    Our AI agent is ready to help you understand and improve your environmental impact!
    """)
    
    if st.session_state.agent_initialized:
        st.success("AI agent is running and ready to assist you! 🤖")

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
    st.header("Sustainability Dashboard")
    
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
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Carbon Footprint",
                    value=f"{metrics['carbon_footprint']:.2f} tons",
                    delta="-0.2 tons"  # We can calculate this when we have historical data
                )
            with col2:
                st.metric(
                    label="Energy Score",
                    value=f"{metrics['energy_score']}/100",
                    delta="↑5" if metrics['energy_score'] > 50 else "↓5"
                )
            with col3:
                st.metric(
                    label="Water Usage",
                    value=f"{metrics['water_usage']:.1f}L/day",
                    delta=f"{metrics['water_delta']:.0f}L"
                )
                
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
                showlegend=True
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
        ["Home", "Dashboard", "Data Input", "Analytics"],
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
