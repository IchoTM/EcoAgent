from datetime import datetime, timedelta
from typing import Dict, Any, Optional
print("Note: Using mock AgentMail SDK for testing")
from config.email_templates import (
    WEEKLY_REPORT_TEMPLATE,
    ECO_TIP_TEMPLATE,
    ACTION_REMINDER_TEMPLATE
)

class AgentMailClient:
    def __init__(self):
        self.email = "ecoagent@agentmail.to"
        print(f"Initialized AgentMail client with email: {self.email}")
    
    async def send_report(self, user_email: str, report_data: dict):
        """Send a sustainability report email"""
        # Format recommendations as bullet points
        recommendations_text = "\n".join(
            f"• {rec['title']}: {rec['description']}"
            for rec in report_data.get('recommendations', [])
        )
        
        content = WEEKLY_REPORT_TEMPLATE['template'].format(
            name=report_data.get('name', 'Eco Friend'),
            carbon_footprint=f"{report_data.get('carbon_footprint', 0):.1f}",
            energy_score=report_data.get('energy_score', 0),
            water_usage=report_data.get('water_usage', 0),
            recommendations=recommendations_text
        )
        
        print(f"\nMock: Sending report to {user_email}")
        print(f"Subject: {WEEKLY_REPORT_TEMPLATE['subject']}")
        print(f"Content preview: {content[:200]}...")
    
    async def schedule_eco_tips(self, user_email: str, preferences: dict):
        """Schedule and send eco-tips"""
        tip = preferences.get('tip', ECO_TIP_TEMPLATE)
        
        message = await self.agent.compose(
            recipient=user_email,
            subject=tip['subject'],
            content=tip['template'].format(
                name=preferences.get('name', 'Eco Friend'),
                tip_title=tip.get('title', 'Daily Eco Tip'),
                tip_description=tip.get('description', ''),
                tip_impact=tip.get('impact', '')
            )
        )
        await message.send()
    
    async def send_reminder(self, user_email: str, action_data: dict):
        """Send reminder emails for sustainable actions"""
        message = await self.agent.compose(
            recipient=user_email,
            subject=ACTION_REMINDER_TEMPLATE['subject'],
            content=ACTION_REMINDER_TEMPLATE['template'].format(
                name=action_data.get('name', 'Eco Friend'),
                action_description=action_data.get('description', ''),
                action_impact=action_data.get('impact', ''),
                action_deadline=action_data.get('deadline', 'soon')
            )
        )
        await message.send()
    
    async def send_campaign_message(self, user_email: str, campaign_data: dict):
        """Send a campaign message to a user"""
        message = await self.agent.compose(
            recipient=user_email,
            subject=campaign_data['subject'],
            content=campaign_data['content'].format(**campaign_data.get('variables', {}))
        )
        await message.send()
