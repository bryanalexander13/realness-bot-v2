import requests
import time
import json
import os
from datetime import datetime, timedelta
import play4

class User:
    """Users information"""
    def __init__(self, user_id, name, nickname, realness = 0, abilities = [], protected = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), thornmail = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.realness = realness
        self.abilities = abilities
        self.protected = self.datetime_read(protected)
        self.thornmail = self.datetime_read(thornmail)
        self.switch = {"protect" : "self.protect(ability.val)", 
                       "thornmail" : "self.thornmailed(ability.val)",
                       "bomb" : "self.bomb(person, ulist, message, ability.val, post_params)"}
        self.ability_read()
        self.properties = self.__dict__().keys()

    def __dict__(self):
        return {"user_id": self.user_id,
                "name": self.name,
                "nickname": self.nickname,
                "realness": self.realness,
                "abilities": self.ability_write(),
                "protected": self.datetime_write(self.protected),
                "thornmail": self.datetime_write(self.thornmail)}

    def add_realness(self, multiplier=1):
        self.realness += multiplier

    def subtract_realness(self, multiplier=1):
        self.realness -= multiplier

    def add_ability(self, ability):
        self.abilities += [ability]

    def remove_ability(self, ability):
        self.abilities.remove(ability)

    def changeNickname(self, nickname):
        self.nickname = nickname

    def use_ability(self, rest, ulist, message, post_params):
        if len(rest) == 2 and rest[1].isdigit():
            for ability in self.abilities:
                if (rest[0] == ability.type and int(rest[1]) == ability.val):
                    self.remove_ability(ability)
                    exec(self.switch[ability.type])
                    post_params['text'] = "Ability used"
                    send_message(post_params)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        elif len(rest) >= 3 and rest[1].isdigit() and message.attachments != []:
            for ability in self.abilities:
                if (rest[0] == ability.type and int(rest[1]) == ability.val):
                    self.remove_ability(ability)
                    person = message.attachments[0]['user_ids'][0]
                    exec(self.switch[ability.type])
                    post_params['text'] = "Ability used"
                    send_message(post_params)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        else:
            post_params['text'] = "I'm not sure what ability that is"
            send_message(post_params)

    def protect(self, time):
        self.protected = datetime.now() + timedelta(hours = time)
        
    def thornmailed(self, time):
        self.thornmail = datetime.now() + timedelta(hours = time)
    
    def bomb(self, person, ulist, message, power, post_params):
        adjust_realness(person, ulist, message, "subtract", post_params, multiplier=10*power)
        
    def datetime_write(self, date):
        return date.strftime("%Y-%m-%d %H:%M:%S.%f")

    def datetime_read(self, date):
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")

    def ability_write(self):
        return [(i.type, i.val) for i in self.abilities]

    def ability_read(self):
        self.abilities = [Ability(i[0],i[1]) for i in self.abilities]

    def value(self, val, post_params):
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
            self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected'], i['thornmail']) for i in udict]
        except:
            try:
                self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected']) for i in udict]
            except:
                self.ulist = [User(i['user_id'], i["name"], i['nickname']) for i in udict]
        self.ids = {i.user_id:i for i in self.ulist}
        self.names = {i.name:i for i in self.ulist}
        self.nicknames = {i.nickname:i for i in self.ulist}
        self.realnesses = {i.realness:i for i in self.ulist}

    def find(self, user_id):
        try:
            return self.ids[user_id]
        except:
            return User("0", "invalid", "invalid")

    def findByName(self, name):
        try:
            return self.names[name]
        except:
            return User("0", "invalid", "invalid")

    def findByNickname(self, nickname):
        try:
            return self.nicknames[nickname]
        except:
            return User("0", "invalid", "invalid")
    
    def findByRealness(self, realness):
        try:
            return self.realnesses[realness]
        except:
            return User("0", "invalid", "invalid")

    def add(self, user):
        self.ulist += [user]
        self.ids[user.user_id] = user
        self.names[user.name] = user
        self.nicknames[user.nickname] = user
        self.realnesses[user.realness] = user

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


