import requests
import time
import json
import os
from datetime import datetime, timedelta


class User:
    """Users information"""    
    def __init__(self, user_id, name, nickname, realness = 0, abilities = []):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.realness = realness
        self.abilities = abilities
        
    def add_realness(self):
        self.realness += 1
    
    def subtract_realness(self):
        self.realness -= 1
    
    def add_ability(self, ability):
        self.abilities += ability
        
    def remove_ability(self, ability):
        self.abilities.remove("ability")
        
    def changeNickname(self, nickname):
        self.nickname = nickname
        
        
class UserList:
    def __init__(self, udict):
        self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities']) for i in udict]
        self.ids = [i['user_id'] for i in udict]
        self.names = [i['name'] for i in udict]
        self.nicknames = [i['nickname'] for i in udict]
        self.realness = [i['user_id'] for i in udict]
    
    def find(self, user_id):
        try:
            return [i for i in self.ulist if i.user_id == user_id][0]
        except:
            return User("0", "invalid", "invalid")
    
    def findByName(self, name):
        try:
            return [i for i in self.ulist if i.name == name][0]
        except:
            return User("0", "invalid", "invalid")
        
    def findByNickname(self, nickname):
        try:
            return [i for i in self.ulist if i.nickname == nickname][0]
        except:
            return User("0", "invalid", "invalid")
        
    def add(self, user):
        self.ulist += user
        self.ids += user.user_id
        
    def remove(self, user_id):
        user = self.find(user_id)
        try:
            self.ids.remove(user_id)
            self.ulist.remove(user)
        except:
            return
        
    def ranking(self, post_params):
        text = 'The current realness levels are: \n'
        for user in sorted(self.ulist, key=lambda x: x.realness, reverse=True):
            text += user.nickname +': '+ str(user.realness) + '\n'
        post_params['text'] = text
        send_message(post_params)
    
    def update(self, message):
        user = self.find(message.sender_id)
        if user.nickname == message.name:
            return False
        else:
            user.nickname = message.name
            return True
    
    
class Message:
    """A message handler"""

    def __init__(self,
                    attachments,
                    avatar_url,
                    created_at,
                    favorited_by,
                    group_id,
                    id,
                    name,
                    sender_id,
                    sender_type,
                    source_guid,
                    system,
                    text,
                    user_id):
        self.attachments = attachments
        self.avatar_url = avatar_url
        self.created_at = created_at
        self.liked = favorited_by
        self.group_id = group_id
        self.id = id
        self.name = name
        self.sender_id = sender_id
        self.sender_type = sender_type
        self.source_guid = source_guid
        self.system = system
        self.text = text
        self.user_id = user_id

    def count_likes(self):
        return len(self.liked)


#loads token and group_id
def auth_load():
    with open(os.path.abspath('auth.json'),'r') as auth:
        file = auth.readlines()
        data = json.loads(file[0])
        return data['token'], data['group_id'], data['bot_id']


def users_load():
    with open(os.path.abspath('users2.json'),'r') as users:
        file = users.readlines()
        data = json.loads(file[0])
        return data
    
def users_write(ulist):
    with open(os.path.abspath('users2.json'),'w') as users:
        users.write(json.dumps([i.__dict__ for i in ulist.ulist]))

#loads last message checked
def last_load():
    with open(os.path.abspath('last.json'),'r') as last:
        file = last.readlines()
        data = json.loads(file[0])
        return data['last_read']

#writes json file with last message id
def last_write(last_message):
    if int(last_message) > int(last_load()):
        with open(os.path.abspath('last.json'),'w') as l:
            l.write(json.dumps({'last_read':last_message}))

#sends a message
def send_message(post_params):
    requests.post("https://api.groupme.com/v3/bots/post", params = post_params)

#removes mention text from message
def remove_mention_text(message,ulist):
    message_text = message.text
    for user in message.attachments[0]['user_ids']:
        mention = '@'+ (ulist.find(user).nickname)
        message_text = message_text.replace(mention,'')
    return message_text

