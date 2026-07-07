#!/usr/bin/env python3
'''Web prototype: play XueZhan mahjong against three AI seats driven by the
   repo strategies. Zero dependencies — stdlib http.server only; the game
   engine is imported unmodified from the repo root.

   Run:  python3 webgame/server.py [port]     (default port 8765, or $PORT)
   Then open http://localhost:8765

   API: POST /api/new  {"seed": int?, "ai": "initial"|"advanced"}
        POST /api/act  {"type": "daque"|"discard"|"action", ...}
        POST /api/step {}          advance the engine by ONE action (pacing)
        GET  /api/state, /api/hint

   Every human decision is logged to divergence_log.jsonl together with what
   the strategy would have played (for human-vs-AI divergence studies).
'''
import json
import os
import random
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from xzdealer import MahjongDealer as Dealer
from xzplayer import MahjongPlayer as Player
from xzround import MahjongRound as Round
from xzjudger import MahjongJudger as Judger
import utils.xzscore as score
import utils.daque as dq
import strategy_initial21_7attr as strategy_initial
from dfncy.block_dfncy import dfncy

STRATEGIES = {'initial': strategy_initial}
try:
    #the advanced strategy is private (not in the public repo); optional
    import strategyz0614 as strategy_advanced
    STRATEGIES['advanced'] = strategy_advanced
except ImportError:
    strategy_advanced = None
try:
    #defense layer over the best available base strategy
    import strategy_defense
    STRATEGIES['defensive'] = strategy_defense
except ImportError:
    strategy_defense = None
try:
    #strategyz with a more decline-prone hu decision (oracle-motivated)
    import strategy_huev
    STRATEGIES['huev'] = strategy_huev
except ImportError:
    strategy_huev = None
DIVERGENCE_LOG = os.path.join(_HERE, 'divergence_log.jsonl')


def _unique(tiles):
    out = []
    for t in tiles:
        if t not in out:
            out.append(t)
    return out


def _settlement(p):
    '''Itemized score movements of one player, from the engine ledgers.
       The amounts sum exactly to p.myscore.'''
    rows = []
    for rec in p.scoreRecords:
        others = rec[1] if isinstance(rec[1], list) else [rec[1]]
        rows.append({'kind': rec[0], 'others': others, 'fan': rec[2],
                     'amount': rec[-1] * len(others)})
    for row in p.kongScore:
        amt = row[2]
        tags = [x for x in row[3:] if isinstance(x, str)]
        if 'hujiaozhuanyi_income' in tags:
            rows.append({'kind': 'zhuanyi_in', 'others': [row[1]],
                         'tile': row[0], 'amount': amt})
            continue
        rows.append({'kind': 'kong', 'others': [row[1]],
                     'tile': row[0], 'amount': amt})
        for tag in tags:
            if tag == 'beihujiaozhuanyi':
                rows.append({'kind': 'zhuanyi_out', 'others': [row[1]],
                             'tile': row[0], 'amount': -amt})
            elif tag == 'beituishui':
                rows.append({'kind': 'tuishui_out', 'others': [row[1]],
                             'tile': row[0], 'amount': -amt})
            elif tag == 'tuishui_return':
                rows.append({'kind': 'tuishui_back', 'others': [row[1]],
                             'tile': row[0], 'amount': -amt})
    return rows


