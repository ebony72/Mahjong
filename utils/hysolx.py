#@20.01.29 adapted for xuezhan
import utils.pusolx as ps
from utils.xzutils import *

''' hysol.py and pusol.py do not conisder the knowledge base, and thus the result is differnt from hyval in hytreekong.py'''
#Bamboo, Character, Dot
#h_tile = list([x,y] for x in range(0,3) for y in range(1,10))

def is_h_solx(H, dc):
    ''' Check if a hybrid k-tile (k=14-3*pg) H is xuezhan-complete
        Args:
            H (list): a hybrid k-tile
            dc (int): the daque color
        Return:
            (Bool)
    '''
    if list(x for x in H if x[0] == dc):
        return False
    if numPair(H) == 7: #2020021507-sl: 7-pair solutions added
        return True
    
    V_b = hand_bp(H)[:]
    V_c = hand_cp(H)[:]
    V_d = hand_dp(H)[:]

    if min(len(V_b),len(V_c),len(V_d)) > 0:
        return False
    if (len(V_b)+len(V_c)+len(V_d)) % 3 != 2:
        return False
    
    if ps.is_solx(V_b) and ps.is_solx(V_c) and ps.is_solx(V_d):
        return True
    else:
        return False
    
def numS(T, Pg, KB, dc):
    ''' The number of tiles that can complete T
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            dc (int): the discard (daque) color of the player
        Return:
            num (int): the number of tiles that can complete T
    '''
    if list(t for t in T if t[0] == dc):
        return 0
    X = list(t for t in MJ() if t[0] != dc and KB[kbf(t)])
    num = 0
    for x in X:
        U = T[:]
        U.append(x)
        U.sort()
        if is_h_solx(U,dc): 
            num += KB[kbf(x)]  
              
    return num
    
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

if __name__ == '__main__':
    # main_test
    import time
    start = time.time()

    dc = 1 
    c = 2 
    T = [[0, 2], [0, 2], [0, 4], [0, 4], [2, 7], [2, 1], [2, 1], [2, 2], [2, 2], [2, 3], [2, 3], [2, 4], [2, 4]] 
    Pg =  [] 
    KB = [4, 2, 4, 2, 4, 4, 1, 4, 4, 4, 4, 1, 4, 4, 4, 4, 3, 4, 2, 1, 2, 1, 4, 3, 2, 4, 3]
    print(KB[kbf([2, 7])])
    print(numPair(T))
    print(numS(T, Pg, KB, dc))
    
    end = time.time()
    print('It takes %s seconds' %(end-start))
