---
name: flights
description: Search for flights using Google Flights data. Use when the user asks about flight prices, availability, or wants to find flights between airports. Handles one-way and round-trip searches with passenger and seat class options.
---

# Flight Search

Search Google Flights for prices and availability.

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
| `--children` | No | Number of children (default: 0) |
| `--limit` | No | Max results (default: 10) |
| `--json` | No | Output as JSON |

## Examples

**One-way economy:**
```bash
python3 skills/flights/scripts/search_flights.py --from BCN --to LHR --date 2026-03-01
```

**Round-trip business class:**
```bash
python3 skills/flights/scripts/search_flights.py --from NYC --to TYO --date 2026-04-10 --return-date 2026-04-20 --trip round-trip --seat business
```

**Family trip:**
```bash
python3 skills/flights/scripts/search_flights.py --from LAX --to CDG --date 2026-06-15 --adults 2 --children 2
```

## Airport Codes

Use standard IATA codes. Common examples:
- NYC/JFK/LGA/EWR — New York area
- LAX — Los Angeles
- LHR — London Heathrow
- CDG — Paris Charles de Gaulle
- BCN — Barcelona
- TYO/NRT/HND — Tokyo area
- SFO — San Francisco

For unknown codes, search "IATA code [city name]".

## Interpreting Results

- **Price trend**: `low`, `typical`, or `high` — indicates if current prices are good
- **⭐ BEST**: Google's recommended option (balance of price/duration/stops)
- **Stops**: `Nonstop` or number of stops

## How It Works

The script has a two-tier approach:
1. **Primary:** `fast-flights` library (faster, cleaner parsing)
2. **Fallback:** Direct web fetch + custom parsing (more reliable for edge cases)

Use `--method library` or `--method fetch` to force a specific method. Default is `auto`.

## Limitations

- Scrapes Google Flights (not an official API) — may occasionally change
- EU region may have consent page issues (fallback usually handles this)
- Avoid rapid repeated searches (be reasonable)

## Troubleshooting

If searches fail:
1. Check airport codes are valid IATA codes
2. Ensure date is in the future and format is YYYY-MM-DD
3. Try `--method fetch` to force the fallback parser
4. Try again — transient failures happen with scraping
