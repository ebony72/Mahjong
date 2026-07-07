# XueZhan Mahjong: Strategy Validation and System Redesign

**Technical note, 2026-07-07.**
Covers all theory and design changes made on top of the baseline repo
(engine + `strategy_initial21_7attr` from arXiv:1903.03294, deficiency
calculator `dfncy/block_dfncy.py` from arXiv:2108.06832, advanced strategy
`strategyz0614`, published together with `hytreekong.py` in 2026-07 after
having been kept private since 2021).

---

## 1. Summary of findings

1. **The advanced strategy (strategyz) beats the published baseline by
   +2.74 points per paired seed, 95% CI [+1.51, +3.97]** (4000 games).
   The entire edge is zimo conversion: it wins *fewer* hands but converts
   far more of them to self-draws, which in xuezhan are doubled and paid by
   all three opponents.
2. **strategyz is locally near-optimal within its information set.** Four
   independent attacks failed to improve it, each with a measured,
   mechanism-level explanation:
   - a heuristic defense (防点炮) layer — three variants, all ≤ 0;
   - a determinized Monte-Carlo discard oracle — cross-validated regret
     −0.05 ± 0.20 per decision;
   - lowering its hu-decline threshold (oracle-motivated) — exactly 0 over
     2000 paired seeds, with the predicted gain and the offsetting cost both
     visible in the income decomposition;
   - kong/zikong/pong/zimo reaction decisions — all validated by the
     reaction oracle (zimo at 93% oracle agreement).
3. **Structural theory of why defense is weak in xuezhan** (measured, not
   conjectured): only ~2.6% of discards deal in; ~40% of deal-ins are
   forced single-choice daque discards; a dodged deal-in frequently
   converts into the opponent's zimo, which costs the dodger *double*;
   discarding daque tiles out of the natural order feeds opponents' melds;
   and "quiet" waits symmetrically reduce one's own dianpao-win income
   because the same circulation that makes a tile dangerous to discard
   makes it likely to be fed to you.
4. **Methodological results**: (i) raw "max of noisy means" oracle regret
   is dominated by winner's-curse bias (+1.10 apparent vs −0.05
   cross-validated on identical data) — only cross-validated regret is
   trustworthy; (ii) oracle EVs computed with weak rollout opponents
   systematically overestimate the value of waiting/passivity — every
   oracle finding must be confirmed with the paired benchmark before
   adoption.
5. **Negative result on dfncy acceleration**: a per-suit lookup table is
   incompatible with the KB-aware semantics of arXiv:2108.06832 (break
   points, pseudo-chow feasibility and tile reservations all read KB), and
   with memoization in place the Python profile is flat — an exact
   micro-optimization of the hottest path measured 0% wall-clock gain and
   was reverted. Real speedups require a C port or an
   exactness-preserving DP rewrite.
6. **Scoring rule verified**: winning on the fourth copy of a tile one has
   ponged counts as 1 根 (gen) and doubles the fan (pays 2, not 1);
   confirmed by unit test of `compute_hu_score`.

---

## 2. Evaluation methodology (theory)

### 2.1 Paired seat-swapped benchmark

`webgame/compare_ai.py`. Every seed is played twice with seat assignments
swapped (A-B-A-B, then B-A-B-A), so seat-position bias cancels and the two
strategies face identical deals. The statistic is the **paired per-seed
score difference** d(seed) = Σ A-seat scores − Σ B-seat scores over both
arrangements; we report mean ± 95% CI over seeds. Per-game score variance
is large (paired sd ≈ 20–37 depending on the matchup), so conclusions
require ≥ 500 seeds; the pilot runs in this project (40–100 seeds) were
repeatedly overturned by full runs. A useful property: when a change is
*localized* (e.g. one decision rule), games that never reach a differing
decision replay bit-identically and contribute exact zeros, raising power.

### 2.2 Income-source decomposition

Score movements are reconstructed exactly from the engine's existing
ledgers (`player.scoreRecords`, `player.kongScore`) with two semantic
details that were previously undocumented:

- multi-payer records (`zimo`, `tianhu`/`dihu`, `chadajiao`, `chahuazhu`)
  store the **per-payer** amount together with the payer-id list — the
  total is amount × len(ids);
- `kongScore` rows carry transfer tags (`hujiaozhuanyi_income`,
  `beihujiaozhuanyi`, `beituishui`, `tuishui_return`) that reassign kong
  income at hu/game-end time.

The reconstruction satisfies the invariant Σ(categorized amounts) =
`myscore` for every player in every game (checked continuously; 0
violations over >7000 games after the multi-payer fix). Decomposition
categories: hu, zimo, dianpao, beizimo, kong, zhuanyi, tuishui,
chadajiao/beichadajiao, chahuazhu/beichahuazhu, tianhu/dihu.

