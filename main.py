import streamlit as st
import asyncio
from agent.eco_agent import EcoAgent
from agent.sustainability_analyzer import SustainabilityAnalyzer
from agent.agentmail_client import AgentMailClient
from config.config import load_config
import plotly.express as px

# Initialize clients
agentmail_client = AgentMailClient()

# Initialize Fetch.ai agent
from agent.fetchai_agent import FetchAIAgent
fetchai_agent = FetchAIAgent()

# Start the Fetch.ai agent in the background
import threading
agent_thread = threading.Thread(target=fetchai_agent.start, daemon=True)
agent_thread.start()

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
            sustainability_data = {
                "electricity": electricity,
                "gas": gas,
                "car_miles": car_miles,
                "public_transport": public_transport,
                "diet_type": diet
            }
            
            # Create query for the Fetch.ai agent
            query = SustainabilityQuery(
                query_type="analyze",
                user_id=st.session_state.get("user_id", "anonymous"),
                data=SustainabilityData(**sustainability_data)
            )
            
            try:
                # Get analysis from Fetch.ai agent
                response = asyncio.run(fetchai_agent._analyze_sustainability(query.data))
                
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
                    asyncio.run(agentmail_client.send_report(
                        st.session_state.email,
                        {
                            "carbon_footprint": response.carbon_footprint,
                            "energy_score": response.energy_score,
                            "recommendations": response.recommendations
                        }
                    ))
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
                
                # Create async tasks for email settings
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
                
                # Run async tasks
                asyncio.run(update_email_settings())
                
                st.success("Email preferences saved successfully! You'll start receiving your personalized eco-updates soon.")
            except Exception as e:
                st.error(f"Error saving preferences: {str(e)}")
        elif submitted:
            st.warning("Please enter your email address.")

if __name__ == "__main__":
    main()
