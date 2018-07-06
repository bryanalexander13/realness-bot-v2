import requests
import time
import json
import pandas
import os


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

#adds point of realness, updates new dictionary
def add_realness(names, udict, message):
    global post_params
    header = 'Real '
    text = str()
    if len(names[0]) == 8:
        for name in names:
            if name not in udict.keys():
                continue
            elif name == message.sender_id:
                post_params['text'] = 'You can\'t do that.'
                send_message(post_params)
            else:
                udict[name]['realness'] += 1
                text += udict[name]['name'].capitalize() + '. '
    else:
        for name in names:
            id = id_lookup(name,udict)
            if id == 'no id':
                post_params['text'] = 'Invalid Name'
                send_message(post_params)
            elif id == message.sender_id:
                post_params['text'] = 'You can\'t do that.'
                send_message(post_params)
            else:
                udict[id]['realness'] += 1
                text += name.capitalize() + '. '
    if len(text) > 0:
        post_params['text'] = header + text
        send_message(post_params)
        update_users(udict)

#subtracts point of realness, updates new dictionary
def subtract_realness(names, udict, message):
    global post_params
    terminal = False
    header = 'Not Real '
    text = str()
    if len(names[0]) == 8:
        for name in names:
            if name not in udict.keys():
                continue
            elif name == message.sender_id:
                post_params['text'] = 'You can\'t do that.'
                send_message(post_params)
            else:
                udict[name]['realness'] -= 1
                text += udict[name]['name'].capitalize() + '. '
                if udict[name]['name'] == 'carter':
                    terminal = True
    else:
        for name in names:
            id = id_lookup(name,udict)
            if id == 'no id':
                post_params['text'] = 'Invalid Name'
                send_message(post_params)
            elif id == message.sender_id:
                post_params['text'] = 'You can\'t do that.'
                send_message(post_params)
            else:
                udict[id]['realness'] -= 1
                text += name.capitalize() + '. '
                if name == 'carter':
                    terminal = True
    if len(text) > 0:
        post_params['text'] = header + text
        send_message(post_params)
        update_users(udict)
    if terminal == True:
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
        elif message['sender_type'] == 'system':
            continue
        elif message['user_id'] not in list(userdict.keys()):
            userdict[message['user_id']] = {'name':'','nickname': message['name'],'realness' : 0}
        elif userdict[message['user_id']]['nickname'] != message['name']:
            userdict[message['user_id']]['nickname'] = message['name']
    update_users(userdict)
    return message_list

#Just slap this shit in here
def timer(rest, user_id, message):
    global i
    global timer
    timer = (True, i + (60 * int(rest[2])), user_id, message)


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
            last_write(message.id)
            text = message.text.split('@rb ')[1]
            if text.lower().startswith('very real'):
                if len(text.split('very real')[1]) == 0:
                    post_params['text'] = 'Nothing to add realness to.'
                    send_message(post_params)
                elif len(message.attachments) > 0:
                    add_realness(message.attachments[0]['user_ids'], udict, message)
                else:
                    modtextlist = text.lower().split()
                    modtextlist.remove('very')
                    modtextlist.remove('real')
                    add_realness(modtextlist, udict, message)
            elif text.lower().startswith('not real'):
                if len(message.attachments) > 0:
                    subtract_realness(message.attachments[0]['user_ids'], udict, message)
                elif len(text.split('not real')[1]) == 0:
                    post_params['text'] = 'Nothing to add realness to.'
                    send_message(post_params)
                else:
                    modtextlist = text.lower().split()
                    modtextlist.remove('not')
                    modtextlist.remove('real')
                    subtract_realness(modtextlist, udict, message)
            elif text == 'rankings':
                realness(udict)
            elif text.lower().startswith('timer'):
                if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
                    name = message.attachments[0]['loci'][0]
                    rest = text[name[0] + name[1]:].strip().split(" ")
                    if (len(rest) == 1 and rest[0].isdigit()):
                        timer(rest, message.attachments[0]['user_ids'][0], message)
                        post_params['text'] = 'Timer set for ' + rest[1] + 'minutes'
                        send_message(post_params)
                    else: 
                        post_params['text'] = "I don't know when that is"
                        send_message(post_params)
                else:
                    post_params['text'] = "I don't know who that is"
                    send_message(post_params)

                    
def run():
    global request_params
    global group_id
    global userdict
    global i
    global timer
    #i = 0
    while (i < 2000000):
        message_list = read_messages(request_params, group_id)
        commands(message_list, userdict)
        last_write(message_list[0].id)
        if (timer[0] and timer[1] < i):
            post_params['text'] = "Hey Retard. You're Late."
            send_message(post_params)
            subtract_realness([time[2] for i in range(50)], userdict, timer[3])
            timer = (False, 0, "", "")
        
        i += 1
        time.sleep(1)

if __name__ == "__main__":
    userdict = user_load()
    auth = auth_load()
    group_id = auth[1]
    request_params = {'token':auth[0]}
    post_params = {'text':'','bot_id':auth[2],'attachments':[]}
    i = 0
    timer = (False, 0, "", "")

    print('The current realness levels are: ')
    for k, v in userdict.items():
        print('{} : {}'.format(v['name'],v['realness']))
    run()
