import utils.daque as dq #20200612-sl: replace daque with daquex 
from utils.xzutils import *
import utils.xzscore as score
from copy import deepcopy
from dfncy.block_dfncy import dfncy 
#sl assume each card is a tile
# import json
##import os
# import ast

class MahjongPlayer(object):

    def __init__(self, player_id):
        ''' Initilize a player.
        Arg:
            player_id (int): The id of the player
        '''
        self.player_id = player_id
        self.hand = [] #sl a list of 
        self.pile = [] #sl: pile is a list of lists of cards
        self.daque_color = None #sl: the color to discard (daque)
        #self.kgbase = [4]*27
        self.winning_card = None
        self.winning = False
        self.myscore = 0 #the score of the player
        self.hu_way = [] #the hu_way of the player: a list of strings ['kongshanghua', 'pengpenghu', 'qingyise', n_gen]
        self.deficiency = 14 #the deficiency of the player's hand
        self.kongScore = [] #score details [kong-card, the players who pay, the prize each player pay], used for tax return
        self.scoreRecords = [] #score records

        self.dominant_color = None #2020021207-sl
        self.chadajiao_score = None #the chadajiao score of the player if perform punishment at the end of the game        
        
    def get_player_id(self):
        ''' Return the id of the player
        '''
        return self.player_id

    def get_daque_color(self):
        ''' Return the daque color. The function can only be called once in the very beginning of the game 
        '''
        self.daque_color = dq.daquex(self.hand)
        return self.daque_color        

    def get_daque_tiles(self):
        ''' Return the daque color
        '''
        dc = self.daque_color
        hand = self.hand
        Q = [t[1] for t in hand if t[0] == dc]
        Q.sort()
        return Q
    
    def get_nondaque_tiles(self):
        ''' Return the daque color
        '''
        dc = self.daque_color
        hand = self.hand
        HD = list(t for t in hand if t[0] != dc)
        HD.sort(key=lambda t: t[0:2])
        return HD
    
    #2020021207-sl
    def get_dominant_color(self):
        ''' Return the dominant color 0, 1, 2, or None'''
        dc = self.daque_color
        hand = self.hand
        pile = self.pile
        pile_color = set()
        #2020021521-sl
        if pile:
            for p in pile:
                pile_color.add(p[0][0])
        if len(pile_color) > 1:
            return None
        for c in {0, 1, 2}:
            if c == dc:
                continue
            #2020031017-sl: revised
            hand_c = list(t for t in hand if t[0] == c)
            if len(hand_c) + 3*len(pile) > 8 and \
               (not pile or (pile and c in pile_color)): #2020031210-sl
                #q is 8 a good estimation?
                return c
        return None

    #2020021607-sl
    def get_pure_color_index(self):
        ''' Return the dominant color '''
        dc = self.daque_color
        hand = self.hand
        pile = self.pile
        c = self.get_dominant_color()
        if c == None:
            return 0
        hand_c = list(t for t in hand if t[0] == c)
        index = len(hand_c) + 3*len(pile)
        return index
               
    
    def kgbase(self, dealer, players):
        ''' Compute the knowledgebase of the player
        Args:
            dealer (object): Dealer
            players (list): List of all players
        '''
        KT = deepcopy(self.hand)
        for player in players:
            for p in player.pile:
                for card in p:
                    KT.append(card)

        KT = KT + dealer.table                   
        
        K = [4]*27
        for x in MJ():
            p = x[0]*9 + x[1] - 1
            a = KT.count(x)
            K[p] = 4 - a
        return K


    def get_deficiency(self, dealer, players): #used in xzscore.py
        #q check if this function is necessary
        ''' Compute the deficiency of the player's hand
        '''                
        T = deepcopy(self.hand)
        Pg = [ p[0] for p in self.pile]
        dc = self.daque_color
        KB = self.kgbase(dealer, players)
        # Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color
        HD = [t for t in T if t[0] != dc] #sl tiles without daque color
        HD.sort(key=lambda t: t[0:2])
        # KW = [KB[0:9],KB[9:18],KB[18:27]]
        x = dfncy(HD, Pg, KB, dc) # the deficiency of the player's hand
