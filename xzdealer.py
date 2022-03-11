#Revised on June 2, 2020 -- introduced dealer.n_hu()

import random
from utils.xzutils import *
from copy import deepcopy

class MahjongDealer(object):
    ''' Initialize a mahjong dealer class
    '''
    def __init__(self):
        self.deck = init_deck() #sl from xzutils
        self.shuffle()
        self.table = [] #sl define one ability/parameter of the dealer

        #2020022709-sl: record all public information
        self.dqc = [-1]*4 # the daque color list of the four players
        self.win_info = [None]*4 # public win_info of each player: None, ['zimo', card, score], ['hu', card, score]
        self.discard_lists = [[]]*4 # record each player's list of discarded tiles
        self.draw_times = [0]*4 # record each player's time of drawing a card from the Wall
        self.numWl = 55
        self.act_history = [] # record the action history of the game
                                # [ [i, 'draw'], [i, 'discard', t], [j, 'pong', t], [j, 'kong', t], [k, 'zimo', t], [i, 'hu', t] ... ]
    def n_hu(self):
        X = list(p for p in range(4) if self.win_info[p] != None)
        return len(X)
            
    def shuffle(self):
        ''' Shuffle the deck
        '''
        random.shuffle(self.deck)

    def deal_cards(self, player, num): #sl: = player draws a mjzero tile from the wall
        ''' Deal some cards (which are indeed mjzero tiles) from deck to one player

        Args:
            player (object): The object of DoudizhuPlayer
            num (int): The number of cards to be dealed
        '''
        for _ in range(num):
            '''This means that the player draws from the end of the Wall!!!'''
            player.hand.append(self.deck.pop())
            
        #2020022709-sl: record all public information
        if num == 1 and self.numWl <= 55:
            self.draw_times[player.player_id] += 1
            self.numWl += -1
            self.act_history.append([player.player_id, 'draw'])
            #print('Player %s draws %s' %(player.player_id,player.hand[-1]))
            #print(self.draw_times, self.numWl)
    def extract_player_history(self, i):
        ''' Extract the action history of Player i '''
        i_act_history = list(x for x in self.act_history if x[0] == i)
        return i_act_history

    def proceed_color_distribution(self, phi, dc, action, last_card):
        ''' Proceed the color distribution based on current distribution and the player's last action
            Args:
                phi (list): the current distribution
                dc (int): daque color
                last_card (mahjong tile): either the last discarded tile or the pong/kong tile
                action (str): 'discard', 'pong', 'kong', etc


        '''
        if action == 'draw': #what is last_card here? set as None
            for i in range(0,3):
                phi[i] += 1/3
            return phi
        

        c = last_card[0] #last_card could be the discarded tile or pong/kong-tile
        if action == 'discard':
            if c == dc:
                if phi[c] >= 1: # we still have daque color
                    phi[c] += -1
                else: # for example, if we have discarded the daque color 3 times, phi[c] is at most 1 here if no pong/kong happend before 
                    theta = (phi[c]-1)/2
                    phi[(c+1)%3] += theta
                    phi[(c+2)%3] += theta
                    phi[c] = 0
                return phi
            ''' If c != dc, we retract as the player has no daque color in his hand'''
            
            theta = (phi[dc]-1)/2
            phi[(dc+1)%3] += theta
            phi[(dc+2)%3] += theta
            phi[dc] = 0
            return phi

        if c == dc:
            print('The color of last_card should not be the daque color here.')
            return phi

        ''' When last_action is pong/kong/hu/zimo/ankong/jiakong '''
        
        if dc == (c+1)%3:
            cx = (c+2)%3
        else:
            cx = (c+1)%3
        h = phi[c] + phi[cx] + phi[dc] #number of tiles in the hand

        if action == 'pong':                            
            if phi[c] >= 2.5:
                phi[c] += -2
            else: #adjust phi
                phi[cx] += phi[c]-2.5
                phi[c] = 0.5 # very unlikely we don't have color c in hand?
            return phi
        if action == 'kong': # revealed kong
            if phi[c] >= 3.5:
                phi[c] += -3
            else: #adjust phi
                phi[cx] += phi[c]-3.5
                phi[c] = 0.5
            return phi
        if action == 'ankong': # ankong (the player just drew a tile)
            if phi[c] >= 4.5:
                phi[c] += -4
            else: #adjust phi
                phi[cx] += phi[c]-4.5
                phi[c] = 0.5
            return phi
        if action == 'jiakong': # jiakong (the player just drew a tile)
            if phi[c] >= 1.5:
                phi[c] += -1
            else: #adjust phi
                phi[cx] += phi[c]-1.5
                phi[c] = 0.5
            return phi
        if action in {'hu', 'zimo', 'robkong'}:
            theta = phi[dc]
            phi[(dc+1)%3] += theta/2
            phi[(dc+2)%3] += theta/2
            phi[dc] = 0
            return phi

        
    def guess_color_distribution(self, j):
        ''' Compute the color distribution of the hand of player j from the viewpoint of player i
        Args:
            players (objects):
            j (int): The id of a player
        Return: 
            pi (list): A distribution of three colors such that pi[0] + pi[1] + pi[2] is the
                        length of the hand of player j and pi[0] is the estimated number of Bamboo tiles 
        '''
        j_act_history = self.extract_player_history(j)
        #discard_list = deepcopy(self.discard_lists[j])
        dc = self.dqc[j]
        #win_info = self.win_info[j]
        #draw_time = self.draw_times[j]

        '''Set the initial distribution '''
        phi = [0, 0, 0]
        if j == 0:
            phi[dc] = 4
        else:
            phi[dc] = 3
        phi[(dc+1)%3] = 5
        phi[(dc+2)%3] = 5

        l = len(j_act_history)
        for act in j_act_history:
            if act[0] != j:
                print('Something wrong! The actor is not %s' %j)
                return phi
            action = act[1]
            if action == 'draw':
                last_card = None
            else:
                last_card = act[2]
            phi = self.proceed_color_distribution(phi, dc, action, last_card)

        return [round(phi[0], 1), round(phi[1], 1), round(phi[2], 1)]
            
        