class Timer:
    
    def __init__(self, punishment, time, user):
        self.punishment = punishment
        self.time = time
        self.person = user
        
    def explode(self, post_params):
        if self.punishment:
            self.person.subtract_realness()
            post_params['text'] = "Hey Retard. You're late"
            post_params['attachments'] = [{'loci': [[4,6]], 'type':'mentions', 'user_ids':[self.person.user_id]}]
            send_message(post_params)
            post_params['attachments'] = []
        else:
            post_params['text'] = "@" + self.person.nickname + " You're Timer Is Up!"
            post_params['attachments'] = [{'loci': [[0,len(self.person.nickname)]], 'type':'mentions', 'user_ids':[self.person.user_id]}]
            send_message(post_params)
            post_params['attachments'] = []
            

class TimerList:
    
    def __init__(self, timers = []):
        self.timerlist = timers
        self.timerdict = {i.time:i for i in timers}
        self.iddict = {i.person.user_id:i for i in timers}
    
    def add(self, timer):
        self.timerlist += [timer]
        self.timerdict[timer.time] = timer
        self.iddict[timer.person.user_id] = timer
        
    def remove(self, timer):
        try:
            del self.timerdict[timer.time]
            del self.iddict[timer.person.user_id]
            self.timerlist.remove(timer)
            return True
        except:
            return False
    
    def upnext(self):
        try:
            return self.timerdict[min(self.timerdict)]
        except:
            return Timer(False, datetime.now() + timedelta(days= 1), "Invalid")
    
    def check(self, post_params):
        timer = self.upnext()
        if timer.time <= datetime.now():
            timer.explode(post_params)
            self.remove(timer)       
    
    def cancel_timer(self, user_id, post_params):
        if self.remove(user_id):
            post_params['text'] = "Finally"
            send_message(post_params)
    
    def set_timer(self, text, message, ulist, post_params):
        if (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
            name = message.attachments[0]['loci'][0]
            rest = text[name[0] + name[1]-3:].strip().split(" ")
            if (len(rest) == 1 and rest[0].isdigit()):
                self.add(Timer(True, datetime.now() + (timedelta(minutes=int(rest[0]))), ulist.find(message.attachments[0]['user_ids'][0])))
                post_params['text'] = 'Timer set for ' + rest[0] + ' minutes'
                send_message(post_params)
            else:
                post_params['text'] = "I don't know when that is: '" + str(text[name[0] + name[1]-3:]) + "'"
                send_message(post_params)
        elif (len(text.split(' ')) == 2 and text.split(' ')[1].isdigit()):
            self.add(Timer(False, datetime.now() + (timedelta(minutes=int(text.split(' ')[1]))), ulist.find(message.sender_id)))
            post_params['text'] = 'Timer set for ' + text.split(' ')[1] + ' minutes'
            send_message(post_params)
        else:
            post_params['text'] = ("I don't know when or who that is.\n" +
                                   "Ex. @rb timer @Employed Degenerate 10 or\n" +
                                   "@rb timer 10")
            send_message(post_params)
            
        

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
        auth.close()
    return data

def users_load():
    """Loads users from users2.json.
    :return list: user dictionaries"""
    with open(os.path.abspath('users2.json'),'r') as users:
        file = users.readlines()
        data = json.loads(file[0])
        users.close()
    return data

def users_write(ulist):
    """Writes user dictionaries to users2.json.
    :param UserList ulist: user list of User objects"""
    with open(os.path.abspath('users2.json'),'w') as users:
        users.write(json.dumps([i.__dict__() for i in ulist.ulist]))
        users.close()

def last_load():
    """Loads last message id read.
    :return str: message id"""
    with open(os.path.abspath('last.json'),'r') as last:
        file = last.readlines()
        data = json.loads(file[0])
        last.close()
    return data['last_read']

def last_write(last_message):
    """Writes last message id to last.json.
    :param str last_message: last message id"""
    if int(last_message) > int(last_load()):
        with open(os.path.abspath('last.json'),'w') as l:
            l.write(json.dumps({'last_read':last_message}))
            l.close()

def stat_write(stat):
    with open(os.path.abspath('users2.json'),'a') as s:
        s.write(str(stat) + '\n')
        s.close()

def update_everyone(request_params, group_id, ulist, auth):
    group = requests.get('https://api.groupme.com/v3/groups/' +group_id, params = request_params).json()['response']
    if group['id'] == auth['equipo']['group_id']:
        for member in group['members']:
            user = ulist.find(member['user_id'])
            if user.name == 'invalid':
                ulist.add(User(member['user_id'], member['nickname'], member['nickname']))
            else:
                user.nickname = member['nickname']

def members(request_params, group_id):
    group = requests.get('https://api.groupme.com/v3/groups/' + group_id, params = request_params).json()['response']
    return group['members']

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", json = post_params)

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
def adjust_realness(target_id, ulist, message, reason, post_params, multiplier=1):
    """Adds or subtracts realness from User. Calls add_realness() or
    subtract_realness() of User and find methods of UserList and send_message().
    Calls users_write().
    :param str id: user id of user to modify
    :param UserList ulist: user list of User objects
    :param Message message: message object that calls this function
    :param reason: type of adjust, add or subtract
    :return bool: True if success, False if failure"""
    person = ulist.find(target_id)

    if target_id == message.sender_id:
        post_params['text'] = 'You can\'t change your own realness.'
        send_message(post_params)
        return False
    elif reason == 'add':
        person.add_realness(multiplier)
        return True
    elif reason == 'subtract':
        if person.protected > datetime.now():
            post_params['text'] = 'Sorry, ' + person.nickname + ' is protected.'
            send_message(post_params)
            return False
        elif person.thornmail > datetime.now():
            ulist.find(message.sender_id).realness -= 1
            post_params['text'] = 'Sorry, ' + person.nickname + ' is protected.'
            send_message(post_params)
            return False
        else:
            person.subtract_realness(multiplier)
            return True
    users_write(ulist)
    return True

def text_change_realness(names, ulist, message, reason, post_params):
    """Adds or Subtracts realness with multiple values. Posts messages with
    realness updates.  Calls send_message() and adjust_realness(). Uses findByName
    method of UserList.
    :param list names: ids with multiplier value following the id
    :param UserList ulist: user list of User objects
    :param Message message: message object that calls this function
    :param reason: type of adjust, add or subtract"""
    realness_list = []
    dmultiplier = 1
    for i, name in enumerate(names):
        try:
            if (int(name) < 1 and i != 0 and ulist.find(name).name == 'invalid'):
                del names[i-1]
                names.remove(name)
                post_params['text']= 'That doesn\'t make sense'
                send_message(post_params)
        except:
            continue
    multiplier_bool = [bool(name.isdigit() and ulist.find(name).name == 'invalid') for name in names]
    for i,name in enumerate(names):
        if (name.isdigit() and len(name)==8 and ulist.find(name).name != 'invalid'):
            try:
                if multiplier_bool[i+1]:
                    realness_list.append((name,int(names[i+1])))
                else:
                    realness_list.append((name,dmultiplier))
            except IndexError:
                realness_list.append((name,dmultiplier))
        elif (name.isdigit() and ulist.find(name).name == 'invalid'):
            continue
        else:
            try:
                if multiplier_bool[i+1]:
                    realness_list.append((ulist.findByName(name).user_id,int(names[i+1])))
                else:
                    realness_list.append((ulist.findByName(name).user_id,dmultiplier))
            except:
                realness_list.append((ulist.findByName(name).user_id,dmultiplier))
    if [x[0] for x in realness_list].count('0') >= 1:
        post_params['text'] = 'Invalid IDs'
        send_message(post_params)
        return
    text = str()
    if reason == 'add':
        text = 'Real '
    elif reason == 'subtract':
        text = 'Not Real '
    for actual_id in [id_tuple for id_tuple in realness_list if (id_tuple[0] != '0')]:
        if adjust_realness(actual_id[0], ulist, message, reason, post_params) == False:
            continue
        elif int(actual_id[1])-1 == 0:
            text += ulist.find(actual_id[0]).name.capitalize() + ' '+ str(actual_id[1]) + '. '
        else:
            adjust_realness(actual_id[0], ulist, message, reason, post_params, actual_id[1]-1)
            text += ulist.find(actual_id[0]).name.capitalize() + ' '+ str(actual_id[1]) + '. '
    if text != 'Real ' and text != 'Not Real ':
        post_params['text'] = text
        send_message(post_params)
    if (reason == 'subtract' and ulist.findByName("carter").user_id in realness_list):
        post_params['text'] = 'It is terminal.'
        send_message(post_params)

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id, ulist, post_params, auth, timerlist):
    """Reads in messages from GroupMe API through requests.get().
    Converts messages into Message objects. Filters system and bot messages.
    Updates ulist with update method of UserList.  Calls commands().  Calls
    last_write().
    :param dict request_params: dictionary of token
    :param str group_id: group id
    :param UserList ulist: user list of User objects
    :return list: list of Message objects"""
    try:
        response_messages = requests.get('https://api.groupme.com/v3/groups/{}/messages'.format(group_id), params = request_params).json()['response']['messages']
    except:
        print('connection problem')
        time.sleep(10)
        return
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
            commands(mess, ulist, post_params, timerlist, request_params, group_id)
            update_everyone(request_params, group_id, ulist, auth)
            users_write(ulist)

    if len(message_list) > 0:
        last_write(message_list[0].id)

    return message_list


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


