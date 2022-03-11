# import copy
from utils.xzutils import MJ
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\ 
########################################
### IMPORTANT ##########################
### DEFINITION ##################/\\####
########################################
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
## definition of partial solutions when n=3
# assume a1 <= a2 <= a3 
V = list(range(0,2))
def sol2(V):
    if V[0] == V[1]:
        return True
    return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(0,3))
def sol3(V):
    if V[0] == V[1] == V[2]:
        return True
    if V[1] == V[0] + 1 and V[2] == V[1] + 1:
        return True
    return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(0,5))
def sol5(V):
    if V[0] >= V[4]:
        return False
    for i in range(0,4):
        if V[i] > V[i+1]:
            return False
    if V[0] == V[1] and sol3([V[2], V[3], V[4]]):
        return True
    elif V[1] == V[2] and sol3([V[0], V[3], V[4]]):
        return True
    elif V[2] == V[3] and sol3([V[0], V[1], V[4]]):
        return True
    elif V[3] == V[4] and sol3([V[0], V[1], V[2]]):
        return True
    else:
        return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(0,6))
def sol6(V):
    if V[0] >= V[4] or V[1] >=V[5]:
        return False
    for i in range(0,5):
        if V[i] > V[i+1]:
            return False
    if (sol3([V[0], V[1], V[2]]) and sol3([V[3], V[4], V[5]])):
        #include the cases 111123, 111234, and 123333
        return True
    elif V[0] == V[1] and V[2] == V[3] and V[4] == V[5] and sol3([V[0], V[2], V[4]]): #112233
        return True
    elif V[1] == V[2] and V[3] == V[4] and V[5] == V[4] + 1 and \
         (sol3([V[0], V[1], V[3]]) or sol3([V[0], V[1], V[5]])) : #122334 or 122223
        return True
    return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(8))
def sol8(V):
    for i in range(0,4):
        if V[i] >= V[i+4]:
            return False
    for i in range(0,7):
        if V[i] > V[i+1]:
            return False
    if V[0] == V[1] and sol6([V[2], V[3], V[4], V[5], V[6], V[7]]):
        return True
    elif V[1] == V[2] and sol6([V[0], V[3], V[4], V[5], V[6], V[7]]):
        return True
    elif V[2] == V[3] and sol6([V[0], V[1], V[4], V[5], V[6], V[7]]):
        return True
    elif V[3] == V[4] and sol6([V[0], V[1], V[2], V[5], V[6], V[7]]):
        return True
    elif V[4] == V[5] and sol6([V[0], V[1], V[2], V[3], V[6], V[7]]):
        return True
    elif V[5] == V[6] and sol6([V[0], V[1], V[2], V[3], V[4], V[7]]):
        return True
    elif V[6] == V[7] and sol6([V[0], V[1], V[2], V[3], V[4], V[5]]):
        return True
    else:
        return False

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(9))
def ninetile(V):
    for i in range(8):
        if V[i] > V[i+1] or V[i] <= 0 or V[i] >= 10:
            return False       
    for i in range(5):
        if V[i] >= V[i+4]:
            return False
    return True

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(9))
def sol9(V):
    if sol3([V[0], V[1], V[2]]): #111 or #123
        if sol6([V[3], V[4], V[5], V[6], V[7], V[8]]):
            return True
    elif V[0] == V[1] and V[2] == V[0] + 1: #112
        if V[2] == V[5] and V[6] == V[2] + 1 and sol6([V[1], V[3], V[4], V[5], V[7], V[8]]): #1122223
            return True
        elif V[2] == V[4] and V[5] == V[2] + 1 and sol6([V[1], V[3], V[4], V[6], V[7], V[8]]): #112223
            return True
        elif V[2] == V[3] and V[4] == V[2] + 1 and sol6([V[1], V[3], V[5], V[6], V[7], V[8]]): #11223
            return True
    elif V[1] == V[0] + 1: #12
        if V[1] == V[4] and sol3([V[0], V[1], V[5]]) and sol3([V[6], V[7], V[8]]): #122223+333 or 345 etc
            return True
        elif V[1] == V[3] and sol3([V[0], V[1], V[4]]) and sol6([V[2], V[3], V[5], V[6], V[7], V[8]]): #12223
            return True
        elif V[1] == V[2] and sol3([V[0], V[1], V[3]]) and sol6([V[2], V[4], V[5], V[6], V[7], V[8]]): #1223
            return True
    return False
# there are in total 627 9-sols

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(11))
def eleventile(V):
    for i in range(0,7):
        if V[i] >= V[i+4]:
            return False
    for i in range(0,10):
        if V[i] > V[i+1]:
            return False
    return True
# definition of partial solutions when n=11
# assume a1 <= a2 <= a3 <= a4 <= a5 <= a6 <= a7 <= a8 <= a9 <= a10 <= a11

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def sol11(V):
    if not eleventile(V):
        return False
    elif V[0] == V[1] and sol9([V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10]]):
        return True
    elif V[1] == V[2] and sol9([V[0], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10]]):
        return True
    elif V[2] == V[3] and sol9([V[0], V[1], V[4], V[5], V[6], V[7], V[8], V[9], V[10]]):
        return True
    elif V[3] == V[4] and sol9([V[0], V[1], V[2], V[5], V[6], V[7], V[8], V[9], V[10]]):
        return True
    elif V[4] == V[5] and sol9([V[0], V[1], V[2], V[3], V[6], V[7], V[8], V[9], V[10]]):
        return True
    elif V[5] == V[6] and sol9([V[0], V[1], V[2], V[3], V[4], V[7], V[8], V[9], V[10]]):
        return True
    elif V[6] == V[7] and sol9([V[0], V[1], V[2], V[3], V[4], V[5], V[8], V[9], V[10]]):
        return True
    elif V[7] == V[8] and sol9([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[9], V[10]]):
        return True
    elif V[8] == V[9] and sol9([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[10]]):
        return True
    elif V[9] == V[10] and sol9([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[8]]):
        return True
    else:
        return False
