# Amadeus Travel API Skill

Search flights, hotels, and destinations using Amadeus GDS data. Designed for travel research and proposal preparation.

## Capabilities

- **Flight Search**: Find flights by route, date, and passengers
- **Airport Lookup**: Resolve city names to airport codes
- **Hotel Search**: Find hotels by destination with availability
- **Points of Interest**: Discover attractions, restaurants, landmarks

## Usage

### Flight Search

```bash
# Basic one-way search
python scripts/flights/search_flights.py --from BCN --to JFK --date 2026-03-15

# Round trip with options
python scripts/flights/search_flights.py \
  --from BCN --to JFK \
  --date 2026-03-15 \
  --return 2026-03-22 \
  --passengers 2 \
  --class business \
  --currency EUR

# Direct flights only
python scripts/flights/search_flights.py --from MAD --to LHR --date 2026-04-01 --direct
```

### Airport/City Lookup

```bash
# Find airport codes
python scripts/flights/find_airports.py "Barcelona"
python scripts/flights/find_airports.py "New York"
```

### Hotel Search

```bash
# Find hotels in a city
python scripts/hotels/search_hotels.py --city PAR --checkin 2026-03-15 --checkout 2026-03-20

# With filters
python scripts/hotels/search_hotels.py \
  --city NYC \
  --checkin 2026-03-15 \
  --checkout 2026-03-20 \
  --guests 2 \
  --stars 4,5
```

### Points of Interest

```bash
# Find attractions near coordinates
python scripts/destinations/points_of_interest.py --lat 48.8566 --lon 2.3522 --radius 2

# Filter by category
python scripts/destinations/points_of_interest.py --lat 40.7128 --lon -74.0060 --category RESTAURANT
```

**Note:** POI API requires production credentials (not available in test environment)

## Configuration

Required environment variables:
- `AMADEUS_API_KEY`: Your Amadeus API key
- `AMADEUS_API_SECRET`: Your Amadeus API secret
- `AMADEUS_ENV`: Environment (`test` or `production`, default: `test`)

## Output Format

All scripts output JSON for easy parsing:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "source": "amadeus",
    "environment": "test",
    "cached": false,
    "timestamp": "2026-01-28T14:55:00Z"
  }
}
```

## Error Handling

On error:
```json
{
  "success": false,
  "error": "Error description",
  "code": 400
}
```

## Rate Limits

- Test environment: 10 requests/second
- Production: Based on your subscription tier
- Caching enabled (15 min TTL) to reduce API calls

## References

- [Amadeus API Reference](https://developers.amadeus.com/self-service/apis-docs)
- [IATA Airport Codes](references/iata-codes.md)
