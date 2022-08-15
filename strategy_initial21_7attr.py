'''An evolved version of strategy_initial and do not update the latter anymore'''

'''Revised on June 2, 2020: removed n_hu from all check_xxx 
        as it can be obtained from dealer.n_hu() '''
'''Revised on June 5, 2020: revised vec_discard_val by deleting important tiles 
    from the discard list but the effect is almost the same as before '''
'''Revised on June 4, 2020: 
    vec_discard_val revised to address all essential tile issue'''
    
from dfncy.block_dfncy import dfncy 
from utils.xzutils import *

'''In this program, player choose this imperfect strtegy to decide whether to hu/
   robkong/zimo/pong/kong/zikong and which card to discard
'''

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
        
def check_hu(player, dealer, last_player, players):
    ''' Check if the player hu when someone discards a card which completes his hand
    Args:
        player (object)
        dealer (object): Dealer
        last_player (int): the id of the last player
    '''
    return 'hu'

    
def check_robkong(player, dealer, jiakong_card, players):
    '''Check if the player robkong when some other player jiakong
    '''
    return 'robkong'

 
def check_zimo(player, dealer, last_drawn_card, players):
    ''' Check if the player zimo when he draws a card
    Args:
        dealer (object): Dealer
    '''
    return 'zimo' 
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\


def check_zikong(player, dealer, players):
    ''' Check if the player zikong when he draws a card
    Args:
        dealer (object): Dealer
    '''
    
    T = player.hand[:]
    Pg = [ p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer,players)
    # Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color
    HD = [t for t in T if t[0] != dc] #sl tiles without daque color
    HD.sort(key=lambda t: t[0:2])
    cur_dfncy = dfncy(HD,Pg,KB,dc) # the deficiency of player's hand
    
    KS = remove_duplicates(HD)
    Kong_candidates = list(x for x in KS if HD.count(x) == 4) +\
                      list(x for x in KS if x in Pg) #Kong_to_be_made in HD
    
    '''The procedure below indeed only considers the first Kong candidate,
            but this is okay for this imperfect strategy.
            Instead, we may directly use the check_kong function from strategyz. '''
    for s in Kong_candidates:
        H1 = HD[:]
        
        if s in Pg:
            H1.remove(s)
            Pg1 = Pg[:]
        else:                
            H1.remove(s)
            H1.remove(s)
            H1.remove(s)
            H1.remove(s)
            Pg1 = Pg + [s]

        after_kong_dfncy = dfncy(H1, Pg1, KB, dc)
        numWl = len(dealer.deck)        
        if numWl >= 25 or after_kong_dfncy <= cur_dfncy: 
            if HD.count(s) == 4:  
                return ['ankong', s]
            return ['jiakong', s]
    return ['stand', 'zikong']
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
        
# we define a function to test if we should pong when some agent discard t
def ipong(T, Pg, KB, t, numWl, dc): #does not involve KB
    ''' Test if we should pong when some agent discards t
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            t (list): the tile [c,i] just discarded by another player
            numWl (int): the number of tiles in the Wall
            dc (int): the discard (daque) color of the player
        Return:
            (Bool): True or False (list)
    ''' 
    xx = dfncy(T, Pg, KB, dc) 

    S = T[:]
    S.remove(t)
    S.remove(t)
    Pg1 = Pg[:]
    Pg1.append(t)
    newdfncy = dfncy(S,Pg1,KB,dc)
    # print(xx, newdfncy)    
    # print('T =', S)
    # print('Pg =', Pg1)
    # print('KB =', KB)
    # print('dc =', dc)
    if newdfncy <= xx: return True
    if newdfncy < xx+2 and numWl >= 25: return True
    return False

def check_pong(player, dealer, players):
    ''' Check if the player pong when someone discards a card which he can pong
    Args:
        dealer (object): Dealer
        players (list of players)
    '''
    card = dealer.table[-1]
    T = player.hand[:]
    Pg = [p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer,players)
    HD = [t for t in T if t[0] != dc]

    numWl = len(dealer.deck)       
    if ipong(HD, Pg, KB, card, numWl, dc):
        return 'pong'
    return 'stand'

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

def ikong(T, Pg, KB, t, numWl, dc): # dose not involve KB
    ''' Test if and when should we kong t discarded by other player
        (We didn't consider if this t will be robbed)
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            t (list): the tile [c,i] just discarded by another player
            numWl (int): the number of tiles in the Wall
            dc (int): the discard (daque) color of the player
        Return:
            (Bool): True or False (list)
    ''' 
    cur_dfncy = dfncy(T, Pg, KB, dc)
   
    S = T[:]
    S.remove(t)
    S.remove(t)
    S.remove(t)
    Pg1 = Pg[:]
    Pg1.append(t)
    after_kong_dfncy = dfncy(S, Pg1, KB, dc) 
    if after_kong_dfncy < cur_dfncy or numWl >= 20:
        return True
    if after_kong_dfncy == cur_dfncy and (cur_dfncy==1 or numWl >= 15):
        return True
    return False

