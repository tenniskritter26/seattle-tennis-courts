#!/bin/bash
# Nightly scrape — runs at 11:49 PM via Mac cron.
# Scrapes tomorrow's reservations into reservations.json and the day after into
# tomorrow.json, then pushes both directly to GitHub via the API.
#
# Setup:
#   1. Create a GitHub Personal Access Token (PAT) with "Contents: Read & Write"
#      at https://github.com/settings/tokens
#   2. Add the following line to ~/.zshenv (create the file if it doesn't exist):
#         export GITHUB_TOKEN="your_token_here"
#   3. Make this script executable:  chmod +x nightly_scrape.sh
#   4. Add to cron (run: crontab -e):
#         49 23 * * * /bin/bash /path/to/nightly_scrape.sh >> /tmp/court_scrape.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load GITHUB_TOKEN from environment (set in ~/.zshenv)
source ~/.zshenv 2>/dev/null || true

echo "=== Nightly scrape starting at $(date) ==="

python3 scrape.py --output data/reservations.json --days-ahead 1 --push
python3 scrape.py --output data/tomorrow.json     --days-ahead 2 --push

echo "=== Done at $(date) ==="
