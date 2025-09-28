import os
from dotenv import load_dotenv
from agents.eco_monitor_agent import eco_monitor
from agents.eco_advisor_agent import eco_advisor, RecommendationRequest
from uagents import Bureau
import asyncio

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test that required environment variables are set"""
    required_vars = ['GOOGLE_API_KEY', 'UAGENTS_SEED']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    print("✅ All required environment variables are set")
    return True

async def test_eco_advisor():
    """Test the eco advisor agent"""
    print("\nTesting Eco Advisor Agent...")
    
    # Sample test data
    test_data = {
        "consumption_data": {
            "electricity": 150,
            "water": 200
        },
        "user_preferences": {
            "budget": "medium",
            "implementation_time": "short-term"
        }
    }
    
    request = RecommendationRequest(
        consumption_data=test_data["consumption_data"],
        user_preferences=test_data["user_preferences"]
    )
    
    # Create a test message
    try:
        await eco_advisor.start()
        print("✅ Eco Advisor Agent started successfully")
    except Exception as e:
        print(f"❌ Failed to start Eco Advisor Agent: {str(e)}")

async def test_eco_monitor():
    """Test the eco monitor agent"""
    print("\nTesting Eco Monitor Agent...")
    try:
        await eco_monitor.start()
        print("✅ Eco Monitor Agent started successfully")
    except Exception as e:
        print(f"❌ Failed to start Eco Monitor Agent: {str(e)}")

async def main():
    """Run all tests"""
    print("Starting Agent Verification Tests...")
    print("=" * 50)
    
    # Test environment variables
    if not test_environment_variables():
        return
    
    # Test both agents
    await asyncio.gather(
        test_eco_advisor(),
        test_eco_monitor()
    )
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(main())
