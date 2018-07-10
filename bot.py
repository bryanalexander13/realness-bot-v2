import requests
import time
import json
import os
from datetime import datetime, timedelta


class User:
    """Users information"""
    def __init__(self, user_id, name, nickname, realness = 0, abilities = [], protected = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.realness = realness
        self.abilities = abilities
        self.protected = protected
        self.switch = {"protect" : "self.protect(ability.val)"}
        self.datetime_read()
        self.ability_read()
        self.properties = self.__dict__().keys()

    def __dict__(self):
        return {"user_id": self.user_id,
                "name": self.name,
                "nickname": self.nickname,
                "realness": self.realness,
                "abilities": self.ability_write(),
                "protected": self.datetime_write()}

    def add_realness(self):
        self.realness += 1

    def subtract_realness(self):
        self.realness -= 1

    def add_ability(self, ability):
        self.abilities += [ability]

    def remove_ability(self, ability):
        self.abilities.remove(ability)

    def changeNickname(self, nickname):
        self.nickname = nickname

    def use_ability(self, rest):
        if len(rest) == 2 and rest[1].isdigit():
            for ability in self.abilities:
                if (rest[0] == ability.type and int(rest[1]) == ability.val):
                    self.remove_ability(ability)
                    exec(self.switch[ability.type])
                    post_params['text'] = "Upgrade used"
                    send_message(post_params)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        else:
            post_params['text'] = "I'm not sure what ability that is"
            send_message(post_params)

    def protect(self, time):
        self.protected = datetime.now() + timedelta(hours = time)

    def datetime_write(self):
        return self.protected.strftime("%Y-%m-%d %H:%M:%S.%f")

    def datetime_read(self):
        self.protected = datetime.strptime(self.protected, "%Y-%m-%d %H:%M:%S.%f")

    def ability_write(self):
        return [(i.type, i.val) for i in self.abilities]

    def ability_read(self):
        self.abilities = [Ability(i[0],i[1]) for i in self.abilities]

    def value(self, val):
        if val not in self.properties or val == 'user_id':
            post_params['text'] = ("The properties are:\n" +
                                    "name\n" +
                                    "nickname\n" +
                                    "realness\n" +
                                    "abilities\n" +
                                    "protected")
            send_message(post_params)
        else:
            post_params['text'] = str(self.__dict__()[val])
            send_message(post_params)



class Ability:
    def __init__(self, typ, val):
        self.type = typ
        self.val = val

class UserList:
    def __init__(self, udict):
        try:
            self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected']) for i in udict]
        except:
            self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness']) for i in udict]
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


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def auth_load():
    """Loads authenitcation data from auth.json.
    :return str: token, group_id, bot_id"""
    with open(os.path.abspath('auth.json'),'r') as auth:
        file = auth.readlines()
        data = json.loads(file[0])
        return data['token'], data['group_id'], data['bot_id']

def users_load():
    """Loads users from users2.json.
    :return list: user dictionaries"""
    with open(os.path.abspath('users2.json'),'r') as users:
        file = users.readlines()
        data = json.loads(file[0])
        return data

def users_write(ulist):
    """Writes user dictionaries to users2.json.
    :param UserList ulist: user list of User objects"""
    with open(os.path.abspath('users2.json'),'w') as users:
        users.write(json.dumps([i.__dict__() for i in ulist.ulist]))

def last_load():
    """Loads last message id read.
    :return str: message id"""
    with open(os.path.abspath('last.json'),'r') as last:
        file = last.readlines()
        data = json.loads(file[0])
        return data['last_read']

def last_write(last_message):
    """Writes last message id to last.json.
    :param str last_message: last message id"""
    if int(last_message) > int(last_load()):
        with open(os.path.abspath('last.json'),'w') as l:
            l.write(json.dumps({'last_read':last_message}))

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", params = post_params)

def remove_mention_text(message, ulist):
    """Removes mention text from message (@nickname).
    :param Message message: message object to act on
    :param UserList ulist: user list of User objects
    :return str: message text"""
    message_text = message.text
    for user in message.attachments[0]['user_ids']:
        mention = '@'+ (ulist.find(user).nickname)
        message_text = message_text.replace(mention,'')
    return message_text

#changes realness in dictionary, updates
def adjust_realness(id, ulist, message, reason):
    """Adds or subtracts realness from User. Calls add_realness() or
    subtract_realness() of User and find methods of UserList and send_message().
    Calls users_write().
    :param str id: user id of user to modify
    :param UserList ulist: user list of User objects
    :param Message message: message object that calls this function
    :param reason: type of adjust, add or subtract
    :return bool: True if success, False if failure"""
    global post_params
    person = ulist.find(id)

    if id == message.sender_id:
        post_params['text'] = 'You can\'t change your own realness.'
        send_message(post_params)
        return False
    elif reason == 'add':
        person.add_realness()
        return True
    elif reason == 'subtract':
        if person.protected > datetime.now():
            post_params['text'] = 'Sorry, ' + person.nickname + ' is protected.'
            send_message(post_params)
            return False
        else:
            person.subtract_realness()
            return True
    users_write(ulist)
    return True

def text_change_realness(names, ulist, message, reason):
    """Adds or Subtracts realness with multiple values. Posts messages with
    realness updates.  Calls send_message() and adjust_realness(). Uses findByName
    method of UserList.
    :param list names: ids with multiplier value following the id
    :param UserList ulist: user list of User objects
    :param Message message: message object that calls this function
    :param reason: type of adjust, add or subtract"""
    global post_params
    realness_list = []
    dmultiplier = 1
    for i, name in enumerate(names):
        try:
            if (int(name) < 1 and i != 0 and name not in ulist.ids):
                del names[i-1]
                names.remove(name)
                post_params['text']= 'That doesn\'t make sense'
                send_message(post_params)
        except:
            continue
    multiplier_bool = [bool(name.isdigit() and name not in ulist.ids) for name in names]
    for i,name in enumerate(names):
        if (name.isdigit() and len(name)==8 and name in ulist.ids):
            try:
                if multiplier_bool[i+1]:
                    realness_list.append((name,int(names[i+1])))
                else:
                    realness_list.append((name,dmultiplier))
            except IndexError:
                realness_list.append((name,dmultiplier))
        elif (name.isdigit() and name not in ulist.ids):
            continue
        else:
            try:
                if multiplier_bool[i+1]:
                    realness_list.append((ulist.findByName(name).user_id,int(names[i+1])))
                else:
                    realness_list.append((ulist.findByName(name).user_id,dmultiplier))
            except:
                realness_list.append((ulist.findByName(name).user_id,dmultiplier))
    if [x[0] for x in realness_list].count('0') > 1:
        post_params['text'] = 'Invalid IDs'
        send_message(post_params)
        return
    text = str()
    if reason == 'add':
        text = 'Real '
    elif reason == 'subtract':
        text = 'Not Real '
    for actual_id in [id_tuple for id_tuple in realness_list if (id_tuple[0] != '0')]:
        if adjust_realness(actual_id[0], ulist, message, reason) == False:
            continue
        else:
            [adjust_realness(actual_id[0], ulist, message, reason) for x in range(actual_id[1]-1)]
            text += ulist.find(actual_id[0]).name.capitalize() + ' '+ str(actual_id[1]) + '. '
    if text != 'Real ' and text != 'Not Real ':
        post_params['text'] = text
        send_message(post_params)
    if (reason == 'subtract' and ulist.findByName("carter").user_id in realness_list):
        post_params['text'] = 'It is terminal.'
        send_message(post_params)

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id, ulist):
    """Reads in messages from GroupMe API through requests.get().
    Converts messages into Message objects. Filters system and bot messages.
    Updates ulist with update method of UserList.  Calls commands().  Calls
    last_write().
    :param dict request_params: dictionary of token
    :param str group_id: group id
    :param UserList ulist: user list of User objects
    :return list: list of Message objects"""
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
            users_write(ulist)

    if len(message_list) > 0:
        last_write(message_list[0].id)

    return message_list

