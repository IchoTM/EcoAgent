"""Email template definitions for various notification types"""

WEEKLY_REPORT_TEMPLATE = {
    'subject': 'Your Weekly Sustainability Report',
    'template': """
    Hi {name},
    
    Here's your weekly sustainability update:
    
    🌡️ Carbon Footprint: {carbon_footprint} tons CO2
    ⚡ Energy Score: {energy_score}/100
    💧 Water Usage: {water_usage}L
    
    Top Recommendations:
    {recommendations}
    
    Keep up the great work in making our planet greener!
    
    Best regards,
    Your EcoAgent 🌱
    """
}

ECO_TIP_TEMPLATE = {
    'subject': 'Your Daily Eco-Tip',
    'template': """
    Hi {name},
    
    Here's your daily eco-friendly tip:
    
    {tip_title}
    
    {tip_description}
    
    Impact: {tip_impact}
    
    Small changes make a big difference!
    
    Best regards,
    Your EcoAgent 🌱
    """
}

ACTION_REMINDER_TEMPLATE = {
    'subject': 'Sustainability Action Reminder',
    'template': """
    Hi {name},
    
    This is a friendly reminder about your sustainable action goal:
    
    {action_description}
    
    Expected Impact: {action_impact}
    
    You can do this! 💪
    
    Best regards,
    Your EcoAgent 🌱
    """
}
