#!/usr/bin/env python3
"""
EcoAgent - AI Sustainability Assistant
Main application entry point
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import streamlit as st
from agent_core import EcoAgent, SustainabilityRequest

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

def init_agent():
    """Initialize the FetchAI agent"""
    if not st.session_state.agent_initialized:
        st.session_state.fetchai_agent = EcoAgent()
        st.session_state.fetchai_agent.start()
        st.session_state.agent_initialized = True

def main():
    init_session_state()
    st.title("🌱 EcoAgent - AI Sustainability Assistant")
    st.write("Welcome to EcoAgent! Select a page from the sidebar to get started.")
    
    if not st.session_state.agent_initialized:
        if st.button("Initialize Agent", key="init_agent_btn"):
            with st.spinner("Initializing agent..."):
                init_agent()
            st.success("Agent initialized successfully!")
    else:
        st.success("Agent is running!")
        
        # Add test interface when agent is running
        with st.expander("Test Agent"):
            query_type = st.selectbox(
                "Query Type",
                ["sustainability_check", "eco_tips", "carbon_footprint"]
            )
            
            if st.button("Send Query", key="send_query_btn"):
                try:
                    # Create test request
                    request = SustainabilityRequest(
                        query_type=query_type,
                        user_id="test_user",
                        data={"timestamp": str(datetime.now())}
                    )
                    # TODO: Implement message sending mechanism
                    st.info("Query sent! Response handling coming soon...")
                except Exception as e:
                    st.error(f"Error sending query: {str(e)}")

if __name__ == "__main__":
    main()
