#!/usr/bin/env python3
"""
Analyze flight prices for a route and find optimal travel dates.

Uses historical pricing data to identify trends and recommendations.

Examples:
    python analyze_prices.py --from BCN --to JFK --date 2026-03-15
    python analyze_prices.py --from MAD --to NYC --date 2026-04-01 --length 7
    python analyze_prices.py --from PAR --to LAX --date 2026-05-15 --passengers 2 --class business
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


def format_price_analysis(data: dict) -> dict:
    """Format price analysis response for display."""
    return {
        'currency': data.get('currencyCode', 'EUR'),
        'price': float(data.get('price', 0)),
        'price_points': [
            {
                'kind': p.get('kind', ''),
                'price': float(p.get('price', 0)),
            } for p in data.get('pricePoints', [])
        ],
        'recommendation': data.get('recommendation', ''),
        'related_dates': [
            {
                'departure_date': rd.get('departureDate', ''),
                'price': float(rd.get('price', 0)),
            } for rd in data.get('relatedDateOptions', [])
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description='Analyze flight prices and find optimal travel dates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Price recommendations:
  PEAK: Most expensive period
  VERY_HIGH: Very high price
  HIGH: High price
  NORMAL: Normal price
  LOW: Low price (good deal)
  VERY_LOW: Very low price (excellent deal)

Examples:
  python analyze_prices.py --from BCN --to JFK --date 2026-03-15
  python analyze_prices.py --from BCN --to JFK --date 2026-03-15 --length 7
  python analyze_prices.py --from PAR --to LAX --date 2026-05-15 --passengers 2 --class business
        """
    )
    parser.add_argument('--from', '-f', dest='origin', required=True, help='Origin airport code')
    parser.add_argument('--to', '-t', dest='destination', required=True, help='Destination airport code')
    parser.add_argument('--date', '-d', required=True, help='Departure date (YYYY-MM-DD)')
    parser.add_argument('--length', '-l', type=int, help='Trip length in days (for round-trip analysis)')
    parser.add_argument('--passengers', '-p', type=int, default=1, help='Number of adult passengers')
    parser.add_argument('--class', '-c', dest='travel_class', choices=['economy', 'premium_economy', 'business', 'first'], help='Travel class')
    parser.add_argument('--currency', help='Currency code')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        params = {
            'originIataCode': args.origin.upper(),
            'destinationIataCode': args.destination.upper(),
            'departureDate': args.date,
        }
        
        if args.length:
            params['length'] = args.length
        if args.passengers > 1:
            params['adults'] = args.passengers
        if args.travel_class:
            params['travelClass'] = args.travel_class.upper()
        if args.currency:
            params['currencyCode'] = args.currency.upper()
        
        response = client.get('/v1/analytics/itinerary-price-metrics', params)
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        data = response.get('data', [])
        if not data:
            print(json.dumps({
                'success': False,
                'error': 'No price data available for this route',
            }), file=sys.stderr)
            sys.exit(1)
        
        analysis = data[0] if isinstance(data, list) else data
        formatted = format_price_analysis(analysis)
        
        result = {
            'success': True,
            'route': {
                'origin': args.origin.upper(),
                'destination': args.destination.upper(),
                'departure_date': args.date,
                'trip_length': args.length,
                'passengers': args.passengers,
                'class': args.travel_class or 'economy',
            },
            'analysis': formatted,
            'insights': {
                'current_price': formatted['price'],
                'recommendation': formatted['recommendation'],
                'best_dates': sorted(
                    formatted['related_dates'],
                    key=lambda x: x['price']
                )[:5] if formatted['related_dates'] else [],
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
