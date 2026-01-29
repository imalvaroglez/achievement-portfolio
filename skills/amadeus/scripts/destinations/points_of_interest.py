#!/usr/bin/env python3
"""
Search for points of interest (attractions, restaurants, etc.) near coordinates.

Examples:
    python points_of_interest.py --lat 48.8566 --lon 2.3522
    python points_of_interest.py --lat 40.7128 --lon -74.0060 --radius 2 --category RESTAURANT
    python points_of_interest.py --lat 51.5074 --lon -0.1278 --category SIGHTS,RESTAURANT
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


CATEGORIES = {
    'SIGHTS': 'Tourist attractions, landmarks, museums',
    'NIGHTLIFE': 'Bars, clubs, nightlife venues',
    'RESTAURANT': 'Restaurants and dining',
    'SHOPPING': 'Shopping centers and stores',
}


def format_poi(poi: dict) -> dict:
    """Format a point of interest for display."""
    name = poi.get('name', '')
    pois_data = poi.get('data', {})
    
    return {
        'name': name,
        'category': pois_data.get('category', ''),
        'subcategory': pois_data.get('subCategory', ''),
        'tags': pois_data.get('tags', []),
        'coordinates': {
            'latitude': pois_data.get('geoCode', {}).get('latitude'),
            'longitude': pois_data.get('geoCode', {}).get('longitude'),
        },
        'distance_km': pois_data.get('distance', {}).get('value'),
        'description': pois_data.get('description', ''),
        'wikipedia_url': pois_data.get('wikipediaPageUrl', ''),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Search for points of interest near coordinates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Categories:
{chr(10).join(f'  {cat}: {desc}' for cat, desc in CATEGORIES.items())}

Examples:
  python points_of_interest.py --lat 48.8566 --lon 2.3522
  python points_of_interest.py --lat 40.7128 --lon -74.0060 --radius 2 --category RESTAURANT
        """
    )
    parser.add_argument('--lat', type=float, required=True, help='Latitude')
    parser.add_argument('--lon', type=float, required=True, help='Longitude')
    parser.add_argument('--radius', '-r', type=int, default=1, help='Search radius in km (1-20, default: 1)')
    parser.add_argument('--category', '-c', help='Categories (comma-separated: SIGHTS, NIGHTLIFE, RESTAURANT, SHOPPING)')
    parser.add_argument('--max', type=int, default=20, help='Maximum results')
    parser.add_argument('--raw', action='store_true', help='Output raw API response')
    
    args = parser.parse_args()
    
    # Validate coordinates
    if not (-90 <= args.lat <= 90):
        print(json.dumps({
            'success': False,
            'error': 'Latitude must be between -90 and 90',
        }), file=sys.stderr)
        sys.exit(1)
    
    if not (-180 <= args.lon <= 180):
        print(json.dumps({
            'success': False,
            'error': 'Longitude must be between -180 and 180',
        }), file=sys.stderr)
        sys.exit(1)
    
    try:
        client = AmadeusClient()
        
        # Parse categories
        categories = None
        if args.category:
            categories = [c.strip().upper() for c in args.category.split(',')]
            # Validate categories
            valid_cats = set(CATEGORIES.keys())
            invalid = [c for c in categories if c not in valid_cats]
            if invalid:
                print(json.dumps({
                    'success': False,
                    'error': f'Invalid categories: {", ".join(invalid)}. Valid: {", ".join(valid_cats)}',
                }), file=sys.stderr)
                sys.exit(1)
        
        response = client.get_pois(
            latitude=args.lat,
            longitude=args.lon,
            radius=min(args.radius, 20),  # API limit
            categories=categories,
        )
        
        if args.raw:
            print(json.dumps(response, indent=2))
            return
        
        # Format response
        pois = response.get('data', [])
        formatted_pois = [format_poi(poi) for poi in pois[:args.max]]
        
        result = {
            'success': True,
            'search': {
                'coordinates': {
                    'latitude': args.lat,
                    'longitude': args.lon,
                },
                'radius_km': min(args.radius, 20),
                'categories': categories,
            },
            'results_count': len(formatted_pois),
            'pois': formatted_pois,
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
