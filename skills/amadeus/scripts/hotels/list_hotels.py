#!/usr/bin/env python3
"""
List hotels available in a city.

Examples:
    python list_hotels.py --city PAR
    python list_hotels.py --city NYC --radius 10 --ratings 4,5
    python list_hotels.py --city BCN --amenities WIFI,PARKING
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

from client import AmadeusClient, APIError
from auth import AuthError


AMENITIES = {
    'WIFI': 'WiFi',
    'PARKING': 'Parking',
    'POOL': 'Swimming pool',
    'GYM': 'Gym/Fitness',
    'SPA': 'Spa',
    'RESTAURANT': 'Restaurant',
    'BAR': 'Bar',
    'AIRPORT_SHUTTLE': 'Airport shuttle',
    'BUSINESS_CENTER': 'Business center',
    'CONCIERGE': 'Concierge',
}


def format_hotel(hotel: dict) -> dict:
    """Format a hotel listing for display."""
    return {
        'hotel_id': hotel.get('hotelId', ''),
        'name': hotel.get('name', ''),
        'rating': hotel.get('rating', 0),
        'address': {
            'address': hotel.get('address', ''),
            'city': hotel.get('cityName', ''),
            'postal_code': hotel.get('postalCode', ''),
            'country': hotel.get('countryName', ''),
        },
        'distance_km': hotel.get('distance', {}),
        'contact': {
            'email': hotel.get('contact', {}).get('email'),
            'phone': hotel.get('contact', {}).get('phone'),
        },
        'amenities': hotel.get('amenities', []),
    }


def main():
    parser = argparse.ArgumentParser(
        description='List hotels in a city',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Amenities:
{chr(10).join(f'  {key}: {val}' for key, val in AMENITIES.items())}

Examples:
  python list_hotels.py --city PAR
  python list_hotels.py --city NYC --radius 10 --ratings 4,5
  python list_hotels.py --city BCN --amenities WIFI,PARKING
        """
    )
    parser.add_argument('--city', '-c', required=True, help='City IATA code (e.g., PAR, NYC, BCN)')
    parser.add_argument('--radius', '-r', type=int, default=5, help='Search radius in km (default: 5)')
    parser.add_argument('--ratings', help='Filter by star ratings (e.g., 4,5)')
    parser.add_argument('--amenities', '-a', help='Filter by amenities (comma-separated)')
    parser.add_argument('--max', type=int, default=50, help='Maximum results')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        # Parse ratings
        ratings = None
        if args.ratings:
            try:
                ratings = [int(r.strip()) for r in args.ratings.split(',')]
                if any(r < 1 or r > 5 for r in ratings):
                    raise ValueError('Ratings must be between 1 and 5')
            except (ValueError, TypeError) as e:
                print(json.dumps({
                    'success': False,
                    'error': f'Invalid ratings format: {e}',
                }), file=sys.stderr)
                sys.exit(1)
        
        # Parse amenities
        amenities = None
        if args.amenities:
            amenities = [a.strip().upper() for a in args.amenities.split(',')]
            valid_amenities = set(AMENITIES.keys())
            invalid = [a for a in amenities if a not in valid_amenities]
            if invalid:
                print(json.dumps({
                    'success': False,
                    'error': f'Invalid amenities: {", ".join(invalid)}. Valid: {", ".join(valid_amenities)}',
                }), file=sys.stderr)
                sys.exit(1)
        
        response = client.search_hotels_by_city(
            city_code=args.city.upper(),
            radius=args.radius,
            ratings=ratings,
            amenities=amenities,
        )
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        hotels = response.get('data', [])
        formatted_hotels = [format_hotel(h) for h in hotels[:args.max]]
        
        result = {
            'success': True,
            'search': {
                'city': args.city.upper(),
                'radius_km': args.radius,
                'ratings': ratings,
                'amenities': amenities,
            },
            'results_count': len(formatted_hotels),
            'hotels': formatted_hotels,
            'meta': {
                'source': 'amadeus',
                'environment': client.auth.env,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            },
        }
        
        print(json.dumps(result, indent=2))
        
    except AuthError as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'code': 401,
        }), file=sys.stderr)
        sys.exit(1)
        
    except APIError as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'code': e.status_code,
            'details': e.errors,
        }), file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
