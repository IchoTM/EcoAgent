import streamlit as st
import asyncio
from agent.eco_agent import EcoAgent
from agent.sustainability_analyzer import SustainabilityAnalyzer
from agent.agentmail_client import AgentMailClient
from agent.fetchai_agent import SustainabilityData, SustainabilityQuery
from config.config import load_config
import plotly.express as px

# Load configuration and initialize clients
config = load_config()
agentmail_client = AgentMailClient(api_key=config.get('AGENTMAIL_API_KEY'))

# Initialize Fetch.ai agent lazily
fetchai_agent = None

def get_fetchai_agent():
    global fetchai_agent
    if fetchai_agent is None:
        from agent.fetchai_agent import FetchAIAgent
        fetchai_agent = FetchAIAgent()
    return fetchai_agent

# Page configuration
st.set_page_config(
    page_title="EcoAgent - Your AI Sustainability Assistant",
    page_icon="🌱",
    layout="wide"
)

def main():
    st.title("🌱 EcoAgent - AI Sustainability Assistant")
    
    # Sidebar for navigation
    page = st.sidebar.selectbox(
        "Navigate",
        ["Dashboard", "Data Input", "Reports", "Settings"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Input":
        show_data_input()
    elif page == "Reports":
        show_reports()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    st.header("Your Sustainability Dashboard")
    
    # Placeholder for sustainability metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Carbon Footprint", value="2.5 tons", delta="-0.2 tons")
    with col2:
        st.metric(label="Energy Score", value="85/100", delta="↑5")
    with col3:
        st.metric(label="Water Usage", value="150L/day", delta="-10L")

def show_data_input():
    st.header("Enter Your Sustainability Data")
    
    with st.form("sustainability_data"):
        # Energy Usage
        st.subheader("Energy Consumption")
        electricity = st.number_input("Monthly Electricity Usage (kWh)", min_value=0.0)
        gas = st.number_input("Monthly Gas Usage (therms)", min_value=0.0)
        
        # Transportation
        st.subheader("Transportation")
        car_miles = st.number_input("Monthly Car Miles", min_value=0.0)
        public_transport = st.number_input("Monthly Public Transport Miles", min_value=0.0)
        
        # Consumption
        st.subheader("Lifestyle")
        diet = st.selectbox(
            "Diet Type",
            ["Meat Daily", "Meat Weekly", "Vegetarian", "Vegan"]
        )
        
        submitted = st.form_submit_button("Calculate Impact")
        if submitted:
            # Create sustainability data model
            try:
                sustainability_data = SustainabilityData(
                    electricity=float(electricity),
                    gas=float(gas),
                    car_miles=float(car_miles),
                    public_transport=float(public_transport),
                    diet_type=diet
                )
                
                # Create query for the Fetch.ai agent
                query = SustainabilityQuery(
                    query_type="analyze",
                    user_id=st.session_state.get("user_id", "anonymous"),
                    data=sustainability_data
                )
            except ValueError as e:
                st.error(f"Please enter valid numbers for all fields: {str(e)}")
                return
            
            try:
                # Get analysis from Fetch.ai agent
                agent = get_fetchai_agent()
                
                # Create a new event loop in this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Run the analysis in the new event loop
                    response = loop.run_until_complete(agent._analyze_sustainability(query.data))
                finally:
                    # Clean up the event loop
                    loop.close()
                    asyncio.set_event_loop(None)
                
                # Store results in session state
                st.session_state.sustainability_results = response
                
                # Show success message
                st.success("Data analyzed successfully!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Carbon Footprint", f"{response.carbon_footprint:.2f} tons CO2")
                with col2:
                    st.metric("Energy Score", f"{response.energy_score}/100")
                with col3:
                    st.write("Top Recommendations:")
                    for rec in response.recommendations:
                        st.write(f"• {rec['title']}")
                
                # Send report via AgentMail if email is configured
                if st.session_state.get("email"):
                    # Create a new event loop for sending email
                    email_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(email_loop)
                    try:
                        email_loop.run_until_complete(agentmail_client.send_report(
                            st.session_state.email,
                            {
                                "carbon_footprint": response.carbon_footprint,
                                "energy_score": response.energy_score,
                                "recommendations": response.recommendations
                            }
                        ))
                    finally:
                        email_loop.close()
                        asyncio.set_event_loop(None)
            except Exception as e:
                st.error(f"Error analyzing data: {str(e)}")

def show_reports():
    st.header("Sustainability Reports")
    # Placeholder for report generation interface
    st.info("Report generation features coming soon!")

def show_settings():
    st.header("Settings")
    
    # Email Preferences
    st.subheader("Email Notifications")
    with st.form("email_preferences"):
        email = st.text_input("Email Address")
        name = st.text_input("Your Name")
        weekly_report = st.checkbox("Receive Weekly Sustainability Reports")
        eco_tips = st.checkbox("Receive Daily Eco-Tips")
        reminder_frequency = st.selectbox(
            "Action Reminder Frequency",
            ["Daily", "Weekly", "Monthly", "Never"]
        )
        preferred_time = st.time_input("Preferred Email Time", value=None)
        timezone = st.selectbox(
            "Your Timezone",
            ["UTC", "US/Eastern", "US/Central", "US/Pacific"]
        )
        
        submitted = st.form_submit_button("Save Settings")
        if submitted and email:
            try:
                # Prepare preferences
                preferences = {
                    "name": name,
                    "preferred_time": preferred_time.strftime("%H:%M") if preferred_time else "09:00",
                    "timezone": timezone,
                    "user_id": email.lower()  # Using email as user_id for now
                }
                
                # Create and run async tasks for email settings
                settings_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(settings_loop)
                
                try:
                    async def update_email_settings():
                        if weekly_report:
                            await agentmail_client.schedule_eco_tips(
                                email,
                                {**preferences, "frequency": "weekly"}
                            )
                        
                        if eco_tips:
                            await agentmail_client.schedule_eco_tips(
                                email,
                                {**preferences, "frequency": "daily"}
                            )
                        
                        if reminder_frequency != "Never":
                            await agentmail_client.create_campaign(
                                f"eco_reminders_{email}",
                                {
                                    "email": email,
                                    "frequency": reminder_frequency.lower()
                                }
                            )
                    
                    # Run the async tasks in the new event loop
                    settings_loop.run_until_complete(update_email_settings())
                finally:
                    settings_loop.close()
                    asyncio.set_event_loop(None)
                
                st.success("Email preferences saved successfully! You'll start receiving your personalized eco-updates soon.")
            except Exception as e:
                st.error(f"Error saving preferences: {str(e)}")
        elif submitted:
            st.warning("Please enter your email address.")

if __name__ == "__main__":
    main()