#changes realness in dictionary, updates
def adjust_realness(newid, ulist, message, reason):
    global post_params
    if newid == message.sender_id:
        post_params['text'] = 'You can\'t change your own realness.'
        send_message(post_params)
        return False
    elif reason == 'add':
        ulist.find(newid).add_realness()
    elif reason == 'subtract':
        ulist.find(newid).subtract_realness()
    users_write(ulist)
    return True
 
#filters through ids and text names to adjust user dictionary, updates new dictionary
def text_change_realness(names, ulist, message, reason):
    global post_params
    add_list = []
    for name in names:
        if (name.isdigit() and len(name)==8 and name in list(ulist.ids)):
            add_list.append(name)
        else:
            add_list.append(ulist.findByName(name).user_id)
    if len(add_list) == 0:
        return
    if add_list.count('0') > 1:
        post_params['text'] = 'Invalid IDs'
        send_message(post_params)
        return
    if reason == 'add':
        text = 'Real '
    elif reason == 'subtract':
        text = 'Not Real '        
    for newid in add_list:
        if adjust_realness(newid, ulist, message, reason):
            text += ulist.find(newid).name.capitalize() + '. '
    #post final message
    post_params['text'] = text
    send_message(post_params)
    #terminal carter handling
    if (reason == 'subtract' and ulist.findByName("carter").user_id in add_list):
        post_params['text'] = 'It is terminal.'
        send_message(post_params)

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id, ulist):
    response_messages = requests.get('https://api.groupme.com/v3/groups/{}/messages'.format(group_id), params = request_params).json()['response']['messages']
    message_list=[]
    last = last_load()
    
    
    for message in response_messages:
        if int(message['id']) <= int(last):
            break
        mess = Message(message['attachments'],
                        message['avatar_url'],
                        message['created_at'],
                        message['favorited_by'],
                        message['group_id'],
                        message['id'],
                        message['name'],
                        message['sender_id'],
                        message['sender_type'],
                        message['source_guid'],
                        message['system'],
                        message['text'],
                        message['user_id'])
        message_list.append(mess)
        
        if mess.sender_type == 'bot' or mess.sender_type == 'system':
            continue
        else:
            commands(mess, userlist)
            done = ulist.update(mess)
            if done:
                users_write(ulist)
                
    if len(message_list) > 0:
        last_write(message_list[0].id)
        
    return message_list

#Just slap this shit in here
def start_timer(rest, user_id, message):
    global timer
    timer += [(True, datetime.now() + (timedelta(minutes=int(rest[0]))), user_id, message)]
    timer = sorted(timer, key = lambda x:x[1])


def set_timer(text, message):
    if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
        name = message.attachments[0]['loci'][0]
        rest = text[name[0] + name[1]-3:].strip().split(" ")
        if (len(rest) == 1 and rest[0].isdigit()):
            start_timer(rest, message.attachments[0]['user_ids'][0], message)
            post_params['text'] = 'Timer set for ' + rest[0] + ' minutes'
            send_message(post_params)
        else:
            post_params['text'] = "I don't know when that is" + str(text[name[0] + name[1]-1:])
            send_message(post_params)
    else:
        post_params['text'] = "I don't know who that is"
        send_message(post_params)
        

def cancel_timer(user_id):
    global timer
    t = False
    for k, u_id in enumerate([j[2] for j in timer]):
        if user_id == u_id:
            del timer[k]
            t = True
    if t:
        post_params['text'] = "Finally"
        send_message(post_params)
    
    
def helper_main(post_params):
    post_params['text'] = ("These are the following commands:\n" +
                                      "not real [@mention]\n" +
                                      "very real [@mention]\n" +
                                      "timer [@mention] [time]\n" +
                                      "ranking")
    send_message(post_params)


