"""
Amadeus OAuth 2.0 Client Credentials Authentication

Handles token acquisition and refresh for Amadeus API access.
Tokens are cached in memory with automatic refresh before expiry.
"""

import os
import time
import requests
from typing import Optional


class AuthError(Exception):
    """Raised when authentication fails."""
    pass


class AmadeusAuth:
    """
    OAuth 2.0 Client Credentials flow for Amadeus API.
    
    Tokens are cached in memory and automatically refreshed
    when they expire or are close to expiry (60s buffer).
    """
    
    # Token endpoints by environment
    TOKEN_URLS = {
        'test': 'https://test.api.amadeus.com/v1/security/oauth2/token',
        'production': 'https://api.amadeus.com/v1/security/oauth2/token',
    }
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, env: Optional[str] = None):
        """
        Initialize authentication handler.
        
        Args:
            api_key: Amadeus API key (falls back to AMADEUS_API_KEY env var)
            api_secret: Amadeus API secret (falls back to AMADEUS_API_SECRET env var)
            env: Environment ('test' or 'production', falls back to AMADEUS_ENV, default: 'test')
        """
        self.api_key = api_key or os.environ.get('AMADEUS_API_KEY')
        self.api_secret = api_secret or os.environ.get('AMADEUS_API_SECRET')
        self.env = env or os.environ.get('AMADEUS_ENV', 'test')
        
        if not self.api_key or not self.api_secret:
            raise AuthError(
                "Amadeus credentials not configured. "
                "Set AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables."
            )
        
        if self.env not in self.TOKEN_URLS:
            raise AuthError(f"Invalid environment: {self.env}. Must be 'test' or 'production'.")
        
        self._token: Optional[str] = None
        self._token_expiry: float = 0
    
    @property
    def token_url(self) -> str:
        """Get the token endpoint URL for current environment."""
        return self.TOKEN_URLS[self.env]
    
    @property
    def base_url(self) -> str:
        """Get the API base URL for current environment."""
        if self.env == 'test':
            return 'https://test.api.amadeus.com'
        return 'https://api.amadeus.com'
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid (with 60s buffer)."""
        if not self._token:
            return False
        return time.time() < (self._token_expiry - 60)
    
    def _refresh_token(self) -> str:
        """
        Request a new access token from Amadeus OAuth endpoint.
        
        Returns:
            Access token string
            
        Raises:
            AuthError: If token request fails
        """
        try:
            response = requests.post(
                self.token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.api_key,
                    'client_secret': self.api_secret,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout=30,
            )
            
            if response.status_code != 200:
                error_msg = f"Token request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error_description' in error_data:
                        error_msg = f"{error_msg} - {error_data['error_description']}"
                except Exception:
                    pass
                raise AuthError(error_msg)
            
            data = response.json()
            self._token = data['access_token']
            # expires_in is in seconds
            self._token_expiry = time.time() + data.get('expires_in', 1799)
            
            return self._token
            
        except requests.RequestException as e:
            raise AuthError(f"Token request failed: {e}")
    
    def get_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token string
            
        Raises:
            AuthError: If token cannot be obtained
        """
        if self._is_token_valid():
            return self._token
        return self._refresh_token()
    
    def get_headers(self) -> dict:
        """
        Get authorization headers for API requests.
        
        Returns:
            Dict with Authorization header
        """
        return {
            'Authorization': f'Bearer {self.get_token()}',
        }
    
    def invalidate(self) -> None:
        """Force token refresh on next request."""
        self._token = None
        self._token_expiry = 0
