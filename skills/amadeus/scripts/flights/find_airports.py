#!/usr/bin/env python3
"""
Search for airports and cities by keyword.

Examples:
    python find_airports.py "Barcelona"
    python find_airports.py "JFK"
    python find_airports.py "New York" --type CITY
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


def format_location(location: dict) -> dict:
    """Format a location result."""
    address = location.get('address', {})
    
    return {
        'type': location.get('subType', '').lower(),
        'name': location.get('name', ''),
        'iata_code': location.get('iataCode', ''),
        'city': address.get('cityName', ''),
        'country': address.get('countryName', ''),
        'country_code': address.get('countryCode', ''),
        'coordinates': {
            'latitude': location.get('geoCode', {}).get('latitude'),
            'longitude': location.get('geoCode', {}).get('longitude'),
        } if location.get('geoCode') else None,
    }


def main():
    parser = argparse.ArgumentParser(description='Search for airports and cities')
    parser.add_argument('keyword', help='Search keyword (city name, airport code, etc.)')
    parser.add_argument('--type', '-t', dest='subtype', default='AIRPORT,CITY',
                        help='Location type: AIRPORT, CITY, or both (default: AIRPORT,CITY)')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        response = client.search_airports(
            keyword=args.keyword,
            subtype=args.subtype.upper(),
        )
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        locations = response.get('data', [])
        formatted = [format_location(loc) for loc in locations]
        
        result = {
            'success': True,
            'search': {
                'keyword': args.keyword,
                'type': args.subtype,
            },
            'results_count': len(formatted),
            'locations': formatted,
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