def helper_specific(post_params, text):
    reason = text.lower().split(" ")[1:]
    if (len(reason) == 2):
        if (reason[0] == "not"):
            post_params['text'] = ("The not real command is used to shame a user for their lack of realness\n" +
                      "Example: @db not real Carter")
            send_message(post_params)
        elif (reason[0] == "very"):
            post_params['text'] = ("The very real command is used to reward a user for their excess of realness\n" +
                      "Example: @db very real Carter")
            send_message(post_params)
        elif (reason[0] == "ranking"):
            post_params['text'] = ("The ranking command shows how real everyone is\n" +
                      "Example: @db ranking")
            send_message(post_params)
        elif (reason[0] == "timer"):
            post_params['text'] = ("Set a timer in minutes so people aren't late\n" +
                      "Example: @db timer @LusciousBuck 10")
            send_message(post_params)
    else:
        helper_main(post_params)
        

def very_real(text, message, ulist, nameslist):
    if len(text.split('very real')[1]) == 0:
        post_params['text'] = 'Nothing to add realness to.'
        send_message(post_params)
    if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
        nameslist = message.attachments[0]['user_ids']
        nameslist += remove_mention_text(message,ulist).split()[2:]
    else:
        nameslist += text.lower().split()[2:]
    text_change_realness(nameslist, ulist, message, 'add')
    
    
def not_real(text, message, ulist, nameslist):
    if len(text.split('not real')[1]) == 0:
        post_params['text'] = 'Nothing to add realness to.'
        send_message(post_params)
    if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
        nameslist = message.attachments[0]['user_ids']
        nameslist += remove_mention_text(message,ulist).split()[2:]
    else:
        nameslist += text.lower().split()[2:]
    text_change_realness(nameslist, ulist, message, 'subtract')
    
    
#checks for last message and runs commands
def commands(message, ulist):
    global post_params
   
    if message.text == None:
        return
    elif message.text.lower().startswith('here'):
        cancel_timer(message.user_id)
    elif (message.text.lower().startswith('@rb')):
            text = message.text.split('@rb ')
            if len(text) > 1:    
                text = text[1]
                nameslist=[]
                
                if (len(text) == 1):
                    helper_main(post_params)
                    
                elif text.lower().startswith('very real'):
                    very_real(text, message, ulist, nameslist)
                    
                elif text.lower().startswith('not real'):
                    not_real(text, message, ulist, nameslist)
                    
                elif text.lower() == 'rankings' or text.lower() == 'ranking':
                    ulist.ranking(post_params)
                    
                elif text.lower().startswith('timer'):
                    set_timer(text, message)
                        
                elif (text.lower().startswith("help")):
                    helper_specific(post_params, text)
                    
                elif (text.lower().startswith('here')):
                    cancel_timer(message.user_id)
                
                else:
                    helper_main(post_params)
#            elif (text.lower().startswith('shop'))
            else:
                helper_main(post_params)
      
                
def run():
    global request_params
    global group_id
    global userlist
    global timer
    
    while (1 == True):
        message_list = read_messages(request_params, group_id, userlist)
        
        if (len(timer) > 0 and timer[0][0] and timer[0][1] < datetime.now()):
            post_params['text'] = "Hey Retard. You're Late."
            send_message(post_params)
            
            for val in [timer[0][2] for i in range(49)]:
                adjust_realness(val, userlist, timer[0][3], 'subtract')
            text_change_realness([timer[0][2]], userlist, timer[0][3], 'subtract')
            del timer[0]

        time.sleep(1)

if __name__ == "__main__":
    user_dict = users_load()
    userlist = UserList(user_dict)
    auth = auth_load()
    group_id = auth[1]
    request_params = {'token':auth[0]}
    post_params = {'text':'','bot_id':auth[2],'attachments':[]}
    timer = []

    text = 'The current realness levels are: \n'
    for user in sorted(userlist.ulist, key=lambda x: x.realness):
        text += user.nickname +': ' + str(user.realness) + '\n'
    print(text)
    run()
