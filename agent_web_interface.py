"""Agent integration utilities for the web interface"""
from typing import Dict, List, Optional
from datetime import datetime
from agents.eco_monitor_agent import eco_monitor
from agents.eco_advisor_agent import eco_advisor, RecommendationRequest
from database import ConsumptionData, User, get_session

class WebAgentInterface:
    @staticmethod
    async def get_user_insights(user_id: int) -> Dict:
        """Get personalized insights for a user"""
        session = get_session()
        latest_data = session.query(ConsumptionData).filter(
            ConsumptionData.user_id == user_id
        ).order_by(ConsumptionData.timestamp.desc()).first()
        
        insights = {
            "alerts": [],
            "recommendations": [],
            "tooltips": []
        }
        
        if latest_data:
            # Get alerts from eco_monitor
            if latest_data.electricity > 100:
                insights["alerts"].append({
                    "type": "warning",
                    "message": f"Your electricity consumption ({latest_data.electricity} units) is above average.",
                    "tooltip": "Consider using energy-efficient appliances and turning off unused devices."
                })
            
            if latest_data.water > 200:
                insights["alerts"].append({
                    "type": "warning",
                    "message": f"Your water consumption ({latest_data.water} units) is high.",
                    "tooltip": "Check for leaks and consider installing water-saving fixtures."
                })
            
            # Generate personalized recommendations
            consumption_data = {
                "electricity": latest_data.electricity,
                "water": latest_data.water,
                "gas": latest_data.gas,
                "car_miles": latest_data.car_miles,
                "public_transport": latest_data.public_transport
            }
            
            # Add contextual tooltips
            if latest_data.electricity > 0:
                savings_potential = (latest_data.electricity - 100) * 0.15  # Assuming $0.15 per unit
                if savings_potential > 0:
                    insights["tooltips"].append({
                        "element_id": "electricity-chart",
                        "message": f"Potential savings of ${savings_potential:.2f} by reducing consumption to average levels.",
                        "position": "top"
                    })
            
            # Add comparative insights
            if latest_data.public_transport > 0:
                co2_saved = latest_data.public_transport * 0.14  # kg CO2 saved per mile
                insights["tooltips"].append({
                    "element_id": "transport-stats",
                    "message": f"You've saved {co2_saved:.1f}kg of CO2 by using public transport!",
                    "position": "right"
                })
        
        return insights
