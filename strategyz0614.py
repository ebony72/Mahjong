#Revised on June 14, 2020
#-- revised check_hu
#Revised on June 2, 2020
#-- removed n_hu from all check_xxx as it can be obtained from dealer.n_hu()
#Revised on June 4, 2020
#-- Fixed a problem with 'haha, something is wrong ...'
#-- Deleted Pg from the parameters of discard(..)
#-- in check_zikong(..), removed two 'if Q or [..]' 
#Revised on June 7, 2020
#-- introduce DQC in discard_local_value(..,DQC) and discar_value(..,DQC)

import hytreekong as hk
#import hytreekong19 as hkx
from copy import deepcopy
import utils.hutype as hutype
import utils.xzscore as score
import utils.hysolx as hs
import utils.pusolx as ps
from utils.xzutils import *
#introduced discard_local_value to speed up by focusing on a local hand whenver possible
#q: question
#todo: future improve

Oracle = False #change to True if we want to use the oracle of Phi
HU_DECLINE_THRESHOLD = 1 #check_hu declines a dianpao win when zimo_factor
                         #exceeds this; 1 is the original behavior (variants
                         #may lower it — see strategy_huev.py)

'''The player uses this strtegy to decide whether to hu/
   pong/kong/robkong/zimo and which card to discard
   //The strategyza/b/c... versions are old different versions of strategyz
'''
base_score = 1
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

def wgt_minor_list(rnumWl, length_minor_list):
    ''' Weight for minor list (to multiply with the discard value of the color of the minor list)
        WGT[r][l] = s denotes that if rnumWl is close to r and the length of minor list is l,
            then the minor list factor is s. 
        Args:
            rnumWl (float):
            length_minor_list (int): from 0 to 5
        Return:
            (int): >= 1 (the larger the more important)
    '''
    #20200607-sl
    WGT = [[]]*16
    WGT[0]  = [1]*6
    WGT[1]  = [3, 3, 1, 1, 1, 1]
    WGT[2]  = [3, 3, 1, 1, 1, 1]
    WGT[3]  = [3, 3, 1.5, 1, 1, 1]
    WGT[4]  = [3, 3, 2, 1.5, 1, 1]
    WGT[5]  = [3, 3, 2, 1.5, 1, 1]
    WGT[6]  = [3.5, 3.5, 2.5, 1.5, 1, 1]
    WGT[7]  = [3.5, 3.5, 2.5, 1.5, 1, 1]
    WGT[8]  = [4, 4, 3, 2, 1, 1]
    WGT[9]  = [4, 4, 3,  2, 1, 1]
    WGT[10] = [4, 4, 3, 2, 1.5, 1]
    WGT[11] = [4, 4, 3, 2, 1.5, 1]
    WGT[12] = [5, 5, 4, 3, 2, 1]
    WGT[13] = [5, 5, 4, 3, 2, 1.5]
    WGT[14] = [6, 6, 5, 3, 2, 1.5]
    WGT[15] = [6, 6, 5, 3, 2, 1.5]

    r = int(round(min(rnumWl, 15)))
    l = min(length_minor_list, 5) 
    wgt = WGT[r][l]
    return wgt

def f_color(KB, Phi):
    ''' The ratio of non-showing color c tiles not in the Wall
        Args:
            KB (list): the knowledge base
            Phi (list): Phi[i] is the distribution of tiles of colors in the hand of the other players which *I believe*
        Return:
            list
    '''
    f = [0]*3 #f[c] denotes the ratio of color c tile being not in the Wall to all non-showing color c tiles
    for c in range(0, 3):
        n_c = num_kb(KB, c) #number of color c tiles in KB
        ''' 1-(f[c])^kb[x] is the chance of x in the Wall if x[0] == c
            Phi[i][c] denotes the number of tiles with color c in the hand of Player i
        '''
        X = list(Phi[i][c] for i in range(0,4))
        ''' It is possible sum(X) > n_c and/or n_c = 0. In this case, we set f[c] as 1 '''
        f[c] = min(sum(X) / max(n_c, 1), 1) 
    return f

#20200608-sl
def surpress_minor_list(T, KB, c, dc, cur_dfncy, rnumWl, DQC):
    #define cx as the minor color
    for x in range(0,3):
        if x ==c or x==dc:
            continue
        cx = x
        break
    minor_list = list(t for t in T if t[0] == cx) #as t1 and t2 exist, minor_list cannot be empty
    ''' number of players whose daque color is c '''
    num = DQC.count(c) #//todo: need to consider winners' discard color
    wgt = wgt_minor_list(rnumWl, len(minor_list))
    if wgt > 1:
        wgt = (1+num/5) * wgt
    ''' When to suppress minor list wgt: '''
    if (rnumWl < cur_dfncy + 2 and len(minor_list) > 2) or len(minor_list) > 5 or \
       numPair(minor_list) == 2 or [t for t in minor_list if T.count(t) > 2 and KB[kbf(t)] > 0] or \
       (len(minor_list) >= 4 and ps.numS(T, KB, cx)):
        wgt = 1
        return True, wgt
    return False, wgt

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\        
def discard_value(T, Pg, t, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC):
    # we include cur_dfncy here to avoid redundant computations in discard
    ''' The value of t as the tile to discard //used after drawing a tile or pong 
        Achtung! Note here T+Pg*3 is a 14-tile and t is a tile in the hand.
        Args: 
            T (list):  list of mahjong tiles in the player's hand, which contains no tile [dc,j]
            Pg (list): list of ponged tiles with form  [[c1,n1], ...,[ck,nk]]
            KB (list): knowledge base with form [num(t) for t in MJ()]
            t (list): a candidate mahjong tile in T to be discarded
            dc (int): the discard (daque) color of the player
            cur_dfncy (int): the hyval of the current hand
            numWl (int): the number of tiles in the Wall
            n_hu (int): the number of winners
            Phi (list): the collection of distributions of the players
        Return:
            w (float): value (the higher the better, smaller than zero is possible)
    '''
    ''' rnumWl indicts the average time we have to draw a tile before the game is over '''
    rnumWl = numWl/(4-n_hu)

    '''kbf(t) returns the index of t in MJ(), i.e., the number of non-showing t in the game'''
    p0 = kbf(t)

    ''' At this stage, we have decided not to kong/pong/hu. Nevertheless, we have no reason to break a kong/pong'''
    ''' If cur_dfncy is 0, we should have declared 'zimo': recall we always take zimo '''

    if t in Pg or T.count(t) == 4: #kong tile
        val = -2*round(max(int(rnumWl-3), 0), 2)
        '''This seems not necessary as t has been excluded from the disc_list'''
        return val 
    if T.count(t) == 3 and KB[p0] == 1: #potential kong tile
        val = - round(max(int(rnumWl-2), 0), 2) 
        return val
    
    f = f_color(KB, Phi)[:] #f[0] denotes the (guessed) ratio of non-showing Bamboo tiles not in the Wall    
    w = 0
    Tiles_Matter = list(x for x in MJ() if x[0] != dc and KB[kbf(x)] > 0) # or x[0]!=dc? which is better?

    ''' Here we examine ALL tiles which do not make the hyval of T worse when replacing with t
        // We don't consider daque color tiles as they play the same role for all t in NQHand '''
    for x in Tiles_Matter:
        p = kbf(x)
        if x == t:
            continue            # we cannot decrease hyval with x == t
        T1 = xreplace(T, t, x)
        x_dfncy = hk.hyval(T1, Pg, KB, dc) #this is an expensive computation
        ''' Note by the definition of hyval T1 should contain no daque tile [dc, j] '''
        delta = cur_dfncy - x_dfncy
        if delta <= 0:
            continue
        chance_of_x_in_the_Wall = 1- min(pow(f[x[0]], KB[p]), 1)
        w0 = delta * chance_of_x_in_the_Wall / max(numWl, 1) #//compare
        w += w0
        #print(t, x, delta, 'single', KB[p], 'f(x) = ', round(f[x[0]], 3), numWl, 'w0 = ', round(w0,3), '::', 'w = ', round(w,3))    

        ''' Further consider the chance of pong x // here we consider all pairs in T '''
        if T.count(x) < 2:
            continue
        ''' Compute the chance of pong x  '''
        NNH = T[:]
        NNH.remove(t)
        NNH.remove(x)
        NNH.remove(x)
        NPg = Pg[:]
        NPg.append(x)
        after_pong_dfncy = hk.hyval(NNH, NPg, KB, dc)
        n_c = num_kb(KB, x[0]) #number of color x[0] in KB
        delta = cur_dfncy - after_pong_dfncy
        if delta < 0:
            continue
        '''Phi[i][x[0]] denotes the number of tiles with color x[0] in Player i's hand '''
        '''Phi[i][x[0]]/n_c denotes the ratio af non-showing color x[0] tile in Player i's hand to the number of all non-showing x[0] tiles'''
        ''' prob[i] = 1- pow( 1 - Phi[i][x[0]]/n_c,  KB[p]) denotes the chance of x in Player i's hand'''
        ''' Phi[i]=[0,0,0] if i is the current player'''
        #20200606-sl: the chance of pong x revised
        prob = [0]*4
        pong_val = [0]*4 #the pong value of x w.r.t. each player (0 for the current player and prob[i]*(prob of Player i discaring x)  
        for i in range(0,4):
            s = sum(Phi[i]) #an approximation of (may be different from) the numebr of tiles in the hand of Player i
            if not s: #i is the current player
                continue
            if not Phi[i][x[0]]: # Player i has no color x[0] tiles
                continue
            '''prob[i] is the chance that x appears in Player i's hand'''
            prob[i] = 1- pow( 1 - min(Phi[i][x[0]]/max(n_c, 1), 1),  KB[p])
            if DQC[i] == x[0]: #Player i daque x[0]
                pong_val[i] = prob[i]/Phi[i][x[0]]
            else:
                pong_val[i] = prob[i]/s
        w0 = sum(pong_val) #the chance of pong x
        ''' The pong value seems quite big if we set w0 as above. Maybe halve it? '''
        w += w0 * (cur_dfncy/10 + delta)  # We may havle w0 as it seems much larger than the discard value of a single tile
    return w

