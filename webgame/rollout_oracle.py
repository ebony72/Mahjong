#!/usr/bin/env python3
'''Determinized Monte-Carlo rollout oracle: measures how much EV the current
   discard policy leaves on the table.

   Plays all-advanced games; at sampled free-choice discard decisions it
   samples K completions of the hidden information (opponents' concealed
   hands + wall, shuffled; winners' revealed hands stay fixed; opponents who
   have discarded off-suit get their daque tiles swapped into the wall),
   then rolls every candidate discard out to game end with the fast initial
   strategy, using common random numbers across candidates.

   Regret is reported both raw (max of noisy means, optimistically biased)
   and cross-validated (candidate chosen on half the determinizations,
   evaluated on the other half — unbiased).

   Usage: python3 webgame/rollout_oracle.py [n_games] [--workers N]
              [--rollouts K] [--cands C] [--out FILE]
'''
import argparse
import copy
import json
import os
import random
import sys
import time
from multiprocessing import Pool

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_ST = {}


def _init(k_rollouts, n_cands, mode='discard', only=None):
    import strategyz0614 as adv
    import strategy_initial21_7attr as ini
    import utils.xzscore as score
    from xzdealer import MahjongDealer
    from xzplayer import MahjongPlayer
    from xzround import MahjongRound
    from xzjudger import MahjongJudger
    from dfncy.block_dfncy import dfncy
    _ST.update(adv=adv, ini=ini, score=score, Dealer=MahjongDealer,
               Player=MahjongPlayer, Round=MahjongRound, Judger=MahjongJudger,
               dfncy=dfncy, K=k_rollouts, C=n_cands, mode=mode, only=only)


def _new_game(seed):
    random.seed(seed)
    dealer = _ST['Dealer']()
    players = [_ST['Player'](i) for i in range(4)]
    round_ = _ST['Round'](_ST['Judger'](), dealer, 4)
    for p in players:
        dealer.deal_cards(p, 13)
    dealer.deal_cards(players[0], 1)
    for p in players:
        p.get_daque_color()
    dealer.dqc = [p.daque_color for p in players]
    return dealer, players, round_


def _auto_action(dealer, players, round_, strats):
    va = round_.valid_act
    p = players[round_.current_player]
    strat = strats[round_.current_player]
    if va == 'self_check':
        return 'self_check'
    if va == 'zimo':
        return strat.check_zimo(p, dealer, round_.last_drawn_card, players)
    if va == 'hu':
        return strat.check_hu(p, dealer, round_.player_before_act, players)
    if va == 'robkong':
        return strat.check_robkong(p, dealer, round_.jiakong_card, players)
    if va == 'pong':
        return strat.check_pong(p, dealer, players)
    if va == 'kong':
        return strat.check_kong(p, dealer, players)
    if va == 'zikong':
        return strat.check_zikong(p, dealer, players)
    return strat.select_a_card_to_discard(p, dealer, players)


def _run_to_end(dealer, players, round_, strats, first_action=None):
    if first_action is not None and not round_.is_over:
        round_.proceed_round(players, first_action)
    guard = 0
    while not round_.is_over and round_.valid_act is not None and guard < 2000:
        round_.proceed_round(players, _auto_action(dealer, players, round_, strats))
        guard += 1
    if len(dealer.deck) == 0 and len(round_.winners) < 3:
        _ST['score'].update_finalScore(dealer, players)


def _determinize(snap, pid, rng):
    '''Reshuffle hidden information from pid's point of view.'''
    dealer, players, round_ = copy.deepcopy(snap)
    others = [p for p in players if p.player_id != pid and not p.winning]
    pool = [t for p in others for t in p.hand] + list(dealer.deck)
    rng.shuffle(pool)
    i = 0
    for p in others:
        n = len(p.hand)
        p.hand[:] = pool[i:i + n]
        i += n
    dealer.deck[:] = pool[i:]
    # opponents who already discarded off-suit hold no daque tiles: swap out
    for p in others:
        if any(t[0] != p.daque_color for t in dealer.discard_lists[p.player_id]):
            bad = [t for t in p.hand if t[0] == p.daque_color]
            for b in bad:
                repl = [t for t in dealer.deck if t[0] != p.daque_color]
                if not repl:
                    break
                r = repl[rng.randrange(len(repl))]
                bi, di = p.hand.index(b), dealer.deck.index(r)
                p.hand[bi], dealer.deck[di] = dealer.deck[di], p.hand[bi]
    return dealer, players, round_


