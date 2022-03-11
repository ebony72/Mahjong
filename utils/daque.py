#2020-06-04: defined new daquex function

# consider the bcd-type 14-tiles and select one colour to discard
from utils.xzutils import *
import utils.pusolx as ps
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

# determine which color to discard
def f_colors(H):
    ''' Get the type of H

    Arg:
        H (list): The initial hand of a player
    Return:
        a list (a permutation of [0,1,2]): the type of H
    '''
    
    Ub = hand_bp(H)[:]
    Uc = hand_cp(H)[:]
    Ud = hand_dp(H)[:]
    
    if len(Ub) >= len(Uc) >= len(Ud):        
        return [0, 1, 2]
    elif len(Ub) >= len(Ud) > len(Uc):
        return [0, 2, 1]
    elif len(Uc) > len(Ub) >= len(Ud):
        return [1, 0, 2]
    elif len(Uc) >= len(Ud) > len(Ub):
        return [1, 2, 0]
    elif len(Ud) > len(Ub) >= len(Uc):
        return [2, 0, 1]
    else: #len(Ud) > len(Uc) > len(Ub):
        return [2, 1, 0]
        

def color(V,x):
    ''' Color a pure tile suit V with a color x

    Args:
        V: a list of numbers
        x: a color in Bamboo, Character, Dot
    '''
    if not V:
        return []
    else:
        X = [[x,i] for i in V]
        return X
    
def daque(TX):
    ''' Get the daque color of T

    Arg:
        T (list): The initial hand of a player
    Return:
        c (an integer in [0,1,2]): the daque color of T
    '''
    T = TX[:] #sl without this, the initial hands will always be sorted
    T.sort(key=lambda t: t[0:2])
    F = f_colors(T)
    Tb = hand_bp(T)[:]
    Tc = hand_cp(T)[:]
    Td = hand_dp(T)[:]

    H = color(Tb, F.index(0)) + color(Tc, F.index(1)) + color(Td, F.index(2))
    H.sort(key=lambda t: t[0:2])
    Ub = hand_bp(H)[:]
    Uc = hand_cp(H)[:]
    Ud = hand_dp(H)[:]

    #print(len(Ub), len(Uc), len(Ud))
    
    if len(Ud) < 2 or len(Uc) - len(Ud) > 1:
        return F[2]
    elif len(Ud) == len(Uc) - 1 >= 2:
        # if Ud has two pairs or a triplet
        if len(set(Uc)) == len(Uc) and len(set(Ud)) < len(Ud):
            return F[1]
        # to be continued
        #20200330: didn't consider the symmetrical case when len(Uc) == len(Ud) == 3
        return F[2]
    else:        
        return F[2]

