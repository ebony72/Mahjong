
'''action indexes'''
ACTIONS = {
    'draws': 0,
    'discard': 1,
    'pong': 2,
    'jiakong': 3,
    'ankong': 4,
    'kong': 5,
    'zimo': 6,
    'robkong': 7,
    'hu': 8,
    'stand': 9,
    'self_check': 10,
    'self-check': 10
}

'''hu_way indexes'''
HU_WAYS = {
    'pinghu': 0,
    'zimo': 1,
    'robkong': 2,
    'kongshanghua': 3,
    'kongshangpao': 4,
    'pengpenghu': 5,
    'jingoudiao': 6,
    'qingyise': 7,
    'qidui': 8,
    'tianhu': 9,
    'dihu': 10,
    '1 gen': 11,
    '2 gen': 12,
    '3 gen': 13,
    '4 gen': 14
}

def get_tile_idx(c,k):
    '''get idx in [0,26] for a tile [c,k]'''
    return c*9+k-1

def get_tile_color(tile_idx):
    '''get color of a tile given by tile_idx'''
    return tile_idx//9
def get_tile_num(tile_idx):
    '''get num of a tile given by tile_idx'''
    return tile_idx%9+1
