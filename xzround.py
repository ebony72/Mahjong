import utils.xzscore as score
# from copy import deepcopy
from utils.constants import ACTIONS,HU_WAYS,get_tile_idx,get_tile_color,get_tile_num
##from xzutils import *
class MahjongRound(object):

    def __init__(self, judger, dealer, num_players):
        ''' Initialize the round class

        Args:
            judger (object): the object of MahjongJudger
            dealer (object): the object of MahjongDealer
            num_players (int): the number of players in game
        '''
        self.judger = judger
        self.dealer = dealer
        self.current_player = 0 # (int) each game always starts with Player 0 
        self.num_players = num_players  # it's fixed as 4 in xuezhan
        self.is_over = False
        self.player_before_act = None # (int) the id of the discard player or the jiakong player
        self.valid_act = 'self_check' #9: {'self_check', 'discard', 'kong', 'pong', 'hu', 'zimo', 'zikong', 'robkong', None}
        self.last_cards = [] #sl only used for 'pong', 'kong', 'zikong'
        self.winners = [] #sl the list of winners 
        self.Huers = [] # record the players who could hu a discarded card or rob a jiakong
        self.Hu_accept = [] # record the players who could and choose to hu (or rob the jiakong)
        self.Hu_reject = [] # record the players who could but choose not to hu (or rob the jiakong)
        self.jiakong_card = []
        self.kong_index = 0 # (mingkong, ankong and jiakong) used for kongshangpao and kongshanghua
        self.kong_list = [] #used for hujiaozhuanyi
        self.last_drawn_card = []
        self.changshu = 0
        self.step = 0
        self.action_idx = -1
        self.action_tile_idx = -1

        #sl in the first round, player 0 self_check

    def next_player(self, players, player):
        i = player.player_id
        for j in range(1, self.num_players):
            k = (i+j) % 4
            if players[k] in self.winners:
                continue
            return k
        return None

    def information_output(self,players):
        
        String_lists = []
        string_list = []
        string_list.append(str(self.step))
        string_list.append((str(self.current_player)))
        string_list.append(":".join([str(self.action_idx),str(self.action_tile_idx)]))
        string_list.append(str(players[self.current_player].get_deficiency(self.dealer,players)))#20210302N     
        current_winners = [p.player_id for p in players if p.winning]
        string_list.append(",".join([str(winner) for winner in current_winners]))           
        current_scores = [p.myscore for p in players]
        string_list.append(",".join([str(a_score) for a_score in current_scores]))
        temp1 = []
        temp2 = []
        for a_player in players:
            temp1.append(":".join(str(HU_WAYS[way]) for way in a_player.hu_way))
            if a_player.winning_card:
                t = a_player.winning_card[:]
                temp2.append(str(get_tile_idx(t[0],t[1])))
            else:
                temp2.append("")
            
        string_list.append(",".join(str(e) for e in temp1))
        string_list.append(",".join(str(e) for e in temp2))
        String_lists.append(
            ";".join(string_list)
        )
        # format_data(self.changshu, String_lists)
        #&
        pass

    def proceed_round(self, players, action): 

        ''' Call other Classes's functions to keep one round running

        Args:
            players (objects): objects of MahjongPlayer
            action (str): the string of a legal action selected according the strategy and the valid_act (cf. xzgame.py) 
                    from {'stand', 'pong', 'kong', 'hu', 'discard', 'self_check', 'zimo','robkong', None} +
                      {['ankong', card1], ['jiakong', card2], ['stand','zikong']},
                          card1 in ankong_list, card2 in jiakong_list + {any card in current_player.hand} 
        '''
        #print('The initial current player is %s and the initial valid act is %s' %(self.current_player, self.valid_act))

        #sl there is only one player whose hand has form 3*m+2, the other players' hands have length 3*n+1
        for i in range(self.num_players):
            if len(players[i].hand) % 3 == 2: # the player just drew a card
                self.last_drawn_card = players[i].hand[-1] 
                break
            
        if (action != 'discard' and action != None and len(action) == 2) and type(action[0]) == str and action != 'hu':
            #sl the action is resulted from the valid_act 'zikong'
            if action[0] == 'stand': #for action  ['stand', 'zikong'], the second item 'zikong' is auxilary
                self.valid_act = 'discard' #sl the current player should discard a card                

            elif action[0] == 'ankong': #sl no one can rob ankong
                players[self.current_player].ankong(self.dealer, action[1], players)
                self.information_output(players)
                self.dealer.deal_cards(players[self.current_player], 1)
                self.kong_list.append(action[1]) 
                self.kong_index = 1
                self.valid_act = 'self_check'

            else: #action[0] == 'jiakong'                          
                self.jiakong_card = action[1]
                players[self.current_player].jiakong(self.dealer, self.jiakong_card)
                self.information_output(players)
                self.player_before_act = self.current_player #jiakong player

                valid_act = None #sl a temporal valid_act
                self.Huers = []

                #2020021919-sl
                ''' We should ask the players one by one, starting from the next player of the current player //todo'''
                ix = self.current_player
                for j in range(1, 4):
                    k = (ix + j) % 4
                    player = players[k]
                    if player in self.winners:
                #for player in players:
                    #if player.player_id == self.current_player or player.winning:
                        continue
                    if self.judger.judge_hu(player, self.jiakong_card):
                        self.Huers.append(player)
                if self.Huers:
                    self.current_player = self.Huers[0].player_id # we then ask each huer if he rob
                    self.valid_act = 'robkong'                    
                else: #sl if no one could rob kong, the current_player performs jiakong 
                    score.compute_jiagang_score(players[self.player_before_act], players, self.jiakong_card)
                    self.kong_list.append(self.jiakong_card)
                    #for player in players:                                                 
                        #print('Player %s score is: %s' %(player.player_id, player.myscore))  #y
                    self.kong_index = 1
                    self.jiakong_card = []
                    self.dealer.deal_cards(players[self.current_player], 1)
                    self.valid_act = 'self_check'
               
        elif action == 'stand': #the action due to previous self.valid_act 'pong', 'kong', 'hu', 'zimo', 'robkong'
            self.information_output(players)
            if self.valid_act in {'kong', 'pong'}:
                self.current_player = self.next_player(players, players[self.player_before_act])
                #player_before_act is the discard player
                if not self.dealer.deck:
                    self.is_over = True
                    self.valid_act = None
                else:
                    self.dealer.deal_cards(players[self.current_player], 1)
                    self.valid_act = 'self_check'
                
            elif self.valid_act == 'zimo': #sl if current_player zimo but want to wait, we need to check if he zikong
                if self.judger.judge_zikong(self.dealer, players[self.current_player]):
                    self.valid_act = 'zikong'
                else:
                    self.valid_act = 'discard'

            elif self.valid_act == 'robkong':
                #one huer who rejected to rob kong but we still need to consider the next huer
                #print('test: robkong reject')
                self.Hu_reject.append(players[self.current_player])
                
                k = len(self.Hu_accept) + len(self.Hu_reject)
                if k < len(self.Huers):
                    self.current_player = self.Huers[k].player_id #consider the next huer
                    self.valid_act = 'robkong' 
                else:
                    if len(self.Hu_reject) == len(self.Huers): #no one rob and the jiakong player performs jiakong
                        self.current_player = self.player_before_act #the jiakong player
                        score.compute_jiagang_score(players[self.current_player], players, self.jiakong_card)
                        self.kong_list.append(self.jiakong_card)
                        #for player in players:                                                 #y
                            #print('Player %s score is: %s' %(player.player_id, player.myscore))  #y
                        self.information_output(players)
                        self.kong_index = 1
                        self.dealer.deal_cards(players[self.current_player], 1)
                        self.valid_act = 'self_check'
                        
                    else: #perform robkong for each player who accepts hu
                        cur_playerx = self.player_before_act #sl the jiakong player
                        self.dealer.table.append(self.jiakong_card)#y 多个玩家抢杠时，桌面上只添加1张抢杠牌。为后面信息输出正确，放在这里！
                        for player in self.Hu_accept:
                            if player.winning:
                                continue
                            cur_playerx = player.player_id
                            player.hu_way.append('robkong')
                            #Perform robkong
                            player.robkong(self.dealer, players, self.jiakong_card, players[self.player_before_act])
                            player.winning_card = self.jiakong_card
                            self.winners.append(player)
                            self.information_output(players)

                        if len(self.winners) == 3 or not self.dealer.deck:
                            self.is_over = True
                            self.valid_act = None
                        else:
                            self.current_player = self.next_player(players, players[cur_playerx])
                            self.dealer.deal_cards(players[self.current_player], 1) 
                            self.valid_act = 'self_check'

                    #reset
                    self.jiakong_card = []
                    self.Huers = []
                    self.Hu_accept = []
                    self.Hu_reject = []               
                                
            else: #self.valid_act == 'hu':
                ''' One huer rejected to hu but we need to consider the next huer if exists'''
                #print('test: hu reject')
                self.Hu_reject.append(players[self.current_player])

                k = len(self.Hu_accept) + len(self.Hu_reject)
                if k < len(self.Huers): #sl self.Huers is the list of players that dealer.table[-1] completes their hands
                    self.current_player = self.Huers[k].player_id
                    self.valid_act = 'hu' #sl it's the k-th huer's turn to determine if he hu or stand
                else: #sl after all players in self.Huers have responded
                    
                    cur_playerx = self.player_before_act #the last player who discarded a tile
                    if self.Hu_accept:
                        for player in self.Hu_accept:
                            if player.winning:
                                continue
                            cur_playerx = player.player_id
                            if self.kong_index == 1:
                                player.hu_way.append('kongshangpao')
                                score.hujiaozhuanyi(self.kong_list[-1], player, players[self.player_before_act])
                            #2020022711-sl: moved the following operation after appending 'kongshangpao' to hu_way
                            player.hu(self.dealer.table[-1], self.dealer, players, players[self.player_before_act])
                            player.winning_card = self.dealer.table[-1]                                                         
                            self.winners.append(player)
                            self.information_output(players)
                            
                        if len(self.winners) == 3 or not self.dealer.deck:
                            self.is_over = True
                            self.valid_act = None
                        else:
                            self.current_player = self.next_player(players, players[cur_playerx])
                            self.dealer.deal_cards(players[self.current_player], 1)    
                            self.valid_act = 'self_check'
                                           
                    else: #sl as no one accepts hu, we further check if someone can pong/kong
                        (valid_act, player, cards) = self.judger.judge_pong_kong(self.dealer, players, self.player_before_act)
                        if valid_act != False: #sl (revealed) kong or pong or False
                            self.valid_act = valid_act
                            self.current_player = player.player_id
                            self.last_cards = cards
                        else: #sl here player_before_act is the player who discards dealer.table[-1] that completes someone's hand
                            if self.dealer.deck:
                                self.current_player = self.next_player(players, players[self.player_before_act])
                                self.dealer.deal_cards(players[self.current_player], 1)
                                self.valid_act = 'self_check'
                            else:
                                self.is_over = True
                                self.valid_act = None
                    #reset
                    self.kong_index = 0
                    self.Huers = []
                    self.Hu_accept = []
                    self.Hu_reject = []
                    

        elif action == 'kong': #sl revealed kong only
            ''' No one can rob revealed kong (mingkong) as hu has higher priority '''
            #player_before_act is the discard player
            players[self.current_player].kong(self.dealer, self.last_cards, players, self.player_before_act)#2020021110-sl
            #sl the last parameter should be the id of the last player
            self.dealer.table.pop(self.dealer.table.index(self.last_cards[0]))
            self.kong_list.append(self.last_cards[0])
            self.information_output(players)
            self.dealer.deal_cards(players[self.current_player], 1)           
            self.kong_index = 1 #maked in case kongshanghua or kongshangpao
            self.valid_act = 'self_check'

        elif action == 'pong': #sl current_player does not change
            players[self.current_player].pong(self.dealer, self.last_cards)
            self.dealer.table.pop(self.dealer.table.index(self.last_cards[0]))
            self.information_output(players)
            self.valid_act = 'discard'

        elif action == 'robkong':
            ''' This acction is activated by a jiakong and the current huer accepts to rob'''
            #print('test: robkong accept')
            self.Hu_accept.append(players[self.current_player])
            if len(self.Hu_accept) == 1:
                players[self.player_before_act].cancel_jiakong(self.jiakong_card)
                #player_before_act is the jiakong player
            
            k = len(self.Hu_accept) + len(self.Hu_reject)
            if k < len(self.Huers):
                self.current_player = self.Huers[k].player_id
                self.valid_act = 'robkong' 
            else: 
                cur_playerx = self.player_before_act #the jiakong player
                self.dealer.table.append(self.jiakong_card)
                for player in self.Hu_accept:
                    if player.winning:
                        continue
                    cur_playerx = player.player_id
                    #Perform robkong
                    player.hu_way.append('robkong')
                    player.robkong(self.dealer, players, self.jiakong_card, players[self.player_before_act])                    
                    player.winning_card = self.jiakong_card
                    self.winners.append(player)                
                    self.information_output(players)
                #reset
                self.jiakong_card = []
                self.Huers = []
                self.Hu_accept = []
                self.Hu_reject = []                

                if len(self.winners) == 3 or not self.dealer.deck:
                    self.is_over = True
                    self.valid_act = None
                else:
                    self.current_player = self.next_player(players, players[cur_playerx])
                    self.dealer.deal_cards(players[self.current_player], 1)
                    self.valid_act = 'self_check'

        elif action == 'hu':
            ''' The current huer accepts to hu but we still need to ask if the next huer accept '''
            self.Hu_accept.append(players[self.current_player])
            #print('test: hu accept')
            k = len(self.Hu_accept) + len(self.Hu_reject)
            if k < len(self.Huers):
                self.current_player = self.Huers[k].player_id
                self.valid_act = 'hu' #sl we proceed to ask if the k-th huer if he accepts
            else:
                ''' All huers have processed (accept or reject) their hu-invitations '''
                cur_playerx = self.player_before_act #sl who discards dealer.table[-1]
                for player in self.Hu_accept:
                    if player.winning:
                        continue
                    cur_playerx = player.player_id
                    if self.kong_index ==1:
                        player.hu_way.append('kongshangpao')
                        score.hujiaozhuanyi(self.kong_list[-1], player, players[self.player_before_act])
                    player.hu(self.dealer.table[-1], self.dealer, players, players[self.player_before_act])#y                    
                    player.winning_card = self.dealer.table[-1]
                    self.winners.append(player)
                    self.information_output(players)
                    
                #reset
                self.kong_index = 0
                self.Huers = []
                self.Hu_accept = []
                self.Hu_reject = []                
                
                if len(self.winners) == 3 or not self.dealer.deck:
                    self.is_over = True
                    self.valid_act = None
                else:
                    self.current_player = self.next_player(players, players[cur_playerx])
                    self.dealer.deal_cards(players[self.current_player], 1)
                    self.valid_act = 'self_check'

        elif action == 'zimo':

            #'zimo' is appended to hu_way in xzplayer.py
            #players[self.current_player].hu_way.append('zimo')
            if self.kong_index == 1:
                players[self.current_player].hu_way.append('kongshanghua')
                #reset
                self.kong_index = 0

            #2020022711-sl: moved the zimo action after appendding 'kongshanghua' to hu_way
            players[self.current_player].zimo(self.dealer, players)            
            self.last_drawn_card = players[self.current_player].hand[-1]
            players[self.current_player].winning_card = self.last_drawn_card
            self.dealer.table.append(self.last_drawn_card)            
            #print("table: %s" %self.dealer.table)
            self.winners.append(players[self.current_player])
            self.information_output(players)
            
            if len(self.winners) == 3 or not self.dealer.deck:
                self.is_over = True
                self.valid_act = None
            else:
                self.current_player = self.next_player(players, players[self.current_player])
                self.dealer.deal_cards(players[self.current_player], 1)
                self.valid_act = 'self_check'
            
        elif action == 'self_check': #sl current_player does not change
            self.information_output(players)
            self.last_drawn_card = players[self.current_player].hand[-1]
            if self.judger.judge_zimo(players[self.current_player]): #sl last_drawn_card is the last card drawn by current_player
                self.valid_act = 'zimo'
                #print(players[self.current_player].hand)
                #print(players[self.current_player].pile)
            elif self.judger.judge_zikong(self.dealer, players[self.current_player]):
                self.valid_act = 'zikong'
            else:
                self.valid_act = 'discard'
               
        else: # discard tile
            #print(action)
            ''' The current player discards a tile '''
            players[self.current_player].play_card(self.dealer, action)
            self.information_output(players)

            
            #print("table: %s" %self.dealer.table)
            self.player_before_act = self.current_player #the discard player

            self.Huers = []
            valid_act = False #sl a temporal valid_act

            #2020021919-sl
            ''' We should ask the players one by one, starting from the next player of the current player //todo'''
            ix = self.current_player
            for j in range(1, 4):
                k = (ix + j) % 4
                player = players[k]
                if player in self.winners:
            #for player in players:
                #if player.player_id == self.current_player or player.winning:
                    continue
                if self.judger.judge_hu(player, action): #sl here action is a card
                    valid_act = 'hu'
                    self.Huers.append(player)
            #for player in self.Huers:
                #if player.winning: #q is this possible?
                    #print('There is a winner %s included in %s' %(player.player_id, [self.Huers[i].player_id for i in range(len(self.Huers))]))
                    
            if valid_act == 'hu':
                self.current_player = self.Huers[0].player_id
                self.valid_act = 'hu'

            else:
                ''' No one hu the tile and the valid_act is False '''
                
                #sl when kong is possible, the judger needs to ask the player to decide
                #sl kong has priority over pong; if the player decides not kong, he still has the chance to pong

                #reset as the previous kong is safe (for kongshangpao) now
                self.kong_index = 0
                
                (valid_actx, player, cards) = self.judger.judge_pong_kong(self.dealer, players, self.player_before_act)

                if valid_actx != False:
                    self.valid_act = valid_actx
                    self.current_player = player.player_id
                    self.last_cards = cards
                else: # no one hu, pong, kong the card
                    #print('No player takes %s' %(self.dealer.table[-1]))
                    if not self.dealer.deck:
                        #print
                        self.valid_act = None
                        self.is_over = True
                    else:
                        self.current_player = self.next_player(players, players[self.current_player]) 
                        self.dealer.deal_cards(players[self.current_player], 1)
                        self.valid_act = 'self_check'

        #print('End: Player %s and valid act: <<%s>>' %(self.current_player, self.valid_act))
        

    def get_state(self, players, player_id):
        ''' Get player's state
        Args:
            players (list): The list of MahjongPlayer
            player_id (int): The id of the player
        Return:
            state (dict): The information of the state
            state['valid_act'] in {None, ['self_check'], ['zikong', 'stand'], ['kong', 'pong', 'stand'], ['hu', 'stand'],
                                        ['pong', 'stand'], ['zimo', 'stand'], ['robkong', 'stand'], ['discard']}
            state['action_cards'] in { [['ankong', card] for card in an_list] + \
                                      [['jiakong', card] for card in jia_list] + [['stand', 'zikong']],
                                      self.last_cards, players[player_id].hand }
                    Achtung! Note 'action_cards' are not used in the algorithm!
            state['table']: the current table of the dealer
            state['player']: the current player
            state['current_hand']: the current hands of each player
            state['players_pile'] (dict)
        '''
        state = {}
        if self.valid_act == 'zikong':
            an_list = players[self.current_player].ankong_list()
            jia_list = players[self.current_player].jiakong_list()
            state['valid_act'] = ['zikong', 'stand']
            state['table'] = self.dealer.table
            state['player'] = self.current_player #sl current_player == player_id
            state['current_hand'] = players[player_id].hand
            state['players_pile'] = {p.player_id: p.pile for p in players}
            state['action_cards'] =  [['ankong', card] for card in an_list] + \
                                      [['jiakong', card] for card in jia_list] + [['stand', 'zikong']]
                                    #for the last item, we always select 'stand' as 'zikong' is just an auxiliary item

        #elif self.valid_act != False: # pong/kong/hu/zimo/self_check
        elif self.valid_act != 'discard': # pong/kong/hu/zimo/self_check/robkong
            if self.valid_act == None:
                 state['valid_act'] = None               
            elif self.valid_act == 'self_check':
                 state['valid_act'] = ['self_check']               
            elif self.valid_act == 'kong':
                state['valid_act'] = ['kong', 'pong', 'stand']
            else: #sl hu, pong, zimo, robkong                
                state['valid_act'] = [self.valid_act, 'stand']
            state['table'] = self.dealer.table
            state['player'] = self.current_player
            state['current_hand'] = players[self.current_player].hand
            state['players_pile'] = {p.player_id: p.pile for p in players}
            state['action_cards'] = self.last_cards # For doing action (pong, kong, zikong), [] otherwise
       
        else: # Regular Play #sl self.valid_act == 'discard'
            state['valid_act'] = ['discard']
            state['table'] = self.dealer.table
            state['player'] = self.current_player #sl isn't current_player same as player_id?
            state['current_hand'] = players[player_id].hand
            state['players_pile'] = {p.player_id: p.pile for p in players}
            state['action_cards'] = players[player_id].hand #sl For doing action (play)
            #sl: discard a card from hand
        return state

