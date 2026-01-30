#!/usr/bin/env python3
"""
Flight search script using Amadeus API.

This is the main entry point for the flights skill. It wraps the Amadeus
API client with a user-friendly CLI interface matching the original skill contract.

Usage:
    search_flights.py --from JFK --to LAX --date 2026-02-15 [options]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add amadeus lib to path
AMADEUS_LIB = Path(__file__).resolve().parent.parent.parent / 'amadeus' / 'lib'
sys.path.insert(0, str(AMADEUS_LIB))

from client import AmadeusClient, APIError
from auth import AuthError


def parse_args():
    parser = argparse.ArgumentParser(description="Search flights via Amadeus API")
    parser.add_argument("--from", dest="from_airport", required=True,
                        help="Departure airport code (e.g., JFK)")
    parser.add_argument("--to", dest="to_airport", required=True,
                        help="Arrival airport code (e.g., LAX)")
    parser.add_argument("--date", required=True,
                        help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return-date", dest="return_date",
                        help="Return date for round-trip (YYYY-MM-DD)")
    parser.add_argument("--trip", choices=["one-way", "round-trip"], default="one-way",
                        help="Trip type (default: one-way)")
    parser.add_argument("--seat", choices=["economy", "premium-economy", "business", "first"],
                        default="economy", help="Seat class (default: economy)")
    parser.add_argument("--adults", type=int, default=1,
                        help="Number of adult passengers (default: 1)")
    parser.add_argument("--children", type=int, default=0,
                        help="Number of children 2-11 (default: 0)")
    parser.add_argument("--infants", type=int, default=0,
                        help="Number of infants <2 (default: 0)")
    parser.add_argument("--direct", action="store_true",
                        help="Direct/nonstop flights only")
    parser.add_argument("--currency", default=None,
                        help="Currency code (e.g., USD, MXN, EUR)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max results to show (default: 10)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--raw", action="store_true",
                        help="Output raw Amadeus API response")
    return parser.parse_args()


# Map CLI seat names to Amadeus travel class codes
SEAT_MAP = {
    "economy": "ECONOMY",
    "premium-economy": "PREMIUM_ECONOMY",
    "business": "BUSINESS",
    "first": "FIRST",
}


def format_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration (PT9H15M) to human readable (9h 15m)."""
    if not iso_duration:
        return ""
    duration = iso_duration.replace("PT", "")
    parts = []
    if "H" in duration:
        h, duration = duration.split("H", 1)
        parts.append(f"{h}h")
    if "M" in duration:
        m = duration.replace("M", "")
        if m:
            parts.append(f"{m}m")
    return " ".join(parts)


def format_time(iso_datetime: str) -> str:
    """Extract time from ISO datetime string (2026-03-15T10:30:00 -> 10:30)."""
    if not iso_datetime:
        return ""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return iso_datetime


def format_offer(offer: dict, dictionaries: dict) -> dict:
    """Format a single flight offer into a clean structure."""
    price_data = offer.get("price", {})
    traveler_count = len(offer.get("travelerPricings", [1]))
    total = float(price_data.get("total", 0))
    currency = price_data.get("currency", "EUR")

    carriers = dictionaries.get("carriers", {})
    aircraft_dict = dictionaries.get("aircraft", {})

    itineraries = []
    for itin in offer.get("itineraries", []):
        segments = itin.get("segments", [])
        seg_list = []
        airlines_in_itin = set()

        for seg in segments:
            carrier_code = seg.get("carrierCode", "")
            airline_name = carriers.get(carrier_code, carrier_code)
            airlines_in_itin.add(airline_name)
            aircraft_code = seg.get("aircraft", {}).get("code", "")

            seg_list.append({
                "flight": f"{carrier_code}{seg.get('number', '')}",
                "airline": airline_name,
                "aircraft": aircraft_dict.get(aircraft_code, aircraft_code),
                "from": seg.get("departure", {}).get("iataCode", ""),
                "to": seg.get("arrival", {}).get("iataCode", ""),
                "departure": format_time(seg.get("departure", {}).get("at", "")),
                "arrival": format_time(seg.get("arrival", {}).get("at", "")),
                "departure_full": seg.get("departure", {}).get("at", ""),
                "arrival_full": seg.get("arrival", {}).get("at", ""),
                "terminal_dep": seg.get("departure", {}).get("terminal"),
                "terminal_arr": seg.get("arrival", {}).get("terminal"),
                "duration": format_duration(seg.get("duration", "")),
                "stops_in_segment": seg.get("numberOfStops", 0),
            })

        num_stops = len(segments) - 1
        itineraries.append({
            "direction": "outbound" if len(itineraries) == 0 else "return",
            "duration": format_duration(itin.get("duration", "")),
            "stops": num_stops,
            "stops_label": "Nonstop" if num_stops == 0 else f"{num_stops} stop{'s' if num_stops > 1 else ''}",
            "airlines": sorted(airlines_in_itin),
            "segments": seg_list,
        })

    # Cabin class from first traveler pricing
    traveler_pricing = offer.get("travelerPricings", [{}])[0]
    fare_details = traveler_pricing.get("fareDetailsBySegment", [{}])[0]
    cabin = fare_details.get("cabin", "ECONOMY")

    return {
        "id": offer.get("id"),
        "price_total": total,
        "price_per_person": round(total / max(traveler_count, 1), 2),
        "currency": currency,
        "cabin": cabin,
        "itineraries": itineraries,
    }