#2020030815-sl: compare tiles within the same color 
def discard_local_value(T, Pg, t, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC):
    # we include cur_dfncy here to avoid redundant computations in vec1
    ''' The value of t as the tile to discard //used after drawing a tile or pong 
        Achtung! Note here T+Pg*3 is a 14-tile and t is a tile in the hand.
        Args: 
            T (list):  list of mahjong tiles, which contains no tile [dc,j]
            Pg (list): list of ponged tiles with form  [[c1,n1], ...,[ck,nk]]
            KB (list): knowledge base with form [4]*27
            t (list): a candidate mahjong tile in T to be discarded
            dc (int): the discard (daque) color of the player
            cur_dfncy (int): the hyval if computed
            numWl (int): the number of tiles in the Wall
            n_hu (int): the number of winners
            Phi (list): the collection of distributions of the players
        Return:
            w (float): value (the higher the better)
    '''
    '''//todo: determine if t is a dangerous card? e.g., if KB[kbf(t)] == 3 and numWl < 15?
        or when t was ponged by another player and he may needs t to complete his hand'''
    
    ''' If cur_dfncy is 0, we should have declared 'zimo': recall we always take zimo. But we should also consider the after_pong case!!'''
    ''' rnumWl indicts the average time we have to draw a tile before the game is over '''
    rnumWl = numWl/(4-n_hu)
    '''kbf(t) returns the index of t in MJ(), i.e., the number of non-showing t in the game'''
    p0 = kbf(t)

    '''First consider if t is a kong tile //todo: when rnumWl < 3, we could discard a kong tile if necessary'''
    if t in Pg or T.count(t) == 4: 
        val = -2*round(max(int(rnumWl-3), 0), 2)
        '''This seems not necessary as t has been excluded from the disc_list'''
        return val     
    if T.count(t) == 3 and KB[p0] == 1: 
        val = - round(max(int(rnumWl-2), 0), 2) 
        return val
    #if the local hand is complete, we don't discard t unless it is a non-surpressed minor list
    Local_is_complete = ps.is_solx([x[1] for x in T if x[0] == t[0]])
    if Local_is_complete:
        return -1

    f = f_color(KB, Phi)[:]
    w = 0
    #To compare tiles with the same color, we only consider how the deficiency is changed if we draw another tile with the same color
    Tiles_Matter = list(x for x in MJ() if x[0] == t[0] and KB[kbf(x)] > 0)
        
    ''' We examine only tiles with the same color as t which do not make the hyval of T worse when replacing with t
        // We don't consider other color tiles as they play the same role for all t in NQHand '''
    for x in Tiles_Matter:
        p = kbf(x)
        if x == t:
            continue
        # we cannot decrease hyval with x == t
        T1 = xreplace(T, t, x)
        x_dfncy = hk.hyval(T1, Pg, KB, dc) #this is the most expensive computation
        ''' Note by the definition of hyval T1 should contain no daque tile [dc, j] '''
        delta = cur_dfncy - x_dfncy
        if delta <= 0:
            continue
        chance_of_x_in_the_Wall = 1- min(pow(f[x[0]], KB[p]), 1)
        w0 = delta * chance_of_x_in_the_Wall / max(numWl, 1) #//compare
        w += w0
        #print(t, x, cur_dfncy, x_dfncy, 'single', KB[p], 'f(x) = ', round(f[x[0]], 3), numWl, 'w0 = ', round(w0,3), '::', 'w = ', round(w,3))

##    T1 = T[:]
##    T1.remove(t)
##    if ps.is_solx([x[1] for x in T1 if x[0] == t[0]]): # Here we shall already have not Local_is_complete
##        w += 0.1 #20200321-sl: replaced 0.01 by 0.1
##        return w
                
    ''' Further consider the chance of pong t '''
    if T.count(t) == 2 and KB[p0] > 0:
        ''' Compute the chance of pong t. It's value should be negated as we don't want to discard a potential pong tile!'''
        NNH = T[:]
        NNH.remove(t)
        NNH.remove(t)
        NPg = Pg[:]
        NPg.append(t)
        after_pong_dfncy = hk.hyval(NNH, NPg, KB, dc)
        n_c = num_kb(KB, t[0]) #number of color t[0] in KB
        delta = cur_dfncy - after_pong_dfncy
        if delta >= 0:
            prob = [0]*4 #prob[i] is the probability that Player i has an identical tile t
            pong_val = [0]*4 #the pong value of x w.r.t. each player (0 for the current player and prob[i]*(prob of Player i discaring x)  
            for i in range(0,4):
                s = sum(Phi[i])
                if not s: #i is the current player
                    continue
                if not Phi[i][t[0]]: # Player i has no color x[0] tiles
                    continue
                prob[i] = 1- pow( 1 - min(Phi[i][t[0]]/max(n_c, 1), 1),  KB[p0]) #the probability if t appearing in Player i's hand
                if DQC[i] == t[0]:
                    pong_val[i] = prob[i]/Phi[i][t[0]]
                else:
                    pong_val[i] = prob[i]/s
            w0 = sum(pong_val)       
            ''' The pong value seems quite big if we set w0 as above. Maybe halve it? '''
            '''Note here the sign is minus as the smaller the less likely we discard t!'''
            w += -w0 * (cur_dfncy/10 + delta)  # We may havle w0 as it seems much larger than the discard value of a single tile
            #print(t, x, delta, 'double', KB[p], '::', numWl, '::', round(w0,3), round(w,3))
    return w

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
                
