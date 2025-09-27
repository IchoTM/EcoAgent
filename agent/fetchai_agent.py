from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import Field, BaseModel

# Define models using BaseModel for better CLI compatibility
class SustainabilityData(BaseModel):
    electricity: float = Field(description="Monthly electricity usage in kWh")
    gas: float = Field(description="Monthly gas usage in therms")
    car_miles: float = Field(description="Monthly car miles driven")
    public_transport: float = Field(description="Monthly public transport miles")
    diet_type: str = Field(description="Diet type (Meat Daily, Meat Weekly, Vegetarian, Vegan)")

class SustainabilityQuery(BaseModel):
    query_type: str = Field(description="Type of sustainability query")
    user_id: str = Field(description="User identifier")
    data: Optional[SustainabilityData] = Field(default=None, description="User's sustainability data")

class SustainabilityResponse(Model):
    carbon_footprint: float = Field(description="Carbon footprint in tons CO2")
    energy_score: int = Field(description="Energy efficiency score (0-100)")
    recommendations: List[Dict[str, str]] = Field(description="List of sustainability recommendations")

# Create the protocol for sustainability queries
sustainability_protocol = Protocol("Sustainability")

class FetchAIAgent:
    def __init__(self, seed: str = "eco_agent_seed"):
        self.agent = Agent(
            name="eco_agent",
            port=8000,
            endpoint=["http://localhost:8000/submit"]
        )
        
        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            print(f"EcoAgent is starting up and listening on port 8000...")
            print(f"Ready to process sustainability queries!")

        @self.agent.on_event("shutdown")
        async def shutdown(ctx: Context):
            print("EcoAgent is shutting down...")
        
        # Fund the agent if needed
        fund_agent_if_low(self.agent.wallet.address())
        
        # Register message handlers
        self._register_handlers()

    def _register_handlers(self):
        @sustainability_protocol.on_message(model=SustainabilityQuery)
        async def handle_sustainability_query(ctx: Context, sender: str, msg: SustainabilityQuery):
            """Handle incoming sustainability queries"""
            if msg.query_type == "analyze":
                # Calculate sustainability metrics
                response = await self._analyze_sustainability(msg.data)
                # Send response back to the querying agent
                await ctx.send(sender, response)

        # Register the protocol with the agent
        self.agent.include(sustainability_protocol)

    async def _analyze_sustainability(self, data: SustainabilityData) -> SustainabilityResponse:
        """Analyze sustainability data and generate recommendations"""
        # National averages (monthly)
        AVG_ELECTRICITY = 877  # kWh per household
        AVG_GAS = 63  # therms per household
        AVG_WATER = 7000  # gallons per household
        AVG_CAR_MILES = 1000  # miles
        AVG_PUBLIC_TRANSPORT = 150  # miles

        # Constants for calculations
        ELECTRICITY_CO2_PER_KWH = 0.92  # lbs CO2 per kWh
        GAS_CO2_PER_THERM = 11.7  # lbs CO2 per therm
        CAR_CO2_PER_MILE = 0.404  # lbs CO2 per mile
        PUBLIC_TRANSPORT_CO2_PER_MILE = 0.14  # lbs CO2 per mile
        
        # Calculate carbon footprint with diet adjustments
        base_co2 = (
            data.electricity * ELECTRICITY_CO2_PER_KWH +
            data.gas * GAS_CO2_PER_THERM +
            data.car_miles * CAR_CO2_PER_MILE +
            data.public_transport * PUBLIC_TRANSPORT_CO2_PER_MILE
        )
        
        # Diet impact factors
        diet_multipliers = {
            'Meat Daily': 1.0,
            'Meat Weekly': 0.8,
            'Vegetarian': 0.6,
            'Vegan': 0.4
        }
        
        # Apply diet multiplier
        total_co2 = base_co2 * diet_multipliers.get(data.diet_type, 1.0)
        
        # Convert to tons
        carbon_footprint = total_co2 / 2000
        
        # Calculate relative metrics
        electricity_vs_avg = ((data.electricity - AVG_ELECTRICITY) / AVG_ELECTRICITY) * 100
        gas_vs_avg = ((data.gas - AVG_GAS) / AVG_GAS) * 100
        car_vs_avg = ((data.car_miles - AVG_CAR_MILES) / AVG_CAR_MILES) * 100
        
        # Calculate comprehensive energy score
        energy_score = 100
        
        # Deduct points based on usage compared to averages
        if data.electricity > AVG_ELECTRICITY:
            energy_score -= min(30, int(30 * (data.electricity/AVG_ELECTRICITY - 1)))
        if data.gas > AVG_GAS:
            energy_score -= min(20, int(20 * (data.gas/AVG_GAS - 1)))
            
        # Bonus points for good transportation habits
        transport_ratio = data.public_transport / (data.car_miles + 0.1)
        if transport_ratio > 0.5:
            energy_score += min(10, int(10 * transport_ratio))
            
        # Diet impact
        diet_scores = {'Vegan': 10, 'Vegetarian': 7, 'Meat Weekly': 3, 'Meat Daily': 0}
        energy_score += diet_scores.get(data.diet_type, 0)
        
        # Ensure score stays within bounds
        energy_score = max(0, min(100, energy_score))
        
        # Generate targeted recommendations
        recommendations = []
        
        # Electricity recommendations
        if electricity_vs_avg > 10:
            savings = (data.electricity - AVG_ELECTRICITY) * 0.12  # Assume $0.12 per kWh
            recommendations.append({
                'title': 'High Electricity Usage Detected',
                'description': f'Your electricity usage is {electricity_vs_avg:.1f}% above average.',
                'impact': f'Potential savings of ${savings:.2f}/month by reaching average consumption.'
            })
            
        # Transportation recommendations
        if car_vs_avg > 20:
            car_impact = (data.car_miles - AVG_CAR_MILES) * CAR_CO2_PER_MILE / 2000
            recommendations.append({
                'title': 'Consider Alternative Transportation',
                'description': f'Your car usage is {car_vs_avg:.1f}% above average.',
                'impact': f'You could reduce CO2 emissions by {car_impact:.2f} tons by reaching average usage.'
            })
            
        # Diet recommendations
        if data.diet_type == 'Meat Daily':
            recommendations.append({
                'title': 'Explore Plant-Based Options',
                'description': 'Daily meat consumption has a significant environmental impact.',
                'impact': 'Switching to weekly meat consumption could reduce your carbon footprint by 20%.'
            })
        
        return SustainabilityResponse(
            carbon_footprint=carbon_footprint,
            energy_score=energy_score,
            recommendations=recommendations
        )

    def _calculate_energy_score(self, data: SustainabilityData) -> int:
        """Calculate energy efficiency score"""
        # Base score starts at 100
        score = 100
        
        # Deduct points based on usage patterns
        if data.electricity > 900:  # High electricity usage
            score -= 20
        if data.gas > 50:  # High gas usage
            score -= 15
        if data.car_miles > 1000:  # High car usage
            score -= 25
        
        # Add points for positive behaviors
        if data.public_transport > 100:  # Good public transport usage
            score += 10
        if data.diet_type in ["Vegetarian", "Vegan"]:  # Sustainable diet
            score += 15
            
        return max(0, min(100, score))  # Ensure score stays between 0-100

    def _generate_recommendations(self, data: SustainabilityData) -> List[Dict[str, str]]:
        """Generate personalized sustainability recommendations"""
        recommendations = []
        
        # Electricity recommendations
        if data.electricity > 900:
            recommendations.append({
                "title": "Reduce Electricity Usage",
                "description": "Switch to LED bulbs and Energy Star appliances",
                "impact": "Save up to 20% on electricity"
            })
            
        # Transportation recommendations
        if data.car_miles > 1000 and data.public_transport < 100:
            recommendations.append({
                "title": "Increase Public Transit Usage",
                "description": "Consider using public transportation for your daily commute",
                "impact": "Reduce transportation emissions by up to 50%"
            })
            
        # Diet recommendations
        if data.diet_type == "Meat Daily":
            recommendations.append({
                "title": "Reduce Meat Consumption",
                "description": "Consider participating in Meatless Mondays",
                "impact": "Reduce your dietary carbon footprint by 15%"
            })
            
        return recommendations

    def start(self):
        """Start the Fetch.ai agent"""
        self.agent.run()

    async def stop(self):
        """Stop the Fetch.ai agent"""
        await self.agent.stop()
