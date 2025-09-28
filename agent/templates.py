"""Email templates for EcoAgent"""

WEEKLY_REPORT_TEMPLATE = """
Dear {name},

Here's your weekly sustainability report:

Carbon Footprint: {carbon_footprint} tons CO2/year
Energy Usage: {energy_usage} kWh
Water Usage: {water_usage} gallons
Miles Traveled: {miles_traveled} miles

Compared to US Averages:
- Carbon: {carbon_comparison}% of average
- Energy: {energy_comparison}% of average
- Water: {water_comparison}% of average
- Travel: {travel_comparison}% of average

Keep up the good work!

Best regards,
EcoAgent
"""

ECO_TIP_TEMPLATE = """
Hi {name},

Here's your daily eco-tip:

{tip}

Want to learn more? Check out our sustainability guide!

Best regards,
EcoAgent
"""

ACTION_REMINDER_TEMPLATE = """
Hi {name},

Just a friendly reminder about your eco-action:

{action}

Target completion date: {target_date}

You can do it!

Best regards,
EcoAgent
"""
