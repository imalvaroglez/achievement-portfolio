#!/usr/bin/env python3
"""
Find the cheapest travel dates for a specific route.

Helps identify the best time to book for cost savings.

Examples:
    python find_cheapest_dates.py --from BCN --to JFK --date 2026-03-15
    python find_cheapest_dates.py --from MAD --to NYC --date 2026-04-01 --span 30
    python find_cheapest_dates.py --from PAR --to LAX --date 2026-05-15 --max 15
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


def format_date_option(opt: dict) -> dict:
    """Format a date option for display."""
    return {
        'departure_date': opt.get('departureDate', ''),
        'price': float(opt.get('price', 0)),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Find the cheapest travel dates for a route',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python find_cheapest_dates.py --from BCN --to JFK --date 2026-03-15
  python find_cheapest_dates.py --from BCN --to JFK --date 2026-03-15 --span 30
  python find_cheapest_dates.py --from PAR --to LAX --date 2026-05-15 --max 10
        """
    )
    parser.add_argument('--from', '-f', dest='origin', required=True, help='Origin airport code')
    parser.add_argument('--to', '-t', dest='destination', required=True, help='Destination airport code')
    parser.add_argument('--date', '-d', required=True, help='Base departure date (YYYY-MM-DD)')
    parser.add_argument('--span', '-s', type=int, default=7, help='Day span to check around the date (default: 7)')
    parser.add_argument('--max', type=int, default=10, help='Maximum results (default: 10)')
    parser.add_argument('--currency', help='Currency code')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        params = {
            'originLocationCode': args.origin.upper(),
            'destinationLocationCode': args.destination.upper(),
            'departureDate': args.date,
        }
        
        if args.span > 0:
            params['duration'] = args.span
        if args.currency:
            params['currencyCode'] = args.currency.upper()
        
        response = client.get('/v1/shopping/flight-dates', params)
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        dates = response.get('data', [])
        formatted = [format_date_option(d) for d in dates[:args.max]]
        
        # Sort by price (cheapest first)
        formatted_sorted = sorted(formatted, key=lambda x: x['price'])
        
        # Parse base date for context
        base_date = datetime.fromisoformat(args.date)
        
        result = {
            'success': True,
            'search': {
                'origin': args.origin.upper(),
                'destination': args.destination.upper(),
                'base_date': args.date,
                'span_days': args.span,
            },
            'results_count': len(formatted_sorted),
            'dates': formatted_sorted,
            'recommendations': {
                'cheapest_date': formatted_sorted[0] if formatted_sorted else None,
                'most_expensive_date': formatted_sorted[-1] if formatted_sorted else None,
                'price_range': {
                    'min': min(d['price'] for d in formatted_sorted) if formatted_sorted else 0,
                    'max': max(d['price'] for d in formatted_sorted) if formatted_sorted else 0,
                    'savings': max(d['price'] for d in formatted_sorted) - min(d['price'] for d in formatted_sorted) if formatted_sorted else 0,
                },
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
