#!/usr/bin/env python3
'''Head-to-head strategy benchmark: strategyz0614 ("advanced") vs
   strategy_initial21_7attr ("initial").

   Each seed is played twice with the seat assignment swapped
   (A-I-A-I then I-A-I-A) so seat-position bias cancels out.

   Usage: python3 webgame/compare_ai.py [n_seeds]     (default 40)
   Writes one JSON line per game to webgame/compare_results.jsonl.
'''
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from server import GameSession

ARRANGEMENTS = (['advanced', 'initial', 'advanced', 'initial'],
                ['initial', 'advanced', 'initial', 'advanced'])


def play(seed, strategies):
    s = GameSession(seed=seed, strategies=strategies, human=None)
    guard = 0
    while s.stage != 'over' and guard < 2000:
        if not s.step_once():
            break
        guard += 1
    return ([p.myscore for p in s.players], bool(s.error),
            [p.player_id for p in s.round.winners])


def main(n_seeds):
    totals = {'advanced': 0, 'initial': 0}
    hus = {'advanced': 0, 'initial': 0}
    errors = 0
    t0 = time.time()
    out_path = os.path.join(_HERE, 'compare_results.jsonl')
    with open(out_path, 'w') as out:
        for seed in range(n_seeds):
            for arr in ARRANGEMENTS:
                t1 = time.time()
                scores, err, winners = play(seed, arr)
                errors += err
                for i, name in enumerate(arr):
                    totals[name] += scores[i]
                    hus[name] += i in winners
                row = {'seed': seed, 'arr': ''.join(a[0] for a in arr),
                       'scores': scores, 'winners': winners, 'err': err,
                       'secs': round(time.time() - t1, 2)}
                out.write(json.dumps(row) + '\n')
                out.flush()
            print('seed %d done (%.1fs elapsed)' % (seed, time.time() - t0), flush=True)

    seat_games = 2 * n_seeds * 2  # games x 2 seats per strategy
    print('=== %d games (%d seeds x 2 arrangements), %.1fs ===' %
          (2 * n_seeds, n_seeds, time.time() - t0), flush=True)
    for name in ('advanced', 'initial'):
        print('%-9s total %+5d  avg %+7.3f /seat/game   hu-rate %.3f' %
              (name, totals[name], totals[name] / seat_games,
               hus[name] / seat_games), flush=True)
    print('engine errors: %d' % errors, flush=True)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
