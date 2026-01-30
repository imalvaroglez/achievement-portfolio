#!/usr/bin/env python3
"""
Unified travel research CLI — single entry point for all Amadeus travel operations.

Supports: flights, hotels, POI, airports, and combined research.
Outputs JSON for programmatic use or human-readable format for Telegram.

Examples:
    # Search flights
    python travel_research.py flights --from MEX --to CUN --date 2026-03-15

    # Search hotels
    python travel_research.py hotels --city PAR --checkin 2026-03-15 --checkout 2026-03-20

    # Points of interest
    python travel_research.py poi --lat 48.8566 --lon 2.3522

    # Airport lookup
    python travel_research.py airports --query "Cancun"

    # Combined research (flights + hotels + POI)
    python travel_research.py research --from MEX --to CUN --checkin 2026-03-15 --checkout 2026-03-20

    # Combined + Notion proposal
    python travel_research.py research --from MEX --to CUN --checkin 2026-03-15 --checkout 2026-03-20 --notion
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path
LIB_PATH = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB_PATH))

from client import AmadeusClient, APIError
from auth import AuthError


# ─── Formatters ───────────────────────────────────────────────────────────────

def format_duration(iso_duration: str) -> str:
    """PT9H15M -> 9h 15m"""
    if not iso_duration:
        return ""
    d = iso_duration.replace("PT", "")
    parts = []
    if "H" in d:
        h, d = d.split("H", 1)
        parts.append(f"{h}h")
    if "M" in d:
        m = d.replace("M", "")
        if m:
            parts.append(f"{m}m")
    return " ".join(parts)


def format_time(iso_dt: str) -> str:
    """2026-03-15T10:30:00 -> 10:30"""
    if not iso_dt:
        return ""
    try:
        return datetime.fromisoformat(iso_dt).strftime("%H:%M")
    except (ValueError, TypeError):
        return iso_dt


def format_flight_offer(offer: dict, dicts: dict) -> dict:
    """Format a raw Amadeus flight offer into a clean structure."""
    price = offer.get("price", {})
    travelers = offer.get("travelerPricings", [])
    total = float(price.get("total", 0))
    currency = price.get("currency", "EUR")
    carriers = dicts.get("carriers", {})
    aircraft = dicts.get("aircraft", {})

    itineraries = []
    for itin in offer.get("itineraries", []):
        segs = itin.get("segments", [])
        airlines = set()
        segments = []
        for seg in segs:
            cc = seg.get("carrierCode", "")
            name = carriers.get(cc, cc)
            airlines.add(name)
            ac = seg.get("aircraft", {}).get("code", "")
            segments.append({
                "flight": f"{cc}{seg.get('number', '')}",
                "airline": name,
                "aircraft": aircraft.get(ac, ac),
                "from": seg.get("departure", {}).get("iataCode", ""),
                "to": seg.get("arrival", {}).get("iataCode", ""),
                "departure": format_time(seg.get("departure", {}).get("at", "")),
                "arrival": format_time(seg.get("arrival", {}).get("at", "")),
                "departure_full": seg.get("departure", {}).get("at", ""),
                "arrival_full": seg.get("arrival", {}).get("at", ""),
                "duration": format_duration(seg.get("duration", "")),
            })
        stops = len(segs) - 1
        itineraries.append({
            "direction": "outbound" if len(itineraries) == 0 else "return",
            "duration": format_duration(itin.get("duration", "")),
            "stops": stops,
            "stops_label": "Nonstop" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}",
            "airlines": sorted(airlines),
            "segments": segments,
        })

    cabin = "ECONOMY"
    if travelers:
        fare = travelers[0].get("fareDetailsBySegment", [{}])[0]
        cabin = fare.get("cabin", "ECONOMY")

    return {
        "id": offer.get("id"),
        "price_total": total,
        "price_per_person": round(total / max(len(travelers), 1), 2),
        "currency": currency,
        "cabin": cabin,
        "itineraries": itineraries,
    }


def format_hotel_offer(offer: dict) -> dict:
    """Format a raw Amadeus hotel offer."""
    hotel = offer.get("hotel", {})
    offers_list = offer.get("offers", [])

    rooms = []
    for o in offers_list:
        price = o.get("price", {})
        room = o.get("room", {})
        desc = room.get("description", {}).get("text", "")
        rooms.append({
            "id": o.get("id"),
            "price_total": price.get("total"),
            "currency": price.get("currency", "EUR"),
            "checkin": o.get("checkInDate"),
            "checkout": o.get("checkOutDate"),
            "room_type": room.get("typeEstimated", {}).get("category", ""),
            "bed_type": room.get("typeEstimated", {}).get("bedType", ""),
            "beds": room.get("typeEstimated", {}).get("beds"),
            "description": desc[:200] if desc else "",
            "board_type": o.get("boardType", ""),
            "cancellation": "FREE" if o.get("policies", {}).get("cancellations") else "NON_REFUNDABLE",
        })

    return {
        "hotel_id": hotel.get("hotelId", ""),
        "name": hotel.get("name", "Unknown"),
        "city_code": hotel.get("cityCode", ""),
        "latitude": hotel.get("latitude"),
        "longitude": hotel.get("longitude"),
        "rating": hotel.get("rating"),
        "rooms": rooms,
    }


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_flights(args, client: AmadeusClient) -> dict:
    """Search flights."""
    seat_map = {
        "economy": "ECONOMY",
        "premium-economy": "PREMIUM_ECONOMY",
        "business": "BUSINESS",
        "first": "FIRST",
    }

    return_date = args.return_date
    if args.trip == "round-trip" and not return_date:
        return {"success": False, "error": "--return-date required for round-trip"}

    response = client.search_flights(
        origin=args.origin,
        destination=args.destination,
        departure_date=args.date,
        return_date=return_date,
        adults=args.adults,
        children=args.children,
        infants=getattr(args, "infants", 0),
        travel_class=seat_map.get(args.seat),
        non_stop=args.direct,
        currency=args.currency,
        max_results=args.limit,
    )

    offers = [format_flight_offer(o, response.get("dictionaries", {})) for o in response.get("data", [])]

    return {
        "success": True,
        "type": "flights",
        "search": {
            "origin": args.origin.upper(),
            "destination": args.destination.upper(),
            "date": args.date,
            "return_date": return_date,
            "adults": args.adults,
            "children": args.children,
            "seat": args.seat,
            "direct_only": args.direct,
        },
        "results_count": len(offers),
        "offers": offers,
    }


def cmd_hotels(args, client: AmadeusClient) -> dict:
    """Search hotels."""
    # Step 1: List hotels in city
    ratings = None
    if args.stars:
        ratings = [int(s) for s in args.stars.split(",")]

    hotels_data = client.search_hotels_by_city(
        city_code=args.city,
        ratings=ratings,
    )
    hotel_ids = [h.get("hotelId") for h in hotels_data.get("data", [])[:20]]

    if not hotel_ids:
        return {"success": True, "type": "hotels", "results_count": 0, "offers": [],
                "search": {"city": args.city.upper(), "checkin": args.checkin, "checkout": args.checkout}}

    # Step 2: Get offers
    offers_data = client.search_hotel_offers(
        hotel_ids=hotel_ids,
        check_in=args.checkin,
        check_out=args.checkout,
        adults=args.guests,
        currency=args.currency,
    )

    offers = [format_hotel_offer(o) for o in offers_data.get("data", [])[:args.limit]]

    return {
        "success": True,
        "type": "hotels",
        "search": {
            "city": args.city.upper(),
            "checkin": args.checkin,
            "checkout": args.checkout,
            "guests": args.guests,
            "stars": args.stars,
        },
        "results_count": len(offers),
        "offers": offers,
    }


def cmd_poi(args, client: AmadeusClient) -> dict:
    """Search points of interest."""
    categories = None
    if args.category:
        categories = [args.category.upper()]

    response = client.get_pois(
        latitude=args.lat,
        longitude=args.lon,
        radius=args.radius,
        categories=categories,
    )

    pois = []
    for p in response.get("data", [])[:args.limit]:
        pois.append({
            "name": p.get("name", ""),
            "category": p.get("category", ""),
            "rank": p.get("rank"),
            "tags": p.get("tags", []),
            "latitude": p.get("geoCode", {}).get("latitude"),
            "longitude": p.get("geoCode", {}).get("longitude"),
        })

    return {
        "success": True,
        "type": "poi",
        "search": {
            "latitude": args.lat,
            "longitude": args.lon,
            "radius": args.radius,
            "category": args.category,
        },
        "results_count": len(pois),
        "pois": pois,
    }


def cmd_airports(args, client: AmadeusClient) -> dict:
    """Search airports/cities."""
    response = client.search_airports(keyword=args.query)

    locations = []
    for loc in response.get("data", [])[:args.limit]:
        addr = loc.get("address", {})
        locations.append({
            "iata": loc.get("iataCode", ""),
            "name": loc.get("name", ""),
            "type": loc.get("subType", ""),
            "city": addr.get("cityName", ""),
            "country": addr.get("countryName", ""),
            "country_code": addr.get("countryCode", ""),
        })

    return {
        "success": True,
        "type": "airports",
        "search": {"query": args.query},
        "results_count": len(locations),
        "locations": locations,
    }


def cmd_research(args, client: AmadeusClient) -> dict:
    """Combined research: flights + hotels."""
    result = {
        "success": True,
        "type": "research",
        "search": {
            "origin": args.origin.upper(),
            "destination": args.destination.upper(),
            "checkin": args.checkin,
            "checkout": args.checkout,
            "adults": args.adults,
            "children": getattr(args, "children", 0),
            "currency": args.currency,
        },
        "flights": None,
        "hotels": None,
        "errors": [],
    }

    # Flights
    try:
        flight_resp = client.search_flights(
            origin=args.origin,
            destination=args.destination,
            departure_date=args.checkin,
            return_date=args.checkout,
            adults=args.adults,
            children=getattr(args, "children", 0),
            currency=args.currency,
            max_results=args.limit,
        )
        result["flights"] = [
            format_flight_offer(o, flight_resp.get("dictionaries", {}))
            for o in flight_resp.get("data", [])
        ]
    except (APIError, AuthError) as e:
        result["errors"].append(f"Flights: {e}")

    # Hotels
    try:
        hotels_data = client.search_hotels_by_city(args.destination)
        hotel_ids = [h.get("hotelId") for h in hotels_data.get("data", [])[:15]]
        if hotel_ids:
            offers_data = client.search_hotel_offers(
                hotel_ids=hotel_ids,
                check_in=args.checkin,
                check_out=args.checkout,
                adults=args.adults,
                currency=args.currency,
            )
            result["hotels"] = [
                format_hotel_offer(o)
                for o in offers_data.get("data", [])[:args.limit]
            ]
    except (APIError, AuthError) as e:
        result["errors"].append(f"Hotels: {e}")

    # Notion integration
    if args.notion:
        try:
            from notion_helper import NotionHelper, NotionError
            notion = NotionHelper()
            notion_db_id = args.notion_db or "2f7a81f6c8ba8026b70bfcf4e9e9549f"

            origin = result["search"]["origin"]
            dest = result["search"]["destination"]
            title = f"{origin} → {dest} ({args.checkin})"

            page = notion.create_page(
                parent_id=notion_db_id,
                title=title,
                is_database_parent=True,
            )
            page_id = page["id"]

            blocks = _build_notion_blocks(result)
            if blocks:
                notion.append_blocks(page_id, blocks)

            result["notion"] = {
                "page_id": page_id,
                "url": f"https://notion.so/{page_id.replace('-', '')}",
            }
        except Exception as e:
            result["errors"].append(f"Notion: {e}")

    return result


def _build_notion_blocks(research: dict) -> list:
    """Build Notion blocks from research data."""
    from notion_helper import NotionHelper

    blocks = []
    params = research["search"]

    # Summary
    blocks.append(NotionHelper.heading_block("Trip Summary", level=1))
    blocks.append(NotionHelper.paragraph_block(
        f"Route: {params['origin']} → {params['destination']} | "
        f"Dates: {params['checkin']} to {params['checkout']} | "
        f"Travelers: {params['adults']} adult(s)"
    ))
    blocks.append(NotionHelper.divider_block())

    # Flights
    blocks.append(NotionHelper.heading_block("✈️ Flight Options", level=2))
    flights = research.get("flights") or []
    if flights:
        for i, f in enumerate(flights[:5], 1):
            cur = f["currency"]
            blocks.append(NotionHelper.paragraph_block(
                f"Option {i}: {cur} {f['price_total']:,.2f} ({cur} {f['price_per_person']:,.2f}/person) — {f['cabin']}",
                bold=True,
            ))
            for itin in f["itineraries"]:
                airlines = ", ".join(itin["airlines"])
                blocks.append(NotionHelper.paragraph_block(
                    f"  {'🛫' if itin['direction'] == 'outbound' else '🛬'} "
                    f"{itin['duration']} · {itin['stops_label']} · {airlines}"
                ))
                for seg in itin["segments"]:
                    blocks.append(NotionHelper.paragraph_block(
                        f"    {seg['flight']}: {seg['from']} {seg['departure']} → {seg['to']} {seg['arrival']} ({seg['duration']})"
                    ))
    else:
        blocks.append(NotionHelper.paragraph_block("No flight offers found"))

    blocks.append(NotionHelper.divider_block())

    # Hotels
    blocks.append(NotionHelper.heading_block("🏨 Hotel Options", level=2))
    hotels = research.get("hotels") or []
    if hotels:
        for i, h in enumerate(hotels[:5], 1):
            rating = f"⭐{h['rating']}" if h.get("rating") else ""
            blocks.append(NotionHelper.paragraph_block(
                f"Option {i}: {h['name']} {rating}",
                bold=True,
            ))
            for room in h.get("rooms", [])[:1]:
                blocks.append(NotionHelper.paragraph_block(
                    f"  {room['currency']} {room['price_total']} total | "
                    f"{room['room_type']} {room['bed_type']} | "
                    f"{room['cancellation']}"
                ))
    else:
        blocks.append(NotionHelper.paragraph_block("No hotel offers found"))

    blocks.append(NotionHelper.divider_block())

    # Errors
    errors = research.get("errors", [])
    if errors:
        blocks.append(NotionHelper.heading_block("⚠️ Notes", level=2))
        for err in errors:
            blocks.append(NotionHelper.paragraph_block(f"• {err}"))

    # Metadata
    blocks.append(NotionHelper.heading_block("📋 Search Parameters", level=2))
    blocks.append(NotionHelper.code_block(json.dumps(params, indent=2), language="json"))

    return blocks


# ─── CLI Setup ────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified travel research CLI (Amadeus API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--raw", action="store_true", help="Output raw API response")
    sub = parser.add_subparsers(dest="command", required=True)

    # flights
    fl = sub.add_parser("flights", help="Search flights")
    fl.add_argument("--from", dest="origin", required=True)
    fl.add_argument("--to", dest="destination", required=True)
    fl.add_argument("--date", required=True, help="Departure date YYYY-MM-DD")
    fl.add_argument("--return-date", dest="return_date")
    fl.add_argument("--trip", choices=["one-way", "round-trip"], default="one-way")
    fl.add_argument("--seat", choices=["economy", "premium-economy", "business", "first"], default="economy")
    fl.add_argument("--adults", type=int, default=1)
    fl.add_argument("--children", type=int, default=0)
    fl.add_argument("--infants", type=int, default=0)
    fl.add_argument("--direct", action="store_true")
    fl.add_argument("--currency", default=None)
    fl.add_argument("--limit", type=int, default=10)

    # hotels
    ht = sub.add_parser("hotels", help="Search hotels")
    ht.add_argument("--city", required=True, help="City IATA code")
    ht.add_argument("--checkin", required=True)
    ht.add_argument("--checkout", required=True)
    ht.add_argument("--guests", type=int, default=1)
    ht.add_argument("--stars", default=None, help="Filter stars e.g. 4,5")
    ht.add_argument("--currency", default=None)
    ht.add_argument("--limit", type=int, default=10)

    # poi
    po = sub.add_parser("poi", help="Points of interest")
    po.add_argument("--lat", type=float, required=True)
    po.add_argument("--lon", type=float, required=True)
    po.add_argument("--radius", type=int, default=2, help="Radius in km (1-20)")
    po.add_argument("--category", choices=["SIGHTS", "NIGHTLIFE", "RESTAURANT", "SHOPPING"])
    po.add_argument("--limit", type=int, default=20)

    # airports
    ap = sub.add_parser("airports", help="Airport/city lookup")
    ap.add_argument("--query", "-q", required=True, help="City or airport name")
    ap.add_argument("--limit", type=int, default=10)

    # research (combined)
    rs = sub.add_parser("research", help="Combined: flights + hotels + Notion")
    rs.add_argument("--from", dest="origin", required=True)
    rs.add_argument("--to", dest="destination", required=True)
    rs.add_argument("--checkin", required=True)
    rs.add_argument("--checkout", required=True)
    rs.add_argument("--adults", type=int, default=1)
    rs.add_argument("--children", type=int, default=0)
    rs.add_argument("--currency", default=None)
    rs.add_argument("--limit", type=int, default=5)
    rs.add_argument("--notion", action="store_true", help="Create Notion proposal page")
    rs.add_argument("--notion-db", default=None, help="Notion database ID override")

    return parser


COMMANDS = {
    "flights": cmd_flights,
    "hotels": cmd_hotels,
    "poi": cmd_poi,
    "airports": cmd_airports,
    "research": cmd_research,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        client = AmadeusClient()
        handler = COMMANDS[args.command]
        result = handler(args, client)

        # Add metadata
        result["meta"] = {
            "source": "amadeus",
            "environment": client.auth.env,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        print(json.dumps(result, indent=2))

    except AuthError as e:
        print(json.dumps({"success": False, "error": str(e), "code": 401}), file=sys.stderr)
        sys.exit(1)
    except APIError as e:
        print(json.dumps({"success": False, "error": str(e), "code": e.status_code}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
