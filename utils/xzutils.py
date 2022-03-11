'''21.05.17: Bugs with num_disjoint_melds fixed'''
# import math
# import numpy as np
from utils.xzcard import MahjongCard as Card
import time
#from hysolx import is_h_solx

def save_state(name, content):
    name = str(name)
    content = str(content)
    file = open("testRecord/state" + name  + ".txt", mode = 'a')
    file.write(content)
    file.write('\n')
    file.close()

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

def init_deck(): #Achtung! deck contains only mahjong zero tiles (lists), not cards (objects)
    deck = []
    info = Card.info
    for _type in info['type']:
        for _trait in info['trait'][:9]:
            card = Card(_type, _trait)
            deck.append(card.get_mjzero())

    deck = deck * 4
    return deck
    
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def MJ():
    ''' Define the set of mahjong tiles
        arg: None
        return:
            X (list): list of tiles [c,n], where c in {0,1,2}, n in [1,9]
    '''
    X = [[0,0]]*27
    for c in range(3):
        for n in range(1,10):
            if c*9+n <= 27:
                X[c*9+n-1] = [c,n]
    return X

def kbf(card): # the same as MJ().index(card)
    ''' Return the index of a mahjong tile in MJ()
        Arg:
            card (list): a mahjong tile with form [c,i]
        Return:
            n (int): the index of card in MJ()
    '''        
        
    n = card[0]*9 + card[1] - 1
    return n

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def h_14tile(H):
    ''' Check if H (a list with length 14) is a valid hybrid 14-tile '''
    if len(H) != 14:
        return False    
    for i in range(0,14):
        t = H[i]
        if t[0] not in range(0,3) or t[1] not in range(1,10):
            return False
        elif i < 10 and H.count(t) > 4:
            return False
    return True

def numKong(T): # the number of kongs in T
    ''' Compute the number of Kongs in T
        Arg:
            T (list): a sorted list
        Return:
            K (int)
    '''
    l = len(T)
    K = 0
    for i in range(0,l-3):
        if T[i] == T[i+3]:
            K=K+1
    return K

def numPong(T):
    ''' Compute the number of pongs in T
        Arg:
            T (list): a sorted list
        Return:
            (int)
    '''
    U = remove_duplicates(T)
    P = list(x for x in U if T.count(x) == 3)
    n = len(P)
    return n

def numPair(T):
    ''' Compute the number of pairs in T
        Arg:
            T (list): a sorted list
        Return:
            (int)
    '''
    U = remove_duplicates(T)
    P = list(x for x in U if 2 <= T.count(x) <= 3)
    k = numKong(T)
    n = len(P)
    return n+2*k

def has_chow(T):
    ''' Check if T contains a chow '''
    
    U = remove_duplicates(T)
    U.sort()
    for i in U:
        if i+1 in U and i+2 in U:
            return True
    return False

def nxtile(t):
    '''Find the next tile
        If t is a number, then returns t+1;
        if t is a tile, returns [t[0],t[1]+1]
    '''
    if t in range(1,9):
        return t+1
    elif t in MJ() and t[0] in range(3) and t[1] in range(1,9):
        return [t[0],t[1]+1]
    else:
        return None
def nnxtile(t):
    ''' Find the tile next to the next tile of t '''
    if t in range(1,8):
        return t+2
    elif t in MJ() and t[0] in range(3) and t[1] in range(1,8):
        return [t[0],t[1]+2]
    else:
        return None


def hand_bp(H):
    ''' Compute the bamboo suit of a list H of Mahjong tiles
        Arg:
            H (list): a list of Mahjong tiles
        Return:
            H_bp (list): The list of numbers of the bamboo tiles in H
    '''
    
    H_bp = list(x[1] for x in H if x[0] == 0)
    H_bp.sort()
    return H_bp


def hand_cp(H):
    ''' Compute the character suit of a list H of Mahjong tiles
        Arg:
            H (list): a list of Mahjong tiles
        Return:
            H_cp (list): The list of numbers of the character tiles in H
    '''
    
    H_cp = list(x[1] for x in H if x[0] == 1)
    H_cp.sort()
    return H_cp


def hand_dp(H):
    ''' Compute the dot suit of a list H of Mahjong tiles
        Arg:
            H (list): a list of Mahjong tiles
        Return:
            H_bp (list): The list of numbers of the dot tiles in H
    '''
    
    H_dp = list(x[1] for x in H if x[0] == 2)
    H_dp.sort()
    return H_dp

