# Mahjong (ebony72/Mahjong)

XueZhan (血战到底) Mahjong engine + baseline strategy from "Let's Play Mahjong!"
(arXiv:1903.03294); the deficiency (dfncy) calculator implements arXiv:2108.06832.
`docs/2026-07-theory-and-design.md` is the full technical note for the 2026-07
work (benchmark methodology, defense/oracle/hu-threshold studies with numbers,
design changes) — read it before revisiting any strategy-improvement idea.

## Run
- `python3 xzgame_generator.py` — generate a batch of initial games.
- `python3 xzgame.py [changshu] [n_GAME]` — play `n_GAME` games from
  `Ini_Games/game_batch_0302_1000.txt` starting at game `changshu` (0-based).
  E.g. `python3 xzgame.py 0 10`.
- Records are **appended** to `testRecord/` — empty it before comparison runs.
- `python3 webgame/server.py [port]` — browser game: human at seat 0 vs three
  AI seats (stdlib-only; default port 8765, honors `PORT` env). Serves
  `webgame/index.html` at `/` (redirects there) over the HTTP API below, and
  also serves the whole repo as static files (so `webgame/app.html`, the
  offline PWA build, works identically under local dev and GitHub Pages —
  see "Web app / PWA" below). POST
  `/api/new` accepts `{"seed": N, "ai": "initial"|"advanced"|"defensive"}`;
  `/api/hint` returns the strategy's move plus a ranked explanation table for
  discards (per candidate: dfncy after, availability-weighted effective-draw
  count, deal-in danger from strategy_defense); POST `/api/step` advances the
  engine one action (the UI uses it to pace AI turns). At game over the state
  carries per-player `settle` (itemized ledger via `_settlement`, sums exactly
  to myscore) and `decisions` (the divergence log) — the UI renders a
  settlement panel with rule explanations and a review of human-vs-AI
  disagreements. POST `/api/new {"daily": true}` starts the daily challenge
  (seed = YYYYMMDD, advanced opponents); POST `/api/daily_par` returns the
  advanced AI's seat-0 score on the same deal (computed outside the session
  LOCK, cached per seed). Every human decision is appended to
  `webgame/divergence_log.jsonl` together with the strategy's choice
  (human-vs-AI divergence data; gitignored).