def start_timer(rest, user_id, message):
    """Creates timer list of tuples.
    :param str rest: number of minutes
    :param str user_id: user id to start timer for
    :param Message message: message calling this function"""
    global timer
    timer += [(True, datetime.now() + (timedelta(minutes=int(rest[0]))), user_id, message)]
    timer = sorted(timer, key = lambda x:x[1])


def set_timer(text, message):
    """Parses text and calls start_timer() to creat timer.  Sends message with
    send_message() to alert the person being timed.
    :param str text: text split from @rb command ##probably needs be updated
    :param Message message: message calling this function"""
    if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
        name = message.attachments[0]['loci'][0]
        rest = text[name[0] + name[1]-3:].strip().split(" ")
        if (len(rest) == 1 and rest[0].isdigit()):
            start_timer(rest, message.attachments[0]['user_ids'][0], message)
            post_params['text'] = 'Timer set for ' + rest[0] + ' minutes'
            send_message(post_params)
        else:
            post_params['text'] = "I don't know when that is: '" + str(text[name[0] + name[1]-3:]) + "'"
            send_message(post_params)
    else:
        post_params['text'] = "I don't know who that is"
        send_message(post_params)

def cancel_timer(user_id):
    """Cancels timer.
    :param str user_id: user id"""
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
    """Sends message of all commands.
    :param dict post_params: text, bot_id required"""
    post_params['text'] = ("These are the following commands:\n" +
                                      "not real [@mention]\n" +
                                      "very real [@mention]\n" +
                                      "timer [@mention] [time]\n" +
                                      "shop [item] [time]\n" +
                                      "use [ability] [time]\n" +
                                      "help [command]\n"
                                      "[@mention] [stat]\n"+
                                      "ranking")
    send_message(post_params)


