import utils.hysolx as hs
from utils.xzutils import MJ
base_score = 1
#base_score = 400
    
# judge tianhu,dihu
def judge_tiandihu(hu_player, numWl):
    '''Judge tianhu and dihu
        Args:
            hu_player (object)
            numWl (int): the number of Wall tiles
        Returns:
            hu_way (string)
            hu_times (int): fanfan
    '''
    if hu_player.player_id == 0 and numWl == 55:
        return ["tianhu", 32]
    if (hu_player.player_id == 1 and numWl == 54) or (hu_player.player_id == 2 and numWl == 53) \
            or (hu_player.player_id == 3 and numWl == 52):
        return ["dihu", 32]
    return None

# judge pengpenghu, jingoudiao, shibaluohan, longqidui, qidui, these five hu_way cannot happen in the same time
# it's not necessary to distinguish between jingoudiao with shibaluohan, longqidui and qidui
def judge_pengpenghu_qidui(hand, Pile):
    ''' Judge pengpenghu, jingoudiao, or qidui
        Args:
            hand (list)
            Pile (list)
        Returns:
            hu_way (string)
            hu_times (int): fanfan
    '''
    n_pile = len(Pile) # the number of pong and kong
    unique_tile = [] # the different tile in player's hand
    [unique_tile.append(tile) for tile in hand if tile not in unique_tile] #q
    n_pair = 0
    n_pong = 0
    for tile in unique_tile:
        if hand.count(tile) == 4:
            n_pair += 2
            flag = 1
        elif hand.count(tile) == 2:
            n_pair += 1
        elif hand.count(tile) == 3:
            n_pong += 1

    if n_pile == 4:
        return ["jingoudiao", 4]

    elif n_pong + n_pile == 4 and n_pair == 1:
        return ["pengpenghu", 2]
        
    elif n_pair == 7:
            return ["qidui", 4]
    
    return None

# judge qingyise
def judge_qingyise(hand, Pile):
    '''Judge if tiles in the complete hand are in the same color
        Args:
            hand (list)
            Pile (list)
        Returns:
            hu_way,
            hu_times (int): fanfan
    '''
    n_pile = len(Pile) # the number of pong and kong
    unique_tile = [] # the different tile in player's hand
    [unique_tile.append(tile) for tile in hand if tile not in unique_tile]
    color = hand[0][0]
    n_p = 0
    n_t = 0

    for pile in Pile:
        if pile[0][0] == color:
            n_p += 1
    for tile in unique_tile:
        if tile[0] == color:
            n_t += 1
    if n_p == n_pile and n_t == len(unique_tile):
        return ["qingyise", 4]
    return None


def compute_hu_score(hu_player, players, numWl, dianpao_player):
    '''Consider zimo, qingyise and (pengpenghu, qidui, jingoudiao) and compute all related players' score
    Args:
        players (object)
        hu_player (object)
        dianpao_player (object): if zimo, it's None
    Return:
        players (objects): info about players updated
    '''
    
    all_hand = hu_player.hand[:] # all tiles in the hu_player's hand (including pile)
    for pile in hu_player.pile:
        for p in pile:
            all_hand.append(p)
    d_tile = [] # the different tile in player's all_hand
    [d_tile.append(tile) for tile in all_hand if tile not in d_tile]

    n_gen = 0 # the number of gen which contains four identical tile in player's hand.
    for tile in d_tile:
        if all_hand.count(tile) == 4:
            n_gen += 1

            
    result0 = judge_tiandihu(hu_player, numWl) # Check if 'tian-di-hu'
    if result0:
        n_tdhu = 0 #number of other players when tiandihu
        tdhu_id = [] # id of other players when tiandihu
        for player in players:
            if player.winning == True or player.player_id == hu_player.player_id:
                continue            
            player.myscore = player.myscore - result0[1]*base_score
            player.scoreRecords.append(['beitiandihu', hu_player.player_id, result0[1], -result0[1]*base_score])
            tdhu_id.append(player.player_id)
            n_tdhu += 1 

        hu_player.myscore = hu_player.myscore + n_tdhu * result0[1] * base_score
        hu_player.scoreRecords.append([result0[0], tdhu_id, result0[1], +result0[1]*base_score])        
        #hu_player.hu_way.append(result0[0])
        #hu_player.myscore = result0[1]*base_score
        return players 
       
    result1 = judge_pengpenghu_qidui(hu_player.hand, hu_player.pile)
    #'Check if '7-pair', 'peng-peng-hu', or 'jin-gou-diao'
    result2 = judge_qingyise(hu_player.hand, hu_player.pile) #Check if 'qing-yi-se'
    hu_times = 1 #fan
    n_zimo = 0 # the number of other players when hu_player zimo

    #20200603: replace elif with if, as 'zimo' and 'kongshanghua' can happen simultaneously 
    if 'zimo' in hu_player.hu_way:
        hu_times = hu_times*2
    if 'robkong' in hu_player.hu_way:
        hu_times = hu_times*2
    if  'kongshanghua' in hu_player.hu_way:
        hu_times = hu_times*2
    if  'kongshangpao' in hu_player.hu_way:
        hu_times = hu_times*2

    #2020021612-sl: moved to xzround
    #elif not hu_player.hu_way:
        #hu_player.hu_way.append('pinghu')
        #print("hu_times5: %s" %hu_times)
    else:
        pass
                
    if result1:        
        hu_player.hu_way.append(result1[0])
        hu_times = hu_times*result1[1]
    if result2:
        hu_player.hu_way.append(result2[0])
        hu_times = hu_times*result2[1]
    if n_gen > 0:        
        hu_times = hu_times*pow(2,n_gen)
        hu_player.hu_way.append("%s gen" %n_gen)
            

    '''We should also report those public hu information (hu_times, dianpao_player, hu_tile) to the dealer '''   
    # the score of other players
    zimo_id = []
    if 'zimo' in hu_player.hu_way:
        for player in players:
            if player.winning or player.player_id == hu_player.player_id:
                continue            
            player.myscore += - hu_times*base_score
            player.scoreRecords.append(['beizimo', hu_player.player_id, hu_times, -hu_times*base_score])
            zimo_id.append(player.player_id)
            n_zimo += 1 # number of players that were zimo by this hu_player
    else:
        dianpao_player.myscore = dianpao_player.myscore - hu_times*base_score
        dianpao_player.scoreRecords.append(['dianpao', hu_player.player_id, hu_times, -hu_times*base_score])

    # the score of hu_player and the hu_way
    if n_zimo != 0:
        hu_player.myscore += n_zimo * hu_times * base_score
        hu_player.scoreRecords.append(['zimo', zimo_id, hu_times, +hu_times*base_score])
    else:
        hu_player.myscore += hu_times * base_score
        hu_player.scoreRecords.append(['hu', dianpao_player.player_id, hu_times, +hu_times*base_score])
        
    return players

