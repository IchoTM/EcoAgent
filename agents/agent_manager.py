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

def start_agents():
    """Start all agents in the bureau"""
    bureau.run()