def helper_specific(post_params, text):
    """Sends help message for each command.
    :param dict post_params: text, bot_id required
    :param str text: text after @rb command"""
    reason = text.lower().split(" ")[1:]
    if (len(reason) == 1):
        if (reason[0] == "not"):
            post_params['text'] = ("The not real command is used to shame a user for their lack of realness\n" +
                      "Example: @rb not real Carter")
            send_message(post_params)
        elif (reason[0] == "very"):
            post_params['text'] = ("The very real command is used to reward a user for their excess of realness\n" +
                      "Example: @rb very real Carter")
            send_message(post_params)
        elif (reason[0] == "ranking"):
            post_params['text'] = ("The ranking command shows how real everyone is\n" +
                      "Example: @rb ranking")
            send_message(post_params)
        elif (reason[0] == "timer"):
            post_params['text'] = ("Set a timer in minutes so people aren't late\n" +
                      "Example: @rb timer @LusciousBuck 10")
            send_message(post_params)
        elif (reason[0] == 'shop'):
            post_params['text'] = ("Shop for radical abilities dude\n" +
                      "Example: @rb shop protect 10")
            send_message(post_params)
        elif (reason[0] == 'use'):
            post_params['text'] = ("Use you radical abilities dude\n" +
                      "Example: @rb use protect 10")
            send_message(post_params)
        elif (reason[0] == 'stats' or reason[0] == 'stat'):
            post_params['text'] = ("There are six stats to lookup:\n" +
                       "name\n" +
                       "nickname\n" +
                       "realness\n" +
                       "abilities\n" +
                       "protected")
            send_message(post_params)
        elif (reason[0] == 'help'):
            post_params['text'] = ("The help command has 3 uses:\n\n" +
                      "help [command]: find info on how to call commands and what they do\n\n" +
                      "help shop [item]: find info on abilities in the shop\n\n" +
                      "help ability [ability]: find info on what abilities do")
            send_message(post_params)
        else:
            helper_main(post_params)
    elif (len(reason) == 2):
        if (reason[0] == 'shop'):
            if (reason[1] == 'protect'):
                post_params['text'] = ("The protect ability is 10rp per hour")
                send_message(post_params)
            else:
                post_params['text'] = ("Sorry, that's not an ability for sale")
                send_message(post_params)
        elif (reason[0] == 'ability'):
            if (reason[1] == 'protect'):
                post_params['text'] = ("The protect ability protects you from losing rp")
                send_message(post_params)
            else:
                post_params['text'] = ("Sorry, that's not an ability")
                send_message(post_params)
        elif (reason[0] == 'very' and reason[1] == 'real'):
            post_params['text'] = ("The very real command is used to reward a user for their excess of realness\n" +
                      "Example: @rb very real Carter")
            send_message(post_params)
        elif (reason[0] == 'not' and reason[1] == 'real'):
            post_params['text'] = ("The not real command is used to shame a user for their lack of realness\n" +
                      "Example: @rb not real Carter")
            send_message(post_params)
        else:
            helper_main(post_params)
    else:
        helper_main(post_params)


