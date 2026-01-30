# Amadeus Travel API Skill

Search flights, hotels, and destinations using Amadeus GDS data. Designed for travel research and proposal preparation.

## Unified CLI (Recommended)

The **`travel_research.py`** script is the single entry point for all travel operations:

```bash
source ~/.venvs/flights/bin/activate
python3 skills/amadeus/scripts/travel_research.py <command> [options]
```

### Commands

#### `flights` — Search flights
```bash
python3 skills/amadeus/scripts/travel_research.py flights \
  --from MEX --to CUN --date 2026-03-15
python3 skills/amadeus/scripts/travel_research.py flights \
  --from MEX --to BCN --date 2026-04-10 --return-date 2026-04-20 \
  --trip round-trip --seat business --adults 2 --currency MXN
```

#### `hotels` — Search hotels
```bash
python3 skills/amadeus/scripts/travel_research.py hotels \
  --city CUN --checkin 2026-03-15 --checkout 2026-03-20
python3 skills/amadeus/scripts/travel_research.py hotels \
  --city PAR --checkin 2026-04-01 --checkout 2026-04-08 --guests 2 --stars 4,5
```

#### `poi` — Points of interest
```bash
python3 skills/amadeus/scripts/travel_research.py poi \
  --lat 21.1619 --lon -86.8515 --radius 5
python3 skills/amadeus/scripts/travel_research.py poi \
  --lat 48.8566 --lon 2.3522 --category RESTAURANT
```

**Note:** POI requires production credentials.

#### `airports` — Airport/city lookup
```bash
python3 skills/amadeus/scripts/travel_research.py airports --query "Cancun"
python3 skills/amadeus/scripts/travel_research.py airports --query "New York"
```

#### `research` — Combined research (flights + hotels + optional Notion)
```bash
# Quick research
python3 skills/amadeus/scripts/travel_research.py research \
  --from MEX --to CUN --checkin 2026-03-15 --checkout 2026-03-20 --adults 2

# With Notion proposal
python3 skills/amadeus/scripts/travel_research.py research \
  --from MEX --to CUN --checkin 2026-03-15 --checkout 2026-03-20 \
  --adults 2 --notion
```

## Configuration

Required environment variables (set in gateway config):
- `AMADEUS_API_KEY`: Your Amadeus API key
- `AMADEUS_API_SECRET`: Your Amadeus API secret
- `AMADEUS_ENV`: Environment (`test` or `production`, default: `test`)
- `NOTION_API_KEY`: Notion API key (for proposal generation)

### Price Analysis (Production Only)

```bash
# Analyze prices for a route
python3 skills/amadeus/scripts/flights/analyze_prices.py --from BCN --to JFK --date 2026-03-15

# Find cheapest travel dates
python3 skills/amadeus/scripts/flights/find_cheapest_dates.py --from BCN --to JFK --date 2026-03-15 --span 30

# Find cheapest destinations from origin
python3 skills/amadeus/scripts/flights/find_cheap_destinations.py --from BCN --max 20
```

**Note:** Price analysis endpoints require production credentials (not available in test)

## Legacy Individual Scripts

The individual scripts still work but `travel_research.py` is preferred:
- `scripts/flights/search_flights.py` — Flight search
- `scripts/flights/find_airports.py` — Airport lookup
- `scripts/hotels/search_hotels.py` / `list_hotels.py` — Hotel search
- `scripts/destinations/points_of_interest.py` — POI search
- `scripts/combined_research.py` — Combined research (legacy)

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

## Notion Integration

Automatically generate proposal pages in Notion with research data:

```bash
python scripts/combined_research.py \
  --from BCN \
  --to JFK \
  --checkin 2026-03-15 \
  --checkout 2026-03-20 \
  --guest-count 2 \
  --notion-parent "Travel Proposals"
```

See [NOTION_SETUP.md](NOTION_SETUP.md) for complete setup instructions.

## References

- [Amadeus API Reference](https://developers.amadeus.com/self-service/apis-docs)
- [IATA Airport Codes](references/iata-codes.md)
- [Notion Integration Setup](NOTION_SETUP.md)
