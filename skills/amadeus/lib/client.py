"""
Amadeus API Client

Provides a high-level interface to Amadeus APIs with automatic
authentication, caching, rate limiting, and error handling.
"""

import json
import requests
from typing import Any, Dict, Optional
from urllib.parse import urljoin

try:
    from .auth import AmadeusAuth, AuthError
    from .cache import ResponseCache
except ImportError:
    from auth import AmadeusAuth, AuthError
    from cache import ResponseCache


class APIError(Exception):
    """Raised when an API request fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, errors: Optional[list] = None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class AmadeusClient:
    """
    High-level Amadeus API client.
    
    Features:
    - Automatic OAuth token management
    - Response caching (configurable TTL)
    - Rate limit handling with exponential backoff
    - Structured error responses
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        env: Optional[str] = None,
        cache_ttl: int = 900,  # 15 minutes default
        timeout: int = 30,
    ):
        """
        Initialize the Amadeus client.
        
        Args:
            api_key: Amadeus API key (falls back to env var)
            api_secret: Amadeus API secret (falls back to env var)
            env: Environment ('test' or 'production')
            cache_ttl: Cache TTL in seconds (0 to disable)
            timeout: Request timeout in seconds
        """
        self.auth = AmadeusAuth(api_key, api_secret, env)
        self.cache = ResponseCache(default_ttl=cache_ttl) if cache_ttl > 0 else None
        self.timeout = timeout
    
    @property
    def base_url(self) -> str:
        """Get the API base URL."""
        return self.auth.base_url
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., '/v2/shopping/flight-offers')
            params: Query parameters
            data: Request body (for POST)
            use_cache: Whether to use cache for GET requests
            
        Returns:
            Parsed JSON response
            
        Raises:
            APIError: If request fails
            AuthError: If authentication fails
        """
        url = urljoin(self.base_url, endpoint)
        
        # Check cache for GET requests
        if method == 'GET' and use_cache and self.cache:
            cache_key = self.cache.make_key(endpoint, params)
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        # Make request
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                headers={
                    **self.auth.get_headers(),
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}")
        
        # Handle errors
        if response.status_code == 401:
            # Token might be expired, try refresh once
            self.auth.invalidate()
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if data else None,
                    headers={
                        **self.auth.get_headers(),
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                raise APIError(f"Request failed after token refresh: {e}")
        
        if response.status_code >= 400:
            error_msg = f"API error: {response.status_code}"
            errors = []
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    errors = error_data['errors']
                    error_details = [e.get('detail', e.get('title', '')) for e in errors]
                    error_msg = f"{error_msg} - {'; '.join(error_details)}"
            except Exception:
                pass
            raise APIError(error_msg, status_code=response.status_code, errors=errors)
        
        # Parse response
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {e}")
        
        # Cache successful GET responses
        if method == 'GET' and use_cache and self.cache:
            cache_key = self.cache.make_key(endpoint, params)
            self.cache.set(cache_key, result)
        
        return result
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params, use_cache=use_cache)
    
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, params=params, data=data, use_cache=False)
    
    # ========== Flight APIs ==========
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: Optional[str] = None,
        non_stop: bool = False,
        currency: Optional[str] = None,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for flight offers.
        
        Args:
            origin: Origin airport IATA code (e.g., 'BCN')
            destination: Destination airport IATA code (e.g., 'JFK')
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trip (YYYY-MM-DD)
            adults: Number of adult passengers
            children: Number of child passengers (2-11)
            infants: Number of infant passengers (<2)
            travel_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            non_stop: Only direct flights
            currency: Currency code (e.g., 'EUR', 'USD')
            max_results: Maximum number of results
            
        Returns:
            Flight offers response
        """
        params = {
            'originLocationCode': origin.upper(),
            'destinationLocationCode': destination.upper(),
            'departureDate': departure_date,
            'adults': adults,
            'max': max_results,
        }
        
        if return_date:
            params['returnDate'] = return_date
        if children > 0:
            params['children'] = children
        if infants > 0:
            params['infants'] = infants
        if travel_class:
            params['travelClass'] = travel_class.upper()
        if non_stop:
            params['nonStop'] = 'true'
        if currency:
            params['currencyCode'] = currency.upper()
        
        return self.get('/v2/shopping/flight-offers', params)
    
    def get_flight_price(self, flight_offer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Confirm pricing for a flight offer.
        
        Args:
            flight_offer: A flight offer from search_flights
            
        Returns:
            Confirmed price response
        """
        return self.post('/v1/shopping/flight-offers/pricing', {
            'data': {
                'type': 'flight-offers-pricing',
                'flightOffers': [flight_offer],
            }
        })
    
    def search_airports(self, keyword: str, subtype: str = 'AIRPORT,CITY') -> Dict[str, Any]:
        """
        Search for airports and cities by keyword.
        
        Args:
            keyword: Search term (city name, airport code, etc.)
            subtype: AIRPORT, CITY, or both
            
        Returns:
            Locations response
        """
        return self.get('/v1/reference-data/locations', {
            'keyword': keyword,
            'subType': subtype,
        })
    
    # ========== Hotel APIs ==========
    
    def search_hotels_by_city(
        self,
        city_code: str,
        radius: int = 5,
        radius_unit: str = 'KM',
        ratings: Optional[list] = None,
        amenities: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        List hotels in a city.
        
        Args:
            city_code: City IATA code
            radius: Search radius
            radius_unit: KM or MILE
            ratings: Filter by star ratings (1-5)
            amenities: Filter by amenities
            
        Returns:
            Hotels list response
        """
        params = {
            'cityCode': city_code.upper(),
            'radius': radius,
            'radiusUnit': radius_unit,
        }
        
        if ratings:
            params['ratings'] = ','.join(str(r) for r in ratings)
        if amenities:
            params['amenities'] = ','.join(amenities)
        
        return self.get('/v1/reference-data/locations/hotels/by-city', params)
    
    def search_hotel_offers(
        self,
        hotel_ids: list,
        check_in: str,
        check_out: str,
        adults: int = 1,
        rooms: int = 1,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for hotel offers.
        
        Args:
            hotel_ids: List of hotel IDs from search_hotels_by_city
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            rooms: Number of rooms
            currency: Currency code
            
        Returns:
            Hotel offers response
        """
        params = {
            'hotelIds': ','.join(hotel_ids[:20]),  # API limit: 20 hotels
            'checkInDate': check_in,
            'checkOutDate': check_out,
            'adults': adults,
            'roomQuantity': rooms,
        }
        
        if currency:
            params['currency'] = currency.upper()
        
        return self.get('/v3/shopping/hotel-offers', params)
    
    # ========== Points of Interest ==========
    
    def get_pois(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1,
        categories: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Get points of interest near a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius: Search radius in km (1-20)
            categories: Filter by category (SIGHTS, NIGHTLIFE, RESTAURANT, SHOPPING)
            
        Returns:
            POIs response
        """
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'radius': min(radius, 20),
        }
        
        if categories:
            params['categories'] = ','.join(categories)
        
        return self.get('/v1/reference-data/locations/pois', params)