def _candidates(p, dealer, players):
    '''Base choice first, then non-essential tiles by offensive value.'''
    dfncy = _ST['dfncy']
    ini = _ST['ini']
    base_choice = _ST['adv'].select_a_card_to_discard(p, dealer, players)
    T = sorted(p.hand, key=lambda t: (t[0], t[1]))
    Pg = [x[0] for x in p.pile]
    KB = p.kgbase(dealer, players)
    dc = p.daque_color
    cur = dfncy(T, Pg, KB, dc)
    cands = []
    for x in sorted({tuple(t) for t in T}):
        x = list(x)
        if x == base_choice or T.count(x) == 4 or x in Pg:
            continue
        TX = T[:]
        TX.remove(x)
        if dfncy(TX, Pg, KB, dc) <= cur:
            cands.append((ini.discard_val(cur, x, T, Pg, KB, dc), x))
    cands.sort(key=lambda c: -c[0])
    return base_choice, [base_choice] + [x for _, x in cands[:_ST['C'] - 1]], cur


_REACTIONS = ('pong', 'kong', 'zikong', 'hu', 'zimo', 'robkong')


def _reaction_cands(dealer, players, round_, p):
    '''All legal responses to a reaction prompt, base strategy's choice first.'''
    va = round_.valid_act
    if va == 'pong':
        cands = ['pong', 'stand']
    elif va == 'kong':
        cands = ['kong', 'pong', 'stand']
    elif va == 'zikong':
        dc = p.daque_color
        cands = [['ankong', c] for c in p.ankong_list() if c[0] != dc]
        cands += [['jiakong', c] for c in p.jiakong_list()]
        cands += [['stand', 'zikong']]
    else:                       # hu / zimo / robkong
        cands = [va, 'stand']
    base = _auto_action(dealer, players, round_, [_ST['adv']] * 4)
    if base in cands:
        cands.remove(base)
    cands.insert(0, base)
    return cands


def play_seed(seed):
    '''Play one all-advanced game; oracle-evaluate sampled decisions.'''
    adv, mode = _ST['adv'], _ST['mode']
    rng = random.Random(910000 + seed)
    dealer, players, round_ = _new_game(seed)
    rows = []
    guard = 0
    while not round_.is_over and round_.valid_act is not None and guard < 2000:
        guard += 1
        va = round_.valid_act
        if (mode in ('discard', 'both') and va == 'discard' and len(rows) < 3
                and dealer.deck and rng.random() < 0.08):
            p = players[round_.current_player]
            if not any(t[0] == p.daque_color for t in p.hand):
                row = _evaluate(dealer, players, round_, p, rng, seed)
                if row:
                    rows.append(row)
        if (mode in ('reaction', 'both') and va in _REACTIONS
                and (_ST['only'] is None or va in _ST['only'])
                and len(rows) < 4 and dealer.deck
                and (va != 'pong' or rng.random() < 0.4)):
            # pong prompts are frequent; subsample them so the rarer
            # hu/zimo/robkong/kong decisions get budget
            p = players[round_.current_player]
            cands = _reaction_cands(dealer, players, round_, p)
            if len(cands) >= 2:
                row = _evaluate_actions(dealer, players, round_, p.player_id,
                                        cands, seed, va, None)
                if row:
                    rows.append(row)
        round_.proceed_round(players,
                             _auto_action(dealer, players, round_, [adv] * 4))
    return rows


def _evaluate(dealer, players, round_, p, rng, seed):
    base_choice, cands, cur = _candidates(p, dealer, players)
    if len(cands) < 2:
        return None
    return _evaluate_actions(dealer, players, round_, p.player_id,
                             cands, seed, 'discard', cur)


