from uagents import Agent, Context
from .sustainability_analyzer import SustainabilityAnalyzer
from .agentmail_client import AgentMailClient

class EcoAgent:
    def __init__(self, api_key: str):
        self.agent = Agent(name="eco_agent", seed="eco_agent_seed")
        self.sustainability_analyzer = SustainabilityAnalyzer()
        self.agentmail_client = AgentMailClient(api_key)
        self._setup_agent()

    def _setup_agent(self):
        @self.agent.on_interval(period=3600.0)  # Run every hour
        async def check_and_notify(ctx: Context):
            """Periodic check for user data and send notifications"""
            # TODO: Implement periodic checks and notifications
            pass

        @self.agent.on_message("sustainability_query")
        async def handle_sustainability_query(ctx: Context, sender: str, message: dict):
            """Handle incoming sustainability-related queries"""
            # TODO: Implement query handling
            pass

    async def analyze_data(self, user_data: dict) -> dict:
        """Analyze user's sustainability data"""
        results = await self.sustainability_analyzer.analyze(user_data)
        return results

    async def send_report(self, user_email: str, report_data: dict):
        """Send sustainability report via AgentMail"""
        await self.agentmail_client.send_report(user_email, report_data)