- `python3 webgame/rollout_oracle.py [n_games] [--rollouts K] [--cands C]` —
  determinized MC oracle: at sampled free-choice discard decisions of
  all-advanced games, reshuffles hidden tiles (winners' revealed hands fixed,
  daque-consistency enforced) and rolls out every candidate to game end
  (decision seat continues with advanced, opponents with initial). Reports
  raw and cross-validated regret of the advanced discard choice; results in
  `webgame/oracle_results.jsonl`. `--mode reaction` oracle-tests
  pong/kong/zikong/hu/zimo prompts (`webgame/oracle_reactions.jsonl`).
  **Verdicts (2026-07-07):** discards cv-regret -0.05 ± 0.20 (near-optimal;
  raw regret is winner's-curse bias — always report cv). Reactions: pong /
  zikong / zimo validated; hu *declines* validated (-0.07); hu *accepts*
  showed +1.6 ± 0.5 apparent regret — but lowering the decline threshold
  (strategy_huev.py, zimo_factor > 0.6) benchmarked at exactly zero over
  2000 seeds: the promised zimo income (+0.35/game) materialized and was
  fully offset by extra dianpao and beizimo exposure from waiting. Lesson:
  reaction-oracle EVs with initial-strategy opponents overestimate the value
  of waiting; every oracle finding must be benchmark-confirmed before
  adoption. The kong signal (+0.71 at n=50) resolved to zero at n=126
  (`webgame/oracle_kong.jsonl`, `--only kong,zikong,robkong`). All
  policy-level attacks on strategyz (defense layer, discard oracle, hu
  threshold, kong/zikong) now confirm it is locally near-optimal.
- `python3 webgame/compare_ai.py [n_seeds] [stratA] [stratB] [--workers N]`
  — parallel head-to-head benchmark, seat-swapped per seed to cancel position
  bias. Appends one JSON line per game (partial runs analyzable) including an
  income breakdown per seat reconstructed from `scoreRecords`/`kongScore`
  (multi-payer records store the per-payer amount — multiply by
  `len(rec[1])`). `--analyze FILE` reports paired per-seed diff stats
  (mean ± 95% CI) and per-category averages.

## Web app / PWA (2026-07)
Two entry points share one UI (`webgame/game.js`, ~600 lines) and one game
core (`webgame/game_core.py`, the `GameSession` class extracted from
`server.py`) — never duplicate either when changing behavior:
- `webgame/index.html` — desktop, backed by `server.py` over HTTP
  (`webgame/transport_fetch.js`). Full native Python speed. This is what
  the native Mac app (see below) wraps.
- `webgame/app.html` — **offline PWA** ("Add to Home Screen" on iPhone, or
  pin as a web app on Mac). Runs the *unmodified* Python engine client-side
  via Pyodide in a Web Worker (`webgame/worker.js` +
  `webgame/transport_pyodide.js`), so AI "thinking" time never blocks the
  UI thread. `webgame/pwa_bridge.py` mirrors `server.py`'s HTTP routes as
  plain JSON-string functions — the two transports are the only code that
  differs between entry points.
- `webgame/sw.js` — service worker; precaches the app shell + all `.py`
  engine sources at install so a second visit works fully offline. Bump
  `CACHE_NAME` when any precached file's content changes.
- Deployment: GitHub Pages serving the repo root (enabled 2026-07-07) — the
  worker fetches Python sources via paths like `../dfncy/block_dfncy.py`
  relative to its own URL, so Pages must serve the **whole repo**, not a
  subfolder. Live at `https://ebony72.github.io/Mahjong/webgame/app.html`.
- Verified 2026-07-07: cold boot (fresh Pyodide + engine load) ~3.6s on a
  fast connection; a full `initial`-strategy game plays in ~1.2s once
  booted; `strategyz`/`defensive` and the daily-challenge par computation
  (a full 4-seat AI game) also run correctly, just slower (WASM is roughly
  2-5x native). Default AI is `initial` for a snappy first PWA experience.
- Gotcha hit during dev: the service worker cache-first-forever means a
  buggy `worker.js` gets **permanently cached** after its first (crashing)
  load — always `(await navigator.serviceWorker.getRegistrations()).forEach(r=>r.unregister())`
  + `caches.keys().then(ks=>ks.forEach(caches.delete))` before testing a
  worker.js/game_core.py/pwa_bridge.py change, or bump `CACHE_NAME`.

## Native Mac app
`webgame/mac_app/` builds `血战到底.app` — a PyInstaller + pywebview wrapper
around the **existing** `server.py`/`index.html` (full native speed, no
Pyodide). See `webgame/mac_app/README.md` for the build command and the
unsigned-app Gatekeeper workaround; a paid Apple Developer ID is needed
only for distributing a signed/notarized build to other people.

## Strategies
- `strategy_initial21_7attr.py` — published baseline; deficiency via
  `dfncy/block_dfncy.py` (fast, arXiv:2108.06832).
- `strategyz0614.py` — the advanced strategy (ported 2026-07 from the private
  `XuezhanEasyRead2021` snapshot; only imports were changed to `utils.*`
  paths). **Published to the public repo as of 2026-07-07** (originally kept
  private; the owner decided to publish both it and `hytreekong.py`).
  `webgame/server.py` still imports them optionally and falls back to the
  initial strategy on checkouts without them. Its deficiency calculator is `hytreekong.hyval` (tree search, now
  memoized at top level like dfncy — do not mutate its cached inputs). It can
  *decline* a hu (expected-value zimo_factor), so the engine's hu/zimo/robkong
  decisions must be routed through the strategy module, not hardcoded.
- `strategy_defense.py` — defense layer (`defensive` in the server) wrapping
  the best available base strategy (strategyz0614 if present, else initial):
  threat-weighted per-tile danger from public info only (daque suits are
  provably safe, wait-shape counting vs unseen tiles, opponents' own discards
  discounted, flush read from single-suit melds). **Benchmark verdict
  (2026-07-07): heuristic discard-level defense does NOT beat plain
  strategyz** — fold-heavy v1 and calibrated v2 lost significantly
  (v2: -2.65/seed-pair, CI [-4.53,-0.78], n=1500); the current near-zero-cost
  v3 is statistically neutral (-0.58, CI [-1.90,+0.74], n=800). Measured
  reasons: only ~2.6% of discards deal in; ~40% of deal-ins are forced
  single-choice daque discards; a dodged deal-in often converts to the
  opponent's zimo (doubled, all three pay); reordering daque discards feeds
  opponents' melds; and quiet waits cut one's own dianpao-win income. Don't
  re-tune knobs — the next lever is a *learned* danger model (training data:
  `webgame/calibration_events.jsonl`, per-discard danger vectors + deal-in
  labels from all-advanced games).

## Determinism / verifying refactors
Game play is fully deterministic once the hands/wall are loaded from the batch
file (no RNG in strategy or engine). To verify a change is behavior-preserving:
run the same game range in two copies of the repo with clean `testRecord/`
directories and `diff -r` them — outputs must be byte-identical. The committed
`testRecord/game_GameRecord_*_.txt` files are trustworthy references (the
trajectory format still reproduces; the verbose `game_N.txt` log format has
drifted since they were generated).

## Performance notes (2026-07)
- Investigated further dfncy speedups (2026-07-07): a per-suit lookup table is
  blocked by KB-awareness (break points, pchow feasibility and reservations
  all read KB — the paper's core feature), and Python micro-optimization is
  exhausted: with memoization in place the profile is flat (~4M small ops, no
  hot spot; get_type dedup by aggregate signature + remainder caching gave
  zero wall-clock gain and was reverted). Real speedups require a C/Cython
  port or a DP rewrite — verify any such attempt with the fuzz method:
  `git show HEAD:dfncy/block_dfncy.py` as reference, compare outputs on
  ~20k random (hand, Pg, KB, dc) states plus replay of recorded benchmark
  games.
- `dfncy()` dominates runtime (~90%): each discard decision evaluates roughly
  |discard candidates| × ~18 replacement tiles candidate hands.
- `dfncy/block_dfncy.py` memoizes at 5 levels (dfncy, max_pure_type, typeset,
  hand_type, block_dcmp). Keys are immutable copies of the exact inputs;
  caches clear themselves at `_CACHE_LIMIT`. Two deliberate key reductions,
  both exact: typeset/max_pure_type key on `max(cal_em)` (get_type reads
  cal_em only through that), and the dfncy key omits the daque-suit third of
  KB (never read by the computation).
- Do NOT mutate lists/sets returned by the memoized functions — they are
  shared cache objects.
- Tiles `[c,n]` are shared list objects (`deck*4` in init_deck, `MJ()`), so
  they must never be mutated in place — treat tiles as immutable.
