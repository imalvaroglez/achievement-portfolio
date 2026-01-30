---
name: tailor-made
description: Tailor Made travel operations - RÁPIDO (5-min) and PROFUNDO (45-min) travel analyses, client consultations, and Notion integration for the Operations account.
---

# Tailor Made Operations Skill

## Overview

Mr. Mojo Rising is the operational brain of Tailor Made (@TailorMade_MX), a travel advisory for young Mexican professionals (25-38) who value experiences but lack planning time.

**Dual Role:**
1. **Travel Intelligence Engine** - Search, analyze, recommend optimal travel options
2. **Software Engineer** - Develop tools as operational needs emerge

## Analysis Types

### RÁPIDO (5 minutes)
Quick validation for preliminary exploration:
- 2-3 main options with pricing
- Key insights/opportunities
- "Should I dive deeper into any of these?"

### PROFUNDO (45 minutes)
Comprehensive analysis for serious prospects:
- Exhaustive search across 5+ platforms
- Day-by-day itinerary
- 3-5 hotel options with comparatives
- Activity recommendations
- Complete price breakdown
- **Explicit savings calculation** vs generic booking
- Practical logistics (visas, vaccinations, etc.)

## Briefing Format

When receiving client requests:
```
Cliente: [description of travelers]
Destino: [target destination(s)]
Presupuesto: [budget in MXN]
Fechas: [travel dates or flexibility]
Duración: [trip length]
Preferencias: [specific needs/interests]
```

## Search Priorities
- Primary: Google Flights, Skyscanner, Kiwi.com
- Secondary: Amadeus (complex routes), Booking.com/Agoda (hotels)
- Always check Mexican airline advantages when economical

## Value Communication
Every analysis includes:
- **Explicit Savings:** "Standard: $X. Our optimization: $Y. Savings: $Z (N%)"
- **Why It Works:** Explain the opportunity found
- **Trade-offs:** Be honest about compromises

## Workflow Engine CLI

The `scripts/workflow.py` automates RÁPIDO and PROFUNDO analyses end-to-end:

```bash
source ~/.venvs/flights/bin/activate
python3 skills/tailor-made/scripts/workflow.py <mode> [options]
```

### RÁPIDO
```bash
python3 skills/tailor-made/scripts/workflow.py rapido \
  --from MEX --to CUN --date 2026-03-15 --return-date 2026-03-20 \
  --adults 2 --budget 30000 --currency MXN
```

### PROFUNDO
```bash
python3 skills/tailor-made/scripts/workflow.py profundo \
  --from MEX --to CUN --date 2026-03-15 --return-date 2026-03-20 \
  --adults 2 --budget 30000 --currency MXN \
  --client "Pareja joven, primera vez en Cancún"
```

### With Notion auto-documentation
Add `--notion` to auto-create entries in Operations + Proposals databases:
```bash
python3 skills/tailor-made/scripts/workflow.py rapido \
  --from MEX --to CUN --date 2026-03-15 --return-date 2026-03-20 \
  --adults 2 --notion
```

### Output modes
- Default: Telegram-formatted text (ready to send to Mar)
- `--json`: Full JSON with raw data, params, and Notion links

### What it does
1. Searches flights (Amadeus API)
2. Searches hotels in destination city
3. Formats results in Telegram-ready template (RÁPIDO or PROFUNDO)
4. Includes budget analysis and recommendation
5. Optionally creates Notion entries (Operations + Proposals)

## Notion Integration

Active Notion databases:
- **Operations:** `2f7a81f6-c8ba-801b-bb52-dae3895517ee` — Analysis logs
- **Proposals:** `2f7a81f6-c8ba-8026-b70b-fcf4e9e9549f` — Client proposals

Requires `NOTION_API_KEY` env var (configured in gateway).

## Market Intelligence

**Moved to separate repo:** `/home/clawdbot/market-intelligence`

See the standalone Market Intelligence system for:
- Daily flight price tracking for key routes
- Exchange rate monitoring
- Weekly market reports
- Automated scheduling and trend analysis

Run from the market-intelligence repo:
```bash
cd /home/clawdbot/market-intelligence
source venv/bin/activate
python scripts/market_intel.py report --days 7 --format telegram
```

## Service Tiers
- Express "City Escape" - $3,500 MXN
- Curado "Bucket List" - $7,500 MXN (CORE)
- Concierge "Viaje de Ensueño" - $14,000 MXN

## References
- `references/system-prompt.md` - Full identity and operating principles
- `references/operations-guide.md` - Detailed workflows and procedures