# For test
if __name__ == '__main__':
    dealer = MahjongDealer()
##    for card in dealer.deck:
##        print(card.get_str())
    #print(len(dealer.deck))
    act_hist =[[0, 'discard', [0, 3]], [1, 'draw'], [1, 'discard', [2, 8]], [2, 'draw'], [2, 'discard', [1, 6]], [3, 'draw'], [3, 'discard', [0, 6]], \
               [0, 'draw'], [0, 'discard', [0, 2]], [1, 'draw'], [1, 'discard', [2, 3]], [2, 'draw'], [2, 'discard', [1, 2]], [3, 'draw'], \
               [3, 'discard', [0, 2]], [0, 'draw'], [0, 'discard', [0, 8]], [2, 'pong', [0, 8]], [2, 'discard', [1, 9]], [3, 'draw'], \
               [3, 'discard', [0, 7]], [0, 'draw'], [0, 'discard', [2, 9]], [1, 'draw'], [1, 'discard', [2, 2]], [0, 'pong', [2, 2]], \
               [0, 'discard', [1, 8]], [1, 'draw'], [1, 'discard', [2, 1]], [2, 'draw'], [2, 'discard', [2, 1]], [3, 'draw'], [3, 'discard', [0, 1]],\
               [1, 'pong', [0, 1]], [1, 'discard', [0, 2]], [2, 'draw'], [2, 'discard', [1, 6]], [3, 'draw'], [3, 'discard', [0, 1]], [0, 'draw'],\
               [0, 'discard', [2, 3]], [1, 'draw'], [1, 'discard', [1, 6]], [2, 'draw'], [2, 'discard', [2, 9]], [3, 'draw'], [3, 'discard', [1, 7]],\
               [0, 'draw'], [0, 'discard', [0, 9]], [2, 'pong', [0, 9]], [2, 'discard', [0, 4]], [3, 'draw'], [3, 'discard', [0, 6]], [0, 'draw'],\
               [0, 'discard', [1, 1]], [1, 'draw'], [1, 'discard', [0, 3]], [2, 'draw'], [2, 'discard', [2, 9]], [3, 'draw'], [3, 'discard', [1, 1]],\
               [0, 'draw'], [0, 'discard', [1, 2]], [1, 'draw'], [1, 'discard', [1, 1]], [2, 'draw'], [2, 'discard', [1, 8]], [3, 'draw'],\
               [3, 'discard', [1, 7]], [0, 'draw'], [0, 'discard', [2, 5]], [3, 'hu', [2, 5], 0], [0, 'draw'], [0, 'discard', [1, 4]], [1, 'draw'],\
               [1, 'discard', [0, 7]], [2, 'draw'], [2, 'discard', [1, 3]], [0, 'draw'], [0, 'discard', [0, 5]], [1, 'draw'], [1, 'discard', [1, 2]],\
               [2, 'draw'], [2, 'discard', [0, 3]], [0, 'draw'], [0, 'discard', [2, 5]], [1, 'draw'], [1, 'discard', [2, 6]], [0, 'hu', [2, 6], 1],\
               [1, 'draw'], [1, 'discard', [0, 4]], [2, 'draw'], [2, 'discard', [0, 5]], [1, 'draw'], [1, 'discard', [1, 8]], [2, 'draw'],\
               [2, 'discard', [2, 9]], [1, 'draw'], [1, 'discard', [2, 4]], [2, 'draw'], [2, 'discard', [2, 3]], [1, 'draw'], [1, 'discard', [1, 1]],\
               [2, 'draw'], [2, 'discard', [2, 8]], [1, 'draw'], [1, 'discard', [0, 4]], [2, 'draw'], [2, 'discard', [1, 7]], [1, 'draw'],\
               [1, 'discard', [2, 1]], [2, 'draw'], [2, 'discard', [1, 2]], [1, 'draw'], [1, 'discard', [2, 8]], [2, 'draw'], [2, 'discard', [0, 2]],\
               [1, 'draw'], [1, 'discard', [0, 9]], [2, 'draw'], [2, 'zimo', [2, 7]]]

    dealer.act_history = deepcopy(act_hist[18:20])
    print(dealer.act_history)
    test = dealer.extract_player_history(0)
    #print(test)
    Z = [1, 1, 0, 0, 2, 2, 0]
    print(Z[4:9])
    
    
    s = dealer.guess_color_distribution(0)
    print(s)