def very_real(text, message, ulist, post_params):
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
    text_change_realness(nameslist, ulist, message, 'add', post_params)

def not_real(text, message, ulist, post_params):
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
    text_change_realness(nameslist, ulist, message, 'subtract', post_params)


def shop(text, message, ulist, post_params):
    text = text[1].strip().split(' ')
    if text[0] in ['protect', 'thornmail', 'bomb']:
        person = ulist.find(message.sender_id)
        if (len(text) > 1 and text[1].isdigit()):
            if text[0] in ['protect', 'bomb']:
                if person.realness >= 10 * int(text[1]):
                    person.add_ability(Ability(text[0], int(text[1])))
                    person.realness -= 10 * int(text[1])
    
                    post_params['text'] = "Ok, 1 " +text[0]+ " ability."
                    send_message(post_params)
                else:
                    post_params['text'] = 'Fuck off peasant.'
                    send_message(post_params)
            elif text[0] in ['thornmail']:
                if person.realness >= 15 * int(text[1]):
                    person.add_ability(Ability(text[0], int(text[1])))
                    person.realness -= 15 * int(text[1])
    
                    post_params['text'] = "Ok, 1 " +text[0]+ " ability. That'll last yah " + text[1] + ' hours.'
                    send_message(post_params)
                else:
                    post_params['text'] = 'Fuck off peasant.'
                    send_message(post_params)
                
            else:
                post_params['text'] = 'UH OH. Bad Fuckup'
                send_message(post_params)
        else:
            post_params['text'] = 'I think you messed up how long you want this effect for?'
            send_message(post_params)
            
    else:
        post_params['text'] = "I don't have that ability for sale... yet."
        send_message(post_params)