def compute_jiagang_score(jiakong_player, players, card):
    '''Jiagang: current_player get 1x score from other players who have not win yet'''
    n_player = 0
    for player in players:
        if player.winning == True or player.player_id == jiakong_player.player_id:
            continue
        player.myscore = player.myscore - base_score
        n_player += 1
        player.kongScore.append([card, jiakong_player.player_id, -base_score])
        jiakong_player.kongScore.append([card, player.player_id, +base_score])
        
    jiakong_player.myscore = jiakong_player.myscore + n_player*base_score

def compute_ankong_score(ankong_player, players, card):
#def compute_ankong_score(self, players, card): #q here self should be ankong_player
    '''Angang: current_player get 2x score from other players who have not win'''
    n_player = 0
    for player in players:
        if player.winning == True or player.player_id == ankong_player.player_id:
            continue
        player.myscore += -2*base_score
        n_player += 1
        player.kongScore.append([card, ankong_player.player_id, -2*base_score])
        ankong_player.kongScore.append([card, player.player_id, +2*base_score])
    ankong_player.myscore += n_player*2*base_score
   
def compute_kong_score(kong_player, fanggang_player, card):
    '''Minggang: current_player get 2x score from fanggang_player'''
    kong_player.myscore += 2*base_score
    kong_player.kongScore.append([card, fanggang_player.player_id, +2*base_score])
    fanggang_player.kongScore.append([card, kong_player.player_id, -2*base_score])
    fanggang_player.myscore += -2*base_score

#2020021115-sli
def hujiaozhuanyi(card, hu_player, dianpao_player):
    '''Compute the score for hujiaozhuanyi.
        Args:
            card
            hu_player (object): the player who wins the tile discarded by the dianpao_player who just konged card;
           dianpao_player (object): the player who discards a tile after kong card.
    '''
    #revised @20200613-yan
    zhuanyi_score = 0
    for kongscore in dianpao_player.kongScore: #q shouldn't this kongscore the last item in kongScore?
        if kongscore[0] == card:
            zhuanyi_score = zhuanyi_score + kongscore[2]
            kongscore.append('beihujiaozhuanyi')

    hu_player.myscore += zhuanyi_score    
    hu_player.kongScore.append([card, dianpao_player.player_id, +zhuanyi_score, 'hujiaozhuanyi_income'])
    dianpao_player.myscore += -zhuanyi_score

def compute_handScore(hand, Pile):
    '''Compute the score for a given hand
        Args:
            hand (list): the hand
            Pile (list)
        Returns:
    '''
    hu_way = []
    all_hand = hand[:] # all tile in player's hand (include pile)
    for pile in Pile:
        for p in pile:
            all_hand.append(p)
    d_tile = [] # the different tile in player's all_hand
    [d_tile.append(tile) for tile in all_hand if tile not in d_tile]

    n_gen = 0 # the number of gen which contains four identical tile in player's hand.
    for tile in d_tile:
        if all_hand.count(tile) == 4:
            n_gen += 1
       
    result1 = judge_pengpenghu_qidui(hand, Pile)
    result2 = judge_qingyise(hand, Pile) 
    hu_times = 1 

    if result1:        
        hu_way.append(result1[0])
        hu_times = hu_times*result1[1]
    if result2:
        hu_way.append(result2[0])
        hu_times = hu_times*result2[1]
    if n_gen > 0:        
        hu_times = hu_times*pow(2, n_gen)
        hu_way.append("%s gen" %n_gen)
    score = hu_times * base_score
    return score
    
