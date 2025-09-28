"""Authentication module for EcoAgent"""
import os
from typing import Optional, Dict, Any
import requests
from urllib.parse import urlencode
from flask import redirect, request
from dotenv import load_dotenv
from database import User, get_session

# Load environment variables
load_dotenv(override=True)  # Force reload of environment variables

# Auth0 Configuration
AUTH0_CLIENT_ID = os.environ.get('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = os.environ.get('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
AUTH0_M2M_CLIENT_ID = os.environ.get('AUTH0_M2M_CLIENT_ID')
AUTH0_M2M_CLIENT_SECRET = os.environ.get('AUTH0_M2M_CLIENT_SECRET')
BASE_URL = os.environ.get('BASE_URL', 'https://ecoagent-y0vt.onrender.com')
CALLBACK_URL = f"{BASE_URL}/callback"

# Validate required environment variables
if not all([AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_DOMAIN, BASE_URL]):
    raise EnvironmentError("Missing required Auth0 configuration. Check .env file.")

# Validate M2M credentials
if not all([AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET]):
    raise EnvironmentError("Missing required Auth0 M2M credentials. Check AUTH0_M2M_CLIENT_ID and AUTH0_M2M_CLIENT_SECRET in .env file.")

from functools import wraps
from flask import session, jsonify

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

class AuthError(Exception):
    """Custom exception for authentication errors"""
    pass

class Auth:
    """Authentication handler class"""
    
    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.m2m_client_id = AUTH0_M2M_CLIENT_ID
        self.m2m_client_secret = AUTH0_M2M_CLIENT_SECRET
        self.callback_url = CALLBACK_URL
        self._management_token = None
        
    def authorize_redirect(self, callback_url: str) -> str:
        """Generate the Auth0 authorization URL and return a redirect response"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': callback_url,
            'scope': 'openid profile email',
            'audience': f'https://{self.domain}/api/v2/'
        }
        auth_url = f'https://{self.domain}/authorize?{urlencode(params)}'
        return redirect(auth_url)
        
    def get_token(self, code: str = None) -> dict:
        """Exchange authorization code for tokens"""
        if not code:
            code = request.args.get('code')
            if not code:
                raise AuthError('No authorization code provided')

        token_url = f'https://{self.domain}/oauth/token'
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.callback_url
        }
        
        response = requests.post(token_url, json=payload)
        if response.status_code != 200:
            raise AuthError(f'Failed to get token: {response.text}')
            
        return response.json()
        
    def get_userinfo(self, token_response: dict) -> dict:
        """Get user information from Auth0 using the access token"""
        if not token_response or 'access_token' not in token_response:
            raise AuthError('Invalid token response')
            
        userinfo_url = f'https://{self.domain}/userinfo'
        headers = {'Authorization': f'Bearer {token_response["access_token"]}'}
        
        response = requests.get(userinfo_url, headers=headers)
        if response.status_code != 200:
            raise AuthError(f'Failed to get user info: {response.text}')
            
        return response.json()
        
        # Validate M2M credentials at initialization
        if not self.m2m_client_id or not self.m2m_client_secret:
            print("DEBUG: M2M credentials missing in Auth class initialization")
            print(f"M2M Client ID exists: {bool(self.m2m_client_id)}")
            print(f"M2M Client Secret exists: {bool(self.m2m_client_secret)}")
            raise AuthError("M2M credentials not properly initialized")
        
    def _get_management_token(self) -> str:
        """Get an access token for the Auth0 Management API"""
        if not self.m2m_client_id or not self.m2m_client_secret:
            raise AuthError("M2M credentials not configured. Please check AUTH0_M2M_CLIENT_ID and AUTH0_M2M_CLIENT_SECRET in .env")
            
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.m2m_client_id,
            'client_secret': self.m2m_client_secret,
            'audience': f'https://{self.domain}/api/v2/'
        }
        print(f"Requesting management token for audience: {payload['audience']}")
        
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            f'https://{self.domain}/oauth/token',
            data=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            raise AuthError(f"Failed to get management token: {response.text}")
            
        self._management_token = response.json()['access_token']
        return self._management_token
        
    def delete_auth0_user(self, user_id: str) -> bool:
        """Permanently delete a user from Auth0"""
        if not self._management_token:
            self._get_management_token()
            
        headers = {
            'Authorization': f'Bearer {self._management_token}',
            'Content-Type': 'application/json'
        }
        
        # Ensure the user_id is properly formatted
        if not user_id.startswith('auth0|'):
            user_id = f'auth0|{user_id}'
            
        response = requests.delete(
            f'https://{self.domain}/api/v2/users/{user_id}',
            headers=headers
        )
        
        if response.status_code == 204:
            return True
        elif response.status_code == 404:
            # User already deleted or doesn't exist
            return True
        else:
            raise AuthError(f"Failed to delete Auth0 user: {response.text}")
    
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
