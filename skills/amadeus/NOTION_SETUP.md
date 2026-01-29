# Notion Integration Setup

Integrate Amadeus travel research directly into Notion for proposal management.

## Quick Start

1. **Create Notion integration:**
   - Go to https://notion.so/my-integrations
   - Click "New integration"
   - Name it "Amadeus" (or whatever you prefer)
   - Copy the API key

2. **Configure environment:**
   ```bash
   # Set the API key in ~/.clawdbot/config.yaml
   env:
     vars:
       NOTION_API_KEY: "ntn_your_api_key_here"
   ```

3. **Share Notion page/database with integration:**
   - Open a Notion page or database where you want proposals
   - Click "..." menu → "Connect to" → Select "Amadeus" (your integration)

4. **Run research with Notion output:**
   ```bash
   python scripts/combined_research.py \
     --from BCN \
     --to JFK \
     --checkin 2026-03-15 \
     --checkout 2026-03-20 \
     --notion-parent "Travel Proposals"
   ```

## How It Works

The `combined_research.py` script:

1. **Searches flights** — Top 3 offers by price
2. **Searches hotels** — Top 3 available options
3. **Gathers POI data** — Attractions and restaurants (if available)
4. **Creates Notion page** — Formats all data into a readable proposal
5. **Returns JSON** — Full research data for further processing

### Output

On Notion, you get a page like:
```
Trip Summary
---
BCN → JFK | 2026-03-15 to 2026-03-20 | 2 guests

✈️ Flights
Option 1: €277 (1 itinerary, 1 stop)
Duration: 13h 30m | Cabin: ECONOMY

Option 2: €285 (1 itinerary, 1 stop)
Duration: 15h 10m | Cabin: ECONOMY

🏨 Hotels
Option 1: Hotel Name ⭐4
€500 total | €100/night | Double bed

Option 2: Hotel Name ⭐4
€480 total | €96/night | Twin beds

📋 Metadata
(JSON with full search parameters)
```

## Setup Steps (Detailed)

### 1. Create Notion Integration

1. Go to https://notion.so/my-integrations
2. Log in if needed
3. Click "New integration"
4. Fill in:
   - **Name:** "Amadeus Travel Research" (or your choice)
   - **Logo:** (optional)
5. Click "Submit"
6. On the next page, copy your **Internal Integration Token**
   - Starts with `ntn_` or `secret_`

### 2. Add to Clawdbot Config

Edit `~/.clawdbot/config.yaml`:

```yaml
env:
  vars:
    AMADEUS_API_KEY: "your_amadeus_key"
    AMADEUS_API_SECRET: "your_amadeus_secret"
    AMADEUS_ENV: "test"
    NOTION_API_KEY: "ntn_your_notion_key_here"  # Add this line
```

Then restart gateway:
```bash
clawdbot gateway restart
```

### 3. Set Up Notion Database

Create a database in Notion to store proposals:

1. Create a new page in Notion
2. Type `/database` to add a database
3. Create properties:
   - **Name** (Title) — Trip name
   - **Origin** (Text) — Airport code
   - **Destination** (Text) — City/airport code
   - **Check-in** (Date) — Start date
   - **Check-out** (Date) — End date
   - **Status** (Select) — Proposal status (Draft, Sent, Approved, etc.)

4. Click "..." → "Connect to" → Select your integration

### 4. Share Database with Integration

1. In your Notion database, click "..."
2. Select "Connect to"
3. Choose your "Amadeus" integration
4. Click "Allow"

### 5. Use the Combined Research Script

```bash
cd /path/to/amadeus/skills

# Basic usage
python scripts/combined_research.py \
  --from BCN \
  --to JFK \
  --checkin 2026-03-15 \
  --checkout 2026-03-20 \
  --notion-parent "Travel Proposals"

# With guest count
python scripts/combined_research.py \
  --from MAD \
  --to NYC \
  --checkin 2026-04-01 \
  --checkout 2026-04-08 \
  --guest-count 2 \
  --notion-parent "Client Proposals"

# Save to file too
python scripts/combined_research.py \
  --from PAR \
  --to LAX \
  --checkin 2026-05-15 \
  --checkout 2026-05-22 \
  --notion-parent "Travel Proposals" \
  --output proposal.json

# JSON output only (no Notion)
python scripts/combined_research.py \
  --from BCN \
  --to JFK \
  --checkin 2026-03-15 \
  --checkout 2026-03-20 \
  --no-notion
```

## Troubleshooting

### "Notion API key not configured"
- Check `NOTION_API_KEY` is set in `~/.clawdbot/config.yaml`
- Restart gateway after adding the key
- Verify key starts with `ntn_`

### "Notion parent not found"
- Ensure database name is correct (case-sensitive)
- Make sure database is shared with your integration
- Try using the database ID instead: `--notion-parent "abc123def456"`

### "Permission denied"
- Database must be shared with integration
- Click "..." → "Connect to" → Select "Amadeus"

### Page not created but no error
- Check API key is valid
- Verify database structure matches expectations
- Check Notion API rate limits (3 req/second)

## API Reference

### `NotionHelper` Class

```python
from lib import NotionHelper

notion = NotionHelper()

# Search
results = notion.search("Travel Proposals", object_type='database')

# Create page
page = notion.create_page(
    parent_id="abc123",
    title="BCN → JFK (2026-03-15)",
    is_database_parent=True,
)

# Append content
blocks = [
    NotionHelper.heading_block("Trip Summary", level=1),
    NotionHelper.paragraph_block("Content here"),
    NotionHelper.divider_block(),
]
notion.append_blocks(page['id'], blocks)
```

### Block Types Available

- `heading_block(text, level=1|2|3)` — Headings
- `paragraph_block(text, bold=False, code=False)` — Text paragraphs
- `divider_block()` — Horizontal divider
- `code_block(code, language='json')` — Code block
- `table_block(headers, rows)` — Table
- `bulleted_list_block(items)` — Bullet list

## Example Workflow

### Automated Proposal Generation

```bash
#!/bin/bash
# proposal.sh

ORIGIN="BCN"
DESTINATION="JFK"
CHECKIN="2026-03-15"
CHECKOUT="2026-03-20"
GUESTS=2

python scripts/combined_research.py \
  --from $ORIGIN \
  --to $DESTINATION \
  --checkin $CHECKIN \
  --checkout $CHECKOUT \
  --guest-count $GUESTS \
  --notion-parent "Active Proposals" \
  --output proposal_${ORIGIN}_${DESTINATION}_${CHECKIN}.json

echo "✓ Proposal created and saved"
```

Run with:
```bash
bash proposal.sh
```

## Notes

- Notion API rate limit: ~3 requests/second
- Pages created in database inherit the database's properties
- Custom properties must match database structure
- Relation fields require page IDs (not supported in this version)
- Database vs page parent handled automatically