##        y = hk.hyval(HD, Pg, KB, dc)
##
##        if x!= y:
##            print([x,y])
##            print("HD = %s"%HD)
##            print("Pg = %s"%Pg)
##            print("KB = %s"%KB)
##            print("dc = %s"%dc)
##            
        #Achtung! This computation of the deficiency does not consider Q
        return x

    def ankong_list(self):
        lst = [card for card in self.hand if self.hand.count(card) == 4]
        listx = remove_duplicates(lst) 
        return listx

    def jiakong_list(self):
        return [card for card in self.hand if [card]*3 in self.pile]

    #sl real action
    def play_card(self, dealer, card): 
        ''' Play one card
        Args:
            dealer (object): Dealer
            Card (list): The Mahjong tile to play.
        '''
        if card not in self.hand:
            print('card %s is not in hand %s' %(card, self.hand))
        self.hand.pop(self.hand.index(card))

        #2020022709-sl: record all public information
        dealer.table.append(card)
        dealer.act_history.append([self.player_id, 'discard', card])
        discard_list = deepcopy(dealer.discard_lists[self.player_id])
        discard_list.append(card)
        #print(discard_list)
        dealer.discard_lists[self.player_id] = deepcopy(discard_list)
        #print(dealer.discard_lists[self.player_id])


        #print('Player %s discards: %s' %(self.player_id, card))
        #sl: we don't append the card to the table here, as that's the job of the dealer
                #and we shall do this in xzround.py

    #sl real action
    def kong(self, dealer, cards, players, last_player): #s revealed kong
        ''' Perform Kong
        Args:
            Cards (object): The cards (containing 4 identical tiles) to Kong.
            last_player (int): the player who discarded the tile which the current player can kong
        '''
        for card in cards[0:3]: 
            self.hand.pop(self.hand.index(card))
        self.pile.append(cards)
        ''' compute_kong_score updates the scores and score records of all players when one player kong'''
        score.compute_kong_score(self, players[last_player], cards[0])          
        dealer.act_history.append([self.player_id, 'kong', cards[0], last_player])


        #print('Player %s kong: %s' %(self.player_id, cards[0]))
        #for player in players:                                                 
            #print('Player %s score is: %s' %(player.player_id, player.myscore))  

    #sl real action
    def pong(self, dealer, cards):
        ''' Perform Pong
        Arg:
            Cards (object): The cards (containing 3 identical tiles) to pong.
        '''
        #sl the player may have, say, 3 B9, if he decides to pong B9 even when he can kong
        for card in cards[0:2]: #pop two identical tiles
            self.hand.pop(self.hand.index(card))
        self.pile.append(cards[0:3])
        #print('Player %s pong: %s' %(self.player_id, cards[0]))
        dealer.act_history.append([self.player_id, 'pong', cards[0]])


    #sl real action
    def ankong(self, dealer, cardx, players): #concealed kong (ankong)
        ''' Perform Concealed Kong
        Args:
            cardx (object): The card to Kong.
        '''
        if self.hand.count(cardx) != 4:
            return None
        cards = [cardx]*4
        for card in cards: 
            self.hand.pop(self.hand.index(card))
        self.pile.append(cards)
        ''' compute_ankong_score updates the scores and score records of all players when one player ankong'''
        score.compute_ankong_score(self, players, cardx)                               
        #print('Player %s an-kong: %s' %(self.player_id, cardx))
        #for player in players:                                                 
            #print('Player %s score is: %s' %(player.player_id, player.myscore))  
        dealer.act_history.append([self.player_id, 'ankong', cardx])


    #sl real action, but could be canncelled due to robbery       
    def jiakong(self, dealer, cardx):
        ''' Perform jiaKong
        Args:
            Cardx (list): The Mahjong tile to jiaKong.
        '''
        
        cards = [cardx]*3
        if cards not in self.pile or cardx not in self.hand:
            return None
        i = self.pile.index(cards)
        self.pile[i] = [cardx]*4
        self.hand.pop(self.hand.index(cardx))
        #print('Player %s jia-kong: %s' %(self.player_id, cardx))
        #Achtung! Note we don't compute compute_jiagang_score here, which is done in xzround.py
        dealer.act_history.append([self.player_id, 'jiakong', cardx])

    def cancel_jiakong(self, jiakong_card):
        '''Cancel jiakong if there is some one robkong
        '''
        cards = [jiakong_card]*4
        i = self.pile.index(cards)
        self.pile[i] = [jiakong_card]*3
        ''' We don't need to add a cancel_jiakong action in the act_history,
                        as will be clear from the following action. '''        
        #dealer.act_history.append([self.player_id, 'cancel_jiakong', cardx])

        #print("Player %s was robkonged by other player(s) and his jiakong would be canceled" %self.player_id)
        #print("Player %s hand: %s" %(self.player_id,self.hand))
        #print("Player %s pile: %s" %(self.player_id,self.pile))

    def robkong(self, dealer, players, jiakong_card, jiakong_player):
        '''Perform robkong
        '''
        self.winning_card = jiakong_card 
        self.winning = True
        self.hand.append(jiakong_card)
        #print('Player %s robkong: %s' %(self.player_id,jiakong_card))

        numWl = dealer.numWl
        #numWl = len(dealer.deck)
        score.compute_hu_score(self, players, numWl, jiakong_player)
        ''' compute_hu_score updates the scores and score records of all players when one player hu'''

        #2020022709-sl: record all public information
        score_record =  self.scoreRecords[-1] # ['zimo', zimo_id, hu_times, +hu_times*base_score]
                        #['tianhu', tdhu_di, tdhu_fan, +tdhu_fan*base_score]
        dealer.win_info[self.player_id] = [self.winning_card] + score_record
        dealer.act_history.append([self.player_id, 'robkong', jiakong_card, jiakong_player])

        #print('Player %s hu_way: %s' %(self.player_id, self.hu_way))
        #for player in players:        
            #print('Player %s score is: %s' %(player.player_id, player.myscore))

            
    #sl real action
    def zimo(self, dealer, players):
        ''' Perform Zimo
        '''
        self.winning_card = self.hand[-1] #q make sure this card is the last in the hand
        self.winning = True
        #print('Player %s zimo: %s' %(self.player_id, self.hand[-1]))


        self.hu_way.append('zimo')        
        dianpao_player = None
        numWl = dealer.numWl
        #numWl = len(dealer.deck)
        ''' compute_hu_score updates the scores and score records of all players when one player hu'''
        score.compute_hu_score(self, players, numWl, dianpao_player)        
        
        #2020022709-sl: record all public information
        score_record =  self.scoreRecords[-1] # ['zimo', zimo_id, hu_times, +hu_times*base_score]
                        #['tianhu', tdhu_di, tdhu_fan, +tdhu_fan*base_score]
        dealer.win_info[self.player_id] = [self.winning_card] + score_record
        dealer.act_history.append([self.player_id, 'zimo', self.winning_card])
                
        #print('Player %s hu_way: %s' %(self.player_id, self.hu_way))
        #for player in players:        
            #print('Player %s score is: %s' %(player.player_id, player.myscore))

              
    #sl real action
    def hu(self, cardx, dealer, players, dianpao_player):
        #sl card (which is the last card in dealer.table) completes the hand of the player
        ''' Perform Hu
        Args:
            dealer (object): Dealer
            cardx (object): The card to complete the player's hand
            dianpao_player (object): the player who discarded cardx
        '''
        self.winning_card = cardx
        self.winning = True
        self.hand.append(cardx)

        #2020021612-sl: moved from xzscore
        self.hu_way.append('pinghu')
        #print('Player %s hu: %s' %(self.player_id, cardx))

        ''' compute_hu_score updates the scores and score records of all players when one player hu'''
        #numWl = len(dealer.deck)
        numWl = dealer.numWl
        #2020022809-sl: here dianpao_player is an object
        score.compute_hu_score(self, players, numWl, dianpao_player)

        #2020022709-sl: record all public information
        score_record =  self.scoreRecords[-1] # ['hu', dianpao_player.player_id, hu_times, +hu_times*base_score]
        dealer.win_info[self.player_id] = [self.winning_card] + score_record
        dealer.act_history.append([self.player_id, 'hu', cardx, dianpao_player.player_id])

        #print('Player %s hu_way: %s' %(self.player_id, self.hu_way))  
        #for player in players:                                                 
            #print('Player %s score is: %s' %(player.player_id, player.myscore))   

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
if __name__ == '__main__':
    # main_test
    Player = MahjongPlayer(0)
    Player.hand = [[0, 1], [0, 4], [0, 5], [0, 6], [0, 6], [0, 8], [0, 8], [1, 1], [1, 1], [1, 7], [1, 8],\
         [2, 2], [2, 3], [2, 6]]
    dc = Player.get_daque_color()
    Q = Player.get_daque_tiles()
    HD = Player.get_nondaque_tiles()

    print(dc,'\n', Q, '\n', HD)
    print(HD[0:2])