def further_choose(T, vec, KB):
    ''' If there are multiple tiles with the best extended discard value,
            select one which appears in the minor suite of T or the one that appears the fewest times
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l // T cannot have daque tile
            vec (list): the output of vec1
            KB (list): knowledge base with form [4]*27
        Return:
            t (tile): the mahjong tile to discard (could be None if vec is empty)
    '''
                  
    ''' The sublist of tiles with the highest discard value '''
    Candidates = list(x[1] for x in vec if x[0] == vec[0][0])
    if not Candidates:
        return None
    Cand_sing = list(x for x in Candidates if T.count(x) == 1)
    
    '''If there are more single tiles in T with the highest value, select the most isolated one to discard'''
    if len(Cand_sing) >= 1:
        vec_cand_sing = list([x, tile_distance(T, x)] for x in Cand_sing)
        ''' \\todo: Consider the case like T = [6, 8, 8, 9] + ...
                    Define a better tile_distance?  '''
        vec_cand_sing.sort(key=lambda t: t[1], reverse=True)
        selected_tile = vec_cand_sing[0][0]
        #print('The selected single tile is %s' %selected_tile)
        return selected_tile

    #2020021923-sl
    ''' Prefer to discard tiles with small multiplicity  '''    
    Cand_wgt = list([x, T.count(x)] for x in Candidates)
    Cand_wgt.sort(key=lambda t: t[1])
    ''' Prefer to discard tiles which cannot make a pong or kong '''
    New_Cand = list([y[0], KB[kbf(y[0])]] for y in Cand_wgt if y[1] == Cand_wgt[0][1])
    New_Cand.sort(key=lambda t: t[1])
    if not New_Cand:
        print(Cand_wgt, Candidates)
        print(T)
        print(KB)
    selected_tile = New_Cand[0][0]
    #print('The selected double or triple tile is %s' %selected_tile)
    return selected_tile   

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def discard(T, Pile, KB, c, dc, numWl, n_hu, Phi, DQC):
    ''' The discard value list
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l // T has no daque tile
            Pg (list): list of ponged tiles with form  [[c1,n1], ...,[ck,nk]]
            KB (list): knowledge base with form [4]*27
            c (int): the dominant color (maybe None)
            dc (int): the discard (daque) color of the player
            numWl (int): the number of tiles in the Wall
            n_hu (int): the number of winners
            DQC (list): the daque color of the players
        Return:
            (list): a tile to discard
    '''
    Pg = list(t[0] for t in Pile) #20200604-sl
    rnumWl = numWl/(4-n_hu)
    cur_dfncy = hk.hyval(T, Pg, KB, dc)
    #test
    #cur_dfncyx = hkx.hyval(T, Pg, KB, dc)
    #if cur_dfncy != cur_dfncyx:
        #print('T = %s\n Pg = %s\n KB = %s\n dc = %s' %(T, Pg, KB, dc))
        #print(cur_dfncy, cur_dfncyx)   

    f = f_color(KB, Phi)[:]

    '''Establish a discard list'''
    TR = remove_duplicates(T)
    TR.sort(key=lambda t: t[0:2])
    disc_list = TR[:] #tiles that can be discarded
    ''' A tile x is essential if it is a kong tile or, if dfncy is increased after removing it '''
    ''' Don't remove essential tiles with the minor color'''
    for  x in TR:
        if T.count(x) == 4 or x in Pg:       
            disc_list.remove(x)   # We don't discard a kong tile
    disc_listX = disc_list[:]    
    for x in disc_list:
        TX = T[:]
        TX.remove(x)
        if x[0] == c or c == None: # x is not in the minor list if exists 
            new_dfncy = hk.hyval(TX, Pg, KB, dc)
            if new_dfncy > cur_dfncy: #x is essential in T
                    disc_listX.remove(x) #should not discard
    if disc_listX:
        disc_list = disc_listX[:]
    #else:
        #if cur_dfncy:
            #print('Haha, all tiles are essential:\n T = %s \n Pg = %s \n KB = %s ' %(T,Pg,KB))
    #end establishing the discard list
        
    c1 = (dc + 1)%3
    c2 = (dc + 2)%3

    ''' Generte a vector vec of (discard_value, tile) pair [value, tile]'''
    vec = []
    ''' Special Case I '''
    ''' To avoid cha-da-jiao, we need keep T even theoretically ready if rnumWl is small! 
        // For example, the hand will be completed only by [0, 8], which, however, was konged before.'''
    if cur_dfncy > 1 and rnumWl < 3:
        for t in disc_list:
            w = 0
            for x in MJ(): # x==t is possible
                if x[0] == dc:
                    continue
                T1 = xreplace(T, t, x) 
                if hs.is_h_solx(T1, dc): #T1 is theoretically complete and could be used to decide its reward when the game is over 
                     utl = score.compute_handScore(T1, Pile)
                     w = max(w, utl)
            if w > 0:
                vec.append([round(w, 4), t])
        vec.sort(key=lambda t: t[0], reverse = True)
        ''' If vec is nonempty, we should discard vec[0][1]? ''' 
        if vec:
            print('We can only have a theoretical ready hand.') 
            return vec[0][1]
        '''The case when vec is empty is deferred to the end.'''
      
    '''if vec is empty, this is because cur_dfncy <= 1 or rnumWl >= 3 or (cur_dfncy > 1 and rnumWl < 3 and T is not theoretically ready)'''
    
    ''' Special Case II '''
    ''' Consider the special case when T is ready! // The current T is possibly resulted from a pong and T was ready before pong'''
    '''//If the player can hu but decide to pong and now needs to discard a tile, he aims to zimo or zikong or peng-peng-hu
        // As will be implemented in the main function, the following do not discuss 'qing-yi-se' for ready hand!'''

    #20200608-sl
    '''Consider the special case when cur_dfncy == 0. This is the case when the player just ponged and wants to zimo!'''
    #An example 
    #T = [[1,1],[1,1],[2,1],[2,2],[2,3],[2,4],[2,5],[2,6],[2,7],[2,8],[2,9]]
    #Pg = [[2,7]]
    #dc = 0
    #KB = [4,0,0,2,3,2,3,2,3,1,2,4,1,3,4,2,2,1,0,1,2,2,1,3,0,1,0]

    TZ = disc_list[:]
    if cur_dfncy == 0:
        TZ = TR[:]                
    if cur_dfncy <= 1:
        #200613-sl: replaced #0 with #1
        Tiles_Matterx = list(x for x in MJ() if x[0] != dc) #1
        #Tiles_Matterx = list(x for x in MJ() if x[0] != dc and KB[kbf(x)] > 0) #0
        # examine all available tiles which could increase the hyval of T when replacing t
        for t in TZ:
            w = 0
            for x in Tiles_Matterx: # x==t is possible, theoretical solutions
                p = kbf(x) #MJ().index(x)
                T1 = xreplace(T, t, x) 
                if hs.is_h_solx(T1, dc):
                    ''' Note 1- pow(f[x[0]], KB[p]) is the chance of x in the Wall.
                            The chance of drawing it in the next round depends on how many copies if x we have '''
                    utl = score.compute_handScore(T1, Pile)
                    w0 = 0.0001 + (1- min(pow(f[x[0]], KB[p]), 1)) / max(numWl, 1) # // compare
                    w += w0*utl
            if w > 0:
                vec.append([round(w, 4), t])
        vec.sort(key=lambda t: t[0], reverse = True)
        #print('Type II: cur_dfncy = %s :: vec = %s' %(cur_dfncy, vec))
        #if not vec:
            #@game2vs2-0608-oracle-709.txt
            #The player draws [0, 9] and discards [0, 1]
            #numWl = 0
            #T = [[0, 1], [0, 2], [0, 3], [0, 4], [0, 9]] 
            #Pg = [[0, 9], [1, 5], [1, 1]] 
            #KB = [2, 1, 3, 3, 3, 4, 1, 4, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] 
            #print('Hmm, something went wrong with %s %s %s ' %(T, t, cur_dfncy)) #<This is possible!>
            
    ''' We consider the two local hands separately '''
    if vec:
        B1 = list(x for x in vec if x[1][0] == c1)
        B2 = list(x for x in vec if x[1][0] == c2)
    else:
        '''If vec is empty, then cur_dfncy > 1, and rnumWl >= 3 or (rnumWl < 3 but T is not theoretically ready)'''        
        ''' discard-value vector for tiles with color c1 '''
        B1 = list( [round(discard_local_value(T, Pg, t, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC), 3), t] for t in disc_list if t[0] == c1 )
        ''' discard-value vector for tiles with color c2 '''
        B2 = list( [round(discard_local_value(T, Pg, t, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC), 3), t] for t in disc_list if t[0] == c2 )    
    B1.sort(key=lambda t: t[0], reverse = True)    
    B2.sort(key=lambda t: t[0], reverse = True)
    
    ''' Select one tile for each subsuite '''
    t1 = further_choose(T, B1, KB)
    t2 = further_choose(T, B2, KB)
    if t1 == None and t2 == None:
        print('B1=%s, B2=%s cannot be both empty!' %s(B1,B2))
        return None
    if t1 == None:
        return t2
    if t2 == None:
        return t1
    val1 = discard_value(T, Pg, t1, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC)
    val2 = discard_value(T, Pg, t2, KB, dc, cur_dfncy, numWl, n_hu, Phi, DQC)
   
    ''' Compare the two tiles according to their discard values defined by discard_value. Using xval is 13x slow.'''        

    ''' Take minor-list-weight into consideration and update val1 or val2 accordingly'''
    ''' // If the shorter sublist is complete and has less than 4 tiles, this will be discussed in the main function '''
    if c!= None:
        SUP, wgt = surpress_minor_list(T, KB, c, dc, cur_dfncy, rnumWl, DQC)
        if c == c2: #c2 is the dominant color 
            val1 = val1*wgt
        else:
            val2 = val2*wgt            
                        
    ''' Compare the two tiles'''
    if val1 > val2:
        return t1
    if val1 == val2:
        if isolated_tile(T, t1):
            return t1
        if isolated_tile(T, t2):
            return t2
        if c2 == c: #c2 is the dominant color
            return t1
        return t2
    return t2