### 2.3 Determinized Monte-Carlo rollout oracle

`webgame/rollout_oracle.py`. At a sampled decision of an all-strategyz
game, hidden information is re-sampled K times consistent with the decision
player's knowledge: non-winning opponents' concealed hands and the wall are
pooled and reshuffled; **winners' revealed hands stay fixed**; opponents
who have already discarded off-suit get daque tiles swapped back into the
wall (behavioral consistency). Each candidate action is applied and rolled
out to game end under **common random numbers** (the same K
determinizations for every candidate); the decision seat continues with
strategyz, opponents with the fast initial strategy.

Two estimators:

- `regret_raw` = max(candidate means) − mean(base): **positively biased**
  (winner's curse over noisy means) — reported only as a warning;
- `regret_cv` = the candidate chosen on the even-indexed determinizations,
  evaluated on the odd-indexed ones, minus the base on the same held-out
  half: unbiased for "the improvement achievable by switching on this
  oracle's advice".

Known biases, both documented and both encountered: (i) the initial-
strategy opponent environment overvalues waiting (§6); (ii) naive
determinization ignores inference from opponents' discards beyond the
daque-consistency constraint.

---

## 3. Study 1 — baseline comparison (advanced vs initial)

4000 games / 2000 paired seeds, zero engine errors, exact ledgers.

| statistic | value |
|---|---|
| paired diff (advanced − initial) | **+2.742 / seed-pair**, sd 28.11, 95% CI [+1.510, +3.974], t = 4.36 |

Per seat-game decomposition (advanced / initial):

| category | advanced | initial |
|---|---|---|
| hu rate | 0.625 | **0.697** |
| zimo rate | **0.296** | 0.220 |
| zimo income | **+2.212** | +1.351 |
| dianpao-win income | 0.637 | **0.688** |
| dianpao paid | −0.757 | **−0.568** |
| chadajiao | +0.110 | +0.066 |

Interpretation: strategyz plays a zimo-maximizing style (declining cheap
dianpao wins, shaping hands for self-draw), buying +0.86/game of zimo
income at the cost of a −0.19/game deal-in leak. The leak was the natural
target for the defense study — and turned out to be the *price* of the
style, not an inefficiency (§4–6).

---

## 4. Study 2 — defense (防点炮) layer

### 4.1 Danger model (public information only)

`strategy_defense.py`. Per-tile deal-in danger against each opponent:
provably-safe classes (opponent already won; tile in opponent's declared
daque suit), wait-shape counting against unseen-tile counts (each of the
three sequence-completion patterns contributes only if both needed
neighbor tiles are still unseen; pair/shanpon waits require ≥1/≥2 unseen
copies), a ×0.25 discount for tiles the opponent has discarded (statistical
— the engine has no furiten rule), and a flush read from single-suit melds.
Danger is threat-weighted per opponent, threat = f(melds, game progress).

### 4.2 Calibration on real deal-in events

120 all-strategyz games, 6450 discards, 165 deal-ins (2.56%):

- fatal tiles rank at mean percentile **0.612** of the discarder's danger
  vector (median 0.688); mean danger 2.96 vs 1.80 for safe discards — the
  model is informative but moderate;
- 92% of deal-ins occur at threat ≥ 0.55 (the gate was well placed);
  75% at wall < 20;
- **66% of deal-ins happen when the discarder itself is at dfncy ≤ 1**
  (push situations), only a third at dfncy ≥ 2 — folding defends the
  wrong situations;
- **68/165 deal-ins are forced daque discards, and 65 of those had exactly
  one daque tile in hand** — unpreventable at the moment of discard;
- among free-choice deal-ins at dfncy ≤ 1, the fatal tile's median danger
  is 2.22 — barely above typical, capping what a veto can catch.

### 4.3 Variants and benchmark results (vs plain advanced)

| variant | policy | result (advanced − defensive per seed-pair) |
|---|---|---|
| v1 | riichi-style fold at dfncy ≥ 2 under threat | −3.75 (pilot n=40) |
| v2 | calibrated: fold only dead hands, daque hottest-early ordering, wider veto | **+2.653, CI [+0.777, +4.529], n=1500 — significantly worse** |
| v3 | near-zero cost: base daque order below gate, equal-offense veto only | +0.578, CI [−0.744, +1.899], n=800 — neutral |

Mechanism-level explanations from the decompositions:

- v1/v2's folding cost hu income (−0.07/game) without reducing dianpao at
  all (−0.655 vs −0.649);
- v2's "dump the hottest daque tile early" ordering **fed opponents' melds**
  (central tiles are hot precisely because others can use them): zimo
  income fell 2.16 vs 2.60 — the calibration had measured hu-risk but not
  meld-feeding;
- even v3's equal-offense swaps trimmed dianpao-win income (0.607 vs
  0.695): steering waits toward tiles opponents cannot use also means those
  tiles are never discarded *to you*.

