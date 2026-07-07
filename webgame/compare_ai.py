#!/usr/bin/env python3
'''Head-to-head strategy benchmark with paired-seed statistics and an
   income-source breakdown read from the engine's score ledgers
   (player.scoreRecords / player.kongScore — no engine changes needed).

   Each seed is played twice with the seat assignment swapped (A-B-A-B then
   B-A-B-A) so seat-position bias cancels out. One JSON line is appended per
   finished game, so a partial or interrupted run is still analyzable.

   Run:      python3 webgame/compare_ai.py [n_seeds] [stratA] [stratB]
                 [--workers N] [--out FILE]        (default 40 advanced initial)
   Analyze:  python3 webgame/compare_ai.py --analyze FILE
'''
import argparse
import json
import math
import os
import sys
import time
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)


# ------------------------------------------------------------------ ledgers
def ledger_breakdown(player):
    '''Categorized income of one player, reconstructed from the engine's
       ledgers. Categories sum exactly to player.myscore (checked per game).

       scoreRecords rows are [kind, other, fan, amount] with kind in
       {hu, zimo, dianpao, beizimo, tianhu, dihu, beitiandihu,
        chadajiao, beichadajiao, chahuazhu, beichahuazhu}.
       kongScore rows are [card, other_id, amount, *tags]; tags mark the
       later transfers: hujiaozhuanyi (kong income handed to the winner on
       kongshangpao) and tuishui (kong income returned when the konger ends
       the game not tenpai).'''
    b = {}

    def add(cat, amt):
        b[cat] = b.get(cat, 0) + amt

    for rec in player.scoreRecords:
        # multi-payer records (zimo, tianhu/dihu, chadajiao, chahuazhu) store
        # the per-payer amount together with the list of payer ids
        n = len(rec[1]) if isinstance(rec[1], list) else 1
        add(rec[0], rec[-1] * n)
    for row in player.kongScore:
        amt = row[2]
        tags = [x for x in row[3:] if isinstance(x, str)]
        if 'hujiaozhuanyi_income' in tags:
            add('zhuanyi', amt)
            continue
        add('kong', amt)
        for tag in tags:
            if tag == 'beihujiaozhuanyi':   # kong income later handed over
                add('zhuanyi', -amt)
            elif tag == 'beituishui':       # kong income later returned
                add('tuishui', -amt)
            elif tag == 'tuishui_return':   # kong payment later refunded
                add('tuishui', -amt)        # amt < 0, so this adds back
    return b


# --------------------------------------------------------------------- play
_GS = {}


def _init_worker():
    from server import GameSession      # heavy import once per worker
    _GS['cls'] = GameSession


def play_one(job):
    '''Play a single game; returns one result row (JSON-serializable).'''
    seed, strategies = job
    GameSession = _GS['cls']
    t0 = time.time()
    s = GameSession(seed=seed, strategies=list(strategies), human=None)
    guard = 0
    while s.stage != 'over' and guard < 2000:
        if not s.step_once():
            break
        guard += 1
    breakdown = [ledger_breakdown(p) for p in s.players]
    ledger_ok = all(sum(breakdown[i].values()) == p.myscore
                    for i, p in enumerate(s.players))
    return {'seed': seed,
            'strats': list(strategies),
            'scores': [p.myscore for p in s.players],
            'winners': [p.player_id for p in s.round.winners],
            'hu_ways': [list(p.hu_way) for p in s.players],
            'breakdown': breakdown,
            'ledger_ok': ledger_ok,
            'err': bool(s.error),
            'secs': round(time.time() - t0, 2)}


