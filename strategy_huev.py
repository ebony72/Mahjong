'''strategyz0614 with a more decline-prone hu decision.

The rollout oracle (webgame/oracle_reactions.jsonl, 2026-07-07) found that
strategyz's hu *declines* are correct (cv-regret -0.07) but its *accepts*
leave ~+1.6 points per decision on the table: with no furiten rule, staying
tenpai and converting the win to a zimo (doubled, paid by all three) is
often worth more than a small dianpao win. This variant lowers the decline
threshold on zimo_factor; everything else delegates to strategyz unchanged.
Registered in webgame/server.py as strategy name "huev".
'''
import strategyz0614 as base

THRESHOLD = 0.6     # original behavior is 1

check_robkong = base.check_robkong
check_zimo = base.check_zimo
check_zikong = base.check_zikong
check_pong = base.check_pong
check_kong = base.check_kong
select_a_card_to_discard = base.select_a_card_to_discard


def check_hu(player, dealer, last_player, players):
    old = base.HU_DECLINE_THRESHOLD
    base.HU_DECLINE_THRESHOLD = THRESHOLD
    try:
        return base.check_hu(player, dealer, last_player, players)
    finally:
        base.HU_DECLINE_THRESHOLD = old