class GameSession(object):
    '''One game. `human` is the seat index of the human player (None = all AI,
       used for benchmarking). `strategies` is a list of 4 strategy names, or
       use `ai` as the single name for every AI seat.'''

    def __init__(self, seed=None, ai='initial', strategies=None, human=0):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        if strategies is None:
            strategies = [ai if ai in STRATEGIES else 'initial'] * 4
        self.strategy_names = strategies
        self.strats = [STRATEGIES.get(s, strategy_initial) for s in strategies]
        self.human = human
        self.game_id = uuid.uuid4().hex[:8]

        self.dealer = Dealer()
        self.players = [Player(i) for i in range(4)]
        self.judger = Judger()
        self.round = Round(self.judger, self.dealer, 4)
        for p in self.players:
            self.dealer.deal_cards(p, 13)
        self.dealer.deal_cards(self.players[0], 1)

        self.pending = None
        self.error = None
        self.finalized = False
        self.decisions = []  # divergence records for this game

        if human is None:
            for p in self.players:
                p.get_daque_color()
            self.dealer.dqc = [p.daque_color for p in self.players]
            self.daque_suggestion = self.players[0].daque_color
            self.stage = 'play'
        else:
            for p in self.players:
                if p.player_id != human:
                    p.get_daque_color()
            self.daque_suggestion = dq.daquex(self.players[human].hand)
            self.stage = 'choose_daque'

    # ------------------------------------------------------------- engine
    def start_play(self, color):
        self.players[self.human].daque_color = color
        self.dealer.dqc = [p.daque_color for p in self.players]
        self.stage = 'play'

    def step_once(self):
        '''Advance the engine by one action. Returns True if a step was taken;
           False when waiting for the human or the game is over.'''
        if self.stage != 'play':
            return False
        if self.round.is_over or self.round.valid_act is None:
            self._finalize()
            return False
        va = self.round.valid_act
        cur = self.round.current_player
        if cur == self.human and va != 'self_check':
            if self.pending is None:
                self.pending = self._human_pending(va)
            return False
        try:
            action = self._auto_action(va, cur)
            self.round.proceed_round(self.players, action)
        except Exception:
            self.error = traceback.format_exc()
            print(self.error, flush=True)
            self.round.is_over = True
        if self.round.is_over:
            self._finalize()
        return True

    def advance(self):
        while self.step_once():
            pass

    def _auto_action(self, va, cur):
        p = self.players[cur]
        strat = self.strats[cur]
        if va == 'self_check':
            return 'self_check'
        if va == 'zimo':
            return strat.check_zimo(p, self.dealer, self.round.last_drawn_card, self.players)
        if va == 'hu':
            return strat.check_hu(p, self.dealer, self.round.player_before_act, self.players)
        if va == 'robkong':
            return strat.check_robkong(p, self.dealer, self.round.jiakong_card, self.players)
        if va == 'pong':
            return strat.check_pong(p, self.dealer, self.players)
        if va == 'kong':
            return strat.check_kong(p, self.dealer, self.players)
        if va == 'zikong':
            return strat.check_zikong(p, self.dealer, self.players)
        return strat.select_a_card_to_discard(p, self.dealer, self.players)

    def _human_pending(self, va):
        p = self.players[self.human]
        if va == 'discard':
            dc = p.daque_color
            daque_tiles = [t for t in p.hand if t[0] == dc]
            allowed = daque_tiles if daque_tiles else list(p.hand)
            return {'type': 'discard', 'valid_act': va,
                    'prompt': '请打出一张缺色牌' if daque_tiles else '请选择要打出的牌',
                    'allowed': allowed}
        if va == 'zikong':
            dc = p.daque_color
            options = []
            for c in p.ankong_list():
                if c[0] != dc:
                    options.append({'action': ['ankong', c], 'label': 'ankong', 'tile': c})
            for c in p.jiakong_list():
                options.append({'action': ['jiakong', c], 'label': 'jiakong', 'tile': c})
            options.append({'action': ['stand', 'zikong'], 'label': 'pass'})
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以杠',
                    'options': options}
        table = self.dealer.table
        last = table[-1] if table else None
        if va == 'pong':
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以碰', 'tile': last,
                    'options': [{'action': 'pong', 'label': 'pong', 'tile': last},
                                {'action': 'stand', 'label': 'pass'}]}
        if va == 'kong':
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以杠/碰', 'tile': last,
                    'options': [{'action': 'kong', 'label': 'kong', 'tile': last},
                                {'action': 'pong', 'label': 'pong', 'tile': last},
                                {'action': 'stand', 'label': 'pass'}]}
        if va == 'hu':
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以胡', 'tile': last,
                    'options': [{'action': 'hu', 'label': 'hu', 'tile': last},
                                {'action': 'stand', 'label': 'pass'}]}
        if va == 'zimo':
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以自摸',
                    'tile': self.round.last_drawn_card,
                    'options': [{'action': 'zimo', 'label': 'zimo'},
                                {'action': 'stand', 'label': 'pass'}]}
        if va == 'robkong':
            return {'type': 'choice', 'valid_act': va, 'prompt': '可以抢杠',
                    'tile': self.round.jiakong_card,
                    'options': [{'action': 'robkong', 'label': 'robkong'},
                                {'action': 'stand', 'label': 'pass'}]}
        return {'type': 'choice', 'valid_act': va, 'prompt': str(va),
                'options': [{'action': 'stand', 'label': 'pass'}]}

    def _finalize(self):
        if self.round.is_over and not self.finalized:
            if len(self.dealer.deck) == 0 and len(self.round.winners) < 3:
                score.update_finalScore(self.dealer, self.players)
            self.finalized = True
            self.stage = 'over'
            self.pending = None

    # -------------------------------------------------------- divergence
    def _log_decision(self, valid_act, human_action, ai_action):
        rec = {
            'ts': round(time.time(), 3),
            'game': self.game_id,
            'seed': self.seed,
            'ai': self.strategy_names[self.human] if self.human is not None else None,
            'n_history': len(self.dealer.act_history),
            'valid_act': valid_act,
            'human': human_action,
            'strategy': ai_action,
            'agree': json.dumps(human_action) == json.dumps(ai_action),
            'deficiency': self._deficiency(self.players[self.human]),
        }
        self.decisions.append(rec)
        try:
            with open(DIVERGENCE_LOG, 'a') as f:
                f.write(json.dumps(rec) + '\n')
        except OSError:
            traceback.print_exc()

    # -------------------------------------------------------------- human
    def human_act(self, payload):
        kind = payload.get('type')
        if kind == 'daque':
            if self.stage != 'choose_daque':
                raise ValueError('not choosing daque now')
            color = payload.get('color')
            if color not in (0, 1, 2):
                raise ValueError('bad color')
            self._log_decision('daque', color, self.daque_suggestion)
            self.start_play(color)
            return
        if self.stage != 'play' or self.pending is None:
            raise ValueError('no decision pending')
        if kind == 'discard':
            if self.pending['type'] != 'discard':
                raise ValueError('not a discard decision')
            tile = payload.get('tile')
            if not (isinstance(tile, list) and len(tile) == 2):
                raise ValueError('bad tile')
            if tile not in self.pending['allowed']:
                raise ValueError('tile not allowed')
            action = tile
        elif kind == 'action':
            action = payload.get('action')
            if action not in [o['action'] for o in self.pending['options']]:
                raise ValueError('action not offered')
        else:
            raise ValueError('bad request type')

        try:
            ai_action = self.hint()['action']
        except Exception:
            traceback.print_exc()
            ai_action = None
        self._log_decision(self.pending['valid_act'], action, ai_action)
        self.pending = None
        self.round.proceed_round(self.players, action)
        if self.round.is_over:
            self._finalize()

    def hint(self):
        '''What the AI strategy would do in the human's place.'''
        if self.pending is None:
            return None
        p = self.players[self.human]
        strat = self.strats[self.human]
        va = self.pending['valid_act']
        if va == 'discard':
            out = {'action': strat.select_a_card_to_discard(p, self.dealer, self.players)}
            try:
                out.update(self._hint_table())
            except Exception:
                traceback.print_exc()
            return out
        if va == 'pong':
            return {'action': strat.check_pong(p, self.dealer, self.players)}
        if va == 'kong':
            return {'action': strat.check_kong(p, self.dealer, self.players)}
        if va == 'zikong':
            return {'action': strat.check_zikong(p, self.dealer, self.players)}
        if va == 'hu':
            return {'action': strat.check_hu(p, self.dealer, self.round.player_before_act, self.players)}
        if va == 'zimo':
            return {'action': strat.check_zimo(p, self.dealer, self.round.last_drawn_card, self.players)}
        if va == 'robkong':
            return {'action': strat.check_robkong(p, self.dealer, self.round.jiakong_card, self.players)}
        return {'action': va}

    # -------------------------------------------------------- explanations
    def _hint_table(self):
        '''Ranked, human-readable analysis of the current discard choice:
           per candidate tile the deficiency after discarding it, the
           availability-weighted count of effective draws (same measure the
           initial strategy maximizes) and the deal-in danger estimate from
           strategy_defense (if available).'''
        p = self.players[self.human]
        dc = p.daque_color
        KB = p.kgbase(self.dealer, self.players)
        Pg = [x[0] for x in p.pile]

        def danger_map(cands):
            if strategy_defense is None:
                return {}
            scored = strategy_defense.danger_of(cands, p, self.dealer,
                                                self.players, KB)
            return dict((tuple(t), round(d, 2)) for d, t in scored)

        SUIT = ['条', '万', '筒']
        SEAT = {1: '下家', 2: '对家', 3: '上家'}
        opps = [q for q in self.players
                if q.player_id != p.player_id and not q.winning]

        def safety_notes(t):
            notes = []
            if all(t[0] == q.daque_color for q in opps):
                notes.append('所有对手都缺%s，绝对安全' % SUIT[t[0]])
                return notes
            for q in opps:
                who = SEAT.get(q.player_id, '对手')
                if t[0] == q.daque_color:
                    notes.append('%s缺%s，对其安全' % (who, SUIT[t[0]]))
                elif t in self.dealer.discard_lists[q.player_id]:
                    notes.append('%s自己打过此牌，较安全' % who)
            return notes

        daque_tiles = _unique([t for t in p.hand if t[0] == dc])
        if daque_tiles:
            dm = danger_map(daque_tiles)
            rows = [{'tile': t, 'danger': dm.get(tuple(t), 0),
                     'notes': safety_notes(t)[:3]} for t in daque_tiles]
            rows.sort(key=lambda r: r['danger'])
            return {'forced_daque': True, 'rows': rows}

        HD = sorted(p.hand, key=lambda t: (t[0], t[1]))
        cur = dfncy(HD, Pg, KB, dc)
        cands = _unique(HD)
        dm = danger_map(cands)
        rows = []
        for t in cands:
            TX = HD[:]
            TX.remove(t)
            after = dfncy(TX, Pg, KB, dc)
            eff = 0
            detail = []         # the improving draws left: [[tile, count]...]
            if after <= cur:
                for c in range(3):
                    if c == dc:
                        continue
                    for n in range(1, 10):
                        x = [c, n]
                        k = c * 9 + n - 1
                        if x == t or KB[k] <= 0:
                            continue
                        T1 = sorted(TX + [x], key=lambda u: (u[0], u[1]))
                        if dfncy(T1, Pg, KB, dc) == max(0, cur - 1):
                            eff += KB[k]
                            detail.append([x, KB[k]])
            notes = []
            if after <= cur and (HD.count(t) == 1 and not any(
                    x != t and x[0] == t[0] and abs(x[1] - t[1]) <= 2
                    for x in HD)):
                notes.append('孤张，不成搭子')
            notes += safety_notes(t)
            rows.append({'tile': t, 'after': after, 'keeps': after <= cur,
                         'eff': eff, 'detail': detail,
                         'danger': dm.get(tuple(t), 0), 'notes': notes[:3]})
        rows.sort(key=lambda r: (not r['keeps'], -r['eff'], r['danger']))
        return {'forced_daque': False, 'cur_dfncy': cur, 'rows': rows}

    # -------------------------------------------------------------- state
    def _deficiency(self, p):
        if p.daque_color is None or p.winning:
            return None
        HD = sorted((t for t in p.hand if t[0] != p.daque_color),
                    key=lambda t: (t[0], t[1]))
        Pg = [x[0] for x in p.pile]
        KB = p.kgbase(self.dealer, self.players)
        return dfncy(HD, Pg, KB, p.daque_color)

    def state(self):
        me = self.players[self.human if self.human is not None else 0]
        hand = sorted(me.hand, key=lambda t: (t[0], t[1]))
        drawn = me.hand[-1] if len(me.hand) % 3 == 2 else None
        winners = [p.player_id for p in self.round.winners]
        n_dec = len(self.decisions)
        n_agree = sum(1 for d in self.decisions if d['agree'])
        st = {
            'stage': self.stage,
            'seed': self.seed,
            'daily': getattr(self, 'daily_seed', None),
            'ai': self.strategy_names[1],
            'game_id': self.game_id,
            'wall': len(self.dealer.deck),
            'table': self.dealer.table,
            'winners': winners,
            'history': self.dealer.act_history,
            'daque_suggestion': self.daque_suggestion,
            'pending': self.pending,
            'error': self.error,
            'divergence': {'n': n_dec, 'agree': n_agree},
            'you': {
                'id': me.player_id,
                'hand': hand,
                'drawn': drawn,
                'pile': me.pile,
                'daque': me.daque_color,
                'score': me.myscore,
                'winning': me.winning,
                'hu_way': me.hu_way,
                'deficiency': self._deficiency(me) if self.stage != 'choose_daque' else None,
            },
            'opponents': [],
        }
        for p in self.players:
            if p.player_id == st['you']['id']:
                continue
            opp = {
                'id': p.player_id,
                'n_hand': len(p.hand),
                'pile': p.pile,
                'daque': p.daque_color,
                'score': p.myscore,
                'winning': p.winning,
                'hu_way': p.hu_way,
            }
            if self.stage == 'over':
                opp['hand'] = sorted(p.hand, key=lambda t: (t[0], t[1]))
                opp['settle'] = _settlement(p)
            st['opponents'].append(opp)
        if self.stage == 'over':
            st['you']['settle'] = _settlement(me)
            st['decisions'] = self.decisions
        return st


SESSION = None
LOCK = threading.Lock()
DAILY_PAR_CACHE = {}


def compute_daily_par(seed):
    '''Score the strongest AI gets playing seat 0 on this exact deal —
       the "par" a daily-challenge player competes against.'''
    if seed in DAILY_PAR_CACHE:
        return DAILY_PAR_CACHE[seed]
    ai = 'advanced' if 'advanced' in STRATEGIES else 'initial'
    s = GameSession(seed=seed, strategies=[ai] * 4, human=None)
    guard = 0
    while s.stage != 'over' and guard < 2000:
        if not s.step_once():
            break
        guard += 1
    par = s.players[0].myscore
    DAILY_PAR_CACHE[seed] = par
    return par


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

    def do_GET(self):
        global SESSION
        if self.path in ('/', '/index.html'):
            with open(os.path.join(_HERE, 'index.html'), 'rb') as f:
                self._send(200, f.read(), 'text/html; charset=utf-8')
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
