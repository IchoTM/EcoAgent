from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from agentmail import AsyncAgentMail
from .templates import (
    WEEKLY_REPORT_TEMPLATE,
    ECO_TIP_TEMPLATE,
    ACTION_REMINDER_TEMPLATE
)

class AgentMailClient:
    def __init__(self, api_key: str):
        self.client = AsyncAgentMail(api_key=api_key)
        self.inbox = None
        
    async def _ensure_inbox(self):
        """Ensure we have an inbox created"""
        if not self.inbox:
            try:
                # Try to create a new inbox
                self.inbox = await self.client.inboxes.create()
                print(f"Created new inbox with ID: {self.inbox.inbox_id}")
            except Exception as e:
                print(f"Error creating inbox: {str(e)}")
                raise
        return self.inbox
        
    async def _send_message(self, to: str, subject: str, body: str):
        """Send a message using AgentMail"""
        try:
            # Basic email validation
            if not '@' in to or to.endswith('@example.com'):
                raise ValueError(f"Invalid email address: {to}")
                
            # Ensure we have an inbox
            inbox = await self._ensure_inbox()
            
            # Send message through our inbox
            sent_message = await self.client.inboxes.messages.send(
                inbox_id=inbox.inbox_id,  # Use inbox_id from the documentation
                to=to,
                subject=subject,
                text=body,  # Send as plain text
                html=f"<div>{body}</div>"  # Wrap in div for HTML formatting
            )
            return sent_message
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            raise
    
    async def send_report(self, user_email: str, report_data: dict):
        """Send a sustainability report email"""
        recommendations_text = "\n".join(
            f"• {rec['title']}: {rec['description']}"
            for rec in report_data.get('recommendations', [])
        )
        
        await self._send_message(
            to=user_email,
            subject=WEEKLY_REPORT_TEMPLATE['subject'],
            body=WEEKLY_REPORT_TEMPLATE['template'].format(
                name=report_data.get('name', 'Eco Friend'),
                carbon_footprint=f"{report_data.get('carbon_footprint', 0):.1f}",
                energy_score=report_data.get('energy_score', 0),
                water_usage=report_data.get('water_usage', 0),
                recommendations=recommendations_text
            )
        )
    
    async def send_eco_tips(self, user_email: str, eco_tip_data: dict):
        """Send eco-tips email"""
        await self._send_message(
            to=user_email,
            subject=ECO_TIP_TEMPLATE['subject'],
            body=ECO_TIP_TEMPLATE['template'].format(
                name=eco_tip_data.get('name', 'Eco Friend'),
                tip_title=eco_tip_data.get('title', ''),
                tip_description=eco_tip_data.get('description', ''),
                tip_impact=eco_tip_data.get('impact', '')
            )
        )
    
    async def send_reminder(self, user_email: str, action_data: dict):
        """Send reminder emails for sustainable actions"""
        await self._send_message(
            to=user_email,
            subject=ACTION_REMINDER_TEMPLATE['subject'],
            body=ACTION_REMINDER_TEMPLATE['template'].format(
                name=action_data.get('name', 'Eco Friend'),
                action_description=action_data.get('description', ''),
                action_impact=action_data.get('impact', ''),
                due_date=action_data.get('due_date', 
                    (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                )
            )
        )
    
    async def send_campaign_message(self, user_email: str, campaign_data: dict):
        """Send a campaign message to a user"""
        await self._send_message(
            to=user_email,
            subject=campaign_data['subject'],
            body=campaign_data['content'].format(**campaign_data.get('variables', {}))
        )
    
    async def schedule_eco_tips(self, user_email: str, preferences: dict):
        """Schedule and send eco-tips"""
        tip = preferences.get('tip', ECO_TIP_TEMPLATE)
        await self._send_message(
            to=user_email,
            subject=tip['subject'],
            body=tip['template'].format(
                name=preferences.get('name', 'Eco Friend'),
                tip_title=tip.get('title', 'Daily Eco Tip'),
                tip_description=tip.get('description', ''),
                tip_impact=tip.get('impact', '')
            )
        )
