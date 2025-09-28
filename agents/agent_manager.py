"""
Agent manager to handle all uAgents in the application
"""
from uagents import Bureau
from agents.eco_monitor_agent import eco_monitor
from agents.eco_advisor_agent import eco_advisor

# Create a bureau to manage all agents
bureau = Bureau()

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
