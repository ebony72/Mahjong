''' Generate, Load, and Compare on, a batch of games '''
from copy import deepcopy
import json
import os
from datetime import datetime

''' import the Mahjong common modules'''
from xzdealer import MahjongDealer as Dealer
from xzplayer import MahjongPlayer as Player
from xzround import MahjongRound as Round
from xzjudger import MahjongJudger as Judger
from utils.xzutils import *
import utils.xzscore as score
from dfncy.block_dfncy import dfncy 


'''import the two strategies to compare (you may design your own strategy) '''
import strategy_initial21_7attr as strategy #our initial stratey: to be compared with
    

class XZMahjongGame(object):

    def __init__(self, allow_step_back=False):
        '''Initialize the class MajongGame
        '''
        self.num_players = 4

    def init_game(self, index): 
        ''' Initialilze a game
        Arg:
            index (int): 1 if the same game has been played five times and we should reinitiate the game and 0 else
        Returns:
            (tuple): Tuple containing:
            (dict): The first state of the game
            (int): Current player's id
        '''
        # Initialize a dealer that can deal cards
        self.dealer = Dealer()

        # Initialize four players to play the game
        self.players = [Player(i) for i in range(self.num_players)] 
        self.judger = Judger()
        self.round = Round(self.judger, self.dealer, self.num_players)

        state = self.get_state(self.round.current_player)
        self.cur_state = state 

        # Deal 13 cards to each player and 1 card to current_player to prepare for the game
        if index: #
            ''' index is 1 if we have finished all rounds and want to start a new game '''  
            for player in self.players:
                self.dealer.deal_cards(player, 13)
            self.dealer.deal_cards(self.players[self.round.current_player], 1)        
        
        return state, self.round.current_player

    def step(self, action):
        ''' Go to the next state by enforcing the action
        Args:
            action (str): the string of a legal action selected according the strategy and the valid_act
                    from {'stand', 'pong', 'kong', 'hu', 'discard', 'self_check', 'zimo','robkong', None} +
                      {['ankong', card1], ['jiakong', card2], ['stand','zikong']},
                          card1 in ankong_list, card2 in jiakong_list + {any card in current_player.hand} 
           
        Returns:
            round (object): The updated round
            state (dict): The updated state of the current player
            current_player (int): The current player's id
        '''
        self.round.proceed_round(self.players, action)
        state = self.get_state(self.round.current_player)
        self.cur_state = state 
        return state, self.round.current_player

    def get_state(self, player_id):
        ''' Return player's state
        Arg:
            player_id (int): player id
        Return:
            (dict): The state of the player
        '''
        state = self.round.get_state(self.players, player_id)
        return state

    def is_over(self):
        ''' Check if the game is over
        Return:
            (bool): True if the game is over
        '''
        if self.round.is_over: 
            return True
        return False

def save_result(name, content):
    name = str(name)
    content = str(content)
    file = open("testRecord/game" + '_' + name  + ".txt", mode = 'a')
    file.write(content)
    file.write('\n')
    file.close()    

path = "Ini_Games/" 
files= os.listdir(path)

