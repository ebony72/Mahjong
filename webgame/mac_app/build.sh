#!/bin/bash
# Build 血战到底.app: a native Mac wrapper around the existing server.py +
# index.html (full native-Python speed — no Pyodide/WASM, that's app.html's
# job for the offline iPhone/browser build; see webgame/app.html instead).
#
# Usage: pip3 install pywebview pyinstaller && ./build.sh
# Output: webgame/mac_app/dist/血战到底.app
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"

pyinstaller \
  --name "血战到底" \
  --windowed \
  --onedir \
  --icon icon.icns \
  --paths "$ROOT" \
  --paths "$ROOT/webgame" \
  --add-data "$ROOT/webgame/index.html:webgame" \
  --add-data "$ROOT/webgame/style.css:webgame" \
  --add-data "$ROOT/webgame/game.js:webgame" \
  --add-data "$ROOT/webgame/transport_fetch.js:webgame" \
  --noconfirm \
  launcher.py

echo
echo "Built: $(pwd)/dist/血战到底.app"
echo "First run: right-click the app -> Open (unsigned app, Gatekeeper needs one manual approval)."
echo "See README.md for signing/notarization if distributing to other people."
