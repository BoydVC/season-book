#!/usr/bin/env bash
# screenshot.sh <url> <out.png> [width] [height]  (headless Chrome)
URL="$1"; OUT="$2"; W="${3:-1440}"; H="${4:-900}"
PROFILE=$(mktemp -d /tmp/sb-shot-XXXX)
google-chrome --headless=new --user-data-dir="$PROFILE" --no-sandbox --disable-gpu --hide-scrollbars --window-size=$W,$H \
  --virtual-time-budget=5000 --run-all-compositor-stages-before-draw --screenshot="$OUT" "$URL" >/dev/null 2>&1
rm -rf "$PROFILE"; echo "$OUT"
