"""Add this file to .gitignore before adding sensitive data"""
from typing import Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_config() -> Dict[str, str]:
    """Load configuration from environment variables"""
    config = {
        'AGENTMAIL_API_KEY': os.getenv('AGENTMAIL_API_KEY'),
        'FETCHAI_SEED': os.getenv('FETCHAI_SEED'),
        'CLOUDFLARE_API_TOKEN': os.getenv('CLOUDFLARE_API_TOKEN'),
    }
    
    # Validate required config
    required_vars = ['AGENTMAIL_API_KEY']
    missing_vars = [var for var in required_vars if not config[var]]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    return config
