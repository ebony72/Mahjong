'''Defensive layer over the strongest available base strategy.

The base strategy (strategyz0614 if present, else the initial strategy) picks
discards purely by offensive value. This module wraps its
select_a_card_to_discard with a danger model built only from public
information — daque declarations, melds, the table, per-player discard
histories and unseen-tile counts — and overrides the discard when an
opponent looks threatening (calibrated on deal-in events, 2026-07: most
deal-ins happen when the discarder is itself at dfncy <= 1, ~40%% are forced
single-choice daque discards, and general folding costs far more offense
than it saves — so no broad fold mode):

  * daque under threat: discard the safest daque tile (base order below the
    gate — reordering early was measured to feed opponents' melds);
  * dead hand late (dfncy >= DEAD_DFNCY, wall <= DEAD_WALL): pure safety;
  * otherwise (dfncy <= 2): keep the base choice unless it is clearly hot
    and an equal-offense safer alternative exists.

All other decisions (hu/zimo/robkong/pong/kong/zikong) are delegated
unchanged. Registered in webgame/server.py as strategy name "defensive".
'''
from dfncy.block_dfncy import dfncy
from utils.xzutils import kbf, remove_duplicates
import strategy_initial21_7attr as _offense

try:
    import strategyz0614 as base
except ImportError:
    base = _offense

check_hu = base.check_hu
check_robkong = base.check_robkong
check_zimo = base.check_zimo
check_zikong = base.check_zikong
check_pong = base.check_pong
check_kong = base.check_kong

THREAT_ON = 0.55    # engage defense once some opponent's threat reaches this
DEAD_DFNCY = 3      # fold only a dead hand (this far from winning) ...
DEAD_WALL = 24      # ... and only once the wall is this small
HOT = 2.0           # veto the base tile only above this danger
HOT_DROP = 1.0      # ... and only if an alternative is this much safer
OFF_KEEP = 1.0      # ... keeping >= this fraction of offense at dfncy <= 1
OFF_KEEP2 = 1.0     # ... or this fraction at dfncy == 2


def threat(opp, dealer):
    '''Heuristic P(opponent is tenpai-ish), from public info only.'''
    if opp.winning:
        return 0.0
    progress = (55 - dealer.numWl) / 55.0
    return min(1.0, 0.1 + 0.55 * progress + 0.13 * len(opp.pile))


def tile_danger(t, opp, dealer, KB):
    '''Danger that discarding t deals into opp; 0 means provably safe.
       KB is the discarder's unseen-tile count vector.'''
    if opp.winning or t[0] == opp.daque_color:
        return 0.0
    c, n = t[0], t[1]
    unseen = KB[kbf(t)]
    d = 0.0
    # sequence waits that t completes; impossible if a needed neighbor is dead
    for a, b in ((n - 2, n - 1), (n - 1, n + 1), (n + 1, n + 2)):
        if 1 <= a and b <= 9 and KB[kbf([c, a])] > 0 and KB[kbf([c, b])] > 0:
            d += 1.0
    # pair wait needs one unseen copy, shanpon two
    if unseen >= 1:
        d += 0.7
    if unseen >= 2:
        d += 0.4
    # they threw t themselves: no furiten rule, but strong statistical safety
    if t in dealer.discard_lists[opp.player_id]:
        d *= 0.25
    # flush read: two or more melds all in one suit
    if len(opp.pile) >= 2:
        suits = set(p[0][0] for p in opp.pile)
        if len(suits) == 1:
            d *= 1.6 if c in suits else 0.7
    return d


def danger_of(cands, player, dealer, players, KB):
    '''[(danger, tile)] for each candidate, threat-weighted over opponents.'''
    opps = [p for p in players if p.player_id != player.player_id]
    ths = [threat(o, dealer) for o in opps]
    return [(sum(th * tile_danger(t, o, dealer, KB)
                 for th, o in zip(ths, opps)), t) for t in cands]


def _max_threat(player, dealer, players):
    return max(threat(o, dealer) for o in players
               if o.player_id != player.player_id)


def _pick_safest(scored, prefer):
    '''Min-danger tile from [(danger, tile)]; ties keep the base choice,
       then the least central tile.'''
    lo = min(s[0] for s in scored)
    ties = [t for d, t in scored if d <= lo + 1e-9]
    if prefer in ties:
        return prefer
    ties.sort(key=lambda t: (min(t[1] - 1, 9 - t[1]), t[0], t[1]))
    return ties[0]


def select_a_card_to_discard(player, dealer, players):
    t0 = base.select_a_card_to_discard(player, dealer, players)
    KB = player.kgbase(dealer, players)
    dc = player.daque_color
    mth = _max_threat(player, dealer, players)

    Q = [t for t in player.hand if t[0] == dc]
    if Q:
        # below the gate keep the base order — it minimizes feeding
        # opponents' melds (measured: hottest-first early loses zimo income);
        # under threat discard the safest daque tile
        if mth < THREAT_ON:
            return t0
        scored = danger_of(remove_duplicates(Q), player, dealer, players, KB)
        return _pick_safest(scored, t0)

    if t0 is None or mth < THREAT_ON:
        return t0

    T = sorted((t for t in player.hand), key=lambda t: (t[0], t[1]))
    Pg = [p[0] for p in player.pile]
    my_dfncy = dfncy(T, Pg, KB, dc)

    if my_dfncy >= DEAD_DFNCY and dealer.numWl <= DEAD_WALL:
        # dead hand late: win EV is ~nil, safety is all that matters
        scored = danger_of(remove_duplicates(T), player, dealer, players, KB)
        return _pick_safest(scored, t0)
    if my_dfncy > 2:
        return t0       # far from winning but wall still big: keep building

    # veto mode: keep the hand intact, replace only a clearly hot discard
    # with a near-equal safer alternative
    cands = []
    for x in remove_duplicates(T):
        if T.count(x) == 4 or x in Pg:
            continue
        TX = T[:]
        TX.remove(x)
        if dfncy(TX, Pg, KB, dc) <= my_dfncy:   # non-essential
            cands.append(x)
    if t0 not in cands:
        return t0
    scored = danger_of(cands, player, dealer, players, KB)
    d0 = next(d for d, t in scored if t == t0)
    if d0 < HOT:
        return t0
    keep = OFF_KEEP if my_dfncy <= 1 else OFF_KEEP2
    o0 = _offense.discard_val(my_dfncy, t0, T, Pg, KB, dc)
    for d, t in sorted(scored):
        if t == t0 or d > d0 - HOT_DROP:
            continue
        if _offense.discard_val(my_dfncy, t, T, Pg, KB, dc) >= keep * o0:
            return t
    return t0
