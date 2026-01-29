#!/usr/bin/env python3
"""
Flight search script using fast-flights with web_fetch fallback.
Usage: search_flights.py --from JFK --to LAX --date 2026-02-15 [options]
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
from html import unescape

# Try fast-flights first, fall back to web scraping
try:
    from fast_flights import FlightData, Passengers, TFSData, get_flights
    FAST_FLIGHTS_AVAILABLE = True
except ImportError:
    FAST_FLIGHTS_AVAILABLE = False


def parse_args():
    parser = argparse.ArgumentParser(description="Search flights via Google Flights")
    parser.add_argument("--from", dest="from_airport", required=True, help="Departure airport code (e.g., JFK)")
    parser.add_argument("--to", dest="to_airport", required=True, help="Arrival airport code (e.g., LAX)")
    parser.add_argument("--date", required=True, help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return-date", dest="return_date", help="Return date for round-trip (YYYY-MM-DD)")
    parser.add_argument("--trip", choices=["one-way", "round-trip"], default="one-way", help="Trip type")
    parser.add_argument("--seat", choices=["economy", "premium-economy", "business", "first"], default="economy")
    parser.add_argument("--adults", type=int, default=1, help="Number of adult passengers")
    parser.add_argument("--children", type=int, default=0, help="Number of children")
    parser.add_argument("--limit", type=int, default=10, help="Max results to show")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--method", choices=["auto", "library", "fetch"], default="auto", help="Search method")
    return parser.parse_args()


def build_google_flights_url(args):
    """Build Google Flights URL using TFSData protobuf encoding."""
    flight_data = [FlightData(date=args.date, from_airport=args.from_airport, to_airport=args.to_airport)]
    
    if args.trip == "round-trip" and args.return_date:
        flight_data.append(FlightData(date=args.return_date, from_airport=args.to_airport, to_airport=args.from_airport))
    
    seat_map = {"economy": "economy", "premium-economy": "premium-economy", "business": "business", "first": "first"}
    
    tfs = TFSData.from_interface(
        flight_data=flight_data,
        trip=args.trip,
        seat=seat_map.get(args.seat, "economy"),
        passengers=Passengers(adults=args.adults, children=args.children),
    )
    
    b64 = tfs.as_b64()
    if isinstance(b64, bytes):
        b64 = b64.decode('utf-8')
    
    return f"https://www.google.com/travel/flights?tfs={b64}&hl=en"


def search_with_library(args):
    """Search using fast-flights library."""
    flight_data = [FlightData(date=args.date, from_airport=args.from_airport, to_airport=args.to_airport)]
    
    if args.trip == "round-trip" and args.return_date:
        flight_data.append(FlightData(date=args.return_date, from_airport=args.to_airport, to_airport=args.from_airport))
    
    result = get_flights(
        flight_data=flight_data,
        trip=args.trip,
        seat=args.seat,
        passengers=Passengers(adults=args.adults, children=args.children),
        fetch_mode="fallback",
    )
    
    flights = []
    for f in result.flights:
        flights.append({
            "airline": f.name,
            "price": f.price,
            "departure": f.departure,
            "arrival": f.arrival,
            "duration": f.duration,
            "stops": f.stops if f.stops else "Nonstop",
            "is_best": f.is_best,
        })
    
    return {
        "price_trend": result.current_price,
        "total_results": len(result.flights),
        "flights": flights,
        "method": "library",
    }


def fetch_page(url):
    """Fetch a URL and return text content."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8', errors='ignore')


def parse_flight_text(text):
    """Parse flight information from Google Flights page text."""
    flights = []
    price_trend = None
    
    # Look for price insight
    price_match = re.search(r'Prices are currently (\w+)', text, re.IGNORECASE)
    if price_match:
        price_trend = price_match.group(1).lower()
    
    # Pattern for flight entries - looking for time ranges with prices
    # Format: "6:20 AM – 3:00 PM+1AmericanJAL17 hr 40 min1 stop..."
    
    # Split by price pattern to find flight blocks
    flight_blocks = re.split(r'(\$[\d,]+(?:round trip|one way)?)', text)
    
    current_flight = {}
    for i, block in enumerate(flight_blocks):
        # Price block
        if block.startswith('$'):
            price = re.search(r'\$([\d,]+)', block)
            if price and current_flight.get('times'):
                current_flight['price'] = f"${price.group(1)}"
                if current_flight.get('airline') and current_flight.get('duration'):
                    flights.append(current_flight.copy())
                current_flight = {}
            continue
        
        # Look for time patterns: "6:20 AM – 3:00 PM+1"
        time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s*[AP]M)(\+\d)?', block)
        if time_match:
            current_flight['times'] = f"{time_match.group(1)} – {time_match.group(2)}{time_match.group(3) or ''}"
            current_flight['departure'] = time_match.group(1)
            current_flight['arrival'] = f"{time_match.group(2)}{time_match.group(3) or ''}"
            
            # Extract what comes after the time - airline name
            after_time = block[time_match.end():]
            
            # Duration pattern: "17 hr 40 min" or "2 hr 30 min"
            duration_match = re.search(r'(\d+\s*hr(?:\s*\d+\s*min)?|\d+\s*min)', after_time)
            if duration_match:
                current_flight['duration'] = duration_match.group(1)
                # Airline is between time and duration
                airline_text = after_time[:duration_match.start()].strip()
                # Clean up airline name - remove airport codes
                airline_text = re.sub(r'\b[A-Z]{3}\b', '', airline_text).strip()
                airline_text = re.sub(r'Departure.*', '', airline_text).strip()
                if airline_text:
                    current_flight['airline'] = airline_text
            
            # Stops
            stops_match = re.search(r'(\d+)\s*stop|Nonstop', after_time, re.IGNORECASE)
            if stops_match:
                if 'Nonstop' in stops_match.group(0):
                    current_flight['stops'] = 'Nonstop'
                else:
                    current_flight['stops'] = f"{stops_match.group(1)} stop{'s' if stops_match.group(1) != '1' else ''}"
    
    return flights, price_trend