#200620-sl
def color_set(T):
    ''' Compute the set of colors of T
        Arg:
            T (list): a list of Mahjong tiles
        Return:
             (set): A subset of colors {0, 1, 2}
    '''
    M = T[:]
    M1 = remove_duplicates(M)
    M1.sort()
    T_color = set()
    for t in M1:
        if t[0] not in T_color:
            T_color.add(t[0])
    return T_color
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
# color H

def color(V, x):
    ''' Transform a list V of integers (pure Mahjong suit) as Mahjong tiles with color x
        Arg:
            V (list): a list of integers in [1,9]
            x (int): 0 (bamboo), 1 (character), 2 (dot)
        Return:
            X (list): a list of x-tiles
    '''

    V.sort()
    X = list([x,i] for i in V)
    return X
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

def remove_duplicates(x):
    ''' Remove duplicate items from x
        arg:
            x (list): a list
        return:
            s (list): a list with redundant itmes removed from x
    '''
    s = x[:]
    for i in s:
        while s.count(i) > 1:
            s.remove(i)
    return s
    
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def xreplace(H, x, y):
    ''' Replace an item x in H with y
        args:
            H (list): a list of mahjong tiles
            x (list): a mahjong tile in H
            y (list): a mahjong tile not in H
        return:
            T (list): a sorted list of mahjong tiles with one x replaced with y
    '''
    i = H.index(x)
    T = H[:]
    T[i] = y
    T.sort(key=lambda t: t[0:2])
    return T
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\


def pile2list(pile): #sl: an item in a pile is a kong or a pong
    cards_list = []
    for each in pile: # each has form [B3,B3,B3], where B3 = [0,3]
        cards_list.extend(each) #sl i.e., cards_list += each (each is a list)
    return cards_list


##cards = [Card('d', '5'), Card('b', '3'), Card('b', '3')]
def cards2list(cards): #sl: what are in cards? like Card('d', '5'), usually consists of a meld
    cards_list = []
    for each in cards: #sl each is a card
        cards_list.append(each.get_str())
    return cards_list


def tile2card(t):
    ''' Get the card from a Mahjong zero tile

    Arg:
        tile (list), e.g., [0, 3]
    Return:
        card: the card, e.g., Card('b', '3') 
    '''
    trait = str(t[1])
    if t[0] == 0:
        type = 'b'
    elif t[0] == 1:
        type = 'c'
    elif t[0] == 2:
        type = 'd'
    a = Card(type,trait)
    #print(a)
    return a

def kgbasex(T, Piles, Table):
    ''' Compute the knowledgebase of the player
    Args:
        T (list): hand of a player
        Piles (list): list of piles of ALL players
        Table (list): list of tiles on the table
    '''
    KT = T[:]
    for p in Piles:
        #KT += p
        for card in p:
            KT.append(card)
    KT += Table

    K = [4]*27
    for x in MJ():
        p = x[0]*9 + x[1] - 1
        a = KT.count(x)
        K[p] = 4 - a
    return K

#todo: check if MJ().index[x] = p
def isolated_tile(T, t):
    ''' Check if t is isolated in T
    Args:
        T (list): hand of a player
        t (tile): [color, number] 
    '''
    c = t[0]
    n = t[1]
    Tc = list(x[1] for x in T if x[0] == c)
    t_nbr= {n-2, n-1, n+1, n+2}
    if T.count(t) > 1 or (t_nbr & set(Tc)):
        return False
    return True

def has_isolated_tile(T):
    for t in T:
        if isolated_tile(T, t):
            return True
    return False
    
    
# 2020021006-sl: used in further_choose in discardx.py
def tile_distance(T, t):
    ''' Compute the sum of distance from t to tiles in T
    Args:
        T (list): hand of a player
        t (tile): [color, number] 
    '''
    if isolated_tile(T, t):
        return 100

    c = t[0]
    n = t[1]
    Tc = list(x[1] for x in T if x[0] == c)
    Tc.sort()
    if n == 9 and Tc == [6, 8, 9]:
        return 3 # > 2 = tile_distance(T, [c, 6])
    if n == 9 and Tc == [6, 8, 8, 9]:
        return 8 # > 7 = tile_distance(T, [c, 6])
    if n == 9 and Tc == [6, 8, 8, 8, 9]:
        return 10 # > 9 = tile_distance(T, [c, 6])
    if n == 1 and Tc == [1, 2, 4]:
        return 3 # > 2 = tile_distance(T, [c, 4])
    if n == 1 and Tc == [1, 2, 2, 4]:
        return 8 # > 7 = tile_distance(T, [c, 4])
    if n == 1 and Tc == [1, 2, 2, 2, 4]:
        return 10 # > 9 = tile_distance(T, [c, 4])   
    dist = sum([abs(t[1]-x[1]) for x in T if x[0] == t[0]])
    return dist