def _evaluate_actions(dealer, players, round_, pid, cands, seed, kind, cur):
    '''Oracle-evaluate any list of first actions (tiles or reaction actions);
       cands[0] must be the base strategy's choice.'''
    K = _ST['K']
    snap = (dealer, players, round_)
    ev = [[0.0] * K for _ in cands]
    # decision player keeps the advanced continuation; the cheap initial
    # strategy is only the opponents' environment
    strats = [_ST['ini']] * 4
    strats[pid] = _ST['adv']
    ok = []                 # determinizations where every candidate rolled out
    for d in range(K):
        det = _determinize(snap, pid, random.Random(hash((seed, kind, d))))
        try:
            for ci, cand in enumerate(cands):
                d2, p2, r2 = copy.deepcopy(det)
                _run_to_end(d2, p2, r2, strats,
                            first_action=copy.deepcopy(cand))
                ev[ci][d] = p2[pid].myscore
            ok.append(d)
        except Exception:
            continue        # drop this determinization for all candidates
    if len(ok) < 4:
        return None
    means = [sum(e[d] for d in ok) / len(ok) for e in ev]
    # cross-validated: choose on even-indexed determinizations, score on odd
    ev_h, ev_o = ok[0::2], ok[1::2]
    half = [sum(e[d] for d in ev_h) / len(ev_h) for e in ev]
    odd = [sum(e[d] for d in ev_o) / len(ev_o) for e in ev]
    pick = max(range(len(cands)), key=lambda i: half[i])
    return {'seed': seed, 'pid': pid, 'kind': kind, 'wall': dealer.numWl,
            'dfncy': cur, 'n_ok': len(ok), 'base': cands[0], 'cands': cands,
            'ev': [round(m, 3) for m in means],
            'regret_raw': round(max(means) - means[0], 3),
            'regret_cv': round(odd[pick] - odd[0], 3),
            'oracle_agrees': max(range(len(cands)),
                                 key=lambda i: means[i]) == 0}


def summarize(rows):
    import math
    n = len(rows)
    if not n:
        print('no rows', flush=True)
        return
    for name in ('regret_raw', 'regret_cv'):
        vals = [r[name] for r in rows]
        m = sum(vals) / n
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / max(n - 1, 1))
        print('%s: mean %+.4f  (se %.4f)' % (name, m, sd / math.sqrt(n)),
              flush=True)
    print('oracle agrees with advanced choice: %d/%d (%.0f%%)' %
          (sum(r['oracle_agrees'] for r in rows), n,
           100.0 * sum(r['oracle_agrees'] for r in rows) / n), flush=True)
    kinds = sorted({r.get('kind', 'discard') for r in rows})
    if len(kinds) > 1 or kinds != ['discard']:
        for kind in kinds:
            grp = [r for r in rows if r.get('kind', 'discard') == kind]
            vals = [r['regret_cv'] for r in grp]
            m = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / max(len(vals) - 1, 1))
            print('  kind %-8s n=%d  cv-regret %+.4f (se %.4f)  agrees %.0f%%' %
                  (kind, len(grp), m, sd / math.sqrt(len(grp)),
                   100.0 * sum(r['oracle_agrees'] for r in grp) / len(grp)),
                  flush=True)
    for lbl, key, edges in (('dfncy', 'dfncy', [1, 2]),
                            ('wall', 'wall', [20, 35])):
        for lo, hi in zip([-1] + edges, edges + [999]):
            grp = [r['regret_cv'] for r in rows
                   if r.get(key) is not None and lo < r[key] <= hi]
            if grp:
                print('  %s in (%s,%s]: n=%d  cv-regret %+.4f' %
                      (lbl, lo, hi, len(grp), sum(grp) / len(grp)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n_games', nargs='?', type=int, default=60)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--rollouts', type=int, default=16)
    ap.add_argument('--cands', type=int, default=4)
    ap.add_argument('--mode', choices=('discard', 'reaction', 'both'),
                    default='discard')
    ap.add_argument('--only', default=None,
                    help='comma list of reaction kinds to sample, e.g. kong,zikong')
    ap.add_argument('--out', default=os.path.join(_HERE, 'oracle_results.jsonl'))
    ap.add_argument('--analyze', default=None, metavar='FILE')
    args = ap.parse_args()

    if args.analyze:
        summarize([json.loads(l) for l in open(args.analyze) if l.strip()])
        return

    t0 = time.time()
    rows = []
    only = frozenset(args.only.split(',')) if args.only else None
    with open(args.out, 'w') as out, \
            Pool(args.workers, initializer=_init,
                 initargs=(args.rollouts, args.cands, args.mode, only)) as pool:
        for k, rs in enumerate(pool.imap_unordered(play_seed,
                                                   range(7000, 7000 + args.n_games))):
            for r in rs:
                out.write(json.dumps(r) + '\n')
            out.flush()
            rows.extend(rs)
            if (k + 1) % 5 == 0:
                print('%d/%d games, %d decisions, %.0fs' %
                      (k + 1, args.n_games, len(rows), time.time() - t0),
                      flush=True)
    print('wrote %s (%d decisions, %.0fs)' %
          (args.out, len(rows), time.time() - t0), flush=True)
    summarize(rows)


if __name__ == '__main__':
    main()
