"""
EcoAgent core functionality
"""
import asyncio
import random
from typing import Optional
from uagents import Agent, Context, Model

class SustainabilityRequest(Model):
    query_type: str
    data: Optional[dict] = None
    user_id: Optional[str] = None
    message: Optional[str] = None

class SustainabilityResponse(Model):
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None

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
                if msg.query_type == "chat":
                    # Process chat message and generate response
                    response_message = await ctx.agent.generate_response(msg.message, msg.data)
                    response = SustainabilityResponse(
                        status="success",
                        message=response_message,
                        data={"type": "chat"}
                    )
                else:
                    # Handle other request types
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
                
    def process_request(self, request: SustainabilityRequest) -> SustainabilityResponse:
        """Process a request synchronously and return the response"""
        try:
            if request.query_type == "chat":
                # Add artificial thinking time with a progress spinner
                import time
                import streamlit as st
                
                with st.spinner("🤔 Analyzing your sustainability data..."):
                    # Add randomized thinking time between 1-2 seconds
                    time.sleep(1 + random.random())
                    
                    # Generate response based on request type and user data
                    message = self._generate_chat_response(request.message, request.data)
                    
                    # Add slight pause before showing response
                    time.sleep(0.5)
                    
                return SustainabilityResponse(
                    status="success",
                    message=message,
                    data={"type": "chat"}
                )
            else:
                return SustainabilityResponse(
                    status="error",
                    error="Unsupported request type"
                )
        except Exception as e:
            return SustainabilityResponse(
                status="error",
                error=str(e)
            )
    
    def _generate_chat_response(self, message: str, data: dict) -> str:
        """Generate a response to a chat message using the user's data"""
        try:
            # Get the user's latest sustainability data
            latest_data = data.get('latest_data') if data else None
            
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
            
            if "electricity" in message.lower() or "energy" in message.lower():
                if latest_data and latest_data.get('electricity'):
                    kwh = latest_data['electricity']
                    vs_avg = ((kwh - AVG_ELECTRICITY) / AVG_ELECTRICITY) * 100
                    monthly_cost = kwh * 0.12  # Assuming $0.12 per kWh
                    potential_savings = max(0, (kwh - AVG_ELECTRICITY) * 0.12)
                    
                    response = [
                        f"📊 Current Electricity Analysis:",
                        f"• Usage: {kwh:.1f} kWh/month",
                        f"• Compared to Average: {'↑' if vs_avg > 0 else '↓'}{abs(vs_avg):.1f}%",
                        f"• Estimated Monthly Cost: ${monthly_cost:.2f}",
                        f"• CO2 Impact: {(kwh * ELECTRICITY_CO2_PER_KWH / 2000):.2f} tons",
                        "",
                        "🎯 Personalized Recommendations:"
                    ]
                    
                    if vs_avg > 0:
                        response.extend([
                            f"You could save ${potential_savings:.2f}/month by reaching average consumption:",
                            "1. Replace traditional bulbs with LEDs (75% less energy)",
                            "2. Use smart power strips for electronics (saves 5-10%)",
                            "3. Upgrade to Energy Star appliances (15-50% savings)",
                            "4. Install a programmable thermostat (10-15% HVAC savings)"
                        ])
                    else:
                        response.extend([
                            "You're doing better than average! To further improve:",
                            "1. Consider solar panel installation",
                            "2. Explore home energy storage solutions",
                            "3. Share your energy-saving practices with others"
                        ])
                    
                    return "\n".join(response)
                
            elif "water" in message.lower():
                if latest_data and latest_data.get('water'):
                    gallons = latest_data['water']
                    vs_avg = ((gallons - AVG_WATER) / AVG_WATER) * 100
                    monthly_cost = gallons * 0.01  # Assuming $0.01 per gallon
                    
                    response = [
                        f"💧 Water Usage Analysis:",
                        f"• Usage: {gallons:.1f} gallons/month",
                        f"• Compared to Average: {'↑' if vs_avg > 0 else '↓'}{abs(vs_avg):.1f}%",
                        f"• Estimated Monthly Cost: ${monthly_cost:.2f}",
                        "",
                        "🎯 Water Conservation Tips:"
                    ]
                    
                    if vs_avg > 0:
                        response.extend([
                            f"Potential monthly savings: {(gallons - AVG_WATER) * 0.01:.2f}",
                            "1. Fix leaks (save up to 180 gallons/week)",
                            "2. Install low-flow fixtures (save 30-50%)",
                            "3. Use rain barrels for garden (save ~1,300 gallons)",
                            "4. Run full loads of laundry (save 15-45 gallons/load)"
                        ])
                    else:
                        response.extend([
                            "You're below average! Additional tips:",
                            "1. Install a greywater system",
                            "2. Consider drought-resistant landscaping",
                            "3. Share water conservation tips with neighbors"
                        ])
                    
                    return "\n".join(response)
                
            elif "transport" in message.lower() or "car" in message.lower():
                if latest_data:
                    car_miles = latest_data.get('car_miles', 0)
                    public_miles = latest_data.get('public_transport', 0)
                    car_vs_avg = ((car_miles - AVG_CAR_MILES) / AVG_CAR_MILES) * 100
                    
                    car_co2 = (car_miles * CAR_CO2_PER_MILE / 2000)
                    transport_ratio = public_miles / (car_miles + 0.1)
                    
                    response = [
                        f"🚗 Transportation Analysis:",
                        f"• Car Usage: {car_miles:.1f} miles/month",
                        f"• Public Transit: {public_miles:.1f} miles/month",
                        f"• Compared to Average: {'↑' if car_vs_avg > 0 else '↓'}{abs(car_vs_avg):.1f}%",
                        f"• CO2 Impact: {car_co2:.2f} tons/month",
                        "",
                        "🎯 Transportation Recommendations:"
                    ]
                    
                    if car_vs_avg > 0:
                        savings = (car_miles - AVG_CAR_MILES) * 0.50  # Assuming $0.50/mile
                        response.extend([
                            f"Potential monthly savings: ${savings:.2f}",
                            "1. Try carpooling (save 50-75% on commute costs)",
                            "2. Use public transit for regular routes",
                            "3. Combine errands into single trips",
                            "4. Consider an electric/hybrid vehicle"
                        ])
                    else:
                        response.extend([
                            "You're below average in car usage! To further improve:",
                            "1. Consider bike-sharing programs",
                            "2. Explore walking routes for short trips",
                            "3. Share your sustainable transport habits"
                        ])
                    
                    return "\n".join(response)
                
            elif "carbon" in message.lower() or "footprint" in message.lower():
                if latest_data:
                    # Calculate carbon footprint components
                    electricity_impact = float(latest_data.get('electricity', 0)) * ELECTRICITY_CO2_PER_KWH / 2000
                    gas_impact = float(latest_data.get('gas', 0)) * GAS_CO2_PER_THERM / 2000
                    car_impact = float(latest_data.get('car_miles', 0)) * CAR_CO2_PER_MILE / 2000
                    
                    # Diet impact factors
                    diet_multipliers = {
                        'Meat Daily': 1.0,
                        'Meat Weekly': 0.8,
                        'Vegetarian': 0.6,
                        'Vegan': 0.4
                    }
                    
                    diet_factor = diet_multipliers.get(latest_data.get('diet', 'Meat Daily'), 1.0)
                    total_impact = (electricity_impact + gas_impact + car_impact) * diet_factor
                    
                    response = [
                        f"🌍 Carbon Footprint Analysis:",
                        f"Total Impact: {total_impact:.2f} tons CO2/month",
                        "",
                        "Breakdown by Source:",
                        f"• Electricity: {electricity_impact:.2f} tons ({(electricity_impact/total_impact*100):.1f}%)",
                        f"• Natural Gas: {gas_impact:.2f} tons ({(gas_impact/total_impact*100):.1f}%)",
                        f"• Transportation: {car_impact:.2f} tons ({(car_impact/total_impact*100):.1f}%)",
                        "",
                        "🎯 Impact Reduction Opportunities:"
                    ]
                    
                    # Target recommendations based on largest contributors
                    impacts = [
                        ("electricity", electricity_impact),
                        ("gas", gas_impact),
                        ("transportation", car_impact)
                    ]
                    
                    top_contributor = max(impacts, key=lambda x: x[1])[0]
                    
                    if top_contributor == "electricity":
                        response.extend([
                            "Your largest impact comes from electricity usage:",
                            "1. Switch to renewable energy provider",
                            "2. Invest in solar panels",
                            "3. Upgrade to energy-efficient appliances"
                        ])
                    elif top_contributor == "gas":
                        response.extend([
                            "Your largest impact comes from natural gas usage:",
                            "1. Improve home insulation",
                            "2. Install a smart thermostat",
                            "3. Consider heat pump alternatives"
                        ])
                    else:
                        response.extend([
                            "Your largest impact comes from transportation:",
                            "1. Consider an electric vehicle",
                            "2. Use public transportation more often",
                            "3. Explore carpooling options"
                        ])
                    
                    return "\n".join(response)
            
            # General sustainability analysis
            # General sustainability analysis
            if latest_data:
                scores = []
                
                # Calculate energy score
                if 'electricity' in latest_data:
                    if latest_data['electricity'] is not None:
                        vs_avg = ((latest_data['electricity'] - AVG_ELECTRICITY) / AVG_ELECTRICITY) * 100
                        scores.append(("Energy", max(0, min(100, 100 - vs_avg))))
                
                # Calculate water score        
                if 'water' in latest_data:
                    if latest_data['water'] is not None:
                        vs_avg = ((latest_data['water'] - AVG_WATER) / AVG_WATER) * 100
                        scores.append(("Water", max(0, min(100, 100 - vs_avg))))
                
                # Calculate transportation score
                if 'car_miles' in latest_data:
                    if latest_data['car_miles'] is not None:
                        vs_avg = ((latest_data['car_miles'] - AVG_CAR_MILES) / AVG_CAR_MILES) * 100
                        scores.append(("Transportation", max(0, min(100, 100 - vs_avg))))
                
                response = [
                    "📊 Overall Sustainability Analysis:",
                    "",
                    "Performance Scores (100 = Best):"
                ]
                
                for category, score in scores:
                    response.append(f"• {category}: {score:.0f}/100 {'✅' if score >= 80 else '⚠️' if score >= 50 else '❌'}")
                
                response.extend([
                    "",
                    "💡 What would you like to know more about?",
                    "• Type 'electricity' for energy analysis",
                    "• Type 'water' for water usage details",
                    "• Type 'transport' for transportation impact",
                    "• Type 'carbon' for your carbon footprint"
                ])
                
                return "\n".join(response)
            
            # Default response for no data
            return (
                "I can help analyze your sustainability metrics and provide personalized recommendations. "
                "Please provide your consumption data first, and then ask me about:\n"
                "• Electricity usage and energy efficiency\n"
                "• Water consumption patterns\n"
                "• Transportation impact\n"
                "• Overall carbon footprint"
            )
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
