''' Generate, Load, and Compare on, a batch of games '''
import numpy as np
# from copy import deepcopy
import json
import os

from xzdealer import MahjongDealer as Dealer
from xzplayer import MahjongPlayer as Player
from xzround import MahjongRound as Round
from xzjudger import MahjongJudger as Judger


class MahjongGame(object):

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
        ''' Get the next state
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

import datetime
format_date = datetime.date.today()
format_date = format_date.isoformat()

def save_result(name, content):
    name = str(name)
    content = str(content)

    file = open("testRecord/game-1000" + name + ".txt", mode = 'a')
    file.write(content)
    file.write('\n')
    file.close()
    

path = "Ini_Games/" 
files= os.listdir(path)

# For test
if __name__ == '__main__': 
    np.random.seed() #q what's this for?
    game = MahjongGame()
    n_GAME = 2000 # number of changs
    Games = [[]]*n_GAME

    ''' Load a batch of initial games '''
    file_name = 'game_batch_0312_2000' + '.txt'
    current_path = 'Ini_Games/' + file_name
    


    for i in range(n_GAME):       
        state, button = game.init_game(1) #sl button = current_player
        ''' Start a new game and fix the hands and the Wall! '''
 
        H0 = game.players[0].hand[:]
        H1 = game.players[1].hand[:]
        H2 = game.players[2].hand[:]
        H3 = game.players[3].hand[:]
        W = game.dealer.deck[:]

        Games[i] = [H0, H1, H2, H3, W]
        with open(current_path, 'w') as f:
            f.write(json.dumps(Games))
