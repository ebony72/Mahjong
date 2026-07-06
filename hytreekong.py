# Created on May 2, 2019
# Revised on May 11, 2019 for Xuezhan
# Revised on June 08, 2020
# -- Fixed the issue with haha pd, where, given the current KB,
            #no tile in the hand not in the pd can be completed into a pair
# -- Fixed another issue with haha pd.
#q: question
#sl: comments by sanjiang
# pd: pseudo-decomposition
# mpd: maximal pseudo-decomposition

from copy import deepcopy
from utils.xzutils import *

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
''' A pseudo-decomposition (p-decomposition or p-d for short) pi is a list of five blocks, where each block is a list of mahjong tiles
    such that pi[4] is either a pair or empty, and each pi[i] for 0<=i<=3 is either a meld or a p-meld or empty.'''
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

'''haha denotes 'bad' p-ds which cannot envolve into a decomposition'''
def haha(pi, KB, dc): # haha means bad
    ''' Check if a pseudo-decomposition (p-d) pi can be completed based on the current knowledge base, where
        a p-d consists of five lists of tiles, the first four will be developed into melds and the last one the eye.
        Note here we assume no tiles from pi has the daque color dc.
        Args:
            pi (list): a decomposition with form pi = [[]]*5
            KB (list): the knowledge base with form KB = [4]*27
            dc (int): the daque color
        Return:
            Bool
    '''
    if len(pi) != 5:
        return True
    if len(pi[4]) != 2 and pi[4] != []: #We require pi[4] to be either empty or a pair
        return True
    if len(pi[4]) == 2 and pi[4][0] != pi[4][1]:  #if the last list contains two different tiles, pi cannot be completed
        return True

    for i in range(4):
        if len(pi[i]) == 2:
            t = pi[i][0]
            c = t[0]
            n = t[1]
            p = kbf(t)
            #! We don't consider p-d like (B1B3)(B1B3)
            '''Consider the case when a pmeld is not completable!'''
            if pi[i][1] == t and KB[p] == 0: #pi[i] has form [t,t]
                return True
            if pi[i][1][1] == n + 2 and KB[p+1] == 0: #[t, t+2]
                return True
            if pi[i][1][1] == n + 1 and \
                 ((n == 1 and KB[p+2] == 0) or \
                  (n == 8 and KB[p-1] == 0) or \
                  (KB[p-1] == 0 and KB[p+2] == 0)):
                return True
            '''The test is not complete and, thus, the following two lines should be commented out.''' 
            #else:
                #return False

    '''When pi[4] is empty, it is possible that we cannot make an eye from the rest tiles in the hand.
    This case is dealt in the definition of cost(.), where we increase the cost by 2 instead of 1. See the example below'''
    #T = [[0, 6], [0, 7], [0, 8], [1, 2], [1, 3], [1, 4], [1, 6], [1, 7]]
    #pi = [ [[0, 6], [0, 7], [0, 8]], [[1, 2], [1, 3], [1, 4]], [[1, 8], [1, 8], [1, 8]], [[0, 9], [0, 9], [0, 9]], []]
    #dc = 2
    #KB = [0, 0, 0, 2, 4, 3, 3, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 2, 1, 1, 1, 0, 1, 2, 4, 2]
        
    return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

# for Xuezhan, T contains at most two colors and if it has one or more kongs,
def cost(pi, T, Pg, KB, dc):
    ''' Compute the cost of a p-decomposition
        Args:
            pi (list): a p-decomposition with 5 blocks, all tiles in pi are from T+Pg*3
            T (list): a list of tiles with no daque color
            Pg (list): the pong list
            KB (list): the knowledge base
            dc (int): the daque color
        Returns:
            val (int): the cost is non-negative, which is the higher the worse
    '''
    TPg = T + Pg*3
    TPg.sort(key=lambda t: t[0:2])
    val = 0
    if haha(pi, KB, dc): #if pi[4] contains a single tile, it is a haha p-d
        return 14
    TR = remove_duplicates(T)
    M = pi[0] + pi[1] + pi[2] + pi[3] + pi[4] 
    M.sort(key=lambda t: t[0:2])
    Rest_Tiles = list(x for x in TR if TPg.count(x) > M.count(x)) #tiles we can use to form the eye 
    # How many identical x tiles are available?
    NumRT = list(KB[kbf(x)] + TPg.count(x) - M.count(x) for x in Rest_Tiles)
    '''First consider if we can form the eye by using at least one tile from Rest_Tiles'''
    if pi[4] == []: # for Xuezhan, we can assume there is no Kong in T
        if not Rest_Tiles: #no tiles in Rest_Tiles can be completed to form the eye 
            val += -2
        elif Rest_Tiles and max(NumRT) < 2:
            val += -2            
        else:
            val += -1
    for i in range(4):
        if  pi[i] == []:
            val += -2
        elif len(pi[i]) == 2: #As pi is not haha, this pmeld can be completed.
            val += -1
    return -val