**Conclusion.** With a percentile-0.61 danger model, discard-level defense
does not pay in xuezhan; the structural facts (§1.3) cap the ceiling near
zero even for a much better model. The strategyz deal-in leak is the cost
of its zimo-maximizing style.

---

## 5. Study 3 — rollout oracle on discards and reactions

### 5.1 Discards

143 free-choice discard decisions, K=16, 4 candidates:

| estimator | value |
|---|---|
| regret_raw | +1.096 ± 0.176 (winner's-curse artifact) |
| **regret_cv** | **−0.047 ± 0.202 — zero** |
| oracle agrees with strategyz | 44% (ties among near-equivalent candidates) |

The oracle cannot improve strategyz's discards at this strength; the raw/cv
gap on identical data is the cleanest demonstration in this project of why
uncorrected oracle regret must never be reported.

### 5.2 Reactions (pong / kong / zikong / hu / zimo)

478 + 290 decisions across two runs:

| decision | n | regret_cv | verdict |
|---|---|---|---|
| zimo accept/decline | 41 | +0.003 ± 0.29 (93% agreement) | validated |
| pong | 217 | −0.287 ± 0.25 | validated |
| zikong (an/jia-kong) | 163 | −0.515 ± 0.52 | validated |
| kong (claimed) | 126 | +0.041 ± 0.28 | validated (the +0.71 seen at n=50 was noise) |
| hu declines | 83 | −0.072 ± 0.09 | **validated** — individual declines showed rollout EVs of 7–23 points behind a passed-up 4-point win |
| hu accepts | 41 | +1.616 ± 0.51 | apparent leak → refuted in Study 4 |

---

## 6. Study 4 — hu-decline threshold (the oracle finding that did not transfer)

strategyz declines a dianpao win when its `zimo_factor` estimate exceeds 1
(`strategyz0614.py`, now parameterized as `HU_DECLINE_THRESHOLD` with
default-identical behavior). The oracle's +1.6-per-accept suggested
declining more. Variant `strategy_huev.py` (threshold 0.6) over 2000
paired seeds:

| statistic | value |
|---|---|
| paired diff (advanced − huev) | +0.330, CI [−0.534, +1.194] — **zero** |

Decomposition (huev vs advanced, per seat-game): zimo income **+0.35**
(2.797 vs 2.445 — the oracle's promised gain materialized), but dianpao-win
income −0.15, dianpao paid −0.13, beizimo −0.17 — waiting longer exposes
the hand, and the exposure exactly cancels the gain. The weak (initial-
strategy) rollout opponents had shown the upside of waiting without its
cost. **Lesson: benchmark-confirm every oracle finding; oracle EVs with
weak opponents overestimate passivity.**

---

## 7. Negative result — dfncy acceleration

- A per-suit count-vector lookup table (the classic riichi-shanten trick)
  is **incompatible** with the KB-aware algorithm: `break_point`,
  pseudo-chow feasibility (cases 4/5b of `block_dcmp`) and per-pmeld tile
  reservations (`get_type`) all read the unseen-tile vector, whose joint
  state space with the hand (~15⁹ per suit) is not tabulable.
- With the 5-level memoization in place, cProfile shows a flat profile
  (~4M small operations, no hot spot; the apparent `get_type` hotspot was
  profiler overhead). An exact refactor (aggregate-signature dedup +
  remainder caching) was implemented, fuzz-verified (20,000 random states,
  0 mismatches vs `git show HEAD` reference; 24 recorded games replay
  byte-identical) — and measured **0.486s vs 0.489s** on the reference
  workload. Reverted.
- Verification recipe for any future attempt (C port / DP rewrite):
  extract the reference implementation via `git show
  HEAD:dfncy/block_dfncy.py`, compare outputs on ≥20k random
  (hand, Pg, KB, dc) states, then replay recorded benchmark games. Note
  the algorithm contains deliberate approximations (the "1/2 dilemma"
  comments) that an exact rewrite must replicate.

---

## 8. Rules verification

Unit test of `compute_hu_score`: pong 3条 + win on the discarded fourth
3条 → `hu_way = ['pinghu', '1 gen']`, records `['hu', payer, 2, +2]` /
`['dianpao', winner, 2, −2]`. The gen doubling is applied correctly
(1番 × 2¹根 = 2番). A latent baseline-strategy crash was also fixed:
`vec_discard_val` raised "All are kong tiles" when every remaining hand
tile backed one of the player's own kongs (reachable in determinized
rollouts); it now discards one anyway. Verified behavior-preserving on
recorded games (the old path could only crash, never complete).

---

## 9. Design changes (code map)

### Strategy / analysis layer
| file | change |
|---|---|
| `strategy_defense.py` | **new** — danger model + v3 defense policy; registered as `defensive` |
| `strategy_huev.py` | **new** — hu-threshold 0.6 variant; registered as `huev` |
| `strategyz0614.py` | `HU_DECLINE_THRESHOLD` module constant (default 1 = original behavior; replay-verified) |
| `strategy_initial21_7attr.py` | all-kong-tiles fallback in `vec_discard_val` (§8) |
| `webgame/compare_ai.py` | **rewritten** — multiprocessing, arbitrary strategy pairs, one JSON row per game (partial runs analyzable), exact ledger decomposition, paired-CI analysis, `--analyze` |
| `webgame/rollout_oracle.py` | **new** — determinized MC oracle; `--mode discard/reaction/both`, `--only kind,...`, cross-validated regret |

### Webgame (server.py + index.html)
| feature | notes |
|---|---|
| explainable hints | `/api/hint` returns a ranked candidate table: dfncy after discard, availability-weighted effective-draw count with the **per-tile draw list**, deal-in danger, and Chinese reason notes (孤张/安全性); UI candidates are clickable with a full explanation line |
| settlement panel | per-player itemized ledger at game over (sums exactly to each score) with Chinese labels and one-line rule explanations (查大叫/查花猪/退税/呼叫转移) |
| fan arithmetic | results table shows e.g. `平胡·2根` with `1番×4(2根) = 4番`, mirroring `compute_hu_score` |
| decision review | game-over list of all hands where the human diverged from the strategy (both actions as tiles, 向听 at the time) |
| daily challenge | `/api/new {"daily":true}` (seed = YYYYMMDD) + `/api/daily_par` — the advanced AI's score in seat 0 on the identical deal, computed outside the session lock, cached per seed; duplicate-mahjong scoring in the over panel |
| current-move banner | `#nowBar` always shows the latest action + what is expected now; history log is newest-first (no scrolling) |
| localization | hu_way terms, AI suggestions and all analysis text in Chinese |

### Data artifacts (in `webgame/`, gitignored — regenerate via §Reproduction)
| file | contents |
|---|---|
| `compare_advanced_vs_initial.jsonl` | 4000 games, Study 1 |
| `compare_defensive_vs_advanced.jsonl` | 3000 games, defense v2 |
| `compare_defensive_v3_vs_advanced.jsonl` | 1600 games, defense v3 |
| `compare_huev_vs_advanced.jsonl` | 4000 games, Study 4 |
| `oracle_results.jsonl` / `oracle_reactions.jsonl` / `oracle_kong.jsonl` | oracle decisions with per-candidate EVs |
| `calibration_events.jsonl` | 6450 discards with danger vectors + deal-in labels (training data for a learned danger model) |

### Reproduction
```
python3 webgame/compare_ai.py 2000 advanced initial --workers 6
python3 webgame/compare_ai.py --analyze webgame/compare_advanced_vs_initial.jsonl
python3 webgame/rollout_oracle.py 100 --rollouts 16 --cands 4
python3 webgame/rollout_oracle.py 200 --mode reaction --only kong,zikong
```
All runs are deterministic given the seed range; strategies and engine
contain no RNG during play.

---

## 10. Open directions (with effort estimates)

| direction | effort | expected value |
|---|---|---|
| learned danger model (data ready in `calibration_events.jsonl`) | ~1 day incl. compute | near zero for strength (§4 ceiling); fine as a research exercise |
| opponent inference in the determinizer | 1–2 days, subtle correctness (importance weighting must preserve CRN pairing) | improves oracle fidelity; findings still need benchmark confirmation |
| C/Cython port or exact DP rewrite of dfncy | multi-day, high risk | enables K≥128 oracles and RL-scale self-play; only worth it for that agenda |
| webgame flywheel (divergence data, daily challenge retention) | incremental | grows the human-decision dataset |

The strategy-side conclusion of this note — *a fully heuristic strategy
whose every decision type survives benchmark-confirmed rollout-oracle
scrutiny* — is itself a publishable validation result, and the
methodology (paired seat-swapped benchmarks, exact ledger decomposition,
cross-validated determinized oracles, and the weak-opponent-bias lesson)
transfers to other imperfect-information games.
