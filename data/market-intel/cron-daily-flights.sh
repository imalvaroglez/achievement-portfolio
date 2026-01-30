#!/bin/bash
# Market Intelligence - Daily Flight Tracking
# Cron job for Tailor Made

cd /home/clawdbot/clawd
source ~/.venvs/flights/bin/activate
python3 /home/clawdbot/clawd/skills/tailor-made/scripts/market_intel.py track --type flights >> /home/clawdbot/clawd/data/market-intel/flight-tracking.log 2>&1
