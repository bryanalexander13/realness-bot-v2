import requests
import time
import json
import os
import sys


class User:
    """Users information"""
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.realness = 0

    def add_realness(self):
        self.realness += 1

    def subtract_realness(self):
        self.realness -= 1


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

#loads user information
def user_load():
    with open(os.path.abspath('users.json'),'r') as users:
        file = users.readlines()
        data = json.loads(file[0])
        return data

#update userdictionary, realness, nicknames
def update_users(udict):
    with open(os.path.abspath('users.json'),'w') as users:
        users.write(json.dumps(udict))

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
def remove_mention_text(message,udict):
    message_text = message.text
    for user in message.attachments[0]['user_ids']:
        mention = '@'+udict[user]['nickname']
        message_text = message_text.replace(mention,'')
    return message_text

#looks up user_id by name
def id_lookup(name,udict):
    namelist = []
    for id, information in udict.items():
        namelist.append(information['name'])
    if name not in namelist:
        return 'no id'
    for id, information in udict.items():
        if information['name'] == name.lower():
            return id

def nickname_instead_of_name(udict_id_key):
    if len(udict_id_key['name']) == 0:
        return 'nickname'
    else:
        return 'name'
#changes realness in dictionary, updates
def adjust_realness(id, udict, message, type):
    global post_params
    if id == message.sender_id:
        post_params['text'] = 'You can\'t change your own realness.'
        send_message(post_params)
        return False
    elif type == 'add':
        udict[id]['realness'] += 1
    elif type == 'subtract':
        udict[id]['realness'] -= 1
    update_users(udict)
    return True

#filters through ids and text names to adjust user dictionary, updates new dictionary
def text_change_realness(names, udict, message, type):
    global post_params
    add_list = []
    for name in names:
        if (name.isdigit() and len(name)==8 and name in list(udict.keys())):
            add_list.append(name)
        else:
            add_list.append(id_lookup(name, udict))
    if len(add_list) == 0:
        return
    if add_list.count('no id') > 1:
        post_params['text'] = 'Invalid IDs'
        send_message(post_params)
        return
    if type == 'add':
        text = 'Real '
    elif type == 'subtract':
        text = 'Not Real '
    for id in [id for id in list(set(add_list)) if (id != 'no id')]:
        if adjust_realness(id, udict, message, type) == True:
            text += udict[id]['name'].capitalize() + '. '
    #post final message
    post_params['text'] = text
    send_message(post_params)
    #terminal carter handling
    if (type == 'subtract' and id_lookup('carter',udict) in add_list):
        post_params['text'] = 'It is terminal.'
        send_message(post_params)


def realness(udict):
    global post_params
    header = 'The current realness levels are:'
    levels=str()
    realness_list = []
    for id in userdict:
        realness_list.append((udict[id]['realness'],udict[id][nickname_instead_of_name(udict[id])]))
    realness_list = sorted(realness_list,reverse=True)
    for k, v in realness_list:
        levels += '\n' + v.capitalize() +' : '+ str(k)
    txt = header + levels
    post_params['text'] = txt
    send_message(post_params)

#update userdict name
# def update(sender_id, name, udict):
#     global post_params
#     udict[sender_id]['name'] = name.lower()
#     update_users(udict)
#     post_params['text'] = 'Updated.'
#     send_message(post_params)

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id):
    response_messages = requests.get('https://api.groupme.com/v3/groups/{}/messages'.format(group_id), params = request_params).json()['response']['messages']
    message_list=[]
    for message in response_messages:
        message_list.append(Message(message['attachments'],
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
                                        message['user_id']))
        if message['sender_type'] == 'bot':
            continue
        if message['sender_type'] == 'system':
            continue
        if message['user_id'] not in list(userdict.keys()):
            userdict[message['user_id']] = {'name':'','nickname': message['name'],'realness' : 0}
        if userdict[message['user_id']]['nickname'] != message['name']:
            userdict[message['user_id']]['nickname'] = message['name']
        if (message['attachments'] != [] and message['attachments'][0]['type'] =='mentions' ):
            for i,id in enumerate(message['attachments'][0]['user_ids']):
                if userdict[id]['nickname'] != message['text'][message['attachments'][0]['loci'][i][0]+1:message['attachments'][0]['loci'][i][0]+message['attachments'][0]['loci'][i][1]]:
                    userdict[id]['nickname'] = message['text'][message['attachments'][0]['loci'][i][0]+1:message['attachments'][0]['loci'][i][0]+message['attachments'][0]['loci'][i][1]]
    update_users(userdict)
    return message_list

