from board4 import Board
import requests
import os
import json
import datetime
# Insert Player class here.

def auth_load():
    """Loads authenitcation data from auth.json.
    :return str: token, group_id, bot_id"""
    with open(os.path.abspath('auth.json'),'r') as auth:
        file = auth.readlines()
        data = json.loads(file[0])
        return data
        return data['token'], data['group_id'], data['bot_id']

auth = auth_load()
bot = auth['connect']
group = bot['group_id']
request_params = {'token':auth['token']}
post_params = {'text':'','bot_id':bot['bot_id'],'attachments':[]}

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", json = post_params)
    

def read():
    global group
    global request_params
    try:
        response_messages = requests.get('https://api.groupme.com/v3/groups/'+ group +'/messages', params = request_params).json()['response']['messages']
        return response_messages
    except:
        return read()
    
class Player:
    """
    """

    def __init__(self, checker):
        """
        """

        self.checker = checker
        self.num_moves = 0

    def __str__(self):
        """
        """

        return 'Player ' + str(self.checker)

    def __repr__(self):
        """
        """

        return str(self)

    def opponent_checker(self):
        """
        """

        if self.checker == 'o':
            self.opponent = 'x'
        else:
            self.opponent = 'o'

        return self.opponent

    def next_move(self, board, user_id, user_name, user2_id, user2_name):
        """
        """
        global post_params
        if self.checker == 'x':
            post_params['text'] = user_name + "'s Turn\nEnter a column:"
        else:
            post_params['text'] = user2_name + "'s Turn\nEnter a column:"
        send_message(post_params)
        start = datetime.datetime.now()
        
        if self.checker == 'x':
            while board is not None:
                #col = int(input('Enter a column: '))
                response = read()
                if (response[0]['text'].strip().lower() == 'quit' and response[0]['sender_id'] == user_id):
                    return 'quit'
                if (datetime.datetime.now() - start > datetime.timedelta(0, 60, 0)):
                    return 'quit'
                
                col = 200
                if response[0]['text'].isdigit() and response[0]['sender_id'] == user_id:
                    col = int(response[0]['text'])
                    
                if board.can_add_to(col):
                    self.num_moves += 1
                    return col
                else: continue
        else:
            while board is not None:
                #col = int(input('Enter a column: '))
                response = read()
                if (response[0]['text'].strip().lower() == 'quit' or response[0]['sender_id'] == user2_id):
                    return 'quit'
                if (datetime.datetime.now() - start > datetime.timedelta(0, 60, 0)):
                    return 'quit'
                
                col = 200
                if response[0]['text'].isdigit() and response[0]['sender_id'] == user2_id:
                    col = int(response[0]['text'])
                    
                if board.can_add_to(col):
                    self.num_moves += 1
                    return col
                else: continue
                