def Discard_Q_tile(Q, dc, Table, PgOther):
    ''' Select a tile from Q to discard
        Arg:
            Q (list): the list of tiles with the daque color, could be empty
            dc (int): the discard (daque) color of the player
           Table (list): the list of tiles on the table
            PgOther (list): the list of ponged tiles by other players 
        Return:
            (list): a tile            
    '''
    if len(Q) == 1:
        x = Q[0]
        return [dc, x]
    Q.sort()
    tab = len(Table)
    s = min(tab, 4)
    '''Consider at most the last four tiles on the table'''
    for tile in PgOther: # if tile was ponged by other player, we discard it first
        if tile[1] in Q and tile[0] == dc:
            return tile
    for tile in Table[-1:-s:-1]:  
        if tile[0] == dc and tile[1] in Q:
            return tile
    for x in Q:
        if Q.count(x) > 1:
            return [dc, x]

    s = min(list(max(x-5, 5-x) for x in Q)) #otherwise, return the most central tile
    for x in Q:
        if max(x-5, 5-x) == s:
            return [dc, x]
    return [dc, Q[-1]]

def Discard_minor_tile(T, minor_list, cx, Pg, KB, dc, Table, PgOther):
    ''' Select a tile from Q to discard
        Arg:
            minor_list (list): the list of tiles with the minor color, could be empty
            cx (int): the current minor color of the player
           Table (list): the list of tiles on the table
            PgOther (list): the list of ponged tiles by other players 
        Return:
            (list): a tile            
    '''
    M = minor_list[:]
    MR = remove_duplicates(M)
    if len(MR) == 1:
        x = MR[0]
        return x
    M.sort()
    Tiles_Matter = list(x for x in MJ() if x[0] == cx)
    '''If M is complete ...'''
    vec = []
    if ps.is_solx([x[1] for x in M]):
        for t in MR:
            w = 0
            for x in Tiles_Matter:
                p = kbf(x) #MJ().index(x)
                M1 = xreplace(M, t, x) 
                if ps.is_solx([z[1] for z in M1]):
                    w += KB[p]
            if w > 0:
                vec.append([w, t])
        vec.sort(key=lambda t: t[0], reverse = True)
        return vec[0][1]
    '''If M is not complete ...'''
    cur_dfncy = hk.hyval(T, Pg, KB, dc)
    disc_list = MR[:]
    '''Remove the essential tiles from disc_list'''
    for t in MR:
        T1 = T[:]
        T1.remove(t)
        x_dfncy = hk.hyval(T1, Pg, KB, dc)
        if x_dfncy > cur_dfncy:
            disc_list.remove(t)
    '''Every tile in MR is essential?'''                 
    if not disc_list:
        #print('This seems impossible! %s :: %s' %(T,M))
        #Indeed, it is possible:
        # T = [[0, 5], [0, 6], [1, 2], [1, 3], [1, 5], [1, 5], [1, 6], [1, 9]]
        # Pg =  [[1, 8], [1, 1]] 

        # KB = [0, 3, 2, 4, 2, 3, 0, 4, 0, 1, 2, 3, 2, 2, 0, 1, 1, 2, 3, 2, 3, 3, 0, 2, 1, 1, 1]

        s = max(list(max(t[1]-5, 5-t[1]) for t in MR)) #otherwise, return the least central tile
        for t in MR:
            if max(t[1]-5, 5-t[1]) == s:
                return t        
    vec = []
    for t in disc_list:
        w = 0
        for x in Tiles_Matter:
            p = kbf(x)
            if x == t:
                continue            # we cannot decrease hyval with x == t
            T1 = xreplace(T, t, x)
            x_dfncy = hk.hyval(T1, Pg, KB, dc) #this is an expensive computation
            ''' Note by the definition of hyval T1 should contain no daque tile [dc, j] '''
            delta = cur_dfncy - x_dfncy
            if delta <= 0:
                continue
            w += KB[p]
        if w > 0:
            vec.append([w,t])
    if vec:
        vec.sort(key=lambda t: t[0], reverse = True)
        return vec[0][1]
    
    s = max(list(max(t[1]-5, 5-t[1]) for t in MR)) #otherwise, return the least central tile
    for t in MR:
        if max(t[1]-5, 5-t[1]) == s:
            return t         
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
#Main discard function
def select_a_card_to_discard(player, dealer, players):
    ''' Decide which tile to discard when the player draws or pong a tile
    Args:
        player (object)
        dealer (object): Dealer
        players (list of players)
    '''
    ''' The player needs to discard after drawing or pong:
        if 'zimo' then the player will declare win and discard;
        if he can hu & pong/kong but decides to pong, then we shoudl take care '''
    n_hu = dealer.n_hu()
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand) #the hand
    T.sort(key=lambda t: t[0:2])
    '''It's the player's turn to discard and hence len(T) %3 ==2 '''
    dc = player.daque_color
    PgOther = []
    for playerx in players:
        if playerx.player_id == player.player_id:
            continue
        for p in playerx.pile:
            PgOther.append(p[0])
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#            
    Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color    
    if Q:
        ''' If the daque color suit is nonempty, select one to discard. ''' 
        discard_tile = Discard_Q_tile(Q, dc, Table, PgOther)            
        return discard_tile
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#

    Pg = [p[0] for p in player.pile]
    KB = player.kgbase(dealer, players)
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)
    #the daque color list of the players   
    DQC = dealer.dqc
    c = player.get_dominant_color()
    
    ''' Guess color distribution and use this to select the discard tile '''
    Phi = [[]]*4
    GPhi = [[]]*4
    for j in range(4):
        if j == player.player_id:
            Phi[j] = [0, 0, 0] #ignore the current player himself
            GPhi[j] = [0, 0, 0] #ignore the current player himself
        else:
            X = dealer.guess_color_distribution(j)
            Phi[j] = X[:] #1 
            #genuine color distribution (this is an ideal assumption, can only be used as an oracle and for comparison with our guess)  
            Tj = players[j].hand[:]
            GX = [len([t for t in Tj if t[0] == c]) for c in range(0,3)]
            GPhi[j] = GX[:] #2
            #end of genuine color distribution
    #print(Phi)
    #print(GPhi)
    #DIFF = list(abs(GPhi[i][j] - Phi[i][j]) for i in range(0,4) for j in range(0,3))
    #print(round(sum(DIFF),2))
    '''If we want to use the oracle, we need to uncomment the following statement.'''
    if Oracle: #a Boolean introduced in xzgame.py
        Phi = GPhi[:] 
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
    #<><><><><><><><><><><SOME SPECIAL CASES><><><><><><><><><><><><><><><><>#
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#    
    '''Test if 'qing-yi-se' is possible '''    
    if player.get_pure_color_index() >= 11:
        #define cx as the minor color
        for x in range(0,3):
            if x == c or x == dc:
                continue
            cx = x
            break
        minor_list = list(t for t in T if t[0] == cx)
        MLR = remove_duplicates(minor_list)
        ''' number of players whose daque color is c '''
        num = DQC.count(c) #//todo: need to consider winners' discard color            
        wgt = wgt_minor_list(rnumWl, len(minor_list))
        if wgt > 1:           
            wgt = (1+num/5) * wgt  # replaced 2 with 5
        cur_dfncy = hk.hyval(T, Pg, KB, dc)
        ''' Consider the special case //even if the minor list consists of a pair, we still discard '''
        '''If the minor list is a meld or wgt < 2, we don't think qing-yi-se is worth trying'''
        if wgt >= 2 and MLR and not ( ps.is_solx([t[1] for t in minor_list]) and len(minor_list) == 3 and wgt < 3 ):
            discard_tile = Discard_minor_tile(T, minor_list, cx, Pg, KB, dc, Table, PgOther)
            return discard_tile
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#                
    ''' Test 7-pair '''
    if numPair(T) == 6:
        TR = remove_duplicates(T)
        X4 = list(x for x in TR if T.count(x) == 4)
        X1 = list(x for x in TR if T.count(x) == 1)
        X3 = list(x for x in TR if T.count(x) == 3)
        if X3 and rnumWl <= 2: #expect chajiao, X3 must have zero or two tiles
            if not X4 and not X1:
                p = X3[0]
                q = X3[1]
                if KB[kbf(p)] >= KB[kbf(q)]:
                    #print('7-pair-v1 // Discard %s' %q)
                    return q
                #print('7-pair-v1 // Discard %s' %p)
                return p
            if X1:
                #print('7-pair-v1x // Discard %s' %(X1[0]))
                return X1[0]
        if X3 and X1:
            p = X3[0]
            q = X1[0]
            if KB[kbf(q)] <= KB[kbf(p)]:
                #print('7-pair-v2 // Discard %s' %q)
                return q
            #print('7-pair-v2 // Discard %s' %p)
            return p
        if not X3:
            p = X1[0]
            q = X1[1]
            if KB[kbf(p)] >= KB[kbf(q)]:
                #print('7-pair-v3 // Discard %s' %q)
                return q
            #print('7-pair-v3 // Discard %s' %p)
            return p
    if numPair(T) == 5 and rnumWl > 5 and not Pg:
        TR = remove_duplicates(T)
        X1R = list([x, KB[kbf(x)]] for x in TR if T.count(x) == 1)
        X1R.sort(key=lambda t: t[1])
        discard_tile = X1R[0][0]
        #print('7-pair-v4 // Discard %s' %discard_tile)
        return discard_tile

    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
    if c == None or player.get_pure_color_index() < 12: #//todo: check if this is necessary, qys is possible
        ''' Check if 'pong-pong-hu' is nearly ready:
            If the hand contains 3 triples + 2 pairs + 1 single, discard the single tile '''
        M = remove_duplicates(T)
        M4 = [x for x in M if T.count(x) == 4]
        M3 = [x for x in M if T.count(x) == 3]
        M2 = [x for x in M if T.count(x) == 2]
        M1 = [x for x in M if T.count(x) == 1]
        if not M4 and len(M1) == 1 and len(M3)+len(Pg) == 3 and len(M2) == 2\
           and (KB[kbf(M2[0])]+KB[kbf(M2[1])] > 0 or rnumWl <= 2): #case-pph-1
            discard_tile = M1[0]
            ''' Ready for pong-pong-hu-type-a // only when still have chance to complete or Wall near empty '''
            #print('pong-pong-hu-a// Discard %s' %discard_tile)
            return discard_tile
        if len(M3)+len(Pg) == 4: #case-pph-2
            ''' Ready for pong-pong-hu-type-b // If M0 contains two identical tiles t, then the hand was already complete.
                This happens only when the player ponged and M3 is empty!b'''
            M0 = [x for x in T if x not in M3] #M0 contains two (maybe duplicate) tiles
            p = M0[0]
            q = M0[1]
            if KB[kbf(p)] <= KB[kbf(q)]:
                #print('pong-pong-hu-b //Jin-gou-diao? Discard %s' %p)
                return p
            #print('pong-pong-hu-b //Jin-gou-diao? Discard %s' %q)
            return q
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
    # The special case when dfncy <= 1 is considered in the discard function
    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>#
    
    ''' Note qing-yi-se is also considered in the discard function '''
    Pile = player.pile
    discard_tile = discard(T, Pile, KB, c, dc, numWl, n_hu, Phi, DQC)
    #print('The selected tile to discard is %s' %discard_tile)
    return discard_tile

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def Single_Eye(T, dc):
    '''Single Eye'''
    M = remove_duplicates(T)
    for eye_tile in M:
        M1 = T[:]
        M1.remove(eye_tile)
        V_b = hand_bp(M1)[:]
        V_c = hand_cp(M1)[:]
        V_d = hand_dp(M1)[:]
        if [t for t in M if t[0] == dc]:
            return False
        if min(len(V_b),len(V_c),len(V_d)) > 0:
            return False        
        if ps.is_solx(V_b) and ps.is_solx(V_c) and ps.is_solx(V_d):
            return True
    return False