#Just slap this shit in here
def start_timer(rest, user_id, message):
    global i
    global timer
    timer += [(True, i + (60 * int(rest[0])), user_id, message)]
    timer = sorted(timer, key = lambda x:x[1])


#checks for last message and runs commands
def commands(message_list, udict):
    global post_params
    for message in message_list:
        if int(message.id) <= int(last_load()):
            break
        elif message.text == None:
            continue
        elif message.sender_type == 'bot':
            continue
        elif message.text.lower().startswith('@rb'):
            text = message.text.split('@rb ')[1]
            nameslist=[]
            if (len(text) == 1):
                post_params['text'] = ("These are the following commands:\n" +
                                      "not real [@mention]\n" +
                                      "very real [@mention]\n" +
                                      "timer [@mention] [time]\n" +
                                      "ranking")
                send_message(post_params)
            elif text.lower().startswith('very real'):
                if len(text.split('very real')[1]) == 0:
                    post_params['text'] = 'Nothing to add realness to.'
                    send_message(post_params)
                if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
                    nameslist = message.attachments[0]['user_ids']
                    nameslist += remove_mention_text(message,udict).split()[2:]
                else:
                    nameslist += text.lower().split()[2:]
                text_change_realness(nameslist, udict, message, 'add')
            elif text.lower().startswith('not real'):
                if len(text.split('not real')[1]) == 0:
                    post_params['text'] = 'Nothing to add realness to.'
                    send_message(post_params)
                if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
                    nameslist = message.attachments[0]['user_ids']
                    nameslist += remove_mention_text(message,udict).split()[2:]
                else:
                    nameslist += text.lower().split()[2:]
                text_change_realness(nameslist, udict, message, 'subtract')
            elif text.lower() == 'rankings' or text.lower() == 'ranking':
                realness(udict)
            elif text.lower().startswith('timer'):
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
            elif (text.lower().startswith("help")):
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
                    post_params['text'] = ("These are the following commands:\n" +
                                      "not real [@mention]\n" +
                                      "very real [@mention]\n" +
                                      "timer [@mention] [time]\n" +
                                      "ranking")
                    send_message(post_params)
            else:
                    post_params['text'] = ("These are the following commands:\n" +
                                      "not real [@mention]\n" +
                                      "very real [@mention]\n" +
                                      "timer [@mention] [time]\n" +
                                      "ranking")
                    send_message(post_params)
def run():
    global request_params
    global group_id
    global userdict
    global i
    global timerv
    #i = 0
    while (i < 2000000):
        message_list = read_messages(request_params, group_id)
        commands(message_list, userdict)
        last_write(message_list[0].id)
        if (timer[0][0] and timer[0][1] < i):
            post_params['text'] = "Hey Retard. You're Late."
            send_message(post_params)
            for not_real in [timer[0][2] for i in range(49)]:
                adjust_realness(not_real,userdict,timer[0][3],'subtract')
            text_change_realness([timer[0][2]], userdict, timer[0][3], 'subtract')
            del timer[0]
#timer 0 = true timer 1= i  timer 2= id timer 3= message
        i += 1
        time.sleep(1)

if __name__ == "__main__":
    userdict = user_load()
    auth = auth_load()
    group_id = auth[1]
    request_params = {'token':auth[0]}
    post_params = {'text':'','bot_id':auth[2],'attachments':[]}
    i = 0
    timer = [(False, sys.maxsize, "", "")]

    print('The current realness levels are: ')
    for k, v in userdict.items():
        print('{} : {}'.format(v['name'],v['realness']))
    run()
