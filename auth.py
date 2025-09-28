"""Authentication module for EcoAgent"""
import os
from typing import Optional, Dict, Any
import requests
from urllib.parse import urlencode
import streamlit as st
from dotenv import load_dotenv
from database import User, get_session

# Load environment variables
load_dotenv()

# Auth0 Configuration
AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
BASE_URL = 'http://localhost:8501'
CALLBACK_URL = f"{BASE_URL}/callback"

class AuthError(Exception):
    """Custom exception for authentication errors"""
    pass

class Auth:
    """Authentication handler class"""
    
    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.callback_url = "http://localhost:8501/callback"
    
    def get_auth_url(self) -> str:
        """Generate Auth0 authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.callback_url,
            'scope': 'openid profile',
            'audience': f'https://{self.domain}/userinfo'
        }
        return f"https://{self.domain}/authorize?{urlencode(params)}"

    def get_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.callback_url
        }
        
        response = requests.post(
            f"https://{self.domain}/oauth/token",
            json=payload
        )
        
        if response.status_code != 200:
            raise AuthError(f"Failed to get token: {response.text}")
            
        return response.json()

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Get user profile from Auth0"""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(
            f"https://{self.domain}/userinfo",
            headers=headers
        )
        
        if response.status_code != 200:
            raise AuthError(f"Failed to get user profile: {response.text}")
            
        return response.json()

    @staticmethod
    def exchange_code_for_token(code: str) -> Dict[str, Any]:
        """Exchange authorization code for token"""
        response = requests.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            json={
                'grant_type': 'authorization_code',
                'client_id': AUTH0_CLIENT_ID,
                'client_secret': AUTH0_CLIENT_SECRET,
                'code': code,
                'redirect_uri': CALLBACK_URL
            }
        )
        
        if response.status_code != 200:
            raise AuthError(f"Failed to exchange code for token: {response.text}")
            
        return response.json()

    @staticmethod
    def create_or_get_user(profile: Dict[str, Any]) -> User:
        """Create or get user from database"""
        session = get_session()
        st.session_state.db_session = session
        
        try:
            # Get or create user
            user = session.query(User).filter_by(auth0_id=profile['sub']).first()
            if not user:
                user = User(
                    auth0_id=profile['sub'],
                    email=profile.get('email') or f"{profile['sub'].replace('|', '_')}@github.user",
                    name=profile.get('name') or profile.get('nickname', 'GitHub User')
                )
                session.add(user)
                session.commit()
            
            # Keep the session alive and return user
            session.refresh(user)
            return user
            
        except Exception as e:
            session.rollback()
            raise AuthError(f"Database error: {str(e)}")

    @staticmethod
    def handle_callback(code: str) -> bool:
        """Handle OAuth callback"""
        try:
            # Don't process if we've already handled this code
            if hasattr(st.session_state, 'last_processed_code') and st.session_state.last_processed_code == code:
                return True
                
            # Exchange code for token
            token_data = Auth.exchange_code_for_token(code)
            if 'access_token' not in token_data:
                raise AuthError("No access token received")
                
            # Get user profile
            profile = Auth.get_user_profile(token_data['access_token'])
            if not profile:
                raise AuthError("Failed to get user profile")
                
            # Create or get user
            user = Auth.create_or_get_user(profile)
            
            # Set session state
            st.session_state.user = {
                'auth0_id': profile['sub'],
                'email': user.email,
                'name': user.name
            }
            st.session_state.db_user_id = user.id
            st.session_state.last_processed_code = code
            return True
            
        except Exception as e:
            # Only show error if this is a new code
            if not hasattr(st.session_state, 'last_processed_code') or st.session_state.last_processed_code != code:
                st.error(f"Authentication failed: {str(e)}")
            return False

def init_auth():
    """Initialize authentication state"""
    # Handle callback if code is present and hasn't been processed
    if 'code' in st.query_params:
        code = st.query_params['code']
        # Check if we've already processed this code
        if 'last_auth_code' not in st.session_state or st.session_state.last_auth_code != code:
            st.session_state.last_auth_code = code
            if Auth.handle_callback(code):
                st.success("Successfully logged in!")
                # Clear the code from query params by redirecting
                st.rerun()
    
    # Show login/logout in sidebar
    with st.sidebar:
        if 'user' in st.session_state:
            st.write(f"👋 Welcome, {st.session_state.user['name']}!")
            if st.button("Sign Out", key="logout"):
                # Clean up session state
                for key in ['user', 'db_user_id', 'db_session', 'last_auth_code']:
                    if key in st.session_state:
                        # Close database session if it exists
                        if key == 'db_session':
                            st.session_state.db_session.close()
                        del st.session_state[key]
                params = {
                    'client_id': AUTH0_CLIENT_ID,
                    'returnTo': BASE_URL
                }
                logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;url={logout_url}">', 
                          unsafe_allow_html=True)
                st.rerun()
        else:
            if st.button("Sign In with GitHub"):
                st.markdown(f'<meta http-equiv="refresh" content="0;url={Auth.get_auth_url()}">', 
                          unsafe_allow_html=True)

def require_auth(function):
    """Decorator to require authentication for a page"""
    def wrapper(*args, **kwargs):
        if 'user' not in st.session_state:
            st.warning("Please sign in to access this feature.")
            return
        return function(*args, **kwargs)
    return wrapper
