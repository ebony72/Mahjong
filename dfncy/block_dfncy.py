#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 14 07:22:24 2021

@author: sanjiangli
"""
''' This version first computes the type of each block dcmp and then combines ... '''

'''A block B is a sublist of ordered tiles with the same color s.t. B[i]-B[i-1]<=2''' 
'''dcmp = decomposition, pdcmp = pseudo decomposition, pchow = pseudo chow, pmeld = pseudo meld'''
'''dc = daque color, dfncy = deficiency number '''
from utils.xzutils import *


def break_point(i, T, KBase):
    '''Find the first break point of a suit T'''
    if i>=len(T): return False
    t1,t2 = T[i-1],T[i]
    if t2 > t1+2 or (t2 == t1+2 and not KBase[t1]): return True
    if t1==1 and t2==2 and KBase[2]==0 and 3 not in T: return True
    if t1==8 and t2==9 and KBase[6]==0 and 7 not in T: return True
    if 1<t1<8 and t2==t1+1 and KBase[t1-2]==KBase[t2]==0 and\
        t1-1 not in T and t2+1 not in T:
        return True
    return False
    
# find all bolcks in T
'''A block respects KB, i.e., if T=(3,5), but no 4 in KB, then T has two blocks'''
def block_div(T, KBase): 
    ''' Divide a set T of the same color tiles into blocks
    Input:
          T (list): a list of integers (pure tiles, should be sorted)
    Output:
          Block (list): all blocks in T (the block with one element is included!)
    '''
    if not T: return [] 
    if len(T) == 1: return [T]
    for i in range(1,len(T)):
        '''T[i] is a separate point''' 
        if break_point(i, T, KBase):
            Block1 = block_div(T[0:i],KBase)
            Block2 = block_div(T[i:],KBase)
            return Block1+Block2
    return [T]

def block_dcmp(block, KBase):
    '''Return the set of p-decompositions of a block given the current KBase'''
    '''block (a list of integers, denoting nearly consecutive tiles of the same color)
        KBbase (the sublist of KB of this color)
        A dcmp has form (x1,x2,...,xk), where each xi is a (nonempty) meld or pmeld (tuple)
    '''
    blockx = block[:]
    Kb = KBase[:]
    '''((1,1)) == (1,1), we need use ((1,1),)'''
    if len(blockx) <= 1: return {()} #a set of dcmps, each dcmp is represented as a tuple of tuples 

    '''Examine the last tile and decompose recursively'''
    t = blockx[-1] # 1<=t<=9
    result1, result2, result3, result4, result5 = set(), set(), set(), set(), set()
    
    '''Case 1. Simply remove the last tile'''
    newblock1 = blockx[:-1] 
    result1 = block_dcmp(newblock1, Kb) 
    
    '''Case 2. Remove the pong if exists'''    
    if blockx.count(t) >= 3:
        newblock = blockx[:-3] 
        if len(newblock) < 2: 
            result2 = {((t,t,t),)}
        else:
            result0 = block_dcmp(newblock, Kb)
            result2 = concatenate_dcmps(result0, {((t,t,t),)})

    '''Case 3. Remove the pair if exists'''    
    if blockx.count(t) >= 2: #take this as a pmeld, not eye
        newblock = blockx[:-2]
        if len(newblock) < 2: 
            result3 = {((t,t),)}
        else:
            result0 = block_dcmp(newblock, Kb) 
            result3 = concatenate_dcmps(result0, {((t,t),)})

    '''Case 4. Remove the pchow [t-1,t] if it exists''' 
    '''Achtung! Kb[i] is the number of nonshown tile i+1'''
    '''if t=9 and t-2 in blockx, then (789) should be together '''
    if t-1 in blockx and ((t==9 and not (7 in blockx) and Kb[6]>0) or\
                          (t==2 and Kb[2]>0) or\
                        (2<t<9 and Kb[t-3]+Kb[t] > 0)):
        newblock = blockx[:-1]
        newblock.remove(t-1) #newblock may be not a block           
        newKb = Kb[:]
        if t==9: 
            newKb[6] = max(0, newKb[6]-1)
        elif t==2:
            newKb[2] = max(0, newKb[2]-1)
        else: 
            '''//todo: try to resolve the 1/2 dilemma'''
            if newKb[t-3] > 0 and newKb[t] > 0: 
                '''Use the larger one (i.e. t+1) first'''
                # newKb[t-3] = max(0, newKb[t-3]-1/2)
                # newKb[t] = max(0, newKb[t]-1/2)
                newKb[t] -= 1
            elif newKb[t-3] > 0 and newKb[t]==0:
                # newKb[t-3] = max(0, newKb[t-3]-1)
                newKb[t-3] -= 1
            else: # newKb[t-3] == 0 and newKb[t] > 0:
                # newKb[t] = max(0, newKb[t]-1)
                newKb[t] -= 1

        if len(newblock) < 2: 
            result4 = {((t-1,t),)}
        else:        
            result0 = max_pure_dcmps(newblock, newKb)
            result4 = concatenate_dcmps(result0, {((t-1,t),)})

    '''Case 5a. Removing the chow [t-2,t-1,t] if exists'''    
    if t>=3 and t-1 in blockx and t-2 in blockx:
        newblock = blockx[:-1]
        newblock.remove(t-1)
        newblock.remove(t-2)
        
        if len(newblock) < 2: 
            result5 = {((t-2,t-1,t),)}
        else:
            result0 = max_pure_dcmps(newblock, Kb) 
            result5 = concatenate_dcmps(result0, {((t-2,t-1,t),)})
            
        '''Case 5b. Remove the pchow [t-2,t] if exists'''    
    elif t>=3 and t-2 in blockx and Kb[t-2]>0: 
        newblock = blockx[:-1]
        newblock.remove(t-2) #newblock is possibly not a block
        newKb = Kb[:]
        newKb[t-2] -= 1
        
        if len(newblock) < 2: 
            result5 = {((t-2,t),)}
        else:
            result0 = max_pure_dcmps(newblock, newKb) 
            result5 = concatenate_dcmps(result0, {((t-2,t),)})

    '''Combine all these results'''    
    result = {()} | result1 | result2 | result3 | result4 | result5 
    return result

def concatenate_dcmps(comps1, comps2):
    '''Return all concatenations of two sets of decompositions obtained from block_dcmp 
    // we assume comps1 is obtained from a block that is before that of comps2 
    '''
    result = set()
    for pi1 in comps1:
        for pi2 in comps2:
            result.add(pi1+pi2)
    return result

def max_pure_dcmps(T, Kbase): 
    '''Return the set of all decompositions of T (a list of integers denoting pure tiles)'''

    result = {()}
    if not T: return result
    TX = T[:]
    Kb = Kbase[:]
    Blocks = block_div(TX,Kb)

    if not Blocks: return result
    if len(Blocks) == 1: 
        result = block_dcmp(TX, Kb)
        return result 

    for block in Blocks:
        comps = block_dcmp(block, Kb)
        result = concatenate_dcmps(result, comps)
    return result

def remainder(dcmp, T):
    '''Return the list of unused tiles in a maximum pure dcmp
        Here T may consist of tiles that are not singleton blocks '''
    
    if not dcmp: return T
    TX = T[:]
    used_tile = []
    Unused_Tile = TX[:]
    for pmeld in dcmp:
        if not pmeld: continue
        used_tile += pmeld
    for tile in used_tile:
        if tile not in T: raise Exception ('%s tile %s not in %s' %(dcmp,tile,T))
        if tile in Unused_Tile: 
            Unused_Tile.remove(tile)
    Unused_Tile.sort()
    return Unused_Tile  

def reserve_tile(pmeld,Kbase):
    '''return the reserved tile of a pmeld'''
    temp = [0,0,0,0,0,0,0,0,0] #tempKB
    if len(pmeld) != 2: return temp
    t1, t2 = pmeld
    if t1>t2 or t2-t1>2: raise Exception ('pmeld error', pmeld)
    if t1==t2: 
        temp[t1-1] += 0 #don't consider pairs here
        return temp
    if t2 == t1+2:
        temp[t1] += 1
    elif t1==1:
        temp[2] += 1
    elif t1==8:
        temp[6] += 1
    else:
        if Kbase[t2]:
            temp[t2] += 1
        else:
            temp[t1-2] += 1 #//todo: Is this good?

        # temp[t1-2] += 1/2 #//todo: Is this good?
        # temp[t2] += 1/2
    return temp

def get_ini_em(S, Kbase):
    '''Get the initial values of re, rm, and em, where S contains tiles in the  singleton blocks'''
    
    if not S: return 0, 0, 0
    Kb = Kbase[:]
    SX = S[:]
    rm = get_meld(SX, Kb)
    eye_Tile = [t for t in SX if Kb[t-1]>0] #tiles can form the eye
    
    '''re conflicts with rm as they may involve the same tile, like 3, 
        which can form both eye and meld'''
    re = min(len(eye_Tile),1)
    if not rm or len(eye_Tile)!=1: return re, rm, 0
    if len(S)==1 and rm==re==1: return 1,1,1

    '''Crete the eye from eye_Tile and check if we can still make a meld'''
    for t in eye_Tile:
        Kbtemp = Kb[:]
        U = SX[:]
        Kbtemp[t-1] -= 1 #reserve one t for the eye
        U.remove(t)
        if get_meld(U, Kbtemp):
            return 1, 1, 0
    return 1, 1, 1 

def join_em(re1,rm1,em1,re2,rm2,em2):
    if max(re1,rm1,em1) == max(re2,rm2,em2)==1:
        return max(re1,re2), max(rm1,rm2), 0
    return max(re1,re2), max(rm1,rm2), max(em1,em2)

def get_type(dcmp, block, Kbase, blockRest, cal_em, emconflict):
    '''Get the type set of dcmp, calc_em = (re0,rm0,em0)'''
    if not block: return {(0,0,0,0,0,0,0)}
    if list(pm for pm in dcmp if len(pm)!=3 and len(pm)!=2): 
        raise Exception('dcmp error', dcmp)

    Kb = Kbase[:]
    if len(dcmp) == 0: #dcmp is ()
        m,n,p,e = 0,0,0,0
        hasPair = []
        hasEye = []
    else:
        m = len(list(pm for pm in dcmp if len(pm)==3)) #number of melds
        n = len(dcmp) - m 
        
        temp = [0,0,0,0,0,0,0,0,0] #tempKB
        for pmeld in dcmp:
            tempx = reserve_tile(pmeld,Kbase)
            temp = [temp[i]+tempx[i] for i in range(9)]
        '''//todo: Not precise. Consider when KB has only 1 tile 6, 
            but two pmelds (45) and (78) both need 6. '''
        # Kb = [ math.ceil(Kbase[i]-temp[i]) for i in range(9)]
        Kb = [ max(0,Kbase[i]-temp[i]) for i in range(9)]
        
        hasPair = [pm[0] for pm in dcmp if len(pm)==2 and pm[0]==pm[1]]
        hasEye = [t for t in hasPair if Kb[t-1]==0]
        p = len(hasPair)
        e = len(hasEye)
        '''Exclude pi if it has two or more eyes'''
        if e > 1: return {(0,0,0,0,0,0,0)} #@210706

        for t in hasPair:
            if t not in hasEye:
                Kb[t-1] -= 1 #reserve one t to develop a pong [ttt]
                    
    Unused_Tile = remainder(dcmp, blockRest)
    rm = get_meld(Unused_Tile, Kb)
    
    if e: #re does not matter
        return {(m,n,p,e,0,rm,0)}
    
    eye_Tile = [t for t in Unused_Tile if Kb[t-1]>0] #tiles that can form the eye
    
    '''Check if eye-meld conflict exists, i.e., can we form both eye and meld'''
    re = min(len(eye_Tile),1)
    if not emconflict or max(cal_em)==max(re,rm): #conflict cancelled
        return {(m,n,p,e,re,rm,0)}
    
    if len(Unused_Tile) == 1: #re, rm cannot both be 1
        return {(m,n,p,e,re,rm,re*rm)}
    if not p and not re:
        return {(m,n,0,0,0,rm,0)}

    '''If re=0 and p>0, we may use one pair (tt) as the eye. 
        We need to free the reserved t and see if rmp>0'''
    rmp = 0 # check if we can use a freed t to form a meld
    if p>e==0: #use one pair as the eye
        for t in hasPair:
            Kbtemp = Kb[:]
            Kbtemp[t-1] += 1 #free the reserved t 
            U = Unused_Tile[:]
            if get_meld(U, Kbtemp):
                rmp = 1
                break

    '''Crete the eye from eye_Tile and check if we can still make a meld'''
    for t in eye_Tile:
        Kbtemp = Kb[:]
        U = Unused_Tile[:]
        Kbtemp[t-1] -= 1 #reserve one t for the eye
        U.remove(t)
        if get_meld(U, Kbtemp):
            return {(m,n,p,0,1,1,0)}
        
    '''The 3rd type uses one pair as the eye''' 
    return {(m,n,p,0,re,0,0),(m,n,p,0,0,rm,0),(m,n,p,min(p,1),0,rmp,0)} 
    
def typeset(block, Kb, blockRest, cal_em, emconflict):
    '''Return the typeset of block, where cal_em = (re0,rm0,em0), emcomflict (bool)
        blockRest: sublist of tiles in block not in any singleton block of the suite
    '''
    TypeSet = set()
    comps = block_dcmp(block, Kb)  
    for dcmp in comps:
        dtype = get_type(dcmp, block, Kb, blockRest, cal_em, emconflict) #dtype is a set
        TypeSet = TypeSet | dtype
        
    TypeList = list(TypeSet)
    if not TypeList: return [(0,0,0,0,0,0,0)]

    return TypeList


def join_typeset(TypeList1, TypeList2):    
    '''Return the combined TypeList of two blocks '''    
    TypeSet = set()
    
    for type1 in TypeList1:
        for type2 in TypeList2:
            if type1[3]+type2[3] > 1: continue
            re1,rm1,em1 = type1[4:7]
            re2,rm2,em2 = type2[4:7]
            re0,rm0,em0 = join_em(re1,rm1,em1,re2,rm2,em2)
            newtype = (type1[0]+type2[0],type1[1]+type2[1],\
                       type1[2]+type2[2],type1[3]+type2[3],re0,rm0,em0)
            TypeSet.add(newtype)

    TypeList = list(TypeSet)
    return TypeList

def max_pure_type(T, Kbase, cal_em_local, cal_em, emconflict): 
    '''Return all types of a suite T (a list of integers denoting pure tiles)
        cal_em_local is the cal_em of the suite, cal_em is that of the hand
    '''
    if not T: return [(0,0,0,0,0,0,0)]
    TX = T[:]
    Kb = Kbase[:]
    Blocks = block_div(TX,Kb)
    SingBlocks = [b[0] for b in Blocks if len(b)==1]
    TRest = T[:]
    for t in SingBlocks:
        Blocks.remove([t])
        TRest.remove(t)
    
    TypeList = [(0,0,0,0) + cal_em_local]
    if not Blocks: return TypeList  
    for block in Blocks:
        blockRest = [t for t in block if t in TRest]
        TypeListx = typeset(block, Kb, blockRest, cal_em, emconflict) 
        TypeList = join_typeset(TypeList, TypeListx)

    return TypeList

def has_meld(Kbase):
    '''Check if Kbase has a meld'''
    for t in range(1,10):
        if Kbase[t-1]==0: continue
        if Kbase[t-1]>2 or (t>=3 and Kbase[t-3] and Kbase[t-2]) or\
            (8>=t>=2 and Kbase[t-2] and Kbase[t]) or\
                (7>=t and Kbase[t] and Kbase[t+1]):
            return 1
    return 0

def get_meld(U,Kbase):
    '''Check if we can develop a meld from some tile in U '''
    for t in set(U):
        if Kbase[t-1]>1 or (t>=3 and Kbase[t-3] and Kbase[t-2]) or\
            (8>=t>=2 and Kbase[t-2] and Kbase[t]) or\
                (7>=t and Kbase[t] and Kbase[t+1]):
            return 1
    return 0

def noo_type(handtype,pg):
    '''Check if a handtype is illegal or has cost >=6'''
    m,n,p,e,re,rm,em = handtype
    m += pg #the number of pongs
    if e> 1 or m+n > 5: return True
    if m+n==5 and p==0: return True
    if m==0 and n<=3: return True #cost >= 6
    if m==1 and n<=1: return True #cost >= 6
    return False

def hand_type(TypeList1, TypeList2, pg): 
    '''Return the combined TypeList of the two color hand with l existing Pongs
        TypeList1/2 is the TypeList of suite1/2 which are not daque color '''
        
    TypeSet = set()
    for type1 in TypeList1:
        for type2 in TypeList2:
            m,n,p,e = type1[0]+type2[0],type1[1]+type2[1],\
                       type1[2]+type2[2],type1[3]+type2[3]
            re1,rm1,em1 = type1[4:7]
            re2,rm2,em2 = type2[4:7]
            re0,rm0,em0 = join_em(re1,rm1,em1,re2,rm2,em2)
            newtype = (m,n,p,e,re0,rm0,em0)
            TypeSet.add(newtype)
    TypeList = list(TypeSet)
    
    TypeList = [x for x in TypeList if not noo_type(x,pg)]
    TypeList.sort(key=lambda t: t[0:7], reverse=True)
    
    '''Most often, we need only consider the top 5 types, but sometimes
        the optimal cost is obtained from the 18th type:
        17 (3, 0, 0, 0, 1, 1, 1) (1, 4, 1, 0, 0, 0, 0)
       but this restriction does not increase the speed! 
        '''
    # l = len(TypeList)
    # TypeList = TypeList[0:min(l,30)]
    return TypeList

def get_dfncy(TypeList, pg, ke, km, optdfncy):
    '''Calculate the dfncy from the combined TypeList. '''
    TL = TypeList[:]
    # print('ha', len(TL))

    cost = 100
    for i in range(len(TL)):
        m,n,p,e,re,rm,em = TL[i] #the i-th type
        m += pg
        ''' n-e = (n-p) + (p-e) are valid pmelds, e out of p pairs cannot form pongs, 
           're' denotes if the eye can be formed from an existing unused tile '''
        # if e>1 or m+n>5 or (m+n==5 and p==0): raise Exception (TL[i])
        if m+n<=4 and p==re==ke==0: continue #cannot make the eye
        if p>0 and e==re==ke==rm==km==0 and m+n<=4: continue
        if m+n-e <= 3 and rm==km==0: continue #cannot make a meld
        if m+n-e <= 3 and p==ke==km==0 and em==1: continue #cannot make a meld
        
        if m+n-e>=4: 
            if e>0: #we have an eye and 4 (p)melds
                fit = 4-m
            elif m+n>4 and p>0: #use a pair as the eye
                fit = 4-m
            elif re==1: #use a tile in the remainder to form the eye
                fit = 4-m+1
            elif p>0 and rm==1: #use a pair as the eye when m+n=4 & re=0
                fit = 4-m+1 
            else: # (p>e=re=0 & m+n=4 & rm=0 & km=1) or (p=re=0 & ke=1)
                fit = 4-m+2 
        else: # we have less than 4 pmelds
            '''If rm=1 then we assume all empty melds can be made this way''' 
            mcost = 2*rm + 3*(1-rm) #the cost of making a meld
            ecost = re + 2*(1-re)
            if e>0: #create a meld
                '''n-e=#pmelds, 4-(m+n-e) = #empty_melds'''
                fit = (n-e) + mcost*(4-m-n+e) 
            else: #e=0
                if p==0:#as p=0 thus re+ke=1, we also have rm+km=1
                    fit = n + mcost*(4-m-n) + ecost + em 
                elif re==1: #as the cost is finite, we have rm+km=1
                    fit = n + mcost*(4-m-n) + 1
                elif re==ke==0:
                    fit = n-1 + mcost*(4-m-n+1) #use a pair as the eye
                elif re==0 and ke==1 and rm==0: #km=1
                    fit = n + mcost*(4-m-n) + 2
                else: #p>0, re=0, ke=1, rm=1 
                    fit1 = n-1 + mcost*(4-m-n+1) #use a pair as the eye
                    fit2 = n + mcost*(4-m-n) + ecost #create the eye
                    fit = min(fit1,fit2)
        if i==0: 
            fit0 = fit

        if fit <= optdfncy: return fit
        if fit < cost: cost = fit

    return cost

def singBlock(H,Pg,KB,dc):
    c1 = (dc+1) %3
    c2 = (dc+2) %3
    NKB = [KB[0:9], KB[9:18], KB[18:27]]
    KB1 = NKB[c1]
    KB2 = NKB[c2]
    T1 = [t[1] for t in H if t[0] == c1]
    T2 = [t[1] for t in H if t[0] == c2]
    Blocks1 = block_div(T1,KB1)
    SingBlocks1 = [[c1,b[0]] for b in Blocks1 if len(b)==1]
    Blocks2 = block_div(T2,KB2)
    SingBlocks2 = [[c2,b[0]] for b in Blocks2 if len(b)==1]
    SingBlock = SingBlocks1 + SingBlocks2
    return SingBlock
              
def dfncy(H, Pg, KB, dc):
    '''
    Input:
        H (list): a sorted list of tiles in the hand of the player 
        Pg (list): the pong or kong tile
        dc (int): the daque color
        KB (list): the knowledge base
    Output:
        dfncy (int): the final deficiency 
    '''
    H.sort(key=lambda x: x[0:2])
    c1 = (dc+1) %3
    c2 = (dc+2) %3
    NKB = [KB[0:9], KB[9:18], KB[18:27]]
    KB1 = NKB[c1]
    KB2 = NKB[c2]
    T1 = [t[1] for t in H if t[0] == c1]
    T2 = [t[1] for t in H if t[0] == c2]

    DT = [t for t in H if t[0] != dc] # delete all tiles with the daque color
    temp_dfncy1 = 7
    if not Pg:
        useful_sing_tile = [t for t in DT if DT.count(t)%2 == 1 and KB[kbf(t)] ]
        num_pairs_in_KB = sum(KB1[i]//2+KB2[i]//2 for i in range(9)) 
        '''Calculate the deficiency in the case of 7-pair'''
        l = len(useful_sing_tile)
        temp_dfncy1 = 7-numPair(DT) 
        # print('7-pair',temp_dfncy1, l, num_pairs_in_KB)
        if l < temp_dfncy1: #we need creat pairs from KB  
            if num_pairs_in_KB < temp_dfncy1 - l: 
                temp_dfncy1 = 100
            else:
                temp_dfncy1 += temp_dfncy1 - l

    Kbase_has_Meld = 1
    if not has_meld(KB1) and not has_meld(KB2):
        Kbase_has_Meld = 0    
    Kbase_has_Pair = 1 
    if max(KB1) <= 1 and max(KB2) <= 1:
        Kbase_has_Pair = 0
    
    Blocks1 = block_div(T1,KB1)
    SingBlocks1 = [b[0] for b in Blocks1 if len(b)==1]
    Blocks2 = block_div(T2,KB2)
    SingBlocks2 = [b[0] for b in Blocks2 if len(b)==1]
    
    '''Define optdfncy'''
    lsing = len(SingBlocks1)+len(SingBlocks2) #isolated tiles
    ltemp = (14-len(DT)-3*len(Pg))+lsing #isolated + daque tiles
    optdfncy = min(1,ltemp) #the best dfncy we can have
    if 1 <= ltemp <= 2: optdfncy = 1
    if ltemp == 3: optdfncy = 2 #(xxx)(xxx)(xxx)(+2)(xx)
    if 4 <= ltemp <= 5: optdfncy = 3 #(xxx)(xxx)(xxx)(+2)(+1) (xxx)(xxx)(xx+1)(+2)(xx)
    if ltemp == 6: optdfncy = 4 #(xxx)(xxx)(xx+1)(+2)(+1)
    if ltemp == 7: optdfncy = 5 #(xxx)(xx+1)(xx+1)(+2)(+1)
    if ltemp == 8: optdfncy = 5 #(xxx)(xxx)(+2)(+2)(+1)
    
    
    re1, rm1, em1 = get_ini_em(SingBlocks1, KB1)
    re2, rm2, em2 = get_ini_em(SingBlocks2, KB2) 
    re0, rm0, em0 = join_em(re1,rm1,em1,re2,rm2,em2)

    emconflict = True
    if max(re0,rm0) > em0: emconflict = False
    cal_em = (re0,rm0,em0)
    cal_em1 = (re1,rm1,em1)
    cal_em2 = (re2,rm2,em2)

    TypeList1 = max_pure_type(T1, KB1, cal_em1, cal_em, emconflict)
    TypeList2 = max_pure_type(T2, KB2, cal_em2, cal_em, emconflict)
    TypeList = hand_type(TypeList1, TypeList2, len(Pg))
    
    
    temp_dfncy2 = get_dfncy(TypeList, len(Pg), Kbase_has_Pair, Kbase_has_Meld, optdfncy)
    dfncy = min(temp_dfncy1, temp_dfncy2)  

    return dfncy

if __name__ == '__main__':    
    T = [[0, 2], [0, 4], [0, 4], [0, 5], [0, 6], [0, 6], [1, 2], [1, 3], [1, 3], [1, 4], [1, 4], [1, 5], [1, 8], [1, 8]]
    KB = [0, 0, 0, 0, 0, 1, 0, 1, 2, 1, 2, 0, 0, 1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    dc = 2
    Pg = []

    print(dfncy(T,Pg,KB,dc))

 
    