def check_hu(player, dealer, last_player, players):
    ''' The player decides if hu when someone discards a tile which completes his hand
    Args:
        player (object)
        dealer (object): Dealer
        last_player (int): the id of the last player
    '''
    '''Here we should also takes into consideration the other players' states
        e.g., if one player has 2 kongs and/or pure color pongs and/or jin-gou-diao'''
    n_hu = dealer.n_hu()
    card = dealer.table[-1] #the last card discarded by some player
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand)
    TS = T[:]
    TS.sort()
    Pile = player.pile
    Pg = [p[0] for p in Pile]
    dc = player.daque_color
    ''' Knowledge base updated: The last card is already taken into the consideration of KB '''
    KB = player.kgbase(dealer, players)
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)
    ''' Current reward '''                            
    NH = T + [card]   #new hand with the discarded card 
    NH.sort(key=lambda t: t[0:2])   
    #the score of the current hand NH, w/o considering kong-shang-pao or kong-shang-hua or zimo or rob-kong
    utl = score.compute_handScore(NH, Pile)
    c = player.get_dominant_color() #could be None
    numS = hs.numS(TS, Pg, KB, dc) #number of solution tiles, this is not precise as it changes after the player pong
    #pr = round(numWl/sum(KB), 2)
    pr = 0.8
    #estimated tile distribution, only used for test
    Phi = [[]]*4
    for j in range(4):
        if j == player.player_id:
            Phi[j] = [0, 0, 0] #ignore the current player himself
        else:
            X = dealer.guess_color_distribution(j)
            Phi[j] = X[:]                

    ''' factor is the initial zimo factor '''
    factor = (4-n_hu-1) * pow(0.99, 55-numWl) * (1- pow(0.8, rnumWl))/(sum(KB)*(1-0.8)) #0.8 is the step discount factor 
    # (1 - s^n)/(1-s) = 1 (1st draw) + s (2nd draw) +...+s^{n-1}, s=0.8, n=rnumWl

    '''zimo_factor > 1 indicates that it is worth waiting for zimo instead of accepting hu now'''
    '''default zimo_factor: (4-n_hu-1) * 2 * numS * factor * pow(0.99, 55-numWl)'''
    zimo_factor =   2 * numS * factor
