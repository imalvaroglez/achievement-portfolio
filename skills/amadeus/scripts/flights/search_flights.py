#!/usr/bin/env python3
"""
Search for flight offers using Amadeus API.

Examples:
    python search_flights.py --from BCN --to JFK --date 2026-03-15
    python search_flights.py --from BCN --to JFK --date 2026-03-15 --return 2026-03-22 --passengers 2
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


def format_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration to human readable."""
    # PT9H15M -> 9h 15m
    duration = iso_duration.replace('PT', '')
    hours = ''
    minutes = ''
    
    if 'H' in duration:
        parts = duration.split('H')
        hours = f"{parts[0]}h"
        duration = parts[1] if len(parts) > 1 else ''
    
    if 'M' in duration:
        minutes = f" {duration.replace('M', '')}m"
    
    return f"{hours}{minutes}".strip()


def format_flight_offer(offer: dict, dictionaries: dict) -> dict:
    """Format a flight offer for display."""
    itineraries = offer.get('itineraries', [])
    price = offer.get('price', {})
    
    formatted = {
        'id': offer.get('id'),
        'price': {
            'total': float(price.get('total', 0)),
            'currency': price.get('currency', 'EUR'),
            'per_traveler': float(price.get('grandTotal', 0)) / max(offer.get('travelerPricings', [{}]).__len__(), 1),
        },
        'itineraries': [],
    }
    
    carriers = dictionaries.get('carriers', {})
    aircraft = dictionaries.get('aircraft', {})
    
    for itinerary in itineraries:
        segments = itinerary.get('segments', [])
        itin_data = {
            'duration': format_duration(itinerary.get('duration', '')),
            'segments': [],
        }
        
        for seg in segments:
            carrier_code = seg.get('carrierCode', '')
            itin_data['segments'].append({
                'flight': f"{carrier_code}{seg.get('number', '')}",
                'airline': carriers.get(carrier_code, carrier_code),
                'aircraft': aircraft.get(seg.get('aircraft', {}).get('code', ''), ''),
                'departure': {
                    'airport': seg.get('departure', {}).get('iataCode', ''),
                    'time': seg.get('departure', {}).get('at', ''),
                    'terminal': seg.get('departure', {}).get('terminal'),
                },
                'arrival': {
                    'airport': seg.get('arrival', {}).get('iataCode', ''),
                    'time': seg.get('arrival', {}).get('at', ''),
                    'terminal': seg.get('arrival', {}).get('terminal'),
                },
                'duration': format_duration(seg.get('duration', '')),
                'stops': seg.get('numberOfStops', 0),
            })
        
        itin_data['stops'] = len(segments) - 1
        formatted['itineraries'].append(itin_data)
    
    # Cabin class from first traveler pricing
    traveler_pricing = offer.get('travelerPricings', [{}])[0]
    fare_details = traveler_pricing.get('fareDetailsBySegment', [{}])[0]
    formatted['cabin'] = fare_details.get('cabin', 'ECONOMY')
    
    return formatted


def main():
    parser = argparse.ArgumentParser(description='Search for flights')
    parser.add_argument('--from', '-f', dest='origin', required=True, help='Origin airport code (e.g., BCN)')
    parser.add_argument('--to', '-t', dest='destination', required=True, help='Destination airport code (e.g., JFK)')
    parser.add_argument('--date', '-d', required=True, help='Departure date (YYYY-MM-DD)')
    parser.add_argument('--return', '-r', dest='return_date', help='Return date for round trip (YYYY-MM-DD)')
    parser.add_argument('--passengers', '-p', type=int, default=1, help='Number of adult passengers')
    parser.add_argument('--children', type=int, default=0, help='Number of children (2-11)')
    parser.add_argument('--infants', type=int, default=0, help='Number of infants (<2)')
    parser.add_argument('--class', '-c', dest='travel_class', choices=['economy', 'premium_economy', 'business', 'first'], help='Travel class')
    parser.add_argument('--direct', action='store_true', help='Direct flights only')
    parser.add_argument('--currency', help='Currency code (e.g., EUR, USD)')
    parser.add_argument('--max', type=int, default=10, help='Maximum results')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        response = client.search_flights(
            origin=args.origin,
            destination=args.destination,
            departure_date=args.date,
            return_date=args.return_date,
            adults=args.passengers,
            children=args.children,
            infants=args.infants,
            travel_class=args.travel_class.upper() if args.travel_class else None,
            non_stop=args.direct,
            currency=args.currency,
            max_results=args.max,
        )
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        offers = response.get('data', [])
        dictionaries = response.get('dictionaries', {})
        
        formatted_offers = [format_flight_offer(offer, dictionaries) for offer in offers]
        
        result = {
            'success': True,
            'search': {
                'origin': args.origin.upper(),
                'destination': args.destination.upper(),
                'departure_date': args.date,
                'return_date': args.return_date,
                'passengers': {
                    'adults': args.passengers,
                    'children': args.children,
                    'infants': args.infants,
                },
                'class': args.travel_class or 'any',
                'direct_only': args.direct,
            },
            'results_count': len(formatted_offers),
            'offers': formatted_offers,
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
