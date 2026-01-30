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

Automated market tracking for Tailor Made business intelligence:

### CLI Usage
```bash
source ~/.venvs/flights/bin/activate
python3 skills/tailor-made/scripts/market_intel.py <command>
```

**Commands:**
- `track --type flights` — Track flight prices for key routes (MEX→CUN, MIA, JFK, LAX, MAD, CDG)
- `track --type exchange` — Track MXN exchange rates (USD, EUR, GBP)
- `report --days 7 --format telegram` — Generate weekly market report
- `analyze --route MEX-CUN` — Analyze price history for specific route

**Monitored Routes:**
- MEX → CUN (Cancún) — Domestic leisure
- MEX → MIA (Miami) — US East Coast
- MEX → JFK (New York) — US East Coast
- MEX → LAX (Los Angeles) — US West Coast
- MEX → MAD (Madrid) — Europe
- MEX → CDG (Paris) — Europe

**Monitored Currencies:**
- MXN/USD
- MXN/EUR
- MXN/GBP

### Automated Scheduling
**Cron jobs configured:**
- Daily flight tracking: 14:00 UTC (~8am Mexico City)
- Weekly report: Mondays 15:00 UTC (~9am Mexico City)

**Data storage:** `data/market-intel/` (JSON files with timestamps)

### Weekly Report Format
```markdown
📊 INFORME SEMANAL TAILOR MADE
Periodo: 7 días

✈️ Vuelos
📉 Ciudad de México → Cancún
   Actual: $48 USD | Min: $45 USD
   Tendencia: -5.2%  (price drop = opportunity)

💱 Tipo de Cambio
📉 MXN-USD: 17.22 (-0.15)

💡 Oportunidades
• 🔥 OFERTA: MEX→CUN bajó 5.2% ($48 USD)
• 💰 DÓLAR BARATO: MXN subió vs USD
```

### Scripts
- `scripts/market_intel.py` — Main CLI tool
- `data/market-intel/cron-daily-flights.sh` — Daily tracking cron script
- `data/market-intel/cron-weekly-report.sh` — Weekly report cron script

## Service Tiers
- Express "City Escape" - $3,500 MXN
- Curado "Bucket List" - $7,500 MXN (CORE)
- Concierge "Viaje de Ensueño" - $14,000 MXN

## References
- `references/system-prompt.md` - Full identity and operating principles
- `references/operations-guide.md` - Detailed workflows and procedures