def call_all(message, ulist, post_params, request_params, group_id):
    loci = []
    user_ids = []
    people = members(request_params, group_id)
    for i,person in enumerate(people):
        loci += [[i,i+1]]
        user_ids += [person['user_id']]
    post_params['attachments'] = [{'loci': loci, 'type':'mentions', 'user_ids':user_ids}]#[{'loci': [[0, 1], [2,1], [4,1], [6,1], [8,1], [10,1]], 'type':'mentions', 'user_ids': ulist.nicknames}]
    post_params['text'] = "@everyone " + message.text.split('@all')[1].strip()
    send_message(post_params)
    post_params['attachments'] = []


def play(user_id, user_name, user2_id = '', user2_name = '', print_type = 'phone'):
    play4.play_connect4(user_id, user_name, user2_id, user2_name, print_type)


#checks for last message and runs commands
def commands(message, ulist, post_params, timerlist, request_params, group_id):
    if message.text == None:
        return
    elif message.text.lower().startswith('here'):
        timerlist.cancel_timer(message.user_id, post_params)
    elif (message.text.lower().startswith("@all") or message.text.lower().startswith("@everyone")):
        call_all(message, ulist, post_params, request_params, group_id)
    elif (message.text.lower().strip() == '@rb'):
        helper_main(post_params)
    elif (message.text.lower().startswith('@rb ')):
            text = message.text.split('@rb ')

            text = text[1].lower().strip()

            if text.startswith('very real'):
                very_real(text, message, ulist, post_params)

            elif text.startswith('not real'):
                not_real(text, message, ulist, post_params)

            elif text in ['ranking', 'rankings', 'r']:
                ulist.ranking(post_params)

            elif text.startswith('timer'):
                timerlist.set_timer(text, message, ulist, post_params)

            elif (text.startswith("help")):
                helper_specific(post_params, text)

            elif (text.startswith('here')):
                timerlist.cancel_timer(message.user_id, post_params)

            elif (text.lower().startswith('shop')):
                shop((text.split('shop')), message, ulist, post_params)

            elif (text.lower().startswith('use')):
                rest = text.split('use')[1].strip().split(' ')
                ulist.find(message.sender_id).use_ability(rest, ulist, message, post_params)

            elif (text.startswith('play')):
                t = text.split(' ')
                if len(t) == 1 or len(t) == 2:
                    if text.endswith('both'):
                        play(message.sender_id, message.name, '', '', 'both')
                    elif text.endswith('computer'):
                        play(message.sender_id, message.name, '', '', 'computer')
                    else:
                        play(message.sender_id, message.name, '', '', 'phone')
                    return
                elif (message.attachments[0] != [] and message.attachments[0]['type'] == 'mentions'):
                    person = message.attachments[0]['user_ids']
                    if len(person) == 1:
                        if text.endswith('both'):
                            name = ulist.find(person[0]).nickname
                            play(message.sender_id, message.name, person[0], name, 'both')
                        elif text.endswith('computer'):
                            name = ulist.find(person[0]).nickname
                            play(message.sender_id, message.name, person[0], name, 'computer')
                        else:
                            name = ulist.find(person[0]).nickname
                            play(message.sender_id, message.name, person[0], name, 'phone')
                    else:
                        helper_main(post_params)
                else:
                    helper_main(post_params)

            elif (text.lower().startswith('@') and message.attachments != []):
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
                        ulist.find(user[0]).value(rest[0], post_params)
            elif (len(text.split(' ')) == 2 and text.split(' ')[0] in ulist.names):
                rest = text.split(' ')
                ulist.findByName(rest[0]).value(rest[1])
            else:
                helper_main(post_params)


def run(request_params, post_params, timerlist, group_id, userlist, auth):
    while (1 == True):
        message_list = read_messages(request_params, group_id, userlist, post_params, auth, timerlist)

        timerlist.check(post_params)

        time.sleep(1)

def startup():
    user_dict = users_load()
    userlist = UserList(user_dict)
    auth = auth_load()
    bot = auth['equipo']
    group_id = bot['group_id']
    request_params = {'token':auth['token']}
    post_params = {'text':'','bot_id':bot['bot_id'],'attachments':[]}
    timerlist = TimerList()
    text = 'The current realness levels are: \n'
    for user in sorted(userlist.ulist, key=lambda x: x.realness):
        text += user.nickname +': ' + str(user.realness) + '\n'
    print(text)
    run(request_params, post_params, timerlist, group_id, userlist, auth)


if __name__ == "__main__":

    startup()