def update_finalScore(dealer,players):
    '''This only happens when there is no tile in the deck while some player(s)
            haven't tingpai or still have daque color
    '''
    Huers = [] # player(s) who have won
    Huazhu = [] # player(s) who have daque color
    Tingpai = [] # player(s) who have tingpai
    WeiTingpai = [] # player(s) who have not tingpai
            
    
    for player in players:
        if player.winning:
            Huers.append(player)
    for player in players:
        if player not in Huers:
            T = []
            T = player.hand[:]
            c = player.daque_color
            flag = []
            [flag.append(t) for t in T if t[0]==c]
            if flag:
                Huazhu.append(player)
    H_set = Huers + Huazhu
    for player in players:
        if player not in H_set:
            if player.get_deficiency(dealer, players) == 1:                
                Tingpai.append(player)
            else:
                WeiTingpai.append(player)

    weitingpai_id = [] 
    [weitingpai_id.append(player.player_id) for player in WeiTingpai]
    huazhu_id = [] 
    [huazhu_id.append(player.player_id) for player in Huazhu]

    for p in Tingpai:
        p.hand.sort(key=lambda t: t[0:2])

    for p in Huazhu:
        p.hand.sort(key=lambda t: t[0:2])

    for p in WeiTingpai:
        p.hand.sort(key=lambda t: t[0:2])
                       
    if WeiTingpai:
        for player in WeiTingpai:
            if player.kongScore: #return the points received from other players when player konged
                for kscore in player.kongScore: # [card, other_player_id, +points]
                    if kscore[0] and kscore[2] > 0:
                        p = players[kscore[1]]
                        p.myscore += kscore[2]
                        n_id = p.kongScore.index([kscore[0], player.player_id, -kscore[2]])
                        p.kongScore[n_id].append('tuishui_return')
                        #players[kscore[1]].kongScore.append([kscore[0], player.player_id, +kscore[2], 'tuishui_income'])
                        player.myscore = player.myscore - kscore[2]
                        kscore.append('beituishui')


    TingpaiPlayerMaxScore = []
    if Tingpai:
        for player in Tingpai:
            possible_score = [0] 
            max_score = 0
            T = []
            T = player.hand #as player tingpai, [t for t in T if t[0]==dc] is empty
            Pg = [ p[0] for p in player.pile]        
            dc = player.daque_color
            KB = player.kgbase(dealer, players)
            for t in MJ():
                if t[0] != dc:
                    HD = T[:]
                    HD.append(t)
                    HD.sort(key=lambda t: t[0:2])
                    if hs.is_h_solx(HD, dc): #this is faster
                    #if hk.hyval(HD, Pg, KB, dc) == 0:
                        possible_score.append(compute_handScore(HD, player.pile))
            max_score = max(possible_score)
            player.chadajiao_score = max_score #y20201110
            TingpaiPlayerMaxScore.append([player.player_id, max_score])
            player.myscore += max_score * len(WeiTingpai)
            
            if WeiTingpai:
                player.scoreRecords.append(['chadajiao', weitingpai_id, int(max_score/base_score), max_score])
                for weitingpai_player in WeiTingpai:
                    weitingpai_player.myscore +=  - max_score
                    weitingpai_player.scoreRecords.append(['beichadajiao', player.player_id, int(max_score/base_score), -max_score])

    WH = Huers + WeiTingpai 
    if Huazhu and WH:
        for player in WH:
            player.myscore = player.myscore + 16*base_score*len(Huazhu)
            player.scoreRecords.append(['chahuazhu', huazhu_id, 16, 16*base_score])
            for huazhu_player in Huazhu:
                huazhu_player.myscore = huazhu_player.myscore - 16*base_score
                huazhu_player.scoreRecords.append(['beichahuazhu', player.player_id, 16, -16*base_score])
    if Huazhu and Tingpai:
        for e in TingpaiPlayerMaxScore:
            players[e[0]].myscore = players[e[0]].myscore + (16 + e[1])*base_score*len(Huazhu)
            players[e[0]].scoreRecords.append(['chahuazhu', huazhu_id, 16 + e[1], (16 + e[1])*base_score])
            for huazhu_player in Huazhu:
                huazhu_player.myscore = huazhu_player.myscore - (16 + e[1])*base_score
                huazhu_player.scoreRecords.append(['beichahuazhu', players[e[0]].player_id, 16 + e[1], -(16 + e[1])*base_score])
    
