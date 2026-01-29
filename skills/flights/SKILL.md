---
name: flights
description: Search for flights using Amadeus GDS data. Use when the user asks about flight prices, availability, or wants to find flights between airports. Handles one-way and round-trip searches with passenger and seat class options.
---

# Flight Search

Search flights via Amadeus API (GDS data — airline-grade pricing and availability).

## Quick Usage

```bash
source ~/.venvs/flights/bin/activate && python3 skills/flights/scripts/search_flights.py \
  --from JFK --to LAX --date 2026-02-15
```

## Parameters

| Flag | Required | Description |
|------|----------|-------------|
| `--from` | Yes | Departure airport code (IATA) |
| `--to` | Yes | Arrival airport code (IATA) |
| `--date` | Yes | Departure date (YYYY-MM-DD) |
| `--return-date` | No | Return date for round-trip |
| `--trip` | No | `one-way` (default) or `round-trip` |
| `--seat` | No | `economy` (default), `premium-economy`, `business`, `first` |
| `--adults` | No | Number of adults (default: 1) |
| `--children` | No | Number of children 2-11 (default: 0) |
| `--infants` | No | Number of infants <2 (default: 0) |
| `--direct` | No | Direct/nonstop flights only |
| `--currency` | No | Currency code (e.g., USD, MXN, EUR) |
| `--limit` | No | Max results (default: 10) |
| `--json` | No | Output as structured JSON |
| `--raw` | No | Output raw Amadeus API response |

## Examples

**One-way economy:**
```bash
python3 skills/flights/scripts/search_flights.py --from MEX --to CUN --date 2026-03-01
```

**Round-trip business class:**
```bash
python3 skills/flights/scripts/search_flights.py \
  --from MEX --to NRT --date 2026-04-10 \
  --return-date 2026-04-20 --trip round-trip --seat business
```

**Family trip with currency:**
```bash
python3 skills/flights/scripts/search_flights.py \
  --from GDL --to CDG --date 2026-06-15 \
  --adults 2 --children 2 --currency MXN
```

**Direct flights only, JSON output:**
```bash
python3 skills/flights/scripts/search_flights.py \
  --from MEX --to LAX --date 2026-03-01 --direct --json
```

## Airport Codes

Use standard IATA codes. For unknown codes, use the airport lookup:
```bash
source ~/.venvs/flights/bin/activate && python3 skills/amadeus/scripts/flights/find_airports.py "Guadalajara"
```

Common Mexican airports:
- MEX — Mexico City (Benito Juárez)
- GDL — Guadalajara
- CUN — Cancún
- MTY — Monterrey
- SJD — San José del Cabo
- PVR — Puerto Vallarta

## Output Formats

### Human-readable (default)
Formatted terminal output with emoji, pricing, segments, and timing.

### JSON (`--json`)
Structured JSON with full offer details:
```json
{
  "success": true,
  "search": { "origin": "MEX", "destination": "CUN", ... },
  "results_count": 5,
  "offers": [
    {
      "id": "1",
      "price_total": 2450.00,
      "price_per_person": 1225.00,
      "currency": "MXN",
      "cabin": "ECONOMY",
      "itineraries": [
        {
          "direction": "outbound",
          "duration": "2h 30m",
          "stops": 0,
          "stops_label": "Nonstop",
          "airlines": ["Aeromexico"],
          "segments": [...]
        }
      ]
    }
  ],
  "meta": { "source": "amadeus", "environment": "test", ... }
}
```

### Raw (`--raw`)
Unprocessed Amadeus API response — useful for debugging.

## Configuration

Required environment variables (configured in gateway):
- `AMADEUS_API_KEY` — Amadeus API key
- `AMADEUS_API_SECRET` — Amadeus API secret
- `AMADEUS_ENV` — `test` or `production` (default: `test`)

## Architecture

This skill is a CLI wrapper around the shared Amadeus client library:

```
skills/flights/scripts/search_flights.py
  └── skills/amadeus/lib/client.py (AmadeusClient)
        ├── skills/amadeus/lib/auth.py (OAuth 2.0)
        └── skills/amadeus/lib/cache.py (TTL cache)
```

## Related Tools

For advanced searches, use the Amadeus skill directly:
- **Price analysis:** `skills/amadeus/scripts/flights/analyze_prices.py`
- **Cheapest dates:** `skills/amadeus/scripts/flights/find_cheapest_dates.py`
- **Cheap destinations:** `skills/amadeus/scripts/flights/find_cheap_destinations.py`
- **Hotels:** `skills/amadeus/scripts/hotels/search_hotels.py`
- **Combined research:** `skills/amadeus/scripts/combined_research.py`

## Rate Limits

- Test environment: 10 requests/second
- Production: Based on subscription tier
- Caching enabled (15 min TTL) to reduce API calls
