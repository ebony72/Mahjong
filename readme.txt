#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed July 21 07:07:57 2021

@author: sanjiangli
"""

To generate a batch of games, run xzgame_generator.py

To play a batch of games, run xzgame.py [changshu] [n_GAME], where
    - changshu: starting from which game? (the number we use is 0)
    - n_GAME: how many games you want to play (the number we use is 10)
    - the game batch file is fixed in the script (file_name = 'game_batch_0302_1000')
  e.g. python3 xzgame.py 0 10

You may then find the game records in /testRecord/

-- strategy_initial21_7attr.py is the basic published strategy
-- strategyz0614.py is a more advanced strategy (kept private since 2021,
   published here in 2026-07)
-- strategy_defense.py adds a defensive layer ("defensive") on top of the
   best available base strategy: it estimates per-tile deal-in danger from
   public information and folds / re-picks discards when an opponent looks
   threatening (benchmarked neutral — kept as a research scaffold)
-- strategy_huev.py ("huev") is strategyz with a lower hu-decline
   threshold; benchmarked at exactly zero vs plain strategyz over 2000
   paired seeds (see docs/2026-07-theory-and-design.md §6)
-- dfncy/ the dfncy calculator is block_dfncy.py, see Ref. [yan2021fast]
   (https://arxiv.org/abs/2108.06832); used by strategy_initial21_7attr.py
-- hytreekong.py is a second, tree-search deficiency calculator (hyval),
   used by strategyz0614.py
-- utils/ contains all utilities we need
-- docs/2026-07-theory-and-design.md documents the 2026-07 evaluation
   methodology, the strategy-validation studies (benchmarks, deal-in
   calibration, rollout oracles) and all webgame design changes

Both dfncy/block_dfncy.py and hytreekong.py are memoized: a discard decision
evaluates near-identical hands hundreds of times, so caching the block/suit
decompositions gives a large speedup with no change to any output.

_________________________________
modules using dfncy calculator
xzplayer.py
strategy_initial21_7attr.py
____________________________________________
modules using hyval calculator (hytreekong.py)
strategyz0614.py
____________________________________________

Play in the browser: webgame/
  python3 webgame/server.py
  then open http://localhost:8765

You play seat 0 against three AI seats; pick the opponent strategy
(initial, advanced, or defensive) from the dropdown. Features:
  - seeded deals (POST /api/new {"seed": N}) for reproducible games
  - an explainable Hint: the strategy's move plus a ranked analysis of every
    candidate discard (effective draws, dfncy effect, deal-in danger)
  - a live deficiency (dfncy) readout for your hand
  - paced AI-turn replay with a speed selector
  - a full settlement panel at game end (itemized who-paid-whom with fan
    counts, and explanations of chadajiao / chahuazhu / tuishui / hujiao-
    zhuanyi) plus a review of the hands where you diverged from the AI
  - a daily challenge (每日挑战): everyone plays the same date-seeded deal
    and is scored against the "par" the advanced AI achieves in the same
    seat on the identical deal (duplicate-mahjong style)
  - every human decision is logged next to the strategy's choice, to
    webgame/divergence_log.jsonl, for studying human-vs-AI divergence

webgame/rollout_oracle.py measures the EV headroom of the advanced
strategy's discards with determinized Monte-Carlo rollouts:
  python3 webgame/rollout_oracle.py 100 --rollouts 16 --cands 4

webgame/compare_ai.py runs a seat-swapped strategy-vs-strategy benchmark
(parallel; paired per-seed statistics and an income-source breakdown):
  python3 webgame/compare_ai.py 200 advanced initial --workers 6
  python3 webgame/compare_ai.py --analyze webgame/compare_advanced_vs_initial.jsonl
____________________________________________
@misc{li2019lets,
      title={Let's Play Mahjong!},
      author={Sanjiang Li and Xueqing Yan},
      year={2019},
      eprint={1903.03294},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
@misc{yan2021fast,
  title={A Fast Algorithm for Computing the Deficiency Number of a Mahjong Hand},
  author={Yan, Xueqing and Li, Yongming and Li, Sanjiang},
  year={2021},
  eprint={2108.06832},
  archivePrefix={arXiv},
  primaryClass={cs.AI}
}
--------------------------------------------