def parse_flights_from_html(html):
    """Extract flight data from raw HTML using regex patterns."""
    flights = []
    price_trend = None
    
    # Price insight
    insight_match = re.search(r'Prices are currently (\w+)', html, re.IGNORECASE)
    if insight_match:
        price_trend = insight_match.group(1).lower()
    
    # Try to find structured flight data in the HTML
    # Look for aria-labels or structured patterns
    
    # Pattern for flights in list items
    flight_pattern = re.compile(
        r'(\d{1,2}:\d{2}\s*[AP]M)\s*[–-]\s*(\d{1,2}:\d{2}\s*[AP]M)(\+\d)?' +  # Times
        r'.*?' +  # Anything between
        r'([\w\s,]+?)' +  # Airline
        r'(\d+\s*hr(?:\s*\d+\s*min)?|\d+\s*min)' +  # Duration
        r'.*?' +  # Anything between
        r'(Nonstop|\d+\s*stops?)' +  # Stops
        r'.*?' +  # Anything between
        r'\$([\d,]+)',  # Price
        re.IGNORECASE | re.DOTALL
    )
    
    for match in flight_pattern.finditer(html):
        airline = match.group(4).strip()
        # Clean airline name
        airline = re.sub(r'<[^>]+>', '', airline)  # Remove HTML tags
        airline = re.sub(r'\s+', ' ', airline).strip()
        
        flights.append({
            "airline": airline[:50],  # Limit length
            "price": f"${match.group(7)}",
            "departure": match.group(1),
            "arrival": f"{match.group(2)}{match.group(3) or ''}",
            "duration": match.group(5),
            "stops": match.group(6),
            "is_best": False,
        })
    
    # Mark first flight as best if we have results
    if flights:
        flights[0]['is_best'] = True
    
    return flights, price_trend


def search_with_fetch(args):
    """Search using web fetch fallback."""
    if not FAST_FLIGHTS_AVAILABLE:
        raise RuntimeError("fast-flights library required for URL generation")
    
    url = build_google_flights_url(args)
    html = fetch_page(url)
    
    # Try HTML parsing first
    flights, price_trend = parse_flights_from_html(html)
    
    # If that didn't work well, try text-based parsing
    if len(flights) < 2:
        # Convert HTML to rough text
        text = re.sub(r'<[^>]+>', ' ', html)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text)
        flights_text, price_trend_text = parse_flight_text(text)
        if len(flights_text) > len(flights):
            flights = flights_text
            price_trend = price_trend_text or price_trend
    
    return {
        "price_trend": price_trend or "unknown",
        "total_results": len(flights),
        "flights": flights,
        "method": "fetch",
        "url": url,
    }


def search_flights(args):
    """Main search function with fallback logic."""
    method = args.method
    
    if method == "auto":
        # Try library first, fall back to fetch
        if FAST_FLIGHTS_AVAILABLE:
            try:
                return search_with_library(args)
            except Exception as e:
                print(f"[Library failed: {e}. Using fetch fallback...]", file=sys.stderr)
                return search_with_fetch(args)
        else:
            return search_with_fetch(args)
    
    elif method == "library":
        if not FAST_FLIGHTS_AVAILABLE:
            raise RuntimeError("fast-flights library not available")
        return search_with_library(args)
    
    elif method == "fetch":
        return search_with_fetch(args)


def format_output(args, result):
    """Format results for display."""
    flights = result["flights"][:args.limit]
    
    if args.json:
        output = {
            "price_trend": result["price_trend"],
            "total_results": result["total_results"],
            "method": result.get("method", "unknown"),
            "flights": flights,
        }
        return json.dumps(output, indent=2)
    
    lines = []
    lines.append(f"✈️  {args.from_airport} → {args.to_airport} | {args.date}")
    if args.return_date:
        lines.append(f"↩️  Return: {args.return_date}")
    lines.append(f"👥 {args.adults} adult(s), {args.children} child(ren) | {args.seat.title()}")
    
    trend = result.get("price_trend", "unknown")
    trend_emoji = {"low": "🟢", "typical": "🟡", "high": "🔴"}.get(trend, "⚪")
    lines.append(f"📊 Price trend: {trend_emoji} {trend.upper()}")
    lines.append(f"📋 Showing {len(flights)} of {result['total_results']} results")
    lines.append("")
    lines.append("-" * 50)
    
    for idx, f in enumerate(flights, 1):
        best = " ⭐ BEST" if f.get("is_best") else ""
        airline = f.get("airline", "Unknown")
        price = f.get("price", "N/A")
        departure = f.get("departure", "")
        arrival = f.get("arrival", "")
        duration = f.get("duration", "")
        stops = f.get("stops", "")
        
        lines.append(f"{idx}. {airline} | {price}{best}")
        if departure and arrival:
            lines.append(f"   {departure} → {arrival}")
        if duration or stops:
            lines.append(f"   {duration} | {stops}")
        lines.append("")
    
    return "\n".join(lines)


def main():
    args = parse_args()
    
    try:
        result = search_flights(args)
    except Exception as e:
        print(f"Error searching flights: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(format_output(args, result))


if __name__ == "__main__":
    main()
