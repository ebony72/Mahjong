#!/usr/bin/env python3
'''Web prototype: play XueZhan mahjong against three AI seats driven by the
   repo strategies. Zero dependencies — stdlib http.server only; the game
   engine is imported unmodified from the repo root. Game logic lives in
   game_core.py, shared with the in-browser Pyodide build (pwa_bridge.py) —
   this file is only the HTTP transport.

   Run:  python3 webgame/server.py [port]     (default port 8765, or $PORT)
   Then open http://localhost:8765

   API: POST /api/new  {"seed": int?, "ai": "initial"|"advanced"}
        POST /api/act  {"type": "daque"|"discard"|"action", ...}
        POST /api/step {}          advance the engine by ONE action (pacing)
        GET  /api/state, /api/hint

   Every human decision is logged to divergence_log.jsonl together with what
   the strategy would have played (for human-vs-AI divergence studies).

   All other GET requests are served as static files rooted at the repo
   root (not just webgame/), mirroring exactly how GitHub Pages serves the
   repo — so app.html (the offline Pyodide build) and its Python sources,
   which it fetches via relative paths like "../dfncy/block_dfncy.py", work
   identically under local dev and the deployed site.
'''
import json
import mimetypes
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

from game_core import GameSession, STRATEGIES, compute_daily_par

mimetypes.add_type('application/manifest+json', '.webmanifest')

SESSION = None
LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # quieter console
        pass

    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        data = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'{}')

    def _send_static(self, rel_path):
        '''Serve rel_path (repo-root-relative, no leading slash) as a static
           file. Returns False (caller sends 404) if it doesn't resolve to
           an existing file inside the repo root.'''
        abs_path = os.path.normpath(os.path.join(_ROOT, rel_path))
        if os.path.commonpath([abs_path, _ROOT]) != _ROOT or not os.path.isfile(abs_path):
            return False
        ctype, _ = mimetypes.guess_type(abs_path)
        with open(abs_path, 'rb') as f:
            self._send(200, f.read(), (ctype or 'application/octet-stream') +
                       ('; charset=utf-8' if ctype and ctype.startswith('text/') else ''))
        return True

    def do_GET(self):
        global SESSION
        if self.path == '/':
            #redirect (not serve-in-place) so relative asset paths inside
            #index.html resolve against /webgame/, exactly like GitHub Pages
            self.send_response(302)
            self.send_header('Location', '/webgame/index.html')
            self.end_headers()
            return
        if self.path.startswith('/api/state'):
            with LOCK:
                self._send(200, SESSION.state() if SESSION else {'stage': 'none'})
            return
        if self.path.startswith('/api/hint'):
            with LOCK:
                if SESSION is None or SESSION.pending is None:
                    self._send(200, {})
                else:
                    try:
                        self._send(200, SESSION.hint())
                    except Exception:
                        traceback.print_exc()
                        self._send(500, {'error': 'hint failed'})
            return
        if not self.path.startswith('/api/') and self._send_static(self.path.split('?')[0].lstrip('/')):
            return
        self._send(404, {'error': 'not found'})

    def do_POST(self):
        global SESSION
        try:
            payload = self._json_body()
        except Exception:
            self._send(400, {'error': 'bad json'})
            return
        if self.path.startswith('/api/daily_par'):
            #computed outside LOCK: an all-AI game takes seconds and must not
            #block state polling
            with LOCK:
                seed = getattr(SESSION, 'daily_seed', None) if SESSION else None
            if seed is None:
                self._send(400, {'error': 'no daily game'})
            else:
                self._send(200, {'seed': seed, 'par': compute_daily_par(seed)})
            return
        with LOCK:
            try:
                if self.path.startswith('/api/new'):
                    if payload.get('daily'):
                        seed = int(time.strftime('%Y%m%d'))
                        ai = 'advanced' if 'advanced' in STRATEGIES else 'initial'
                        SESSION = GameSession(seed=seed, ai=ai)
                        SESSION.daily_seed = seed
                    else:
                        SESSION = GameSession(seed=payload.get('seed'),
                                              ai=payload.get('ai', 'initial'))
                    self._send(200, SESSION.state())
                elif self.path.startswith('/api/act'):
                    if SESSION is None:
                        raise ValueError('no game')
                    SESSION.human_act(payload)
                    self._send(200, SESSION.state())
                elif self.path.startswith('/api/step'):
                    if SESSION is None:
                        raise ValueError('no game')
                    stepped = SESSION.step_once()
                    st = SESSION.state()
                    st['stepped'] = stepped
                    self._send(200, st)
                else:
                    self._send(404, {'error': 'not found'})
            except ValueError as e:
                self._send(400, {'error': str(e)})
            except Exception:
                traceback.print_exc()
                self._send(500, {'error': 'internal error'})


if __name__ == '__main__':
    #default 0 lets the OS pick any free port; some environments pre-reserve
    #common dev ports (8765/8766) for unrelated tooling
    port = int(sys.argv[1] if len(sys.argv) > 1 else os.environ.get('PORT', 0))
    try:
        httpd = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    except OSError as e:
        print('Could not bind port %s (%s). Try: python3 %s 0  (auto-picks a free port)'
              % (port, e, sys.argv[0]), flush=True)
        raise
    actual_port = httpd.server_address[1]
    print('XueZhan mahjong prototype on http://localhost:%s' % actual_port, flush=True)
    httpd.serve_forever()