########################################
######## IMPORTANT #####################
##add a new block to a pd by action x###
########################################
   
#piz = [[]]*6
#\__/# piz is a list of 6 blocks, x is an action in range(6) or range(4)
def hyaction(piz, x): # how a pmeld can be developed by applying an action
    '''x denotes the code for actions associated with the current tile 'a'
        x=0: delete a from the sequence piz[5], i.e., remove the first tile (i.e., a) of piz[5]
        x=1: put the intersection of [a, a+1, a+2] and piz[5] in the first empty position
        x=2: put [a, a] in the 4th empty (i.e., the eye) position piz[4]
        x=3: put the intersection of [a, a, a] and piz[5] in the first empty position
        x=4: put [a, a+1] in the first empty position if [a, a+1, a+2] is contained in piz[5]
        x=5: add [a, a+2] in the first empty position if [a, a+1, a+2] is contained in piz[5]
        
        Args:
            piz (list): a list of length 6, while the first 5 blocks is a p-decomposition and
                        the last block contains all non-processed tiles in the hand
            x (int): an action symbol
        Return:
            (list): an extended p-decomposition
    ''' 

    pi = piz[:]

    t = 0 # t < 4 is the index of the first empty block in pi
    X = [] # the list of nonempty blocks in the first four blocks of piz
    for i in range(4):
        if pi[i] != []:
            X.append(i)
    t = len(X) # pi[t] is empty if t<4
    
    S_w = piz[5][:] # the set of non-processed tiles
    if S_w == [] or (pi[3] != [] and pi[4] != []):
        # a p-d has been computed and this action is not necessary
        return piz 
    else:
        a = S_w[0] # a is the tile we are examining
        if x == 0: # discard and do not modify pi
            del S_w[0]
            pi[5] = S_w[:]            

        elif t<=3 and (nxtile(a) in S_w or nnxtile(a) in S_w) and x in {1,4,5}:
            
            if x==1 and nxtile(a) in S_w and nnxtile(a) in S_w:
                S_w.remove(a)
                S_w.remove(nxtile(a))
                S_w.remove(nnxtile(a))
                pi[5] = S_w[:]
                pi[t] = [a,nxtile(a),nnxtile(a)]

            # in order to get all mpds, we should consider the following extra actions
            elif x==4 and nxtile(a) in S_w and nnxtile(a) in S_w:
                S_w.remove(a)
                S_w.remove(nxtile(a))
                pi[5] = S_w[:]
                pi[t] = [a,nxtile(a)]
                
            elif x==5 and nxtile(a) in S_w and nnxtile(a) in S_w:
                S_w.remove(a)
                S_w.remove(nnxtile(a))
                pi[5] = S_w[:]
                pi[t] = [a,nnxtile(a)]
                
            elif x==1 and nxtile(a) in S_w and not (nnxtile(a) in S_w):
                S_w.remove(a)
                S_w.remove(nxtile(a))
                pi[5] = S_w[:]
                pi[t] = [a,nxtile(a)]
                
            elif x==1 and not (nxtile(a) in S_w) and (nnxtile(a) in S_w):
                S_w.remove(a)
                S_w.remove(nnxtile(a))
                pi[5] = S_w[:]
                pi[t] = [a,nnxtile(a)]
                
            else: # actions cannot lead to an mpd
                return [[]]*6              
           
        elif x == 2 and pi[4] == [] and len(S_w) > 1 and S_w[1] == a:
            # form an eye starting with S_w[0]
            del S_w[0:2]
            pi[5] = S_w[:]
            
            if t == 0 or (t > 0 and pi[t-1] != [a,a]):
                # if pi[k] == [a,a] for some k < 4, then k must be t-1
                pi[4] = [a,a]
            else:
                return [[]]*6 #as the player has a kong a in his hand, thus the pd pi is not ideal 
            
        elif x == 3 and t<= 3 and len(S_w) > 1 and S_w[1] == a:
            # form a pong starting with S_w[0]
            if len(S_w) > 2 and S_w[2] == a:
                del S_w[0:3]
                pi[5] = S_w[:]
                pi[t] = [a,a,a]
            else:
                del S_w[0:2]
                pi[5] = S_w[:]
                Aa = pi[0] + pi[1] + pi[2] + pi[3]
                if  Aa.count(a) < 2 and pi[4] != [a,a]:
                    pi[t] = [a,a]
                else:
                    return [[]]*6 #as the player has a kong a in his hand, thus the pd pi is not ideal 
        else:
            return [[]]*6
        return pi
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

