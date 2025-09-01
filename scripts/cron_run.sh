#!/usr/bin/env bash
# Cron entry (Beijing time): 0 15 * * 1-5 /path/to/project/scripts/cron_run.sh >> /path/to/project/cron.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
export NASDAQ_API_KEY="${NASDAQ_API_KEY:-YOUR_DATALINK_API_KEY}"
# export HSI_JSON_URL="https://YOUR_VALID_JSON_ENDPOINT"   # optional
# export NASDAQ_COMP_CSV="https://YOUR_OWN_CSV_WITH_DATE_PE_COLUMNS.csv"  # required until you provide Composite feed
python3 -m venv .venv
source .venv/bin/activate
pip -q install -U pip
pip -q install -r requirements.txt
python3 update_data.py