def format_human_output(args, offers, meta):
    """Format results for human-readable terminal output."""
    lines = []
    trip_label = "↩️  Round-trip" if args.return_date else "➡️  One-way"
    lines.append(f"✈️  {args.from_airport.upper()} → {args.to_airport.upper()} | {args.date}")
    if args.return_date:
        lines.append(f"↩️  Return: {args.return_date}")
    pax_parts = [f"{args.adults} adult{'s' if args.adults > 1 else ''}"]
    if args.children:
        pax_parts.append(f"{args.children} child{'ren' if args.children > 1 else ''}")
    if args.infants:
        pax_parts.append(f"{args.infants} infant{'s' if args.infants > 1 else ''}")
    lines.append(f"👥 {', '.join(pax_parts)} | {args.seat.replace('-', ' ').title()}")
    if args.direct:
        lines.append("🔹 Direct flights only")
    lines.append(f"📋 {len(offers)} result{'s' if len(offers) != 1 else ''} found")
    lines.append(f"🔗 Source: Amadeus ({meta.get('environment', 'test')})")
    lines.append("")
    lines.append("=" * 55)

    for idx, offer in enumerate(offers, 1):
        price = offer["price_total"]
        ppp = offer["price_per_person"]
        cur = offer["currency"]
        lines.append("")
        lines.append(f"  #{idx}  💰 {cur} {price:,.2f} total ({cur} {ppp:,.2f}/person)")
        lines.append(f"       Cabin: {offer['cabin'].replace('_', ' ').title()}")

        for itin in offer["itineraries"]:
            direction = "🛫 Outbound" if itin["direction"] == "outbound" else "🛬 Return"
            lines.append(f"       {direction}: {itin['duration']} · {itin['stops_label']}")
            for seg in itin["segments"]:
                dep = seg["departure"]
                arr = seg["arrival"]
                lines.append(f"         {seg['flight']} {seg['airline']}")
                lines.append(f"         {seg['from']} {dep} → {seg['to']} {arr} ({seg['duration']})")
                terms = []
                if seg.get("terminal_dep"):
                    terms.append(f"T{seg['terminal_dep']}")
                if seg.get("terminal_arr"):
                    terms.append(f"→ T{seg['terminal_arr']}")
                if terms:
                    lines.append(f"         Terminals: {' '.join(terms)}")
        lines.append("  " + "-" * 53)

    lines.append("")
    lines.append(f"⏱️  {meta.get('timestamp', '')}")
    return "\n".join(lines)


def search_flights(args):
    """Execute the flight search via Amadeus API."""
    client = AmadeusClient()

    # Determine return date
    return_date = args.return_date
    if args.trip == "round-trip" and not return_date:
        print("Error: --return-date is required for round-trip searches", file=sys.stderr)
        sys.exit(1)

    travel_class = SEAT_MAP.get(args.seat)

    response = client.search_flights(
        origin=args.from_airport,
        destination=args.to_airport,
        departure_date=args.date,
        return_date=return_date,
        adults=args.adults,
        children=args.children,
        infants=args.infants,
        travel_class=travel_class,
        non_stop=args.direct,
        currency=args.currency,
        max_results=args.limit,
    )

    return response


def main():
    args = parse_args()

    try:
        response = search_flights(args)

        # Raw output
        if args.raw:
            print(json.dumps(response, indent=2))
            return

        # Format offers
        raw_offers = response.get("data", [])
        dictionaries = response.get("dictionaries", {})
        offers = [format_offer(o, dictionaries) for o in raw_offers]

        meta = {
            "source": "amadeus",
            "environment": "test",  # will be overridden below
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "cached": False,
        }
        # Detect env from response URL or client
        try:
            meta["environment"] = AmadeusClient().auth.env
        except Exception:
            pass

        # JSON output
        if args.json:
            result = {
                "success": True,
                "search": {
                    "origin": args.from_airport.upper(),
                    "destination": args.to_airport.upper(),
                    "departure_date": args.date,
                    "return_date": args.return_date,
                    "passengers": {
                        "adults": args.adults,
                        "children": args.children,
                        "infants": args.infants,
                    },
                    "seat": args.seat,
                    "direct_only": args.direct,
                },
                "results_count": len(offers),
                "offers": offers,
                "meta": meta,
            }
            print(json.dumps(result, indent=2))
            return

        # Human-readable output
        if not offers:
            print(f"No flights found for {args.from_airport.upper()} → {args.to_airport.upper()} on {args.date}")
            return

        print(format_human_output(args, offers, meta))

    except AuthError as e:
        error = {"success": False, "error": str(e), "code": 401}
        print(json.dumps(error, indent=2), file=sys.stderr)
        sys.exit(1)

    except APIError as e:
        error = {"success": False, "error": str(e), "code": e.status_code, "details": e.errors}
        print(json.dumps(error, indent=2), file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        error = {"success": False, "error": str(e)}
        print(json.dumps(error, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