def check_kong(player, dealer, players):
    ''' Check if the player kong/pong when someone discards a card
    Args:
        dealer (object): Dealer
        players (list of players)
    '''
    card = dealer.table[-1]
    T = player.hand[:]
    Pg = [p[0] for p in player.pile]
    dc = player.daque_color
    KB = player.kgbase(dealer,players)
    HD = [t for t in T if t[0] != dc]
 
    numWl = len(dealer.deck)

    if ikong(HD, Pg, KB, card, numWl, dc): #revealed kong (ming kong)
        return 'kong'       
    if ipong(HD, Pg, KB, card, numWl, dc):
        return 'pong'
    return 'stand'

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\

def discard_val(cur_dfncy, t, T, Pg, KB, dc): # we include hv here to avoid redundant computations in vec_discard_val
    # the total chance of becoming 'better' after discarding t
    #cur_dfncy = hk.hyval(T,Pg) # T has no daque tiles

    ''' The value of t as the tile to discard //check if discard is used only when I draw a tile from the Wall
        Note here T+Pg*3 is a 14-tile. 
        Args:
            T (list):  list of mahjong tiles with form [[0,0]]*l, which contains no tile [dc,j]
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            t (list): a candidate mahjong tile in T to be discarded
            dc (int): the discard (daque) color of the player
            hv (int): the hyval if computed, hv == 0 cannot happen as the player should have declared win
        Return:
            w (int): value (the higher the better)
    '''
    # w = 0
    X = list(x for x in MJ() if x!=t and x[0]!=dc and KB[kbf(x)] \
             and effective_tile(x, t, cur_dfncy, T, Pg, KB, dc) )
    # for x in X:
    #     p = kbf(x)
    #     if KB[p] > 0 and x != t:
    #         T1 = xreplace(T, t, x)
    #         '''Include the case when T is complete but we want to, e.g., zimo'''
    #         if dfncy(T1, Pg, KB, dc) == max(0, cur_dfncy - 1):
    #             w += KB[p]
                
    nn = sum([KB[kbf(x)] for x in X])
    return nn

def effective_tile(x, t, cur_dfncy, T, Pg, KB, dc):
    '''x is an effective tile if we discard t from T'''
    if t not in T: raise Exception('Effective Tile Error', t, T)
    T1 = xreplace(T, t, x)
    if dfncy(T1, Pg, KB, dc) == max(0, cur_dfncy - 1):
        return True
    return False

    
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def vec_discard_val(T, Pg, KB, dc):
    ''' The discard_value list
        args:
            T (list):  list of mahjong tiles with form [[0,0]]*l, T contains no daque tiles
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            dc (int): the discard (daque) color of the player
        return:
            B (list): a sorted list of [value, tile]
    '''
    cur_dfncy = dfncy(T, Pg, KB, dc)
    TR = remove_duplicates(T) #the discard list
    
    disc_list = TR[:] 
    '''Remove kong tiles from the discard list'''
    for  x in TR:
        if T.count(x) == 4 or x in Pg:       
            disc_list.remove(x)   
    if not disc_list: raise Exception ('All are kong tiles', T)
    '''A tile is essential is its removal increase the dfncy!'''
    '''Remove essential tiles from the discard list'''
    disc_listX = disc_list[:]
    for x in disc_list:
        TX = T[:]
        TX.remove(x)
        new_dfncy = dfncy(TX, Pg, KB, dc)
        # print(x, new_dfncy, cur_dfncy)
        if new_dfncy > cur_dfncy: #x is essential in T
            disc_listX.remove(x) #should not discard
            
    '''disc_listX can be empty if we have kong tile,
        e.g., pong 06, T=0608090909, suppose 07 is not available.
        After pong, we have dfncy 1, but 08 is essential 
        
        In this case, we consider meld essential tile'''
    if not disc_listX:
        disc_listY = disc_list[:]
        c1, c2 = (dc+1)%3, (dc+2)%3
        suit1 = [tile[1] for tile in T if tile[0]==c1]
        suit2 = [tile[1] for tile in T if tile[0]==c2]
        # print(suit1, suit2)
        for t1 in suit1:
            if [c1,t1] not in disc_listY: continue
            if meld_essential_tile(t1,suit1):                   
                disc_listY.remove([c1,t1])
        for t2 in suit2:
            if [c2,t2] not in disc_listY: continue
            if meld_essential_tile(t2,suit2):
                disc_listY.remove([c2,t2])
        if not disc_listY:
            printout(T, Pg, KB, dc)
            raise Exception('No preferrable discard tiles')
        disc_list = disc_listY[:]
    else:
        disc_list = disc_listX[:]
    disc_list.sort(key=lambda t: t[0:2]) 
    '''If we want to use discard_val'''
    B = list([discard_val(cur_dfncy, t, T, Pg, KB, dc), t] for t in disc_list)   

    # '''If we want to use discard_step_val when cur_dfncy <= 2'''
    # if cur_dfncy > 2:
    #     B = list([discard_val(cur_dfncy, t, T, Pg, KB, dc), t] for t in disc_list) 
    # else:
    #     B = list([discard_step_val(2, t, T, KB, dc), t] for t in disc_list)   

    B.sort(key=lambda x: x[0], reverse=True)
    return B

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
def further_choose(B, Table):
    ''' If there are multiple tiles with the best extended discard value, select one 
        Arg:
            B (list): the output of vec_discard_val
        Return:
            t (list): the mahjong tile to discard
    '''
    if not B:
        raise Exception ('The discard list R is %s and nR %s Tile %s' %B)
    
    Tile = [x[1] for x in B if x[0]==B[0][0]]
    if len(Tile) == 1:
        return Tile[0]
    
    '''@210604: Discard a tile that appears in the table'''
    tab = len(Table)
    s = min(tab, 4)
    for i in range(s):
        tile = Table[-i-1]
        if tile in Tile:
            return tile 
    
    #sl select the least central tile to discard
    ra = []
    for t in Tile:
        a1 = t[1] - 1
        a2 = 9 - t[1]
        a = min(a1, a2)
        ra.append(a)
    ind = ra.index(min(ra))
    t = Tile[ind]
    return t

