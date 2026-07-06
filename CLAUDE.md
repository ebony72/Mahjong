# Mahjong (ebony72/Mahjong)

XueZhan (血战到底) Mahjong engine + baseline strategy from "Let's Play Mahjong!"
(arXiv:1903.03294); the deficiency (dfncy) calculator implements arXiv:2108.06832.

## Run
- `python3 xzgame_generator.py` — generate a batch of initial games.
- `python3 xzgame.py [changshu] [n_GAME]` — play `n_GAME` games from
  `Ini_Games/game_batch_0302_1000.txt` starting at game `changshu` (0-based).
  E.g. `python3 xzgame.py 0 10`.
- Records are **appended** to `testRecord/` — empty it before comparison runs.
- `python3 webgame/server.py [port]` — browser game: human at seat 0 vs three
  AI seats (stdlib-only; default port 8765, honors `PORT` env). POST
  `/api/new` accepts `{"seed": N, "ai": "initial"|"advanced"}`; `/api/hint`
  returns the strategy's move for the human's decision; POST `/api/step`
  advances the engine one action (the UI uses it to pace AI turns). Every
  human decision is appended to `webgame/divergence_log.jsonl` together with
  the strategy's choice (human-vs-AI divergence data; gitignored).
- `python3 webgame/compare_ai.py [n_seeds]` — head-to-head benchmark of the
  two strategies, seat-swapped per seed to cancel position bias.

## Strategies
- `strategy_initial21_7attr.py` — published baseline; deficiency via
  `dfncy/block_dfncy.py` (fast, arXiv:2108.06832).
- `strategyz0614.py` — the advanced strategy (ported 2026-07 from the private
  `XuezhanEasyRead2021` snapshot; only imports were changed to `utils.*`
  paths). **Deliberately unpublished — never push `strategyz0614.py` /
  `hytreekong.py` to the public remote.** They live in their own commit so
  earlier commits can be pushed without them; `webgame/server.py` imports
  them optionally and falls back to the initial strategy. Its deficiency calculator is `hytreekong.hyval` (tree search, now
  memoized at top level like dfncy — do not mutate its cached inputs). It can
  *decline* a hu (expected-value zimo_factor), so the engine's hu/zimo/robkong
  decisions must be routed through the strategy module, not hardcoded.

## Determinism / verifying refactors
Game play is fully deterministic once the hands/wall are loaded from the batch
file (no RNG in strategy or engine). To verify a change is behavior-preserving:
run the same game range in two copies of the repo with clean `testRecord/`
directories and `diff -r` them — outputs must be byte-identical. The committed
`testRecord/game_GameRecord_*_.txt` files are trustworthy references (the
trajectory format still reproduces; the verbose `game_N.txt` log format has
drifted since they were generated).

## Performance notes (2026-07)
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
