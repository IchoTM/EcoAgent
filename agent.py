import asyncio
from uagents import Agent, Context

class EcoAgent:
    def __init__(self):
        self.agent = Agent(name="eco_agent", seed="eco_agent_seed")
        self.setup_message_handlers()
        
    def setup_message_handlers(self):
        @self.agent.on_interval(period=2.0)
        async def interval_handler(ctx: Context):
            # Add periodic checks here
            pass
            
        @self.agent.on_message()
        async def message_handler(ctx: Context, msg: str):
            # Handle incoming messages
            pass
            
    async def start(self):
        """Start the agent"""
        await self.agent.start()
        
    async def stop(self):
        """Stop the agent"""
        await self.agent.stop()