########################################
######## IMPORTANT #####################
### mpd/value of hybrid k-tiles ########
########################################

#\__/# For simplicity, we restrict the actions to 0-4
    #\__/# Shoud prove this does not affect much!
#Achtung! T contains no daque color
''' hyval is often used to decide which tile to discard, but also used checking, e.g., if after_pong dfncy is smaller '''

'''Memoization: hyval is a pure function of (T, Pg, KB, dc) and the strategy
   evaluates it for hundreds of near-identical hands per discard decision
   (same pattern as dfncy in dfncy/block_dfncy.py). Keys are immutable copies
   of the exact inputs, so cached results are always exact.'''
_hyval_cache = {}
_HYVAL_CACHE_LIMIT = 400000

def hyval(T, Pg, KB, dc):
    T.sort(key=lambda t: t[0:2]) #kept here: callers rely on this side effect
    key = (tuple(map(tuple, T)), tuple(map(tuple, Pg)), tuple(KB), dc)
    result = _hyval_cache.get(key)
    if result is None:
        result = _hyval_impl(T, Pg, KB, dc)
        if len(_hyval_cache) >= _HYVAL_CACHE_LIMIT:
            _hyval_cache.clear()
        _hyval_cache[key] = result
    return result

def _hyval_impl(T, Pg, KB, dc): # return the value of T + Pg*3
    ''' Compute the value of the player's current hand with no tiles with the daque color
        Args:
            T (list): the list of tiles in the player's hand whose color is not the daque color
            Pg (list): the pong list of the player
            KB (list): the knowledge base
            dc (int): the daque color
        Returns:
            val (int): the cost is non-negative, which is the higher the worse
    '''
    T.sort(key=lambda t: t[0:2]) #Achtung!
    TR = remove_duplicates(T)
    k = len(Pg) #q check if Pg is necessary    
    val = 9-2*k # an arbitrary initial value which is hign enough: it's 9 when k=0, 7 when k=1
    if not Pg:
        ''' 7-pair is possible '''
        val = min(val, 7-numPair(T))
        #TP = list(x for x in TR if 1 < T.count(x) < 4)
        #TK = list(x for x in TR if T.count(x) == 4)
        #best_pi = [ [x, x] for x in TP ]
        #for x in TK:
            #best_pi += [[x,x], [x,x]]

    '''Starting form an empty partition with length 6, s.t., the first 5 form a p-d, the last one all non-examined tiles in T''' 
        
    M = [[]]*6
    '''Put all pongs in the front of the p-d '''
    for i in range(k):
        ti = Pg[i] #the i-th pong
        M[i] = [ti, ti, ti]
        
    '''If we want to output the best p-d, we need to remove all relevent '#' in the function'''
    #best_pi = deepcopy(M[0:5])
    if len(T) == 0:
        print('T cannot be empty')
    if len(T) == 1:
        ''' T can be single, e.g., in check_zikong to calculate after_kong_dfncy'''
        t = T[0]
        if KB[kbf(t)]:
            return 1
        return 2
    if len(T) == 2:
        if T[0] == T[1]:
            return 0
        if max([ KB[kbf(t)] for t in T ]):
            return 1
        return 2    
    ''' Extend M step by step by applying one action xi in (0, 4) in each step'''
    for x0 in range(0, 4):
        S = T[:]
        ''' M[5] stores all tiles that are not examined so far '''
        M[5] = S 
        piT = M[:] 
        w = [] # a word or action list over (0,4), initially empty
        w.append(x0)
        ''' w.count(2) <= 1, w.count(1) + w.count(3) + k <= 4, sum(w.count(i)  for i in range(0,4)) == len(w) '''
        P0 = hyaction(piT, x0) # 
        new_pi_0 = P0[0:5] # new_pi_0 denotes a new p-d which envolves from the previous one (i.e., [[]]*5) 
        v0 = cost(new_pi_0, T, Pg, KB, dc)                   
        '''It is possible v0 > val, as we just begin to explore the x0-branch of the search tree'''
        if len(P0[5]) <= 1:
            if v0  >= val:  
                continue
            val = v0
            #best_pi = deepcopy(new_pi_0)
        else:
            for x1 in range(0,4):
                pi0 = P0[:]
                w = [x0] #\__/#\ It is very important to reinitiate w as [x0]
                w.append(x1)
                '''w.count(1) + w.count(3) + k <= 4 iff k <= 2 + w.count(2) + w.count(0) ''' 
                if w == [2,2] or (w.count(2) + w.count(0) < k - 2): # a p-decomposition cannot contain two eyes
                    continue   # consider another x1                
                P1 = hyaction(pi0,x1)
                new_pi_1 = P1[0:5]
                v1 = cost(new_pi_1,T,Pg,KB,dc)               
                if haha(new_pi_1,KB,dc): #haha(pi,KB,dc)
                    continue                                        
                if len(P1[5])<=1:
                    if v1 >= val:
                        continue
                    val = v1
                    #best_pi = deepcopy(new_pi_1)
                else:
                    for x2 in range(0,4):
                        pi1 = P1[:] 
                        w = [x0,x1]
                        w.append(x2)
                        '''w.count(1) + w.count(3) + k <= 4 iff k <= 1 + w.count(2) + w.count(0) ''' 
                        if w.count(2) > 1 or (w.count(2) + w.count(0) < k - 1): # a p-decomposition cannot contain two eyes
                            continue
                        P2 = hyaction(pi1,x2)
                        new_pi_2 = P2[0:5]
                        v2 = cost(new_pi_2,T,Pg,KB,dc)
                        if haha(new_pi_2,KB,dc):
                            continue                           
                        if len(P2[5])<=1:
                            if v2 >= val:
                                continue
                            val = v2
                            #best_pi = deepcopy(new_pi_2)                                                                       
                        else:
                            for x3 in range(0,4):
                                pi2 = P2[:]
                                w = [x0, x1, x2]
                                w.append(x3)
                                '''w.count(1) + w.count(3) + k <= 4 iff k <= w.count(2) + w.count(0) ''' 
                                if w.count(2) > 1 or (w.count(2) + w.count(0) < k):
                                    continue 
                                P3 = hyaction(pi2,x3)
                                new_pi_3 = P3[0:5]
                                v3 = cost(new_pi_3,T,Pg,KB,dc)
                                if haha(new_pi_3,KB,dc):
                                    continue
                                if len(P3[5])<=1:
                                    if v3 >= val:
                                        continue
                                    val = v3
                                    #best_pi = deepcopy(new_pi_3)                                    
                                else:
                                    for x4 in range(0,4):
                                        pi3 = P3[:]
                                        w = [x0, x1, x2, x3]
                                        w.append(x4)
                                        '''sum(w.count(i) for i in range(4)) = 5  and w.count(1) + w.count(3) + k <= 4'''
                                        '''w.count(1) + w.count(3) + k <= 4 iff 1 + k <= w.count(2) + w.count(0) ''' 
                                        if w.count(2) > 1 or (w.count(2) + w.count(0) < k + 1): # k=len(Pg)
                                            continue
                                        P4 = hyaction(pi3,x4)
                                        new_pi_4 = P4[0:5]
                                        v4 = cost(new_pi_4,T,Pg,KB,dc)
                                        if haha(new_pi_4,KB,dc):
                                            continue
                                        if len(P4[5])<=1 or (P4[3] != [] and P4[4] != []):
                                            if v4 >= val:
                                                continue
                                            val = v4
                                            #best_pi = deepcopy(new_pi_4)
                                        else: 
                                            for x5 in range(0,4):
                                                pi4 = P4[:]
                                                w = [x0, x1, x2, x3, x4]
                                                w.append(x5)
                                                '''sum(w.count(i) for i in range(4)) = 6  and w.count(1) + w.count(3) + k <= 4'''
                                                '''w.count(1) + w.count(3) + k <= 4 iff 2 + k <= w.count(2) + w.count(0) ''' 
                                                if w.count(2) > 1 or w.count(2) + w.count(0) < 2+k:
                                                    continue
                                                P5 = hyaction(pi4,x5)
                                                new_pi_5 = P5[0:5]
                                                v5 = cost(new_pi_5,T,Pg,KB,dc)
                                                if P5 == [[]]*6 or haha(new_pi_5,KB,dc):
                                                    continue
                                                if len(P5[5])<=1 or (P5[3] != [] and P5[4] != []):
                                                    if v5 >= val:
                                                        continue
                                                    val = v5
                                                    #best_pi = deepcopy(new_pi_5)
                                                else:
                                                    for x6 in range(0,4):
                                                        pi5 = P5[:]
                                                        w = [x0, x1, x2, x3, x4, x5]
                                                        w.append(x6)
                                                        '''sum(w.count(i) for i in range(4)) = 7  and w.count(1) + w.count(3) + k <= 4'''
                                                        '''w.count(1) + w.count(3) + k <= 4 iff 3 + k <= w.count(2) + w.count(0) ''' 
                                                        if w.count(2) > 1 or w.count(2) + w.count(0) < 3+k:
                                                            continue                                                        
                                                        P6 = hyaction(pi5,x6)
                                                        new_pi_6 = P6[0:5]
                                                        v6 = cost(new_pi_6,T,Pg,KB,dc)                                                        
                                                        if P6 == [[]]*6 or haha(new_pi_6,KB,dc):
                                                            continue
                                                        if len(P6[5])<=1 or (P6[3] != [] and P6[4] != []):
                                                            if v6 >= val:
                                                                continue                                                            
                                                            val = v6
                                                            #best_pi = deepcopy(new_pi_6)
                                                        else:
                                                            for x7 in range(0,4): 
                                                                pi6 = P6[:]
                                                                w = [x0, x1, x2, x3, x4, x5, x6]
                                                                w.append(x7)
                                                                '''sum(w.count(i) for i in range(4)) = 8  and w.count(1) + w.count(3) + k <= 4'''
                                                                '''w.count(1) + w.count(3) + k <= 4 iff 4 + k <= w.count(2) + w.count(0) ''' 
                                                                if w.count(2) > 1 or w.count(2) + w.count(0) < 4+k:
                                                                    continue                                                            
                                                                P7 = hyaction(pi6,x7)
                                                                new_pi_7 = P7[0:5]
                                                                v7 = cost(new_pi_7,T,Pg,KB,dc)                                                                    
                                                                if P7 == [[]]*6 or haha(new_pi_7,KB,dc):
                                                                    continue
                                                                if len(P7[5])<=1 or (P7[3] != [] and P7[4] != []):
                                                                    if v7 >= val:
                                                                        continue
                                                                    val = v7
                                                                    #best_pi = deepcopy(new_pi_7)
                                                                # to save time, we ignore x8
    #if best_pi == []:
        #print('pd with best value:', val, best_pi)
        #print(' T = %s\n Pg = %s\n KB = %s\n dc = %s' %(T, Pg, KB, dc))
    return val

