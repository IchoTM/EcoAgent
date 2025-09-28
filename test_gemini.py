import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini():
    try:
        # Configure API
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        genai.configure(api_key=api_key)
        
        # Create model
        logger.info("Creating model...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Test generation
        logger.info("Testing generation...")
        response = model.generate_content("Say hello!")
        logger.info(f"Response: {response.text}")
        
        logger.info("Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_gemini()