##    print('Type 0 :: card = %s  zimo factor = %s' %(card, round(zimo_factor,1)))
##    content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##      %(numWl, n_hu, dc, c, TS, Pg, numS, KB, Phi)
##    print(content)

    '''Single Eye''' 
    T_color = color_set(T + Pg*3)
    Relevant_Tiles_in_KB = [t for t in MJ() if t[0] in T_color and KB[kbf(t)] > 1]
    numPair_in_KB = len(Relevant_Tiles_in_KB)
    '''card makes Kong'''
    if card in Pg: #T.count(card) = 0
        T_color = color_set(T)
        numMeld = 0
        for c in list(T_color):
            suite = KB[c*9:c*9+9]
            Phic = [round(Phi[i][c]/3) for i in range(4)] #estimation of melds in the other players' hands
            numMeld += num_disjoint_melds(suite) - sum(Phic) * pow(0.99, numWl) #200702-sl
            '''Looks strange, should revise as above, where the 2nd term denotes the number of existing melds in other players' hands!'''
            #numMeld += num_disjoint_melds(suite) * sum(Phic) * pow(0.99, 55-numWl)
        numSY = numS + numMeld * pow(pr, 3) #pr is the ratio of Wall in KB, pr^3 is used as we need to draw 3 times to complete a meld 
        zimo_factor = numSY * factor #kong is gone 
##        print('Type Makekong :: card = %s  zimo factor = %s' %(card, round(zimo_factor,1)))
##        content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n numMeld = %s \n KB = %s \n Phi = %s'\
##          %(numWl, n_hu, dc, c, TS, Pg, numSY, numMeld, KB, Phi)
##        print(content)
        
    if numPair(NH) == 7 or Single_Eye(T, dc): #T.count(card) >= 1, Single_Eye from xzutils.py
        numSX = max(numS, numPair_in_KB * pow(pr, 2)) #200702-sl
        zimo_factor = 2 * numSX * factor
##        print('Type 7-Pair or Single Eye :: card = %s  zimo factor = %s' %(card, round(zimo_factor,1)))
##        content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n numPair \%s \n KB = %s \n Phi = %s'\
##          %(numWl, n_hu, dc, c, TS, Pg, numSX, numPair_in_KB, KB, Phi)
##        print(content)            

    if T.count(card) == 2 and player.get_pure_color_index () == 11 and card[0] != c: #check if 'qingyise' possible
        ''' 'qing-yi-se' is expected but should make sure this is consistent with check_pong!'''
        m = len([t for t in range(1,10) if KB[kbf([c, t])] > 1]) 
        zimo_factor = max(2 * 4 * m *  pow(pr, 2) * factor, zimo_factor) #pr is the ration of Wall in KB 
##        print('Type Nopong-QYS :: card = %s  zimo factor = %s' %(card, round(zimo_factor,1)))
##        content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n m = %s \n KB = %s \n Phi = %s'\
##          %(numWl, n_hu, dc, c, TS, Pg, m, KB, Phi)
##        print(content)
       

    'Fix the after pong/kong hand'
    if T.count(card) == 3: 
        NKH = T[:] #hand after kong
        NKH.remove(card)
        NKH.remove(card)
        NKH.remove(card)
        NKPg = Pg[:]
        NKPg.append(card)
        after_kong_dfncy = hk.hyval(NKH, NKPg, KB, dc) #NKH + 3*NKPg = 13
    if T.count(card) >= 2: 
        NPH = T[:] #hand after pong
        NPH.remove(card)
        NPH.remove(card)
        NPPg = Pg[:]
        NPPg.append(card)        

    zimo_factorx = 0
    if T.count(card) == 3 and after_kong_dfncy == 1 and numWl: #expect 'kong-shang-hua'
            after_kong_numS = hs.numS(NKH, NKPg, KB, dc)
            if Single_Eye(NKH, dc): #200702-sl
                after_kong_numS = max(after_kong_numS, numPair_in_KB*pow(pr,2)) #//todo: check if this is good!
            zimo_factorx = 2 * after_kong_numS * factor *(1 + 1/sum(KB))
##            print('Type kong-shang-hua :: card = %s  zimo factor = %s' %(card, round(zimo_factorx,1)))
##            content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##              %(numWl, n_hu, dc, c, TS, Pg, after_kong_numS, KB, Phi)
##            print(content)
            
    elif T.count(card) >= 2: #expect 'jin-gou-diao' or 'qingyise' 
        ''' Decide if pong is better '''
        #NPH: the hand after pong, NPPg: the Pg after pong
        M1 = remove_duplicates(NPH)
        '''Check what type of hand we have after pong: Single_Eye if we have several melds plus one (unique) single tile'''
        after_pong_numS = 0
        for t in M1:
            M = NPH[:]
            M.remove(t)
            after_pong_numS = max(after_pong_numS, hs.numS(M, NPPg, KB, dc))
        for t in M1:
            M = NPH[:]
            M.remove(t)
            if after_pong_numS == hs.numS(M, NPPg, KB, dc):
                MS = M #select a tile t to discard after pong, and denote by MS the resulted hand
                break

        l = len([t for t in T if t[0] != card[0]])
        if len(T) == 4: #expect 'jin-gou-diao'
            '''Jin-gou-diao is expected and thus we should pong instead of hu'''
            if NPH[0] == NPH[1]:
                delta = 2 # increased by 2
            else:
                delta = 4 # increased by 4
            after_pong_numS = max(after_pong_numS, numPair_in_KB*pr) #//todo: check if this is good!
            zimo_factorx = max(zimo_factorx, 2 * delta * after_pong_numS * factor)
