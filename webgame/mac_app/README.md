# 血战到底.app — native Mac build

A thin native wrapper around the *existing* `webgame/server.py` +
`webgame/index.html` — the same real-Python engine, full native speed, no
browser needed. (For an installable offline build on iPhone or as a web app,
see `webgame/app.html` instead — that one runs in a browser via Pyodide;
this one is a real `.app` you can put in the Dock.)

## Build

```
pip3 install pywebview pyinstaller
cd webgame/mac_app
./build.sh
```

Output: `webgame/mac_app/dist/血战到底.app` (~350MB — PyInstaller bundles a
full Python interpreter plus pywebview's PyObjC/WebKit bindings; this is
normal for PyInstaller+pywebview apps and not something worth trimming for
personal use).

## Running it

**First launch of an unsigned build:** double-clicking will be blocked by
Gatekeeper ("cannot be opened because the developer cannot be verified").
Right-click the app → **Open** → confirm in the dialog. This is a one-time
step; after that it opens normally (including double-click).

The app starts `server.py`'s HTTP server on a random localhost port
(invisible to you — no port to remember) and opens it in a native window.
Closing the window quits the app and stops the embedded server.

## Distributing to other people

An unsigned build works for you but will show the same Gatekeeper warning
(and on an unnotarized build downloaded from the internet rather than built
locally, Gatekeeper is stricter and may refuse to offer the right-click
override at all, depending on macOS version). To distribute a build that
opens cleanly for other people, you need:

1. An **Apple Developer ID** membership ($99/year) — the same Command Line
   Tools already installed on this machine can sign with it once enrolled.
2. Code-sign the bundle: `codesign --deep --force --sign "Developer ID
   Application: NAME (TEAMID)" 血战到底.app`
3. **Notarize** it with `xcrun notarytool submit` (Apple's automated malware
   scan) and staple the ticket with `xcrun stapler staple`.

None of this is needed to run the app yourself on this Mac.

## Updating after code changes

Re-run `./build.sh` — it always does a clean rebuild. If you change
`webgame/index.html`, `style.css`, `game.js`, or `transport_fetch.js`,
those are the only files explicitly listed as `--add-data` in `build.sh`;
everything else (server.py, game_core.py, the engine, all strategies) is
picked up automatically by PyInstaller's import analysis, so no other
changes to build.sh are needed when engine/strategy code changes.

## How the paths work when frozen

`webgame/server.py` detects `sys.frozen` (set by PyInstaller) and points its
static-file root at `sys._MEIPASS` (where PyInstaller extracts bundled data
files) instead of computing it from `__file__`, which would resolve to a
fake path inside the compiled bytecode archive. See the comment at the top
of `server.py` if this needs touching.
