from uagents import Agent, Context, Model
import google.generativeai as genai
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class RecommendationRequest(Model):
    consumption_data: dict
    user_preferences: dict

class Recommendation(Model):
    suggestions: List[str]
    impact_score: float

# Initialize the recommendations agent
eco_advisor = Agent(
    name="eco_advisor",
    seed="your-secure-seed-2",  # Replace with a secure seed
    endpoint=["http://0.0.0.0:8001/eco_advisor"],  # Add endpoint for network communication
    port=8001
)

# Configure Gemini AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

@eco_advisor.on_message(model=RecommendationRequest)
async def generate_recommendations(ctx: Context, sender: str, msg: RecommendationRequest):
    # Analyze the consumption data using Gemini AI
    prompt = f"""
    Based on the following consumption data:
    {msg.consumption_data}
    And user preferences:
    {msg.user_preferences}
    
    Provide 3 specific recommendations to reduce environmental impact.
    Format as a list of actionable items.
    """
    
    response = model.generate_content(prompt)
    suggestions = response.text.split('\n')
    
    # Calculate impact score based on recommendations
    impact_score = 0.8  # Example score
    
    recommendation = Recommendation(
        suggestions=suggestions,
        impact_score=impact_score
    )
    
    # Send the recommendations back
    await ctx.send(sender, recommendation)

if __name__ == "__main__":
    eco_advisor.run()