# ----------------------------------------------------------------- analysis
def analyze(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if not rows:
        print('no rows in %s' % path, flush=True)
        return
    names = sorted({n for r in rows for n in r['strats']})
    if len(names) != 2:
        print('expected exactly 2 strategies, found %s' % names, flush=True)
        return
    A, B = names

    by_seed = {}
    for r in rows:
        by_seed.setdefault(r['seed'], []).append(r)
    complete = {s: g for s, g in by_seed.items() if len(g) == 2}
    n_err = sum(r['err'] for r in rows)
    n_bad = sum(not r['ledger_ok'] for r in rows)

    # paired per-seed score difference (A minus B, summed over both games)
    diffs = []
    for seed, games in sorted(complete.items()):
        d = 0
        for g in games:
            for i, name in enumerate(g['strats']):
                d += g['scores'][i] if name == A else -g['scores'][i]
        diffs.append(d)
    n = len(diffs)
    mean = sum(diffs) / n
    sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (n - 1)) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    ci = 1.96 * se

    # per-strategy seat-game aggregates
    agg = {name: {'games': 0, 'score': 0, 'hu': 0, 'zimo': 0, 'pao_win': 0,
                  'cats': {}} for name in names}
    for r in rows:
        for i, name in enumerate(r['strats']):
            a = agg[name]
            a['games'] += 1
            a['score'] += r['scores'][i]
            if i in r['winners']:
                a['hu'] += 1
                if 'zimo' in r['hu_ways'][i]:
                    a['zimo'] += 1
                else:
                    a['pao_win'] += 1
            for cat, amt in r['breakdown'][i].items():
                a['cats'][cat] = a['cats'].get(cat, 0) + amt

    print('=== %s vs %s: %d games, %d complete seed pairs ===' %
          (A, B, len(rows), n), flush=True)
    print('errors: %d   ledger mismatches: %d' % (n_err, n_bad), flush=True)
    print('\npaired per-seed score diff (%s minus %s):' % (A, B), flush=True)
    print('  mean %+.4f   sd %.3f   95%% CI [%+.4f, %+.4f]   t=%.2f' %
          (mean, sd, mean - ci, mean + ci, mean / se if se else 0.0), flush=True)

    for name in names:
        agg[name]['g'] = max(agg[name]['games'], 1)
    cats = sorted({c for a in agg.values() for c in a['cats']})
    print('\nper seat-game averages:', flush=True)
    print('  %-14s %10s %10s' % ('', A, B), flush=True)
    print('  %-14s %10.4f %10.4f' % ('score',
          agg[A]['score'] / agg[A]['g'], agg[B]['score'] / agg[B]['g']), flush=True)
    print('  %-14s %10.4f %10.4f' % ('hu rate',
          agg[A]['hu'] / agg[A]['g'], agg[B]['hu'] / agg[B]['g']), flush=True)
    print('  %-14s %10.4f %10.4f' % ('zimo rate',
          agg[A]['zimo'] / agg[A]['g'], agg[B]['zimo'] / agg[B]['g']), flush=True)
    print('  %-14s %10.4f %10.4f' % ('dianpao-win',
          agg[A]['pao_win'] / agg[A]['g'], agg[B]['pao_win'] / agg[B]['g']), flush=True)
    for cat in cats:
        print('  %-14s %10.4f %10.4f' % (cat,
              agg[A]['cats'].get(cat, 0) / agg[A]['g'],
              agg[B]['cats'].get(cat, 0) / agg[B]['g']), flush=True)


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n_seeds', nargs='?', type=int, default=40)
    ap.add_argument('stratA', nargs='?', default='advanced')
    ap.add_argument('stratB', nargs='?', default='initial')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--out', default=None)
    ap.add_argument('--analyze', default=None, metavar='FILE')
    args = ap.parse_args()

    if args.analyze:
        analyze(args.analyze)
        return

    out_path = args.out or os.path.join(
        _HERE, 'compare_%s_vs_%s.jsonl' % (args.stratA, args.stratB))
    jobs = []
    for seed in range(args.n_seeds):
        a, b = args.stratA, args.stratB
        jobs.append((seed, (a, b, a, b)))
        jobs.append((seed, (b, a, b, a)))

    t0 = time.time()
    done = 0
    with open(out_path, 'w') as out, \
            Pool(args.workers, initializer=_init_worker) as pool:
        for row in pool.imap_unordered(play_one, jobs, chunksize=1):
            out.write(json.dumps(row) + '\n')
            out.flush()
            done += 1
            if done % 20 == 0 or done == len(jobs):
                el = time.time() - t0
                eta = el / done * (len(jobs) - done)
                print('%d/%d games  %.0fs elapsed  eta %.0fs' %
                      (done, len(jobs), el, eta), flush=True)
    print('wrote %s' % out_path, flush=True)
    analyze(out_path)


if __name__ == '__main__':
    main()