# there are all together 4475 valid 11-sols

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(12))
def twelvetile(V):
    for i in range(0,8):
        if V[i] >= V[i+4]:
            return False
    for i in range(0,11):
        if V[i] > V[i+1]:
            return False
    return True
# definition of partial solutions when n=11
# assume a1 <= a2 <= a3 <= a4 <= a5 <= a6 <= a7 <= a8 <= a9 <= a10 <= a11

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(12))
def sol12(V):
    if not twelvetile(V):
        return False
    elif V[1] == V[0] + 1: #12
        if V[2] == V[1] + 1: #123
            if sol9([V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True
        elif V[3] == V[1] + 1: #1223
            if sol9([V[2], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True
        elif V[4] == V[1] + 1: #12223           
            if sol9([V[2], V[3], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True    
        elif V[5] == V[1] + 1: #122223           
            if sol9([V[2], V[3], V[4], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True
    elif V[0] == V[1] and V[2] == V[0] + 1: #112
#        if V[3] == V[2] + 1: #1123 (impossible)
#            if sol9(V[1], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]):
#                return True
        if V[2] == V[3] and V[4] == V[2] + 1: #11223
            if sol9([V[1], V[3], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True
        elif V[2] == V[4] and V[5] == V[2] + 1: #112223           
            if sol9([V[1], V[3], V[4], V[6], V[7], V[8], V[9], V[10], V[11]]):
                return True    
        elif V[2] == V[5] and V[6] == V[2] + 1: #1122223           
            if sol9([V[1], V[3], V[4], V[5], V[7], V[8], V[9], V[10], V[11]]):
                return True
    elif V[0] == V[2] and V[3] >= V[0] + 1: #1112 #1113
        if sol9([V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
            return True
# we can prove this is always the case if sol12(a), as 111 in a implies 222 and 333 in a 
    elif V[4] == V[0] + 1: #11112
        if sol9([V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
            return True
    else:
        return False
# there are all together 2098 valid 12-sols

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
# definition of partial solutions when n=14
# assume a1 <= a2 <= a3 <= a4 <= a5 <= a6 <= a7 <= a8 <= a9 <= a10 <= a11 <= a12 <= a13 <= a14
V = list(range(14))
def fourteentile(V):
    for i in range(0,13):
        if V[i] > V[i+1]:
            return False
    for i in range(0,10):
        if V[i] >= V[i+4]:
            return False
    return True

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
V = list(range(14))
def is_sol(V):
    if not fourteentile(V):
        return False
    elif V[0] == V[1] and sol12([V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[1] == V[2] and sol12([V[0], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[2] == V[3] and sol12([V[0], V[1], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[3] == V[4] and sol12([V[0], V[1], V[2], V[5], V[6], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True    
    elif V[4] == V[5] and sol12([V[0], V[1], V[2], V[3], V[6], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[5] == V[6] and sol12([V[0], V[1], V[2], V[3], V[4], V[7], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[6] == V[7] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[8], V[9], V[10], V[11], V[12], V[13]]):
        return True   
    elif V[7] == V[8] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[9], V[10], V[11], V[12], V[13]]):
        return True
    elif V[8] == V[9] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[10], V[11], V[12], V[13]]):
        return True
    elif V[9] == V[10] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[11], V[12], V[13]]):
        return True
    elif V[10] == V[11] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[12], V[13]]):
        return True
    elif V[11] == V[12] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[13]]):
        return True
    elif V[12] == V[13] and sol12([V[0], V[1], V[2], V[3], V[4], V[5], V[6], V[7], V[8], V[9], V[10], V[11]]):
        return True
    return False

def is_solx(V):
    ''' Decide if a pure list V of mahjong tiles is k-complete, where k = len(V)
        Arg:
            V (list): a list of pure mahjong tiles (represented as integers in [1,9])
        Return:
            (Bool)
    '''
    V.sort() #@20.02.06
    k = len(V)
    if k==0 or (k==2 and sol2(V)):
        return True
    elif k==3:
        if sol3(V):
            return True
        else:
            return False
    elif k==5:
        if sol5(V):
            return True
        else:
            return False
    elif k==6:
        if sol6(V):
            return True
        else:
            return False
    elif k==8:
        if sol8(V):
            return True
        else:
            return False        
    elif k==9:
        if sol9(V):
            return True
        else:
            return False
    elif k==11:
        if sol11(V):
            return True
        else:
            return False       
    elif k==12:
        if sol12(V):
            return True
        else:
            return False
    elif k==14:
        if is_sol(V):
            return True
        else:
            return False
    else:
        return False

def numpuS(V):
    ''' The number of pure tiles that can complete V '''
    X = list(x for x in range(1,10) if V.count(x) < 4)
    num = 0
    for x in X:
        W = V + [x]
        if is_solx(W):
            num += 1
    return num
    
    
def numS(T, KB, c):
    ''' The number of tiles that can complete T
        Args:
            T (list):  list of pure mahjong tiles with form [0]*l
            KB (list): knowledge base with form [4]*27
            c (int): the color of T
        Return:
            num (int): the number of tiles that can complete T
    '''
    X = list(t for t in MJ() if t[0] == c)
    num = 0
    for x in X:
        p = x[0]*9 + x[1] - 1
        if KB[p] == 0:
            continue
        U = [t[1] for t in T if t[0] == c]
        U.append(x[1])
        if is_solx(U): #sl I can hu t
            num += KB[p]                
    return num
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\ 