def num_kb(KB, i):
    n = sum(KB[9*i:9*i+9])
    return n

def AllMelds(Kbase):
    ''' Compute the list of all different possible melds in the Knowledge Base Kbase of a color
        Arg:
            Kbase  a list of 9 over [0, 4], e.g., [0, 1, 0, 3, 3, 4, 0, 0, 3], i.e.,
            Tile 1 has 0 in Kbase, Tile 2 has 1, Tile 3, 0 ... 
        Return:
            (list) all melds in Kbase 
    '''
    if sum(Kbase) < 3 or (max(Kbase) < 3 and len([k for k in Kbase if k>0]) < 3): 
        return []
    if len(Kbase) != 9: raise Exception ('Ha, wrong allmelds kbase', Kbase)

    result = []
    for i in range(0, 9):
        if Kbase[i] > 2: #T[i] denotes the (i+1)-th tile (not nece. i+1) in Kbase
            result.append([i+1,i+1,i+1])
    for i in range(0,7):
        if min(Kbase[i], Kbase[i+1], Kbase[i+2]) and [i+1,i+2,i+3] not in result:
            result.append([i+1,i+2,i+3])
    return result

def half_num_disjoint_melds(Kbase):
    ''' Compute the number of possible melds in a half Knowledge Base of a color
        Arg:
            Kbase  a list of 9 over [0, 4], e.g., [0, 1, 0, 3, 0, 0, 0, 0, 0],
            where either the first 4 entries are 0 or the last 4 are 0 
        Return:
            max number of disjoint melds in Kbase 
    '''
    if max(Kbase[0:4])>0 and max(Kbase[5:])>0: return None
    if sum(Kbase) < 3 or (max(Kbase) < 3 and len([k for k in Kbase if k>0]) < 3): 
        return 0
    if len(Kbase) != 9: raise Exception ('Ha, wrong allmelds kbase', Kbase)
    
    Melds = []
    Melds = AllMelds(Kbase)
    if not Melds: return 0

    result = 0
    for m in Melds:
        S = Kbase[:]
        if m[0]==m[1]:
            i = m[0] # i denotes the tile of number i 
            if S[i-1] < 3: raise Exception ('disjoint melds error', S, i, S[i-1])
            S[i-1] -= 3 # decrease the number of tile i+1 in KB by 3
        else:                 
            i = m[0]
            if min(S[i-1:i+2]) < 1: raise Exception ('disjoint melds error', S[i-1:i+2])
            S[i-1] -= 1
            S[i] -= 1
            S[i+1] -= 1
        newKbase = S[:]
        result0 = half_num_disjoint_melds(newKbase)
        if result0 < result: continue
        result = result0 + 1
    return result    


