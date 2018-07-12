from board4 import Board
from player4 import Player
import aiplayer4
import random
import requests
import os
import json
# Insert Player class here.

def auth_load():
    """Loads authenitcation data from auth.json.
    :return str: token, group_id, bot_id"""
    with open(os.path.abspath('auth.json'),'r') as auth:
        file = auth.readlines()
        data = json.loads(file[0])
        return data

auth = auth_load()
bot = auth['connect']
group = bot['group_id']
request_params = {'token':auth['token']}
post_params = {'text':'','bot_id':bot['bot_id'],'attachments':[]}

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", json = post_params)
    

def play_connect4(user_id, user_name, user2_id, user2_name):
    if user2_id == '':
        connect_four(Player('x'), aiplayer4.AIPlayer('o', '', 0), user_id, user_name)
    else:
        connect_four(Player('x'), Player('o'), user_id, user_name, user2_id, user2_name)

    
def connect_four(player1, player2, user_id, user_name, user2_id = '', user2_name = ''):
    """ Plays a game of Connect Four between the two specified players,
        and returns the Board object as it looks at the end of the game.
        inputs: player1 and player2 are objects representing Connect Four
                  players (objects of the Player class or a subclass of Player).
                  One of them should use 'X' checkers and the other should
                  use 'O' checkers.
    """
    # Make sure that one is 'X' and one is 'O'.
#    if player1.checker not in 'XO' or player2.checker not in 'XO' \
#       or player1.checker == player2.checker:
#        print('need one X player and one O player.')
#        return None

#    print('Welcome to Connect Four!')
#    print()
    board = Board(6, 7)
#    print(board)
    post_params['text'] = 'Welcome To Connect 4!\n\n' + str(board)
    send_message(post_params)
    
    while True:
        if process_move(player1, board, user_id, user_name, user2_id, user2_name):
            return board

        if process_move(player2, board, user_id, user_name, user2_id, user2_name):
            return board

def process_move(player, board, user_id, user_name, user2_id, user2_name):
    """ determines a move and if it is a win for a person
    input player: player 'X' or 'O'
    input board: connect four board
    """

#    print(str(player) + "'s turn")

    col = player.next_move(board, user_id, user_name, user2_id, user2_name)
    if col == 'quit':
        post_params['text'] = 'Quitting...'
        send_message(post_params)
        return True
        return True
    
    board.add_checker(player.checker, col)

#    print()
#    print(board)
    post_params['text'] = str(board)
    send_message(post_params)

    if board.is_win_for(player.checker):
#        print(str(player), 'wins in', player.num_moves, 'moves.')
#        print('Congratulations!')
        if user2_id == '':
            if player.checker == 'x':
                post_params['text'] = 'Winner Winner Chicken Dinner!'
                send_message(post_params)
                return True
            else:
                post_params['text'] = 'You Lose.'
                send_message(post_params)
                return True
        else:
            if player.checker == 'x':
                post_params['text'] = user_name + ' Wins!'
                post_params['attachments'] = [{"loci": [[0, len(user_name)]],"type": "mentions","user_ids": [user_id]}]
                send_message(post_params)
                return True
            else:
                post_params['text'] = user2_name + ' Wins!'
                post_params['attachments'] = [{"loci": [[0, len(user2_name)]],"type": "mentions","user_ids": [user2_id]}]
                send_message(post_params)
    elif board.is_full():
#        print("It's a tie!")
        post_params['text'] = "It's a tie."
        send_message(post_params)
        return True
    else:
        return False

    
class RandomPlayer(Player):
    """ A player with randomized moves
    """

    def __init__(self, checker):
        """ use the initializer of Player class
        """

        Player.__init__(self, checker)

    def next_move(self, board):
        """ checks for open space and then decides a random column to go
        """

        open_col = [i for i in range(board.width) if board.can_add_to(i)]
        self.num_moves += 1
        return random.choice(open_col)
                
