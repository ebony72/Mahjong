
class MahjongCard(object):

    info = {'type':  ['d', 'b', 'c'],
            'trait': ['1', '2', '3', '4', '5', '6', '7', '8', '9']
            }

    def __init__(self, card_type, trait):
        ''' Initialize the class of MahjongCard

        Args:
            card_type (str): The type of card
            trait (str): The trait of card
        '''
        self.type = card_type
        self.trait = trait

    def get_str(self):
        ''' Get the string representation of card

        Return:
            (str): The string of card's color and trait
        '''
        return self.type + '-' + self.trait

    def get_mjzero(self):
        ''' Get the Mahjong zero representation of card

        Return:
            (list): The list of card's color and trait
        '''
        c = -1
        if self.type == 'b':
            c = 0
        elif self.type == 'c':
            c = 1
        elif self.type == 'd':
            c = 2
        return [c, int(self.trait)]




# for test
if __name__ == '__main__':
    a = MahjongCard('d', '5')
    b = MahjongCard('d', '5')
    c = MahjongCard('c', '3')
    print(a==b)
    cards = [a, b, c]
    for card in cards:
        print(card.get_str(),card.get_mjzero())
        print(len(card.get_mjzero()))