def num_disjoint_melds(Kbase):
    ''' Compute the number of possible melds in the Knowledge Base Kbase of a color
        Arg:
            Kbase  a list of 9 over [0, 4], e.g., [0, 1, 0, 3, 3, 4, 0, 1, 1]
        Return:
            max number of disjoint melds in Kbase 
    '''
    if sum(Kbase) < 3 or (max(Kbase) < 3 and len([k for k in Kbase if k>0]) < 3): 
        return 0
    if len(Kbase) != 9: raise Exception ('Ha, wrong allmelds kbase', Kbase)
    
    Melds = []
    Melds = AllMelds(Kbase)
    if not Melds: return 0
    
    '''Divide the Kbase into two parts from the middle'''
    if Kbase[4] == 0 and max(Kbase[0:4]) and max(Kbase[5:]): 
        index = 4
    elif Kbase[3] == 0 and max(Kbase[0:3]) and max(Kbase[4:]):
        index = 3
    elif Kbase[5] == 0 and max(Kbase[0:5]) and max(Kbase[6:]):
        index = 5
    elif Kbase[2] == 0 and max(Kbase[0:2]) and max(Kbase[3:]):
        index = 3
    elif Kbase[6] == 0 and max(Kbase[0:6]) and max(Kbase[7:]):
        index = 6
    else:
        index = None
        
    if index != None:
        Kb1 = Kbase[0:index] + [0]*(9-index)
        Kb2 = [0]*index+ Kbase[index:]
        return num_disjoint_melds(Kb1) + num_disjoint_melds(Kb2)

    '''Consider all combinations that have a meld that contains tile 5'''
    Melds5 = [m for m in Melds if 5 in m]
    result = 0
    if Melds5: 
        for m in Melds5:
            S = Kbase[:]
            if m[0]==m[1]:
                i = m[0] # i denotes the tile of number i 
                if S[i-1] < 3: raise Exception ('disjoint melds error', S, i, S[i-1])
                S[i-1] -= 3 # decrease the number of tile i+1 in KB by 3
            else:                 
                i = m[0]
                if min(S[i-1:i+2]) < 1: raise Exception ('disjoint melds error', S[i-1:i+2])
                S[i-1] -= 1
                S[i] -= 1
                S[i+1] -= 1
            newKbase = S[:]
            result0 = num_disjoint_melds(newKbase)
            if result0 < result: continue
            result = result0 + 1
    '''Compare with those combinations that have no melds containing tile 5'''
    Kb1 = Kbase[0:4] + [0]*5
    result1 = half_num_disjoint_melds(Kb1)
    Kb2 = [0]*5+ Kbase[5:]
    result2 = half_num_disjoint_melds(Kb2)
    '''Return the larger one'''
    return max(result1 + result2, result)

#@210604
def meld_essential_tile(t,suit):
    '''t (int) is a meld essential tile of a suit: e.g., for 4567, 56 are essential'''

    if t not in suit: raise Exception('t should be a tile in suit', t, suit)
    kbase = [suit.count(i+1) for i in range(9)] #e.g., [0,0,0,1,1,1,1,0,0]
    newkbase = kbase[:]
    newkbase[t-1] -= 1
    if num_disjoint_melds(newkbase) < num_disjoint_melds(kbase):
        return True
    return False

def printout(T,Pg,KB,dc):
    print('T =', T)
    print('Pg =', Pg)
    print('KB =', KB)
    print('dc =', dc)
    
def typevalue(m,n,e,val):
    SL = []
    for m in range(3):
        for n in range(4):
            for e in range(n+1):
                f = (n-e)+2*(4-m-n+e)+1-min(e,1)
                if f > val:
                    # print(f, (m,n,e))
                    SL.append((m,n,e))
    return SL

def xmeld(x,Kbase):
    '''The number of melds x can make, where Kbase is the local KB'''
    num = Kbase[x-1]/2 #1 meld = 1 pong 
    if x==9: #789
        num += min(Kbase[7],Kbase[6])
    elif x==8: #789, 678
        num += min(Kbase[8]+Kbase[5],Kbase[6])
    elif x==1: #123
        num += min(Kbase[1],Kbase[2])        
    elif x==2: #123, 234
        num += min(Kbase[0]+Kbase[3],Kbase[2]) 
    else: #x-2x-1x, x-1xx+1, xx+1x+2
        num += sum([min(Kbase[x-3],Kbase[x-2]),min(Kbase[x-2],Kbase[x]), min(Kbase[x],Kbase[x+1])])           
    return num
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

if __name__ == '__main__':
    # main_test
    # T = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [1, 4], [1, 7], [1, 8]]
    # Pg = [[0, 7], [1, 9]]
    # dc = 2
    # KB = [0, 1, 0, 3, 3, 4, 0, 1, 1, 0, 3, 3, 1, 0, 3, 0, 0, 2, 0, 1, 2, 4, 0, 0, 0, 1, 0]
    # Kbase = KB[0:9]
    # K = Kbase[0:5]+[0]*4
    # print(Kbase,'\n', K)
    # T_color = color_set(T)
    Kbase = [4, 4, 2, 4, 3, 4, 3, 3, 3]
    start = time.time()
    print(Kbase)
    M = num_disjoint_melds(Kbase)
    print(M)
    print(round(time.time()-start,2))
    # numMeld = 0
    # for c in list(T_color):
    #     suit = KB[c*9:c*9+9]
    #     print(suit)
    #     print(AllMelds((suit)))
    #     numMeld += num_disjoint_melds(suit) 
    #     print(numMeld)
    