#2020030814-sl: define a new value function for pure suite with up to 14 tiles
def puval(T, Pg, KB, c, dc):
    if c == dc or list(x for x in T if x[0] == dc):
        print('c should be different from dc and T has no daque color!')
    Tc = list(x for x in T if x[0] == c)
    KBc = [0]*27
    for i in range(0,9):
        KBc[c*9+i] = KB[c*9+i]
    val = hyval(Tc, Pg, KBc, dc)
    return val
        

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\ 
############# THE END  #######33########
if __name__ == '__main__':
    #T=[[0,1],[0,1],[0,2],[0,4],[0,4],[0,7],[0,7],[0,9],[1,2],[1,3],[1,3],[1,6],[1,7],[1,9]]
    #Pg=[]
    #KB=[0,3,0,0,3,2,0,0,3,0,3,0,0,0,3,2,0,4, 2,3,1,0,2,3,1,0,2]
    #dc=2
    #Above showing an example that our program does not calculate the dfncy correctly
    T = [[1, 2], [1, 3], [1, 3], [1, 4], [1, 5], [1, 6], [1, 8], [1, 9], [1, 9], [2, 2], [2, 2], [2, 7], [2, 7], [2, 8]]
    Pg = []
    KB = [4, 3, 4, 4, 2, 4, 4, 3, 4, 2, 3, 2, 3, 2, 3, 3, 3, 2, 4, 2, 4, 4, 4, 4, 2, 3, 4]
    dc = 0
    
    #cost = cost(pi,T, Pg, KB, dc)
    #print(cost)
    print(hyval(T, Pg, KB, dc))
    
