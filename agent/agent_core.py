"""
EcoAgent core functionality - Using Google's Gemini 2.5-flash for advanced AI capabilities
"""
import asyncio
import os
import random
import threading
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import google.generativeai as genai
from uagents import Agent, Context, Model
from dotenv import load_dotenv
from database import ConsumptionData, get_session

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('google.generativeai').setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY environment variable is not set")
    logger.error("Please ensure you have:")
    logger.error("1. Created a .env file in the project root")
    logger.error("2. Added GOOGLE_API_KEY=your-api-key to the .env file")
    logger.error("3. Installed python-dotenv if not already installed")
    logger.error("4. Added 'from dotenv import load_dotenv; load_dotenv()' at the top of your script")
    raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Create a test model to verify the configuration
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Test with a simple prompt to verify complete functionality
        response = model.generate_content("Test")
        logger.info("Successfully configured and tested Gemini API")
    except Exception as model_error:
        logger.error(f"Error initializing/testing Gemini model: {str(model_error)}")
        logger.error("If you see a 'thinking' parameter error, ensure you're using google-generativeai version 0.8.5 or later")
        raise
        
except Exception as e:
    logger.error(f"Error configuring Gemini: {str(e)}")
    logger.error("Please verify your Google API key has access to the Gemini API")
    raise
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    def _get_user_consumption_data(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user's consumption data from the database"""
        session = get_session()
        try:
            from database import User  # Import User model
            
            # First get the user's ID from auth0_id
            user = session.query(User).filter_by(auth0_id=user_id).first()
            if not user:
                return {}

            # Get data from the last 30 days
            start_date = datetime.now() - timedelta(days=30)
            consumption_data = (
                session.query(ConsumptionData)
                .filter(
                    ConsumptionData.user_id == user.id,
                    ConsumptionData.timestamp >= start_date
                )
                .order_by(ConsumptionData.timestamp.desc())
                .all()
            )

            if not consumption_data:
                return {}

            # Calculate averages and totals
            total_electricity = 0
            total_gas = 0
            total_water = 0
            total_car_miles = 0
            total_days = len(consumption_data)

            for record in consumption_data:
                total_electricity += record.electricity or 0
                total_gas += record.gas or 0
                total_water += record.water or 0
                total_car_miles += record.car_miles or 0

            # Calculate daily averages
            return {
                'latest_data': {
                    'electricity': round(total_electricity / total_days, 2),
                    'gas': round(total_gas / total_days, 2),
                    'water': round(total_water / total_days, 2),
                    'car_miles': round(total_car_miles / total_days, 2)
                },
                'trends': {
                    'electricity_trend': self._calculate_trend([d.electricity for d in consumption_data if d.electricity]),
                    'gas_trend': self._calculate_trend([d.gas for d in consumption_data if d.gas]),
                    'water_trend': self._calculate_trend([d.water for d in consumption_data if d.water]),
                    'car_miles_trend': self._calculate_trend([d.car_miles for d in consumption_data if d.car_miles])
                }
            }
        finally:
            session.close()

    def _calculate_trend(self, values: list) -> str:
        """Calculate if a metric is increasing, decreasing, or stable"""
        if not values or len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100
        
        if diff_percent > 5:
            return "increasing"
        elif diff_percent < -5:
            return "decreasing"
        else:
            return "stable"

    def _generate_prompt(self, user_data: Dict[str, Any], message: str) -> str:
        """Generate a detailed context-aware prompt for Gemini"""
        trends = user_data.get('trends', {})
        latest = user_data.get('latest_data', {})

        # National averages (monthly)
        AVG_ELECTRICITY = 877  # kWh per household
        AVG_GAS = 63  # therms per household
        AVG_WATER = 7000  # gallons per household
        AVG_CAR_MILES = 1000  # miles per month

        context = f"""You are an advanced AI sustainability advisor with expertise in environmental science, 
        energy efficiency, and sustainable living. Here is the user's current consumption data and trends:

        Current Monthly Consumption:
        - Electricity: {latest.get('electricity', 'No data')} kWh (US Average: {AVG_ELECTRICITY} kWh)
        - Natural Gas: {latest.get('gas', 'No data')} therms (US Average: {AVG_GAS} therms)
        - Water: {latest.get('water', 'No data')} gallons (US Average: {AVG_WATER} gallons)
        - Car Usage: {latest.get('car_miles', 'No data')} miles (US Average: {AVG_CAR_MILES} miles)

        30-Day Trends:
        - Electricity usage is {trends.get('electricity_trend', 'unknown')}
        - Natural gas usage is {trends.get('gas_trend', 'unknown')}
        - Water consumption is {trends.get('water_trend', 'unknown')}
        - Car usage is {trends.get('car_miles_trend', 'unknown')}

        Carbon Impact Analysis:
        """

        # Calculate carbon impact using EPA emission factors
        total_carbon = 0
        
        # Electricity: 0.85 lbs CO2/kWh (EPA 2021 eGRID national average)
        if latest.get('electricity'):
            electricity_carbon = round(latest['electricity'] * 0.85, 2)
            total_carbon += electricity_carbon
            context += f"- Electricity carbon footprint: {electricity_carbon} lbs CO2/month\n"
            
        # Natural gas: 11.7 lbs CO2/therm (EPA)
        if latest.get('gas'):
            gas_carbon = round(latest['gas'] * 11.7, 2)
            total_carbon += gas_carbon
            context += f"- Natural gas carbon footprint: {gas_carbon} lbs CO2/month\n"
            
        # Vehicle: 0.404 kg CO2/mile = 0.89 lbs CO2/mile (EPA)
        if latest.get('car_miles'):
            vehicle_carbon = round(latest['car_miles'] * 0.89, 2)
            total_carbon += vehicle_carbon
            context += f"- Vehicle carbon footprint: {vehicle_carbon} lbs CO2/month\n"
            
        if total_carbon > 0:
            # Calculate national average total for comparison
            avg_total_carbon = (
                AVG_ELECTRICITY * 0.85 +  # Electricity
                AVG_GAS * 11.7 +         # Natural gas
                AVG_CAR_MILES * 0.89     # Vehicle
            )
            context += f"\nTotal monthly carbon footprint: {round(total_carbon, 2)} lbs CO2"
            context += f"\nNational average: {round(avg_total_carbon, 2)} lbs CO2\n"

        context += f"""
        User's Question: {message}

        Please provide personalized advice that:
        1. Addresses their specific consumption patterns and trends
        2. Suggests actionable improvements based on their data
        3. Compares their usage to national averages
        4. Highlights areas where they're doing well and where they need improvement
        5. Includes specific tips for reducing their environmental impact
        6. Estimates potential cost and carbon savings from suggested improvements

        Keep the response friendly, encouraging, and focused on achievable goals."""

        return context

    def setup_message_handlers(self):
        @self.agent.on_interval(period=2.0)
        async def interval_handler(ctx: Context):
            # Periodic checks can be implemented here
            pass
            
        @self.agent.on_message(model=SustainabilityRequest)
        async def message_handler(ctx: Context, sender: str, msg: SustainabilityRequest):
            try:
                if msg.query_type == "chat":
                    response_message = self._generate_chat_response(msg.message, msg.user_id, msg.data)
                    response = SustainabilityResponse(
                        status="success",
                        message=response_message,
                        data={"type": "chat"}
                    )
                else:
                    response = SustainabilityResponse(
                        status="error",
                        error="Unsupported request type"
                    )
            except Exception as e:
                response = SustainabilityResponse(
                    status="error",
                    error=str(e)
                )
            await ctx.send(sender, response)

    def _generate_chat_response(self, message: str, user_id: str, additional_data: Optional[dict] = None) -> str:
        """Generate a response using Gemini 2.5-flash with user's consumption data"""
        try:
            print(f"DEBUG: Starting chat response generation for message: {message}")
            print(f"DEBUG: User ID: {user_id}")
            
            # Get user's consumption data from database
            user_data = self._get_user_consumption_data(user_id) if user_id else {}
            print(f"DEBUG: Retrieved user data: {user_data}")
            
            # Merge with any additional data provided
            if additional_data:
                user_data.update(additional_data)

            # Generate the context-aware prompt
            prompt = self._generate_prompt(user_data, message)

            # Get response from Gemini
            try:
                # Initialize model with correct model name (without 'models/' prefix)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Add retry logic for potential network issues
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        print(f"DEBUG: Attempting to generate content (attempt {retry_count + 1})")
                        print(f"DEBUG: Prompt length: {len(prompt)} characters")
                        print(f"DEBUG: First 100 chars of prompt: {prompt[:100]}")
                        
                        response = model.generate_content(
                            prompt,
                            generation_config={
                                'temperature': 0.7,
                                'top_k': 40,
                                'top_p': 0.95,
                                'max_output_tokens': 1024,
                            }
                        )
                        
                        if response and hasattr(response, 'text') and response.text:
                            print(f"DEBUG: Successfully generated response of length: {len(response.text)}")
                            return response.text
                        
                        print(f"DEBUG: Empty response received, attempt {retry_count + 1} of {max_retries}")
                        print(f"DEBUG: Response object: {response}")
                        
                        retry_count += 1
                        if retry_count < max_retries:
                            import time
                            time.sleep(2)  # Increased wait time between retries
                    except Exception as inner_e:
                        print(f"DEBUG: Error during generation attempt {retry_count + 1}")
                        print(f"DEBUG: Error type: {type(inner_e)}")
                        print(f"DEBUG: Error message: {str(inner_e)}")
                        print(f"DEBUG: API Key length: {len(GOOGLE_API_KEY)} characters")
                        
                        retry_count += 1
                        if retry_count < max_retries:
                            import time
                            time.sleep(2)
                        else:
                            raise
                
                return "I apologize, but I encountered an issue generating a response. This might be due to an API configuration issue. Please try again later."
            except Exception as e:
                print(f"DEBUG: Error in Gemini content generation: {str(e)}")
                print(f"DEBUG: Error type: {type(e)}")
                import traceback
                print("DEBUG: Full traceback:")
                print(traceback.format_exc())
                raise
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

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
            self._process.daemon = True
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
                print(f"\nDEBUG: Processing new chat request")
                print(f"DEBUG: Message: {request.message}")
                print(f"DEBUG: User ID: {request.user_id}")
                print(f"DEBUG: Additional data: {request.data}")
                
                try:
                    message = self._generate_chat_response(
                        request.message,
                        request.user_id,
                        request.data
                    )
                    print("DEBUG: Successfully generated response")
                    
                    return SustainabilityResponse(
                        status="success",
                        message=message,
                        data={"type": "chat"}
                    )
                except Exception as chat_error:
                    print(f"DEBUG: Error in chat response generation: {str(chat_error)}")
                    import traceback
                    print("DEBUG: Full traceback:")
                    print(traceback.format_exc())
                    return SustainabilityResponse(
                            status="error",
                            error=f"Error generating response: {str(chat_error)}"
                        )
            else:
                return SustainabilityResponse(
                    status="error",
                    error="Unsupported request type"
                )
        except Exception as e:
            print(f"DEBUG: Unexpected error in process_request: {str(e)}")
            import traceback
            print("DEBUG: Full traceback:")
            print(traceback.format_exc())
            return SustainabilityResponse(
                status="error",
                error=f"Unexpected error: {str(e)}"
            )
