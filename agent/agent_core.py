import os
import logging
import google.generativeai as genai
from uagents import Agent, Context, Model
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from database import ConsumptionData, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set")

genai.configure(api_key=GOOGLE_API_KEY)
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# Environmental constants (US averages)
AVG_ELECTRICITY = 893  # kWh/month
AVG_GAS = 567         # therms/year
AVG_CAR_MILES = 1146  # miles/month

class SustainabilityRequest(Model):
    query_type: str
    user_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None

class SustainabilityResponse(Model):
    status: str
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None

class EcoAgent:
    def __init__(self):
        self.agent = Agent(
            name="eco_agent",
            seed="eco_agent_seed"
        )
        self.setup_message_handlers()

    def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        try:
            session = get_session()
            data = session.query(ConsumptionData).filter(
                ConsumptionData.user_id == user_id
            ).order_by(
                ConsumptionData.timestamp.desc()
            ).first()
            
            if not data:
                return {}
                
            return {
                "electricity": data.electricity,
                "gas": data.gas,
                "car_miles": data.car_miles,
                "timestamp": data.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"Database error: {e}")
            return {}

    def _build_prompt(self, user_data: Dict[str, Any], query: str) -> str:
        prompt = []
        total_carbon = 0

        if user_data:
            if "electricity" in user_data:
                elec_carbon = user_data["electricity"] * 0.85
                total_carbon += elec_carbon
                prompt.append(f"Electricity: {user_data['electricity']} kWh/month")
                prompt.append(f"Electricity CO2: {elec_carbon:.2f} lbs/month")

            if "gas" in user_data:
                gas_carbon = user_data["gas"] * 11.7
                total_carbon += gas_carbon
                prompt.append(f"Natural gas: {user_data['gas']} therms/month")
                prompt.append(f"Gas CO2: {gas_carbon:.2f} lbs/month")

            if "car_miles" in user_data:
                car_carbon = user_data["car_miles"] * 0.89
                total_carbon += car_carbon
                prompt.append(f"Driving: {user_data['car_miles']} miles/month")
                prompt.append(f"Vehicle CO2: {car_carbon:.2f} lbs/month")

            if total_carbon > 0:
                avg_carbon = (
                    AVG_ELECTRICITY * 0.85 +
                    (AVG_GAS / 12) * 11.7 +
                    AVG_CAR_MILES * 0.89
                )
                prompt.append(f"\nTotal CO2: {total_carbon:.2f} lbs/month")
                prompt.append(f"US Average: {avg_carbon:.2f} lbs/month")

        prompt_text = "\n".join([
            "Analyze this environmental impact data:",
            *prompt,
            f"\nUser Question: {query}",
            "\nProvide eco-friendly advice that:",
            "1. Analyzes their consumption patterns",
            "2. Suggests practical improvements",
            "3. Compares to national averages",
            "4. Highlights achievements and areas for improvement",
            "5. Gives specific sustainability tips",
            "6. Estimates environmental impact of suggestions",
            "\nKeep the response encouraging and practical."
        ])

        return prompt_text

    def _generate_response(self, message: str, user_id: str = None, extra_data: Optional[dict] = None) -> str:
        try:
            user_data = self._get_user_data(user_id)
            if extra_data:
                user_data.update(extra_data)
            
            prompt = self._build_prompt(user_data, message)
            
            # Format content for gemini-2.5-flash
            content = [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]
            
            response = MODEL.generate_content(
                contents=content,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            if not response or not hasattr(response, 'text'):
                raise ValueError("No response generated")
                
            return response.text.strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            logger.error(f"Error details: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

    def process_request(self, request: SustainabilityRequest) -> SustainabilityResponse:
        try:
            if request.query_type != "chat":
                return SustainabilityResponse(
                    status="error",
                    error="Unsupported request type"
                )

            message = self._generate_response(
                request.message,
                request.user_id,
                request.data
            )
            
            return SustainabilityResponse(
                status="success",
                message=message,
                data={"type": "chat"}
            )
        except Exception as e:
            logger.error(f"Request error: {e}")
            return SustainabilityResponse(
                status="error",
                error=str(e)
            )

    def setup_message_handlers(self):
        @self.agent.on_message(model=SustainabilityRequest)
        async def handle_message(ctx: Context, sender: str, msg: SustainabilityRequest):
            try:
                response = self.process_request(msg)
                await ctx.send(sender, response)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                await ctx.send(sender, SustainabilityResponse(
                    status="error",
                    error=str(e)
                ))
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

genai.configure(api_key=GOOGLE_API_KEY)
MODEL = genai.GenerativeModel("gemini-pro")

AVG_ELECTRICITY = 893
AVG_GAS = 567
AVG_CAR_MILES = 1146

import os
import logging
import google.generativeai as genai
from uagents import Agent, Context, Model
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from database import ConsumptionData, get_session
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)
MODEL = genai.GenerativeModel("gemini-pro")

# Constants for environmental calculations
AVG_ELECTRICITY = 893  # kWh/month (US average)
AVG_GAS = 567         # Therms/year (US average)
AVG_CAR_MILES = 1146  # Miles/month (US average)

class SustainabilityRequest(Model):
    query_type: str
    user_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None

class SustainabilityResponse(Model):
    status: str
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None

class EcoAgent:
    
    def __init__(self):
        self.agent = Agent(
            name="eco_agent",
            seed="eco_agent_seed"
        )
        self.setup_message_handlers()

    def _get_user_consumption_data(self, user_id: str) -> Dict[str, Any]:
        try:
            session = get_session()
            data = session.query(ConsumptionData).filter(
                ConsumptionData.user_id == user_id
            ).order_by(
                ConsumptionData.timestamp.desc()
            ).first()
            
            if data:
                return {
                    "electricity": data.electricity,
                    "gas": data.gas,
                    "car_miles": data.car_miles,
                    "timestamp": data.timestamp.isoformat()
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching consumption data: {str(e)}")
            return {}

    def _generate_sustainability_prompt(self, user_data: Dict[str, Any], query: str) -> str:
        prompt = "As an eco-friendly AI assistant, analyze the following data and query:\n\n"
        
        if user_data:
            latest = user_data
            total_carbon = 0
            
            if latest.get("electricity"):
                elec_carbon = round(latest["electricity"] * 0.85, 2)
                total_carbon += elec_carbon
                prompt += f"Electricity usage: {latest['electricity']} kWh/month\n"
                prompt += f"Electricity carbon footprint: {elec_carbon} lbs CO2/month\n"
            
            if latest.get("gas"):
                gas_carbon = round(latest["gas"] * 11.7, 2)
                total_carbon += gas_carbon
                prompt += f"Natural gas usage: {latest['gas']} therms/month\n"
                prompt += f"Gas carbon footprint: {gas_carbon} lbs CO2/month\n"
            
            if latest.get("car_miles"):
                vehicle_carbon = round(latest["car_miles"] * 0.89, 2)
                total_carbon += vehicle_carbon
                prompt += f"Monthly driving: {latest['car_miles']} miles\n"
                prompt += f"Vehicle carbon footprint: {vehicle_carbon} lbs CO2/month\n"
            
            if total_carbon > 0:
                avg_total_carbon = (
                    AVG_ELECTRICITY * 0.85 +
                    (AVG_GAS / 12) * 11.7 +
                    AVG_CAR_MILES * 0.89
                )
                prompt += f"\nTotal monthly carbon footprint: {round(total_carbon, 2)} lbs CO2\n"
                prompt += f"National average: {round(avg_total_carbon, 2)} lbs CO2\n\n"

        prompt += f"""
User Question: {query}

Provide eco-friendly advice that:
1. Addresses specific consumption patterns
2. Suggests practical improvements
3. Compares to averages when relevant
4. Highlights both achievements and areas for improvement
5. Gives actionable sustainability tips
6. Estimates potential environmental impact of suggestions

Keep responses encouraging, practical, and focused on achievable goals."""

        return prompt

    def _generate_chat_response(self, message: str, user_id: str = None, additional_data: Optional[dict] = None) -> str:
        try:
            user_data = self._get_user_consumption_data(user_id)
            if additional_data:
                user_data.update(additional_data)
            
            prompt = self._generate_sustainability_prompt(user_data, message)
            response = MODEL.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("No response generated from AI model")
                
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try again or rephrase your question."

    def process_request(self, request: SustainabilityRequest) -> SustainabilityResponse:
        try:
            if request.query_type == "chat":
                message = self._generate_chat_response(
                    request.message,
                    request.user_id,
                    request.data
                )
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
            logger.error(f"Error processing request: {str(e)}")
            return SustainabilityResponse(
                status="error",
                error=f"Error: {str(e)}"
            )

    def setup_message_handlers(self):
        @self.agent.on_message(model=SustainabilityRequest)
        async def handle_message(ctx: Context, sender: str, msg: SustainabilityRequest):
            try:
                response = self.process_request(msg)
                await ctx.send(sender, response)
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
                error_response = SustainabilityResponse(
                    status="error",
                    error=f"Error processing message: {str(e)}"
                )
                await ctx.send(sender, error_response)
    
try:
    # Configure Gemini globally
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Test the configuration
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        if response.text:
            logger.info("Successfully configured and tested Gemini API")
        else:
            raise ValueError("Empty response from Gemini API test")
    except Exception as model_error:
        logger.error(f"Error initializing/testing Gemini model: {str(model_error)}")
        logger.error("If you see API errors, verify your API key has access to the Gemini API")
        raise
except Exception as e:
    logger.error(f"Error configuring Gemini: {str(e)}")
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
        """Retrieve user consumption data from the database"""
        session = get_session()
        try:
            from database import User  # Import User model
            
            # First get the user ID from auth0_id
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

        context = f"""As an advanced AI sustainability advisor with expertise in environmental science, energy efficiency, and sustainable living, analyze this user data:

Monthly Consumption Data:
* Electricity: {latest.get('electricity', 'No data')} kWh (Average: {AVG_ELECTRICITY} kWh)
* Natural Gas: {latest.get('gas', 'No data')} therms (Average: {AVG_GAS} therms)
* Water: {latest.get('water', 'No data')} gallons (Average: {AVG_WATER} gallons)
* Car Usage: {latest.get('car_miles', 'No data')} miles (Average: {AVG_CAR_MILES} miles)

Recent Trends:
* Electricity: {trends.get('electricity_trend', 'unknown')}
* Natural Gas: {trends.get('gas_trend', 'unknown')}
* Water: {trends.get('water_trend', 'unknown')}
* Car Usage: {trends.get('car_miles_trend', 'unknown')}

User Question: {message}

Provide a helpful, friendly response focused on sustainability and environmental impact. Use bullet points for any recommendations."""

        total_carbon = 0
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
Question: {message}

Please provide personalized advice that:
1. Addresses their specific consumption patterns and trends
2. Suggests actionable improvements based on their data
3. Compares their usage to national averages
4. Highlights areas where they are doing well and where they need improvement
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
        """Generate a response using Gemini Pro with the user consumption data"""
        try:
            logger.info(f"Starting chat response generation for user: {user_id}")
            
            # Get user consumption data from database
            user_data = self._get_user_consumption_data(user_id) if user_id else {}
            
            # Merge with any additional data provided
            if additional_data:
                user_data.update(additional_data)

            # Generate the context-aware prompt
            prompt = self._generate_prompt(user_data, message)

            # Get response from Gemini
            try:
                # Use the globally configured Gemini instance
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Add retry logic for potential network issues
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        logger.info(f"Attempting to generate content (attempt {retry_count + 1})")
                        
                        # Start a chat session
                        chat = model.start_chat(history=[])
                        response = chat.send_message(prompt, generation_config={
                            'temperature': 0.7,
                            'top_p': 0.95,
                            'max_output_tokens': 1024,
                        })
                        
                        if response and response.text:
                            logger.info(f"Successfully generated response")
                            return response.text
                        
                        logger.warning(f"Empty response received, attempt {retry_count + 1} of {max_retries}")
                        retry_count += 1
                        if retry_count < max_retries:
                            import time
                            time.sleep(2)  # Wait between retries
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
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.agent.run())
    
    def start(self):
        if not self._running:
            self._running = True
            self._process = threading.Thread(target=self._run_agent)
            self._process.daemon = True
            self._process.start()
        
    def stop(self):
        if self._running:
            self._running = False
            if self._process:
                self._process.join(timeout=1.0)
                
    def process_request(self, request: SustainabilityRequest) -> SustainabilityResponse:
        try:
            if request.query_type == "chat":
                try:
                    message = self._generate_chat_response(
                        request.message,
                        request.user_id,
                        request.data
                    )
                    return SustainabilityResponse(
                        status="success",
                        message=message,
                        data={"type": "chat"}
                    )
                except Exception as chat_error:
                    logger.error(f"Chat response error: {str(chat_error)}")
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
            logger.error(f"Request processing error: {str(e)}")
            return SustainabilityResponse(
                status="error",
                error=f"Unexpected error: {str(e)}"
            )