##            print('Type Pong-JGD :: card = %s  zimo factor = %s' %(card, round(zimo_factorx,1)))
##            content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##              %(numWl, n_hu, dc, c, TS, Pg, after_pong_numS, KB, Phi)
##            print(content)
        elif c == card[0] and l == 2:
            ''' 'qing-yi-se' is expected but should make sure this is consistent with check_pong!'''
            m = len([t for t in range(1,10) if KB[kbf([c, t])] > 1]) 
            zimo_factorx = max(zimo_factorx, 2 * 4 * m *  pow(0.8,2) * factor) #0.8 is step discount 
            #will become ready after l tile change and assume 
##            print('Type Pong-QYS :: card = %s  zimo factor = %s' %(card, round(zimo_factorx,1)))
##            content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##              %(numWl, n_hu, dc, c, TS, Pg, m, KB, Phi)
##            print(content)            
        elif Single_Eye(MS, dc):
            after_pong_numS = max(after_pong_numS, numPair_in_KB*pow(pr,2))
            zimo_factorx = max(zimo_factorx, 2 * after_pong_numS * factor)
##            print('Type Pong-OTHER :: card = %s  zimo factor = %s' %(card, round(zimo_factorx,1)))
##            content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##              %(numWl, n_hu, dc, c, TS, Pg, after_pong_numS, KB, Phi)
##            print(content)


##    print('zimo factor = %s & zimo factorx = %s' %(round(zimo_factor,1), round(zimo_factorx,1)))
    zimo_factor = max(zimo_factor, zimo_factorx) 
    ''' 'kongshangpao' has been appended to the player's hu_way before applying this function '''
    if 'kongshangpao' in player.hu_way: #other player discards after kong #q
        zimo_factor = zimo_factor * ( 2*(1 + 1/utl) ) 
        #zimo reward vs kongshangpao reward = (4-n_hu-1) * 2 *utl vs 2*utl + 2 (hu-jiao-zhuan-yi)
##        print('Type Kong-Shang-Pao :: card = %s  zimo factor = %s' %(card, round(zimo_factor,1)))
##        content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##          %(numWl, n_hu, dc, c, TS, Pg, numS, KB, Phi)
##        print(content)
        
    Kong_Tile = set()
    TR = remove_duplicates(T)
    Kong_Tile = [x for x in TR if T.count(x) == 3 and KB[kbf(x)]] + [x for x in Pg if KB[kbf(x)]]
    zimo_factor += len(Kong_Tile) * max(numWl-5, 0)/sum(KB) * pow(0.95, 55-numWl)
##    print('Revised zimo factor =  %s as lenK = %s and tile = %s' %(round(zimo_factor, 1), len(Kong_Tile), card))
##    content = ' numWl = %s \n n_hu = %s \n dc = %s \n c = %s \n NQHand = %s \n Pg =  %s \n numS = %s \n KB = %s \n Phi = %s'\
##      %(numWl, n_hu, dc, c, TS, Pg, numS, KB, Phi)
##    print(content)

    if zimo_factor > HU_DECLINE_THRESHOLD:
##        print('Final decision: stand')
        return 'stand'
##    print('Final decision: hu')
    return 'hu'
            

def check_pong(player, dealer, players):
    ''' Check if the player pong when someone discards a card which the player can pong
    Args:
        dealer (object): Dealer
        players (objects)
        n_hu (int): number of winners
    Return:
        (Bool)
    '''

    n_hu = dealer.n_hu()
    card = dealer.table[-1]
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand)
    Pg = [p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer, players)
    Q = [t[1] for t in T if t[0] == dc]
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)
       
    c = player.get_dominant_color()
    #200614-sl
    if c != None and card[0] != c: 
        length_minor = len([t for t in T if t[0] != c and t[0] != dc])
        length_dominant = len([t for t in T if t[0] == c])
        if  length_minor < 4 and length_dominant + 3*len(Pg) > 8 and \
            rnumWl >= 3 * (length_minor + len(Q)): # 4->12, 3->9, 2->6
            ''' we still have a chance to make 'qing-yi-se' '''
            return 'stand'
    if Q:
        return 'pong'

    #200613-sl
    '''Include the special case of jin-gou-diao//:: since we have declined hu, this step seems natural'''
    #if len(T) == 4:
        #return 'pong'

    cur_dfncy = hk.hyval(T, Pg, KB, dc) #! Here len(T+Pg*3) < 14
    S = T[:]
    S.remove(card)
    S.remove(card)
    Pg1 = Pg[:]
    Pg1.append(card)
    after_pong_dfncy = hk.hyval(S, Pg1, KB, dc)

    '''//todo: Consider the special case when the current player can hu t, but declined. '''
    if after_pong_dfncy <= 1: # hu was possibly declined
        return 'pong'
    
    if after_pong_dfncy <= cur_dfncy or rnumWl >= 10 or \
       (after_pong_dfncy == cur_dfncy + 1 and 3*after_pong_dfncy <= rnumWl):
        '''It's safe to pong'''
        return 'pong'

    return 'stand'

    
def check_kong(player, dealer, players):
    ''' Check if the player kong/pong when someone discards a card which the player can kong
    Args:
        player (object)
        dealer (object): Dealer
        players (object list)
        n_hu (int): number of winners
    Returns:
        'pong', 'kong', or 'stand'
    '''
    n_hu = dealer.n_hu()
    card = dealer.table[-1]
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand)
    Pg = [p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer, players)
    Q = [t[1] for t in T if t[0] == dc]    
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)
    
    Tx = T[:] # a temporary hand
    Tx.remove(card)
    Tx.remove(card)
    
    #after_pong_dfncy
    Txx = Tx[:]
    Txx.remove(card)
    Pgx = Pg[:] # a temporary pong set
    Pgx.append(card)

    ''' Note here cur_dfncy is after taking the last discarded card into consideration:
        It is possible that the card is the last one which can complete the hand.   '''
    cur_dfncy = hk.hyval(T, Pg, KB, dc) #! len(T+Pg*3) < 14
    after_pong_dfncy = hk.hyval(Tx, Pgx, KB, dc)    
    after_kong_dfncy = hk.hyval(Txx, Pgx, KB, dc) #! len(Txx+Pgx*3) < 14
    
    if after_kong_dfncy == 1:
        ''' Gang_shang_hua is expected '''
        return 'kong'    
    #20200607-sl
