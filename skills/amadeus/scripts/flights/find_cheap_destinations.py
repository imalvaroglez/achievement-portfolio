#!/usr/bin/env python3
"""
Find the cheapest flight destinations from an origin airport.

Useful for identifying bargain destinations when the destination is flexible.

Examples:
    python find_cheap_destinations.py --from BCN --max 20
    python find_cheap_destinations.py --from JFK --date 2026-04-01 --max 15
    python find_cheap_destinations.py --from MAD --date 2026-03-15 --currency EUR --max 10
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

from client import AmadeusClient, APIError
from auth import AuthError


def format_destination(dest: dict) -> dict:
    """Format a destination result."""
    return {
        'iata_code': dest.get('iataCode', ''),
        'name': dest.get('name', ''),
        'price': float(dest.get('price', 0)),
        'departure_date': dest.get('departureDate', ''),
        'return_date': dest.get('returnDate', ''),
        'type': dest.get('type', ''),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Find the cheapest flight destinations from an origin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python find_cheap_destinations.py --from BCN --max 20
  python find_cheap_destinations.py --from JFK --date 2026-04-01 --max 15
  python find_cheap_destinations.py --from MAD --date 2026-03-15 --currency EUR --max 10
        """
    )
    parser.add_argument('--from', '-f', dest='origin', required=True, help='Origin airport code')
    parser.add_argument('--date', '-d', help='Departure date (YYYY-MM-DD, default: today + 7 days)')
    parser.add_argument('--currency', help='Currency code (e.g., EUR, USD)')
    parser.add_argument('--max', type=int, default=10, help='Maximum results (default: 10)')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        # Default departure date: one week from today
        departure_date = args.date
        if not departure_date:
            departure_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        params = {
            'origin': args.origin.upper(),
            'departureDate': departure_date,
        }
        
        if args.currency:
            params['currency'] = args.currency.upper()
        
        response = client.get('/v1/shopping/flight-destinations', params)
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        destinations = response.get('data', [])
        formatted = [format_destination(d) for d in destinations[:args.max]]
        
        # Sort by price
        formatted_sorted = sorted(formatted, key=lambda x: x['price'])
        
        result = {
            'success': True,
            'search': {
                'origin': args.origin.upper(),
                'departure_date': departure_date,
                'currency': args.currency or 'default',
            },
            'results_count': len(formatted_sorted),
            'destinations': formatted_sorted,
            'savings': {
                'cheapest': formatted_sorted[0] if formatted_sorted else None,
                'most_expensive': formatted_sorted[-1] if formatted_sorted else None,
                'average': round(
                    sum(d['price'] for d in formatted_sorted) / len(formatted_sorted), 2
                ) if formatted_sorted else 0,
            },
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
