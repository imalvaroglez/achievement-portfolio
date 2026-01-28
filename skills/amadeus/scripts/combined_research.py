#!/usr/bin/env python3
"""
Combined travel research - search flights, hotels, and POI, then save to Notion.

One command to research a destination and create a proposal page.

Examples:
    python combined_research.py --from BCN --to JFK --checkin 2026-03-15 --checkout 2026-03-20 --guest-count 2
    python combined_research.py --from MAD --to NYC --checkin 2026-04-01 --checkout 2026-04-08 --notion-parent "Travel Proposals"
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from client import AmadeusClient, APIError
from auth import AuthError
from notion_helper import NotionHelper, NotionError


def research_destination(
    client: AmadeusClient,
    origin: str,
    destination: str,
    checkin: str,
    checkout: str,
    guest_count: int = 1,
) -> dict:
    """
    Research a destination: flights, hotels, and POI.
    
    Returns structured data for all three searches.
    """
    research = {
        'search_params': {
            'origin': origin.upper(),
            'destination': destination.upper(),
            'checkin': checkin,
            'checkout': checkout,
            'guests': guest_count,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        },
        'flights': None,
        'hotels': None,
        'pois': None,
        'errors': [],
    }
    
    # Search flights
    try:
        flight_data = client.search_flights(
            origin=origin,
            destination=destination,
            departure_date=checkin,
            return_date=checkout if guest_count == 1 else None,
            adults=guest_count,
            max_results=5,
        )
        research['flights'] = flight_data.get('data', [])[:3]  # Top 3 offers
    except (APIError, AuthError) as e:
        research['errors'].append(f'Flight search failed: {e}')
    
    # Search hotels
    try:
        # Get city code from destination (simplified - assumes it's a city code)
        hotels_data = client.search_hotels_by_city(destination)
        hotel_ids = [h.get('hotelId') for h in hotels_data.get('data', [])[:10]]
        
        if hotel_ids:
            offers_data = client.search_hotel_offers(
                hotel_ids=hotel_ids,
                check_in=checkin,
                check_out=checkout,
                adults=guest_count,
            )
            research['hotels'] = offers_data.get('data', [])[:3]  # Top 3 offers
    except (APIError, AuthError) as e:
        research['errors'].append(f'Hotel search failed: {e}')
    
    return research


def create_proposal_page(
    notion: NotionHelper,
    parent_id: str,
    research: dict,
    is_database: bool = True,
) -> str:
    """
    Create a Notion page with travel proposal.
    
    Returns page ID.
    """
    origin = research['search_params']['origin']
    destination = research['search_params']['destination']
    checkin = research['search_params']['checkin']
    title = f'{origin} → {destination} ({checkin})'
    
    # Create page
    page = notion.create_page(
        parent_id=parent_id,
        title=title,
        is_database_parent=is_database,
    )
    page_id = page['id']
    
    # Prepare blocks
    blocks = []
    
    # Trip summary
    blocks.append(NotionHelper.heading_block('Trip Summary', level=1))
    blocks.append(NotionHelper.paragraph_block(
        f"Origin: {origin} | Destination: {destination} | "
        f"Check-in: {checkin} | Check-out: {research['search_params']['checkout']} | "
        f"Guests: {research['search_params']['guests']}"
    ))
    blocks.append(NotionHelper.divider_block())
    
    # Flights section
    blocks.append(NotionHelper.heading_block('✈️ Flights', level=2))
    if research['flights']:
        for i, offer in enumerate(research['flights'][:3], 1):
            price = offer.get('price', {})
            itineraries = offer.get('itineraries', [])
            
            blocks.append(NotionHelper.paragraph_block(
                f"Option {i}: €{price.get('total', 'N/A')} "
                f"({len(itineraries)} itinerary, {len(itineraries[0].get('segments', [])) - 1 if itineraries else 0} stops)",
                bold=True,
            ))
            
            if itineraries:
                itin = itineraries[0]
                duration = itin.get('duration', '').replace('PT', '')
                blocks.append(NotionHelper.paragraph_block(
                    f"Duration: {duration} | Cabin: {offer.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0].get('cabin', 'N/A')}"
                ))
    else:
        blocks.append(NotionHelper.paragraph_block('No flight offers available'))
    
    blocks.append(NotionHelper.divider_block())
    
    # Hotels section
    blocks.append(NotionHelper.heading_block('🏨 Hotels', level=2))
    if research['hotels']:
        for i, offer in enumerate(research['hotels'][:3], 1):
            hotel = offer.get('hotel', {})
            blocks.append(NotionHelper.paragraph_block(
                f"Option {i}: {hotel.get('name', 'Unknown')} ⭐{hotel.get('rating', 'N/A')}",
                bold=True,
            ))
            
            rooms = offer.get('rooms', [])
            if rooms:
                room = rooms[0]
                price = room.get('price', {})
                blocks.append(NotionHelper.paragraph_block(
                    f"€{price.get('total', 'N/A')} total | "
                    f"€{price.get('per_night', 'N/A')}/night | "
                    f"{room.get('room', {}).get('bedType', 'N/A')}"
                ))
    else:
        blocks.append(NotionHelper.paragraph_block('No hotel offers available'))
    
    blocks.append(NotionHelper.divider_block())
    
    # Metadata
    blocks.append(NotionHelper.heading_block('📋 Metadata', level=2))
    metadata = json.dumps(research['search_params'], indent=2)
    blocks.append(NotionHelper.code_block(metadata, language='json'))
    
    # Add blocks to page
    if blocks:
        notion.append_blocks(page_id, blocks)
    
    return page_id


def main():
    parser = argparse.ArgumentParser(
        description='Combined travel research and proposal generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python combined_research.py --from BCN --to JFK --checkin 2026-03-15 --checkout 2026-03-20
  python combined_research.py --from MAD --to NYC --checkin 2026-04-01 --checkout 2026-04-08 \\
    --guest-count 2 --notion-parent "Travel Proposals"
        """
    )
    
    # Search parameters
    parser.add_argument('--from', '-f', dest='origin', required=True, help='Origin airport code')
    parser.add_argument('--to', '-t', dest='destination', required=True, help='Destination city code')
    parser.add_argument('--checkin', required=True, help='Check-in date (YYYY-MM-DD)')
    parser.add_argument('--checkout', required=True, help='Check-out date (YYYY-MM-DD)')
    parser.add_argument('--guest-count', '-g', type=int, default=1, help='Number of guests')
    
    # Notion parameters
    parser.add_argument('--notion-parent', help='Notion page/database name or ID to create proposal in')
    parser.add_argument('--no-notion', action='store_true', help='Skip Notion integration, output JSON only')
    
    # Output
    parser.add_argument('--output', '-o', help='Save JSON output to file')
    
    args = parser.parse_args()
    
    try:
        # Research
        client = AmadeusClient()
        print(f"Researching {args.origin} → {args.destination}...", file=sys.stderr)
        research = research_destination(
            client,
            args.origin,
            args.destination,
            args.checkin,
            args.checkout,
            args.guest_count,
        )
        
        # Notion integration
        if not args.no_notion and args.notion_parent:
            print(f"Creating Notion page...", file=sys.stderr)
            notion = NotionHelper()
            
            # Search for parent
            results = notion.search(args.notion_parent, object_type='database')
            if results:
                parent = results[0]
                parent_id = parent.get('id')
                is_database = parent.get('object') == 'data_source'
                
                page_id = create_proposal_page(notion, parent_id, research, is_database)
                research['notion_page_id'] = page_id
                research['notion_url'] = f"https://notion.so/{page_id.replace('-', '')}"
                print(f"✓ Page created: {research['notion_url']}", file=sys.stderr)
            else:
                print(f"⚠ Notion parent not found: {args.notion_parent}", file=sys.stderr)
        
        # Output
        result = {
            'success': True,
            'research': research,
            'meta': {
                'source': 'amadeus',
                'environment': client.auth.env,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            },
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(result, indent=2))
        
    except (AuthError, APIError, NotionError) as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
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