def Discard_Q_tile(Q, dc, Table):
    ''' Select a tile from Q to discard
        Arg:
            Q (list): the list of tiles with the daque color, assumed to be nonempty
            Table (list): the list of discarded tiles on the table
            dc (int): the discard (daque) color of the player
        Return:
            (list): a tile            
    '''
    Q.sort()
    x0 = Q[-1]
    tab = len(Table)
    s = min(tab, 4)
    for i in range(s):
        tile = Table[-i-1]
        if tile[0]==dc and tile[1] in Q:
            return tile
    
    for x in Q:
        if Q.count(x)>1:
            x0 = x
            break            
     # if we know the set of discarded tiles, we may select the one in Q which was discarded before
    discard_tile = [dc, x0]
    return discard_tile

def Discard_tile(HD, Pg, KB, Table, dc):    
    ''' Select a tile from HD to discard when, and only when, Q is empty 
        Arg:
            Q (list): the list of tiles with the daque color, should be empty//deleted
            HD (list): the list of tiles in the player's hand (may include dicard color tiles)
            Pg (list): list of ponged tiles with form  [[0,0]]*k
            KB (list): knowledge base with form [4]*27
            dc (int): the discard (daque) color of the player
            Table (list): the list of discarded tiles on the table//edeleted
            //PgOther (list): the list of ponged tiles by other players [not used here]
        Return:
            B (list): a sorted list of [value, tile]            
    '''   
    M = HD[:]
    M.sort(key=lambda t: t[0:2])
    D = vec_discard_val(M, Pg, KB, dc)
    # if len(D)>1: 
    #     print('Found it!')
    #     print(D)
    #     print(M)
    #     print(Pg)
    td = further_choose(D, Table)  #td = D[0][1] # discard t, could make it a random one in D
    return td

#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\


def select_a_card_to_discard(player, dealer, players):
    ''' Check if the player pong/kong/hu when someone discards a card
    Args:
        dealer (object): Dealer
        players (list of players)
    '''
    
    Table = dealer.table[:]
    T = player.hand[:]
    dc = player.daque_color
   
    Q = [t[1] for t in T if t[0] == dc] #sl tiles of daque color
    if Q:
        discard_tile = Discard_Q_tile(Q, dc, Table)
        return discard_tile

    T.sort(key=lambda t: t[0:2])                 
    Pg = [p[0] for p in player.pile]
    KB = player.kgbase(dealer, players)
    
    
    #test @210525    
    # h = report_diff_selected_tile(T,Pg,KB,dc)
    # if h: print('ha', h)
    #end test
    discard_tile = Discard_tile(T, Pg, KB, Table, dc)

    return discard_tile
#\__/#\#/\#\__/#\#/\__/--\__/#\__/#\#/~\
# For test
if __name__ == '__main__':
    numWl = 48 
    n_hu = 0 
    dc = 0 
    c = None 
    Q = [] 
    T = [[1, 1], [1, 2], [1, 5], [1, 5], [1, 7], [1, 9], [2, 1], [2, 2], [2, 6], [2, 8], [2, 8]] 
    Pg =  [[2, 5]] 
    Table = [[2, 9], [2, 3], [0, 2], [2, 9], [2, 7], [2, 7], [2, 9]] 
    KB = [4, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 4, 4, 2, 4, 3, 4, 3, 3, 3, 3, 4, 1, 3, 2, 2, 1]
    discard_tile = Discard_tile(T, Pg, KB, Table, dc)
    print(discard_tile)
    # s = ipong(T, Pg, KB, t, numWl, dc)
    # print(s)
