import asyncio
from agent.eco_agent import EcoAgent
from agent.fetchai_agent import SustainabilityData, SustainabilityQuery
from agent.agentmail_client import AgentMailClient
from config.config import load_config

async def test_eco_agent():
    print("Testing EcoAgent implementation...")
    
    # Test 1: AgentMail Integration
    print("\n1. Testing AgentMail Integration:")
    try:
        config = load_config()
        client = AgentMailClient(api_key=config['AGENTMAIL_API_KEY'])
        await client.send_report(
            "test@agentmail.to",
            {
                "name": "Test User",
                "carbon_footprint": 2.5,
                "energy_score": 85,
                "recommendations": [
                    {"title": "Test Recommendation", "description": "Test Description", "impact": "Test Impact"}
                ]
            }
        )
        print("✅ AgentMail test completed")
    except Exception as e:
        print(f"❌ AgentMail test failed: {str(e)}")

    # Test 2: Sustainability Analysis
    print("\n2. Testing Sustainability Analysis:")
    try:
        # Create test data
        test_data = SustainabilityData(
            electricity=750,
            gas=30,
            car_miles=500,
            public_transport=100,
            diet_type="Meat Weekly"
        )
        
        # Create test query
        query = SustainabilityQuery(
            query_type="analyze",
            user_id="test_user",
            data=test_data
        )
        
        # Initialize FetchAI agent and analyze data
        from agent.fetchai_agent import FetchAIAgent
        agent = FetchAIAgent()
        result = await agent._analyze_sustainability(test_data)
        
        print(f"Carbon Footprint: {result.carbon_footprint:.2f} tons CO2")
        print(f"Energy Score: {result.energy_score}")
        print("Recommendations:")
        for rec in result.recommendations:
            print(f"- {rec['title']}")
        print("✅ Sustainability analysis test completed")
    except Exception as e:
        print(f"❌ Sustainability analysis test failed: {str(e)}")

    # Test 3: Fetch.ai Agent Communication
    print("\n3. Testing Fetch.ai Agent Communication:")
    try:
        from agent.fetchai_agent import agent
        print(f"Agent Address: {agent.address}")
        print("✅ Fetch.ai agent initialized successfully")
    except Exception as e:
        print(f"❌ Fetch.ai agent initialization failed: {str(e)}")

if __name__ == "__main__":
    print("Starting EcoAgent Tests...")
    asyncio.run(test_eco_agent())