def daquex(TX):
    ''' Get the daque color of T (defined @2020.03.30)

    Arg:
        TX (list): The initial hand of a player
    Return:
        c (an integer in [0,1,2]): the daque color of T
    '''
    T = TX[:] #sl without this, the initial hands will always be sorted
    T.sort(key=lambda t: t[0:2])
    F = f_colors(T)
    Tb = hand_bp(T)[:]
    Tc = hand_cp(T)[:]
    Td = hand_dp(T)[:]

    H = color(Tb, F.index(0)) + color(Tc, F.index(1)) + color(Td, F.index(2))
    H.sort(key=lambda t: t[0:2])

    '''After rearrangement, Ub is the longest suit with color F[0], Ud the shortest with color F[2]''' 
    Ub = hand_bp(H)[:]
    Uc = hand_cp(H)[:]
    Ud = hand_dp(H)[:]
    #print(Ub)
    #print(Uc)
    #print(Ud)

    #print(len(Ub), len(Uc), len(Ud))    
    if len(Ud) < 2 or (not numPong(Ud) and len(Uc) - len(Ud) > 1): #553: if Ud has pong
        return F[2]
    if len(Ud) == 2 and len(Uc) - len(Ud) <= 1: #compare c, d
        if numPair(Ud) and (not numPair(Uc) or has_chow(Uc)):
            return F[1]
        return F[2]

    if len(Ud) == len(Uc) == 3: #numPong -> numPair
        if numPong(Uc):
            return F[2]
        if numPong(Ud):
            return F[1]
        if ps.is_solx(Uc):
            return F[2]
        if ps.is_solx(Ud):
            return F[1]
        if numPair(Uc) and numPair(Ud):
            if Uc[-1] - Uc[0] > Ud[-1] -Ud[0]: 
                return F[1]
            return F[2]
        if numPair(Ud): #don't care much about the difference between 228 and 223? may be refined!
            return F[1]
        if numPair(Uc):
            return F[2]        
        if min(Uc[1]-Uc[0], Uc[2]-Uc[1])  > min(Ud[1]-Ud[0], Ud[2]-Ud[1]): 
        #if Uc[-1] - Uc[0] > Ud[-1] - Ud[0]: 
            return F[1]
        if min(Uc[1]-Uc[0], Uc[2]-Uc[1])  < min(Ud[1]-Ud[0], Ud[2]-Ud[1]): 
            return F[2]
        if max(Uc[1]-Uc[0], Uc[2]-Uc[1])  > max(Ud[1]-Ud[0], Ud[2]-Ud[1]):
            return F[1]
        return F[2]
        
    if len(Ud) == 3 and len(Uc) == 4: #20200330
        if numPong(Uc) or numKong(Uc):
            return F[2]
        if numPong(Ud): #2255 > 888; 2234 > 888? 3445 > 888?
            #if numPair(Uc) == 2 or ps.numpuS(Uc) > 2:
                #return F[2]
            return F[1]
        if numPair(Uc) or has_chow(Uc): #2378 > 229?
            return F[2]
        if len(set(Uc)) == len(Uc) and (not has_chow(Uc)) and (numPair(Ud) or has_chow(Ud)):
            return F[1]
        return F[2]

    if len(Ud) == 3 and numPong(Ud) and len(Uc) == 5: #20200330
        if len(Ub) == 5:
            if (numPair(Uc) or ps.numpuS(Uc)) and (numPair(Ub) or ps.numpuS(Ub)):
                return F[2]
            if not (numPair(Uc) or ps.numpuS(Uc)) and (numPair(Ub) or ps.numpuS(Ub)):
                return F[1]
            if (numPair(Uc) or ps.numpuS(Uc)) and not (numPair(Ub) or ps.numpuS(Ub)):
                return F[0]
            if not (numPair(Uc) or ps.numpuS(Uc)) and not (numPair(Ub) or ps.numpuS(Ub)):
                if has_chow(Uc) and not has_chow(Ub):
                    return F[0]            
                if not has_chow(Uc) and has_chow(Ub): 
                    return F[1]
                if has_chow(Uc) and has_chow(Ub): #12369 > 777?
                    return F[2]
                if has_isolated_tile([ [x,0] for x in Uc ]):
                    return F[1]
                return F[0]
            return F[2]
        if len(Ub) == 6:
            if not (numPair(Uc) or ps.numpuS(Uc)):
                return F[1]
            return F[2]
            
    ''' Consider type 544 or 554 or 644 when Ud has no Pong'''
    if len(Ud) == 4:
        ''' Ud has two pairs '''   
        if numPair(Ud) == numPair(Uc) == 2:
            if not numPair(Ub) and not ps.is_solx(Ub): #e.g., Ub = 123457 < 2288?
                return F[0]
            if len(Ub) == 5 and numPair(Ub) < 2 and not ps.is_solx(Ub): #e.g., Ub = 12345?
                return F[0]
            return F[2]
        if numPair(Ud) == 2 and numPair(Uc) < 2: #if Ud has kong, numPair(Ud) is 2
            if numPair(Ub) == 2 or ps.is_solx(Ub) or ps.numpuS(Ub) > ps.numpuS(Uc):
                return F[1]
            if ps.is_solx(Uc) or ps.numpuS(Uc):
                return F[0]
            return F[1] 
        ''' Ud has a kong '''
        if numKong(Ud) and numKong(Uc) and numKong(Ub):
            return F[2]
        if numKong(Ud) == numKong(Uc) > numKong(Ub): 
            return F[0]
        if numKong(Ud) == numKong(Ub) > numKong(Uc): 
            return F[1]        
        if numKong(Ud) > numKong(Uc): 
            if len(Uc) == 4 and len(Ub) == 6: #544 or 644
                #the case when numPair(Ub) == 2 is considered before
                return F[1]
            if ps.is_solx(Ub) or numKong(Ub): #compare c and d: 554 or 544
                return F[1]
            if ps.is_solx(Uc): #c=5
                return F[0]
            if numPair(Uc) == 2 > numPair(Ub):
                return F[0]
            if has_chow(Uc) and not has_chow(Ub):
                return F[0]
            if len(Uc) == 5 and ps.numpuS(Uc) > ps.numpuS(Ub):
                return F[0]
            return F[1]
        ''' Ud has a pong '''
        if numPong(Ud) and numPong(Uc) and numPong(Ub):
            if ps.is_solx(Uc) and ps.is_solx(Ub):
                return F[2]
            if ps.numpuS(Ud) > ps.numpuS(Uc) and ps.is_solx(Ub):
                return F[1]
            if ps.numpuS(Ud) > ps.numpuS(Ub) and ps.is_solx(Uc):
                return F[0]
            if ps.numpuS(Ud) > ps.numpuS(Uc) >= ps.numpuS(Ub):
                return F[0]
            if ps.numpuS(Ud) > ps.numpuS(Ub) >= ps.numpuS(Uc):
                return F[1]
            return F[2]
        if numPong(Ud) and numPong(Uc) and not numPong(Ub) and not numKong(Ub):
            if len(Ub) == 5 and not ps.is_solx(Ub) and numPair(Ub) < 2: #554
                return F[0]
            if len(Uc) == 4 and ps.numpuS(Ud) > ps.numpuS(Uc): #544 or 644
                return F[1]
            return F[2]       
        if numPong(Ud) > numPong(Uc) and not numKong(Uc):
            if len(Uc) == 4 and len(Ub) == 6: #544 or 644: prefer d:[2888] over c:[2233]?
                if numPair(Uc) == 2:
                    if ((not numPair(Ub) and not ps.is_solx(Ub)) or \
                        (numPair(Ub) == 1 and not has_chow([x for x in Ub if Ub.count(x) < 2])) ):
                        return F[0]
                    return F[1]
                #is 112589 better than 1234 and 2288?
                return F[1]
            if ps.is_solx(Ub) or numKong(Ub) or numPong(Ub) or numPair(Ub) > 1: #compare c and d: 554 or 544
                return F[1]
            if ps.numpuS(Ub) > ps.numpuS(Uc):
                return F[1]
            if ps.is_solx(Uc) or ps.numpuS(Uc) > ps.numpuS(Ub): #c=5
                return F[0]
            if numPair(Uc) == 2 > numPair(Ub):
                return F[0]
            if has_chow(Uc) and not has_chow(Ub) and not numPair(Ub):
                return F[0]
            return F[1]
        
        ''' Ud and Uc both have 4 tiles '''
        if len(Uc) == 4: #numPair(Ud) < 2 in this case
            if numPong(Uc) or numKong(Uc): #compare Ub & Ud
                if numKong(Ub) or numPong(Ub) or ps.is_solx(Ub) or numPair(Ub) > 1 or has_chow(Ub) \
                   or (len(Ub) == 6 and not numPair(Ud) and not has_chow(Ud)):
                    return F[2]
                if not ps.numpuS(Ud):
                    return F[2]
                return F[0]         
            if not numPong(Uc) and not numPong(Ud):
                if ps.numpuS(Ud) and ps.numpuS(Uc):
                    if not numPair(Ub) and not has_chow(Ub) and len(Ub)==5: #e.g., Ub=124589
                        return F[0]
                    if ps.numpuS(Ud) > ps.numpuS(Uc) and numPair(Ud): #e.g., 3499 > 4567 > 4556
                        return F[1]
                    if ps.numpuS(Ud) == ps.numpuS(Uc)==6 and numPair(Ud): #e.g., 3455 > 4567
                        return F[1]
                    return F[2]                
                if ps.numpuS(Ud) and not ps.numpuS(Uc): # for Uc (with length 4) numpuS iff has_chow
                    return F[1]
                if ps.numpuS(Uc) and not ps.numpuS(Ud):
                    return F[2]
                if numPair(Ud) > numPair(Uc):
                    return F[1]
                return F[2]
            return F[2]
        if ps.numpuS(Ud) and len(Uc) == len(Ub) == 5: #e.g., 6679 > 13468
            if (numPair(Uc) or has_chow(Uc)) and (numPair(Ub) or has_chow(Ub)):
                return F[2]
            if (numPair(Uc) or has_chow(Uc)) and not (numPair(Ub) or has_chow(Ub)):
                return F[0]
            if not (numPair(Uc) or has_chow(Uc)) and (numPair(Ub) or has_chow(Ub)):
                return F[1]
            return F[1]

        if ps.numpuS(Ud) and len(Uc) == 5 and len(Ub) == 6: 
            if numPair(Uc) or has_chow(Uc): #12256 vs 1477
                return F[2]
            return F[1]
        
        return F[2]
        
#q: are [1, 2, 3, 4, 6] and [1, 2, 3, 6, 8] better than [2, 2, 7, 8]?

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

if __name__ == '__main__':
    # main_test
    H = [[0, 1], [0, 3], [0, 4], [0, 6], [0, 7], [1, 5], [1, 9], [1, 9], [1, 9], [2, 1], [2, 2], [2, 4], [2, 6]]

    
    
    H.sort(key=lambda t: t[0:2])

    print(H)
    print(daque(H))
    print(daquex(H))
