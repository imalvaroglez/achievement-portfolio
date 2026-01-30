#!/bin/bash
# Market Intelligence - Weekly Report
# Cron job for Tailor Made (runs on Mondays)

cd /home/clawdbot/clawd
source ~/.venvs/flights/bin/activate
python3 /home/clawdbot/clawd/skills/tailor-made/scripts/market_intel.py report --days 7 --format telegram > /tmp/market-intel-weekly.txt

# Send to Telegram via clawdbot message
# Note: Configure actual Telegram channel/user
echo "Weekly report generated at /tmp/market-intel-weekly.txt"
