#!/usr/bin/env python3
"""
Search for hotel offers by destination and dates.

Examples:
    python search_hotels.py --city PAR --checkin 2026-03-15 --checkout 2026-03-20
    python search_hotels.py --city NYC --checkin 2026-03-15 --checkout 2026-03-20 --guests 2 --rooms 1
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


def format_room_offer(offer: dict) -> dict:
    """Format a room offer for display."""
    room = offer.get('room', {})
    price = offer.get('price', {})
    policies = offer.get('policies', {})
    
    return {
        'type': room.get('type', ''),
        'beds': room.get('bedType', ''),
        'bed_count': room.get('numberOfBeds', 1),
        'size_sqm': room.get('size', ''),
        'description': room.get('description', ''),
        'price': {
            'total': float(price.get('total', 0)),
            'per_night': float(price.get('total', 0)) / max(
                (datetime.fromisoformat(offer.get('checkOutDate', '2026-03-20')) - 
                 datetime.fromisoformat(offer.get('checkInDate', '2026-03-15'))).days, 1
            ),
            'currency': price.get('currency', 'EUR'),
        },
        'policies': {
            'cancellation': policies.get('cancellation', {}).get('type', ''),
            'checkInFrom': policies.get('checkInFrom'),
            'checkOutUntil': policies.get('checkOutUntil'),
        },
        'amenities': offer.get('amenities', []),
    }


def format_hotel_offer(offer: dict) -> dict:
    """Format a hotel offer for display."""
    hotel = offer.get('hotel', {})
    
    formatted = {
        'id': offer.get('id', hotel.get('hotelId', '')),
        'name': hotel.get('name', ''),
        'rating': hotel.get('rating', 0),
        'distance': offer.get('distance', {}),
        'contact': {
            'phone': hotel.get('contact', {}).get('phone'),
            'email': hotel.get('contact', {}).get('email'),
        },
        'address': {
            'address': hotel.get('address', {}).get('address'),
            'city': hotel.get('address', {}).get('cityName', ''),
            'postal_code': hotel.get('address', {}).get('postalCode', ''),
            'country': hotel.get('address', {}).get('countryName', ''),
        },
        'amenities': hotel.get('amenities', []),
        'rooms': [format_room_offer(room) for room in offer.get('rooms', [])],
    }
    
    # Get cheapest room option
    if formatted['rooms']:
        prices = [r['price']['total'] for r in formatted['rooms']]
        formatted['cheapest_room'] = min(prices)
    
    return formatted


def main():
    parser = argparse.ArgumentParser(description='Search for hotel offers')
    parser.add_argument('--city', '-c', required=True, help='City IATA code (e.g., PAR, NYC)')
    parser.add_argument('--checkin', required=True, help='Check-in date (YYYY-MM-DD)')
    parser.add_argument('--checkout', required=True, help='Check-out date (YYYY-MM-DD)')
    parser.add_argument('--guests', '-g', type=int, default=1, help='Number of adult guests')
    parser.add_argument('--rooms', '-r', type=int, default=1, help='Number of rooms')
    parser.add_argument('--currency', help='Currency code (e.g., EUR, USD)')
    parser.add_argument('--max', type=int, default=10, help='Maximum results')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    try:
        client = AmadeusClient()
        
        # First, get hotel IDs for the city
        city_hotels = client.search_hotels_by_city(args.city.upper())
        hotel_ids = [h.get('hotelId') for h in city_hotels.get('data', [])[:20]]
        
        if not hotel_ids:
            print(json.dumps({
                'success': False,
                'error': f'No hotels found for city code: {args.city.upper()}',
            }), file=sys.stderr)
            sys.exit(1)
        
        # Search for offers
        response = client.search_hotel_offers(
            hotel_ids=hotel_ids,
            check_in=args.checkin,
            check_out=args.checkout,
            adults=args.guests,
            rooms=args.rooms,
            currency=args.currency,
        )
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        offers = response.get('data', [])
        formatted_offers = [format_hotel_offer(offer) for offer in offers[:args.max]]
        
        # Calculate nights
        checkin = datetime.fromisoformat(args.checkin)
        checkout = datetime.fromisoformat(args.checkout)
        nights = (checkout - checkin).days
        
        result = {
            'success': True,
            'search': {
                'city': args.city.upper(),
                'checkin': args.checkin,
                'checkout': args.checkout,
                'nights': nights,
                'guests': args.guests,
                'rooms': args.rooms,
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
