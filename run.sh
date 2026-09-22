#!/usr/bin/env bash
# Tampa Maids Cleaning — start everything.
#   ./run.sh              start on http://localhost:8000
#   ./run.sh 9000         start on a different port
#   ./run.sh --lan        also reachable from your phone on the same Wi-Fi
set -e
cd "$(dirname "$0")"

PORT=8000
HOST=127.0.0.1
for arg in "$@"; do
  case "$arg" in
    --lan) HOST=0.0.0.0 ;;
    [0-9]*) PORT="$arg" ;;
  esac
done

if [ ! -f data/bookings.db ] && [ ! -f data/gulfcoast.db ]; then
  echo "  First run — creating the database and staff accounts..."
  python3 server/seed.py --demo
fi

if [ "$HOST" = "0.0.0.0" ]; then
  IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "your-ip")
  echo ""
  echo "  On your phone (same Wi-Fi):  http://$IP:$PORT/app"
fi

exec python3 server/app.py --port "$PORT" --host "$HOST"