def very_real(text, message, ulist):
    """Parses very real text command.  Calls text_change_realness() to add
    realness.
    :param str text: text after @rb command
    :param Message message: message calling this command
    :param UserList ulist: user list of User objects"""
    if len(text.split('very real')[1]) == 0:
        post_params['text'] = 'Nothing to add realness to.'
        send_message(post_params)

    if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
        for i, id in enumerate(message.attachments[0]['user_ids']):
            text = text.replace((message.text[message.attachments[0]['loci'][i][0] : message.attachments[0]['loci'][i][0]+message.attachments[0]['loci'][i][1]]).lower(),id)
        nameslist = text.lower().split('very real')[1].split()
    else:
        nameslist = text.lower().split('very real')[1].split()
    text_change_realness(nameslist, ulist, message, 'add')

def not_real(text, message, ulist):
    """Parses very real text command.  Calls text_change_realness() to subtract
    realness.
    :param str text: text after @rb command
    :param Message message: message calling this command
    :param UserList ulist: user list of User objects"""
    if len(text.split('not real')[1]) == 0:
        post_params['text'] = 'Nothing to add realness to.'
        send_message(post_params)
    if (message.attachments!= [] and message.attachments[0]['type'] == 'mentions'):
        for i, id in enumerate(message.attachments[0]['user_ids']):
            text = text.replace((message.text[message.attachments[0]['loci'][i][0] : message.attachments[0]['loci'][i][0]+message.attachments[0]['loci'][i][1]]).lower(),id)
        nameslist = text.lower().split('not real')[1].split()
    else:
        nameslist = text.lower().split('not real')[1].split()
    text_change_realness(nameslist, ulist, message, 'subtract')


def shop(text, message, ulist):
    text = text[1].strip().split(' ')
    if text[0] in ['protect']:
        person = ulist.find(message.sender_id)
        if (len(text) > 1 and text[1].isdigit()):
            if person.realness > 10 * int(text[1]):
                person.add_ability(Ability(text[0], int(text[1])))
                person.realness -= 10 * int(text[1])

                post_params['text'] = "Ok, 1 " +text[0]+ " ability. That'll last yah " + text[1] + ' hours.'
                send_message(post_params)
            else:
                post_params['text'] = 'Fuck off peasant.'
                send_message(post_params)
        else:
            post_params['text'] = 'I think you messed up how long you want this effect for?'
            send_message(post_params)
    else:
        post_params['text'] = "I don't have that ability for sale... yet."
        send_message(post_params)

#checks for last message and runs commands
def commands(message, ulist):
    global post_params

    if message.text == None:
        return
    elif message.text.lower().startswith('here'):
        cancel_timer(message.user_id)
    elif (message.text.lower().startswith('@rb')):
            text = message.text.split('@rb ')

            if (len(text) == 1):
                helper_main(post_params)
                return
            text = text[1].lower().strip()

            if text.startswith('very real'):
                very_real(text, message, ulist)

            elif text.startswith('not real'):
                not_real(text, message, ulist)

            elif text in ['ranking', 'rankings', 'r']:
                ulist.ranking(post_params)

            elif text.startswith('timer'):
                set_timer(text, message)

            elif (text.startswith("help")):
                helper_specific(post_params, text)

            elif (text.startswith('here')):
                cancel_timer(message.user_id)

            elif (text.lower().startswith('shop')):
                shop((text.split('shop')), message, ulist)

            elif (text.lower().startswith('use')):
                rest = text.split('use')[1].strip().split(' ')
                ulist.find(message.sender_id).use_ability(rest)

            elif (text.lower().startswith('@') and message.attachments[0] != []):
                user = message.attachments[0]['user_ids']
                if len(user) > 1:
                    post_params['text'] = "One person at a time please"
                    send_message(post_params)
                else:
                    loc = message.attachments[0]['loci'][0]
                    rest = text[(loc[0] + loc[1]) - 3 : ]
                    rest = rest.strip().split(' ')
                    if (len(rest) < 1):
                        post_params['text'] = "This call should look like:\n @rb @LusciousBuck abilities"
                        send_message(post_params)
                    else:
                        ulist.find(user[0]).value(rest[0])
            elif (len(text.split(' ')) == 2 and text.split(' ')[0] in ulist.names):
                rest = text.split(' ')
                ulist.findByName(rest[0]).value(rest[1])
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

#            for val in [timer[0][2] for i in range(49)]:
#                adjust_realness(val, userlist, timer[0][3], 'subtract')
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
