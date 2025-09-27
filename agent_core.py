"""
EcoAgent core functionality
"""
import asyncio
from typing import Optional
from uagents import Agent, Context, Model

class SustainabilityRequest(Model):
    query_type: str
    data: Optional[dict] = None
    user_id: Optional[str] = None

class SustainabilityResponse(Model):
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None

import multiprocessing
import threading
import queue

class EcoAgent:
    def __init__(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        self.agent = Agent(name="eco_agent", seed="eco_agent_seed", loop=loop)
        self.setup_message_handlers()
        self._process = None
        self._running = False
        self._message_queue = queue.Queue()
        
    def setup_message_handlers(self):
        @self.agent.on_interval(period=2.0)
        async def interval_handler(ctx: Context):
            # Add periodic checks here
            pass
            
        @self.agent.on_message(model=SustainabilityRequest)
        async def message_handler(ctx: Context, sender: str, msg: SustainabilityRequest):
            # Handle incoming messages
            try:
                # Process the request
                response = SustainabilityResponse(
                    status="success",
                    data={"message": f"Processed request type: {msg.query_type}"}
                )
            except Exception as e:
                response = SustainabilityResponse(
                    status="error",
                    error=str(e)
                )
            await ctx.send(sender, response)
    def _run_agent(self):
        """Run the agent in a separate process"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.agent.run())
            
    def start(self):
        """Start the agent in a separate process"""
        if not self._running:
            self._running = True
            self._process = threading.Thread(target=self._run_agent)
            self._process.daemon = True  # Thread will be terminated when main process exits
            self._process.start()
        
    def stop(self):
        """Stop the agent"""
        if self._running:
            self._running = False
            if self._process:
                self._process.join(timeout=1.0)