if __name__ == '__main__': 
    import time
    start = time.time()
    ''' Load a batch of initial games '''
    file_name = 'game_batch_0302_1000'
    current_path = 'Ini_Games/' + file_name + '.txt'
    with open(current_path, 'r') as f: 
        Games = json.loads(f.read())
    summary = 'summary'
            
    n_GAME = 1 # number of games
    '''Select you test game, here we consider the first game'''
    changshu = 0  #the game id starts from changshu, which is between 0 and 999 
    
    now = datetime.now()
    
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print(changshu, n_GAME)
    for _ in range(n_GAME):

        changshu += 1
        content = '***** %s-CHANG-%s *****'%(file_name, changshu)
        # print(content)
        save_result(changshu, content)
        save_result(summary, content)
        
        game = XZMahjongGame()
        state, button = game.init_game(1) #sl button = current_player
        ''' Start a new game and fix the hands and the Wall (deck) '''
        
        '''Replace the hands and deck with the game read from Games, a list of pre-generated inital games'''
        game.players[0].hand = Games[changshu-1][0]
        game.players[1].hand = Games[changshu-1][1]
        game.players[2].hand = Games[changshu-1][2]
        game.players[3].hand = Games[changshu-1][3]
        game.dealer.deck = Games[changshu-1][4]

        #fix the hands and wall, which will be used in all Jus 
        H0 = game.players[0].hand[:]
        H1 = game.players[1].hand[:]
        H2 = game.players[2].hand[:]
        H3 = game.players[3].hand[:]
        W = game.dealer.deck[:]
        HS = [H0, H1, H2, H3] #used in line 167
        
        content = 'The initial setting of the game is as follows:'
        save_result(changshu, content)

        '''Record the initial state and determine the daque colors of the players'''
        DQC = [-1]*4 
        last_drawn_card = H0[-1]
        for player in game.players:            
            HX = deepcopy(game.players[player.player_id].hand)
            HX.sort()
            content = 'H%s = %s' %(player.player_id, HX)
            save_result(changshu, content)
            save_result(summary, content)
            player.daque_color = player.get_daque_color()
            DQC[player.player_id] = player.daque_color #fix the daque color
            content = 'Player %s: daque %s' %(player.player_id, player.daque_color)
            save_result(changshu, content)
        content = 'W = %s' %game.dealer.deck
        save_result(changshu, content)
        save_result(summary, content)        
        content = 'DQC = %s' %DQC
        save_result(changshu, content)
        save_result(summary, content)

        game_record = [H0, H1, H2, H3, W, DQC] #the initial state

        state, button = game.init_game(1) #sl button = current_player
            #0 indicates that the initial state should be the same as the previous round

        #reset the initial state of the game of this Ju as that specified in the beginning of this Chang
        for i in range(4): #use the fixed hand and daque color
            game.players[i].hand = deepcopy(HS[i])
            game.players[i].daque_color = DQC[i]                             
        game.dealer.deck = W[:]
        game.dealer.dqc = DQC           
    
        i = 0 #step number           
        num_state_change = 0
        while not game.is_over():

            current_player = game.round.current_player # (int)
            last_player = game.round.player_before_act # (int)
            numWl = len(game.dealer.deck) #number of tiles in the Wall
            table = game.dealer.table
            content = ' Table = %s' %table
            save_result(changshu, content)

            i += 1
            #num_state_change += 1
            valid_act = game.round.valid_act
            n_hu = len(game.round.winners)
            if n_hu != game.dealer.n_hu():
                print('%s %s  is incorrect!' %(n_hu, game.dealer.n_hu()))

            '''For each valid act, the players select a legal action to execute according to his strategy. '''
            PerformStrategy = strategy
            save_result(changshu, content)
                                
            '''There are 27+6+1 = 34 different valid_acts except None (27 cards, hu, pong, kong, zimo, zikong, robkong) '''
            if valid_act == None:
                ''' This is the case only when the game is over // check! '''
                if game.dealer.deck == 0 and len(game.round.winners) < 3: 
                     score.update_finalScore(game.dealer, game.players)
                content = 'Game over and the winners are in %s' %([p.player_id for p in game.players if p.winning])                         
                # print(content)
                #num_state_change += -1 #the state is not changed by None
            elif valid_act == 'self_check':
                ''' immediately before this valid_act is generated, the dealer has just dealt a card '''
                #num_state_change += -1 #the state is not changed by self_check
                action = 'self_check'
                #we assume, in step 1, Player 0 draws the last_drawn_card. In reality, it was dealt by the dealer before step 1. 
                if i == 1: #the first step, current_player should be 0
                    content = 'Step %s : Game starts and Player %s self-check \n Wall = %s' \
                              %(i, current_player, numWl)
                if i > 1:
                    last_drawn_card = game.players[current_player].hand[-1] #Achtung! Assume hand is not sorted.
                    content = 'Step %s : Player %s draws %s and self-check \n Wall = %s \n Winners = %s' \
                              %(i, current_player, last_drawn_card, numWl, [p.player_id for p in game.players if p.winning])
            elif valid_act == 'hu':
                action = 'hu'
                content = 'Step %s : Player %s can hu and shall execute %s' %(i, current_player, action)
            elif valid_act == 'pong':
                action = PerformStrategy.check_pong(game.players[current_player], game.dealer, game.players)
                content = 'Step %s : Player %s can pong and shall execute %s' %(i, current_player, action)
            elif valid_act == 'kong':
                action = PerformStrategy.check_kong(game.players[current_player], game.dealer, game.players)
                content = 'Step %s : Player %s can kong and shall execute %s' %(i, current_player, action)
            elif valid_act == 'zimo':
                action = 'zimo' #actually both strategies choose 'zimo'
                content = 'Step %s : Player %s shall execute zimo' %(i, current_player)
            elif valid_act == 'zikong':
                action = PerformStrategy.check_zikong(game.players[current_player], game.dealer, game.players)                
                content = 'Step %s : Player %s can zikong and shall execute %s' %(i, current_player, action)
            elif valid_act == 'robkong':
                action = 'robkong'
                content = 'Step %s : Player %s can rob kong and shall execute %s' %(i, current_player, action)
            else:  #valid_act == 'discard'
                ''' If the valid_act is 'discard', the player then selects one tile to discard according to his strategy. ''' 
                action = PerformStrategy.select_a_card_to_discard(game.players[current_player], game.dealer, game.players)
                content = 'Step %s : Player %s shall discard %s' %(i, current_player, action)
                #sl the action here is a card in the player's hand
                #sl at this time the action (tile) has already been appended to dealer.table   
            
            save_result(changshu, content)

            '''Record the state info of the player'''
            T = deepcopy(game.players[current_player].hand)
            dc = DQC[game.players[current_player].player_id]
            Q = list(x[1] for x in T if x[0] == dc)
            Q.sort()
            NQ = list(x for x in T if x[0] != dc)
            NQ.sort(key=lambda t: t[0:2])
            n_hu = len([p.player_id for p in game.players if p.winning])
            KB = game.players[current_player].kgbase(game.dealer, game.players)
            c = game.players[current_player].get_dominant_color()
            
            Pile = game.players[current_player].pile
            Pg = list(t[0] for t in Pile)
              
            content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n Q = %s \n NQHand = %s \n Pile =  %s \n Table = %s \n KB = %s'\
                      %(numWl, n_hu, dc, c, Q, NQ, game.players[current_player].pile, game.dealer.table, KB)
            save_result(changshu, content)
            
            #added on 19/09/2022
            cur_dfncy = dfncy(NQ,Pg,KB,dc) # the deficiency of player's hand
            content = '  The current deficiency of the player is' %cur_dfncy'
            save_result(changshu, content)
            
            
            if action != None and action != 'stand' and action[0] != 'stand':
                num_state_change += 1
            '''Proceed to the next round '''
            state, button = game.step(action)
                        
        if game.is_over:
            content = '****** Game Over *****'
            save_result(changshu, content)
            content = 'The game stops with valid_act: %s and %s cards in the Wall and %s winners'\
                      %(game.round.valid_act, len(game.dealer.deck), len(game.round.winners))
            save_result(changshu, content)   
            content = 'The last action is: %s' %action
            save_result(changshu, content)
        else:
            content = 'Check why the game is not over :-('
            save_result(changshu, content)
            print(content)

        content = 'The winners are in: %s' %([p.player_id for p in game.players if p.winning])
        save_result(changshu, content)

        content = 'There are %s state changes' %(num_state_change)
        save_result(changshu, content)

        if len(game.dealer.deck) == 0 and len(game.round.winners) < 3: 
            score.update_finalScore(game.dealer, game.players)            

        content = 'The hu_way of four players are: %s' %([p.hu_way for p in game.players])
        save_result(changshu, content)

        content = 'The scores of four players are: %s' %([p.myscore for p in game.players])
        print(content)
        save_result(changshu, content)
        save_result(summary, content)

        score_result = []            
        for p in game.players:
            score_result.append(p.myscore)

        game_record.append(game.dealer.act_history)        
        game_record.append([p.myscore for p in game.players])
        save_result('GameRecord'+'_'+ str(changshu) + '_', game_record)

        '''Record the final state and scores '''    
        for player in game.players:
            content = 'Player %s scoreRecords: %s' %(player.player_id, player.scoreRecords)
            save_result(changshu, content)
            content = 'Player %s kongRecords: %s' %(player.player_id, player.kongScore)
            save_result(changshu, content)
        for p in game.round.winners:
            p.hand.sort(key=lambda t: t[0:2])
            content = 'Player %s: Hand %s' %(p.player_id, p.hand)
            save_result(changshu, content)
            content = 'Player %s: Pile %s' %(p.player_id, p.pile)
            save_result(changshu, content)
        content = 'Weihupai Player' 
        save_result(changshu, content)
        for p in game.players:
            if p.winning == False:
                p.hand.sort(key=lambda t: t[0:2])
                content = 'Player %s: Hand %s' %(p.player_id, p.hand)
                save_result(changshu, content)
                content = 'Player %s: Pile %s' %(p.player_id, p.pile)
                save_result(changshu, content)
                    
        save_result(changshu, game.dealer.act_history)
        save_result(summary, content)
                                
    end = time.time()  
    save_result(summary, content)
    print('The game ends in %s seconds' %(round(end-start)))
