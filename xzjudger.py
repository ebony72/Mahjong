# -*- coding: utf-8 -*-
''' Implement Mahjong Judger class
'''
# from collections import defaultdict
from xzplayer import MahjongPlayer as Player
from xzdealer import MahjongDealer as Dealer
from copy import deepcopy
import utils.hysolx as hs

class MahjongJudger(object):
    ''' Determine what cards a player can play
    '''

    def __init__(self):
        ''' Initilize the Judger class for Mahjong
        '''
        pass

    @staticmethod
    def judge_pong_kong(dealer, players, last_player): #sl not consider +kong, ankong
        ''' Judge which player can pong/kong the last card on the table
        Args:
            dealer (object): The dealer
            players (objects): List of all players
            last_player (int): The player id of last player

        '''
        last_card = dealer.table[-1] #sl or the last card drew by current_player
        color = last_card[0]

        for player in players:
            if player.winning or player.daque_color == color or last_player == player.player_id:
                continue
            hand = deepcopy(player.hand)
            # check kong
            if hand.count(last_card) == 3 and dealer.deck:
                return 'kong', player, [last_card]*4
            # check pong
            if hand.count(last_card) == 2:
                return 'pong', player, [last_card]*3
        return False, None, None

    def judge_zikong(self, dealer, player): 
        ''' Judge if the player is able to make a concealed kong (ankong) or a jiakong
        Args:
            player (object): current_player
        '''
        if not dealer.deck:
            return False
        
        T = deepcopy(player.hand)
        Pg = [p[0] for p in player.pile]
        dc = player.daque_color
        # Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color
        HD = [t for t in T if t[0] != dc] #sl tiles without daque color
        HD.sort(key=lambda t: t[0:2])
        
        Kong_candidates = [x for x in HD if HD.count(x) == 4 or x in Pg] #Kong_to_be_made in HD
        
        if Kong_candidates:
            return True
        else:
            return False

    def judge_hu(self, player, cardx):
        #sl here we need call our xuezhan algorithm to determine if a hand is complete
        ''' Judge whether cardx can complete the player's hand
        Args:
            player (object): Target player
        Return:
            Result (bool): Complete or not
        '''
        if player.winning:
            return None
            
        T = deepcopy(player.hand)
        T.append(cardx)
        # Pg = [p[0] for p in player.pile]
        dc = player.daque_color
        #KB = [0]*27 #2020021113-sl: removed
        HD = [t for t in T if t[0] != dc]
        HD.sort(key=lambda t: t[0:2])

        if not [t for t in T if t[0] == dc] and hs.is_h_solx(HD, dc):
            return True
        else:
            return False


    def judge_zimo(self, player):
        ''' Judge whether the player has a complete hand
        Args:
            player (object): Target player
        Return:
            Result (bool): Complete or not
        '''
        if player.winning:
            return None
            
        T = deepcopy(player.hand)
        # Pg = [p[0] for p in player.pile]
        dc = player.daque_color
        HD = [t for t in T if t[0] != dc]
        HD.sort(key=lambda t: t[0:2])

        if not [t for t in T if t[0] == dc] and hs.is_h_solx(HD, dc):
            return True
        else:
            return False

if __name__ == "__main__":
    judger = MahjongJudger()
    dealer = Dealer()
    dealer.table = [[2,2]]
    players = [Player(i) for i in {0,1,2,3}]
    players[0].hand = [[0, 4], [0, 5], [0, 3], [2, 2], [2, 3], [2, 2], [2, 3]]    
    players[0].pile = [[[0, 9], [0, 9], [0, 9]], [[0, 1], [0, 1], [0, 1]]]
    print(judger.judge_hu(players[0],[2,2]))