##    if rnumWl > 10 and n_hu > 0:
##        ''' It is not necessary to wait for jiakong '''
##        return 'kong'
##    if 3*after_kong_dfncy <= rnumWl <= 10:
##        '''If we still have chance to win and there are many (but not so many) tiles in the Wall''' 
##        return 'kong'

    #introduce after_pong_dfncy
    if after_kong_dfncy <= cur_dfncy or (after_kong_dfncy <= after_pong_dfncy and rnumWl >= 6):
        ''' It is good to have an extra chance to draw a tile '''
        return 'kong'
    #20200607-sl
    if after_pong_dfncy < min(after_kong_dfncy, cur_dfncy):
        return 'pong'
           
    ''' If there are so many tiles in the Wall and no one has won, we could first pong and then jiakong '''
    x = check_pong(player, dealer, players) 
    return x
 
def check_zimo(player, dealer, last_drawn_card, players):
    ''' Check if the player zimo when he draws a card that completes his hand
        // in this strategy, we always declare win when zimo
    Args:
        dealer (object): Dealer
    '''
    return 'zimo'

def check_zikong(player, dealer, players):
    ''' Check if the player zikong when he draws a card
    Args:
        dealer (object): Dealer
    '''
    n_hu = dealer.n_hu()    
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand) # T%3 == 2
    Pg = [ p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer, players)
    Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color
    T.sort(key=lambda t: t[0:2])
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)
    
    an_list = player.ankong_list()
    jia_list = player.jiakong_list()
    Kong_candidates = [[t,9,0] for t in an_list] + [[t,9,1] for t in jia_list] #9 is an upper bound for deficiency 
    
    KSS = [] #the updated Kong_candidates with s[1] updated as the real after_kong_dfncy
    for s in Kong_candidates:
        H1 = deepcopy(T)
        
        if s[2] == 0: #ankong               
            H1.remove(s[0])
            H1.remove(s[0])
            H1.remove(s[0])
            H1.remove(s[0])
            Pg1 = Pg + [s[0]]
        else: #jiakong
            H1.remove(s[0])
            Pg1 = deepcopy(Pg)

        #sl decide if I kong s
        after_kong_dfncy = hk.hyval(H1, Pg1, KB, dc)
        s[1] = after_kong_dfncy  #update s[1] as its real deficiency
        KSS.append(s)
        
    if len(KSS) > 1:
        print('We have more than one kong candidates %s and shall select the best' %(KSS))
        
    KSS0 = [s[0:2] for s in KSS if s[2] == 0] #ankong
    KSS0.sort(key=lambda x: x[1])
    KSS1 = [s[0:2] for s in KSS if s[2] == 1] #jiakong   
    KSS1.sort(key=lambda x: x[1])   

    val0 = 9
    if KSS0:
        s = KSS0[0]
        val0 = s[1]
        
    if val0 == 1:
        ''' gang-shang-hua is expected '''
        return ['ankong', s[0]]
        
    val1 = 9
    if KSS1:
        s = KSS1[0]
        val1 = s[1]
              
    if val1 == 1:
        ''' gang-shang-hua is expected '''
        return ['jiakong', s[0]]

    #if rnumWl > 10: #kong has immediate reward
    if (KSS0 and rnumWl > 6 + min(4, val0)) or (not KSS0 and rnumWl > 6 + min(4, val1)): #20200603-sl 
        if KSS0:
            s = KSS0[0]
            val0 = s[1]
            return ['ankong', s[0]]        
        s = KSS1[0]
        val1 = s[1]        
        return ['jiakong', s[0]]
        
    cur_dfncy = hk.hyval(T, Pg, KB, dc) # the deficiency of player's hand
    if val1 < val0:
        s = KSS1[0]    
        if s[1] <= cur_dfncy + 2 and rnumWl >= 10\
           or (s[1] <= cur_dfncy + 1 and rnumWl >= 4) or s[1] == cur_dfncy:
            ''' if we still have chance to complete, then we kong '''
            return ['jiakong', s[0]]
        
    #if else then val0 <= val1 <= 9 and thus KSS0
    if val1 >= val0 and val0 < 9:
        s = KSS0[0]    
        #if Q or (s[1] <= cur_dfncy + 2 and rnumWl >= 6) \
        #The 'Q' condition should also be restricted, e.g.,
        #NQHand = [[1, 4], [1, 6], [1, 7], [1, 8]] 
        #Pile =  [[[1, 9], [1, 9], [1, 9], [1, 9]], [[1, 7], [1, 7], [1, 7]], [[1, 1], [1, 1], [1, 1], [1, 1]]] 
        #KB = [1, 0, 3, 3, 1, 1, 2, 2, 4, 0, 0, 0, 2, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0] 
        if (s[1] <= cur_dfncy + 2 and rnumWl >= 6) \
           or (s[1] <= cur_dfncy + 1 and rnumWl >= 4) or s[1] == cur_dfncy:
            ''' if we still have chance to complete, then we kong '''
            return ['ankong', s[0]]
        
    ''' Else, we choose to stand '''        
    return ['stand', 'zikong']
    
def check_robkong(player, dealer, jiakong_card, players):
    '''Check if the player robkong when some other player jiakong (mingkong or revealed kong)
        Args:
            jiakong_card: the tile some other player just jiakong
    '''
    n_hu = dealer.n_hu()
    Table = deepcopy(dealer.table)
    T = deepcopy(player.hand)
    Pg = [p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer, players)
    Q = [t[1] for t in T if t[0] == dc]
    T.sort(key=lambda t: t[0:2])
    Pile = player.pile
    numWl = dealer.numWl
    rnumWl = numWl/(4-n_hu)

    NH = T + [jiakong_card]    
    NH.sort(key=lambda t: t[0:2])

    #the hand score if we take the jiakong card    
    utl = score.compute_handScore(NH, Pile)
    numS = hs.numS(T, Pg, KB, dc)
    '''(utl == base_score and numS <= 4 and rnumWl <= 5) is replaced with (numS <= 4 and rnumWl <= 5)'''

    if (utl > base_score or rnumWl < 4) \
       or (numS <= 4 and rnumWl <= 5)\
       or numS <= 1:        
        return 'robkong'    
    return 'stand'

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
if __name__ == '__main__':
    # main_test
    import time

    start = time.time()
    
    DQC = [2, 2, 0, 1]
    numWl = 11 
    n_hu = 0 
    dc = 1 
    c = None 
    Q = [] 
    NQHand = [[0, 3], [0, 3], [0, 7], [0, 8], [0, 8], [0, 9], [0, 9], [0, 9]] 
    Pile =  [[[2, 2], [2, 2], [2, 2], [2, 2]], [[0, 2], [0, 2], [0, 2]]] 
    Table = [[2, 5], [2, 9], [0, 4], [1, 2], [2, 6], [2, 6], [1, 2], [2, 6], [2, 4], [0, 7], [1, 2], [2, 4], [2, 8], [0, 8], [0, 1], [2, 5], [2, 7], [2, 1], [1, 2], [2, 3], [2, 7], [2, 1], [2, 7], [1, 4], [2, 8], [0, 1], [2, 5], [2, 5], [2, 1], [2, 7], [1, 8], [2, 3], [0, 1], [2, 8], [2, 9], [2, 3], [2, 6], [2, 3], [2, 9], [2, 4], [0, 2]] 
    KB = [1, 0, 2, 3, 1, 1, 2, 1, 1, 4, 0, 1, 3, 0, 1, 1, 3, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1] 
    Phi = [[6.0, 2.0, 0], [1.5, 2.5, 0], [0, 1.0, 6.0], [0, 0, 0]]
    Pg = [[2,2],[0,2]]
    
    vec = discard(NQHand, Pile, KB, c, dc, numWl, n_hu, Phi, DQC)
    print(vec)
    end = time.time()
    print('It takes %s seconds' %(round(end-start,3)))
