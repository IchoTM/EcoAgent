"""
Agent manager to handle all uAgents in the application
"""
import os
from dotenv import load_dotenv
from uagents import Bureau
from agents.eco_monitor_agent import eco_monitor
from agents.eco_advisor_agent import eco_advisor

# Load environment variables
load_dotenv()

# Get environment variables or use defaults
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8000')
AGENT_PORT = int(os.getenv('PORT', 8000))  # Render provides PORT environment variable

# Create a bureau to manage all agents
bureau = Bureau(
    endpoint=[f"{RENDER_EXTERNAL_URL}/bureau"],
    port=AGENT_PORT
)

# Add agents to the bureau
bureau.add(eco_monitor)
bureau.add(eco_advisor)

import asyncio

def start_agents():
    """Start all agents in the bureau"""
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the bureau asynchronously
        loop.create_task(bureau.run_async())
        loop.run_forever()
    except Exception as e:
        print(f"Error starting agents: {e}")
    finally:
        loop.close()
