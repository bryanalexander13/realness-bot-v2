import requests
import time
import json
import os
from datetime import datetime, timedelta
import play4
import random
from reddit_bot import Reddit
import string
from collections import defaultdict

class User:
    """Users information"""
    def __init__(self, user_id, name, nickname, realness = 0, abilities = [], protected = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), thornmail = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), reward = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f"), permission = 'user'):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.realness = realness
        self.abilities = abilities
        self.permission = permission
        self.protected = self.datetime_read(protected)
        self.thornmail = self.datetime_read(thornmail)
        self.reward = self.datetime_read(reward)
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
                "thornmail": self.datetime_write(self.thornmail),
                "reward": self.datetime_write(self.reward),
                "permission": self.permission}
        

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
                    self.use(ability, post_params)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        elif len(rest) >= 3 and rest[1].isdigit() and message.attachments != []:
            for ability in self.abilities:
                if (rest[0] == ability.type and int(rest[1]) == ability.val):
                    self.use(ability, post_params)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        else:
            post_params['text'] = "I'm not sure what ability that is"
            send_message(post_params)
    
    def use(self, ability, post_params):
        self.remove_ability(ability)
        exec(self.switch[ability.type])
        post_params['text'] = "Ability used"
        send_message(post_params)

    def protect(self, time):
        self.protected = datetime.now() + timedelta(days = time)

    def thornmailed(self, time):
        self.thornmail = datetime.now() + timedelta(days = time)

    def bomb(self, person, ulist, message, power, post_params):
        person.adjustRealness(ulist, message, "subtract", post_params, multiplier=10*power)

    def daily_reward(self, post_params):
        if self.reward <= datetime.now() - timedelta(days=1):
            ran = random.randint(0,9)
            if ran > 2:
                rew = max(min(round(abs(random.gauss(5,5)-5)), 10), 1) 
                self.add_realness(rew)
                post_params['text'] = "You got " + str(rew) + "rp"
                send_message(post_params)
            else:
                ran = random.randint(0,2)
                if ran == 0:
                    ab = Ability('protect', max(min(round(abs(random.gauss(3,1) -3)), 3), 1))
                elif ran == 1:
                    ab = Ability('thornmail', max(min(round(abs(random.gauss(3,1) -3)), 3), 1))
                elif ran == 2:
                    ab = Ability('bomb', max(min(round(abs(random.gauss(3,1) -3)), 3), 1))
                self.add_ability(ab)
                post_params['text'] = "You got a " + ab.type + " " + str(ab.val)
                send_message(post_params)
            self.reward = datetime.now()
        else:
            post_params['text'] = "Sorry, you already got your reward for today."
            send_message(post_params)
                
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
            
    def adjustRealness(self, message, reason, ulist, post_params, multiplier = 1):
        if (message.sender_id == self.user_id):
            return ReturnObject(False, "You can't adjust your own realness")
        elif (multiplier > 3):
            return ReturnObject(False, "You're limited to changing 3 realness at a time")
        elif (reason == 'add'):
            self.add_realness(multiplier)
            return ReturnObject(True, multiplier)
        else:
            for ability in self.abilities:
                if (ability.type in ["protect", "thornmail"]):
                    self.use(ability, post_params)
            if self.protected > datetime.now():
                return ReturnObject(False, 'Sorry, ' + self.nickname + ' is protected.')
            elif self.thornmail > datetime.now():
                ulist.find(message.sender_id).realness -= multiplier
                return ReturnObject(False, 'Sorry, ' + self.nickname + ' is protected.')
            else:
                self.subtract_realness(multiplier)
                return ReturnObject(True, multiplier)



class Ability:
    def __init__(self, typ, val):
        self.type = typ
        self.val = val


class UserList:
    def __init__(self, udict):
        try:
            self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected'], i['thornmail'], i['reward'], i['permission']) for i in udict]
        except:
            try:
                self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected'], i['thornmail'], i['reward']) for i in udict]
            except:
                self.ulist = [User(i['user_id'], i["name"], i['nickname']) for i in udict]
        self.ids = {i.user_id:i for i in self.ulist}
        self.names = {i.name:i for i in self.ulist}
        self.nicknames = {i.nickname:i for i in self.ulist}
        self.realnesses = {i.user_id:i.realness for i in self.ulist}
        self.peopleFinders = [self.find, self.findByName, self.findByNickname]

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
        
    def findPerson(self, word):
        for finder in self.peopleFinders:
            person = finder(word)
            if (person.name != 'invalid'):
                return ReturnObject(True, person)
        return ReturnObject(False)

    def add(self, user):
        self.ulist += [user]
        self.ids[user.user_id] = user
        self.names[user.name] = user
        self.nicknames[user.nickname] = user

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
    
    def clearRealness(self, sender):
        if (self.find(sender).permission == 'admin'):
            for user in self.ulist:
                user.realness = 0
            return ReturnObject(True)
        else:
            return ReturnObject(False, "Sorry, only admins have this ability")
        

class Timer:

    def __init__(self, punishment, time, user, reward = False):
        self.punishment = punishment
        self.time = time
        self.person = user
        self.reward = reward

    def explode(self, post_params):
        if self.punishment:
            self.person.subtract_realness()
            post_params['text'] = "Hey Retard. You're late"
            post_params['attachments'] = [{'loci': [[4,6]], 'type':'mentions', 'user_ids':[self.person.user_id]}]
            send_message(post_params)
            post_params['attachments'] = []
        else:
            post_params['text'] = "@" + self.person.nickname + " Your Timer Is Up!"
            post_params['attachments'] = [{'loci': [[0,len(self.person.nickname)]], 'type':'mentions', 'user_ids':[self.person.user_id]}]
            send_message(post_params)
            post_params['attachments'] = []


class TimerList:

    def __init__(self, timers = []):
        self.timerlist = (timers + [Timer(False, datetime.now() + timedelta(days= 1000000), User("Invalid", "Invalid", "Invalid"))])
        self.timerdict = {i.time:i for i in self.timerlist}
        self.iddict = {i.person.user_id:i for i in self.timerlist}
        self.min = min(self.timerlist)

    def add(self, timer):
        self.timerlist += [timer]
        self.timerdict[timer.time] = timer
        self.iddict[timer.person.user_id] = timer
        self.min = min(self.timerdict)

    def remove(self, timer, reward, explode):
        try:
            if timer.reward:
                if not reward:
                    return False
                if not explode:
                    timer.person.add_realness()
            del self.timerdict[timer.time]
            del self.iddict[timer.person.user_id]
            self.timerlist.remove(timer)
            self.min = min(self.timerdict)
            return True
        except:
            return False

    def upnext(self):
        try:
            return self.timerdict[self.min]
        except:
            return Timer(False, datetime.now() + timedelta(days= 1000000), "Invalid")

    def check(self, post_params):
        timer = self.upnext()
        if timer.time <= datetime.now():
            timer.explode(post_params)
            self.remove(timer, True, True)
    
    def cancel_timer(self, user_id, post_params):
        try:
            timer = self.iddict[user_id]
        except:
            return
        if self.remove(timer, False, False):
            post_params['text'] = "Finally"
            send_message(post_params)
            
    def games_answer(self, user_id, play, post_params):
        try:
            timer = self.iddict[user_id]
        except:
            return
        if play:
            if self.remove(timer, True, False):
                post_params['text'] = "Let's Go"
                send_message(post_params)
        else:
            timer.person.subtract_realness()
            self.remove(timer, True, True)
            post_params['text'] = "Not Real."
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


class StatEvaluator:
    def __init__(self, group_id):
        self.group_id = group_id
        self.word_dict = self.readDict()
        self.person_stats = defaultdict(lambda: defaultdict(int))
        self.total_stats = defaultdict(int)
        
    def readDict(self):
        try:
            with open(os.path.abspath('word_'+self.group_id+'.json'),'r') as s:
                file = s.readlines()
                word_dict = json.loads(file[0])
                s.close()
            return word_dict
        except:
            return {}
            
    def evaluate(self, ulist):
        for user in ulist.ulist:
            messages = self.word_dict[user.user_id].values()
            for ind, message in enumerate(messages):
                try:
                    message =  message.strip().lower().translate(''.maketrans("","",string.punctuation)).split()
                
                    for word in message:
                        self.total_stats[word] += 1
                        self.person_stats[user.user_id][word] += 1
                except:
                    continue
                
            print(max(self.person_stats[user.user_id]))
            

class Recorder:
    def __init__(self, group_id, ulist, realness_stat = '', word_dict = ''):
        self.group_id = group_id
        self.ulist = ulist
        if (word_dict == ''):
            self.read_dict()
        else:
            self.word_dict = word_dict
        if (realness_stat == ''):
            self.read_realness()
        else:
            self.realness_stat = realness_stat
    
    def realness(self):
        self.realness_stat[str(datetime.now())] = self.ulist.realnesses
        self.record_realness()
        
    def record_realness(self):
        with open(os.path.abspath('realness_stat.json'),'w') as s:
            s.write(json.dumps(self.realness_stat))
            s.close()
            
    def read_realness(self):
        try:
            with open(os.path.abspath('realness_stat.json'),'r') as s:
                file = s.readlines()
                self.realness_stat = json.loads(file[0])
                s.close()
        except:
            self.realness_stat = {}
    
    def add(self, user_id, text):
        try:
            self.word_dict[user_id][str(datetime.now())] = text
            self.record_dict()
        except:
            self.word_dict[user_id] = {str(datetime.now()) : text}
            self.record_dict()
            
    def record_dict(self):
        with open(os.path.abspath('word_'+self.group_id+'.json'),'w') as s:
            s.write(json.dumps(self.word_dict))
            s.close()
            
    def read_dict(self):
        try:
            with open(os.path.abspath('word_'+self.group_id+'.json'),'r') as s:
                file = s.readlines()
                self.word_dict = json.loads(file[0])
                s.close()
        except:
            self.word_dict = {}
            
    

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
    
class ReturnObject:
    def __init__(self, success = False, obj = None):
        self. success = success
        self.obj = obj


class Parser():
    def __init__(self, text, message, ulist):
        self.text = text
        self.message = message
        self.ulist = ulist
        self.split = []
        self.numbers = []
        self.totals = {}
        self.currentPersonToChange = None
        self.max = 3
        
    def whoToChange(self):
        validate = self.valid_command()
        if (not validate.success):
            return validate
        if (self.message.attachments != []):
            self.removeMentions()
        self.removeNonsense()
        return self.findPeopleAndAmounts()
    
    def valid_command(self):
        strip_command = self.text.split(' ')[2:] 
        if (strip_command == []):
            return ReturnObject(False, "You need to tell me a person too.")
        else:
            self.split = strip_command
            if (len(self.split) == 1 and self.split[0].isdigit()):
                return ReturnObject(False, "You need to tell me a person too.")
            else:
                return ReturnObject(True)      
    
    def removeMentions(self):
        user_ids = self.message.attachments[0]['user_ids'][::-1]
        locations = self.message.attachments[0]['loci'][::-1]
        for ind, user in enumerate(user_ids):
            person = self.ulist.find(user)
            replacement = person.name
            location = locations[ind]
            self.message.text = self.message.text[0:location[0]] + replacement + self.message.text[location[0] + location[1]:]
        self.text = self.message.text[4:].lower().strip()
        self.split = self.text.split(' ')[2:]
        
    def removeNonsense(self):
        toDel = []
        for ind, word in enumerate(self.split):
            personResult = self.ulist.findPerson(word)
            if personResult.success: continue
            
            digit = word.isdigit()
            if digit: continue
            
            if self.split[ind:ind+2] == ["mad","realness"]:
                self.split[ind] = "3"
            elif word == "madrealness":
                self.split[ind] = "3"
            else:
                toDel += [ind]
            
        for ind,i in enumerate(toDel):
            del self.split[i - ind]
    
    def findPeopleAndAmounts(self):
        check = 'person'
        for word in self.split:
            if (check == 'amount'):
                result = self.addAmountToPerson(word)
                check = 'person'
                if (result.success):
                    continue
                
            if (check == 'person'):
                personResult = self.addPersonToTotal(word)
                if (not personResult.success):
                    return personResult
                check = 'amount'
        
        for key in self.totals:
            self.totals[key] = min(self.totals[key],self.max)
        
        return ReturnObject(True, self.totals)
            
    def addPersonToTotal(self, word):
        person = self.ulist.findPerson(word)
        if (person.success):
            self.currentPersonToChange = person.obj
            try:
                self.totals[person.obj] += 1
            except:
                self.totals[person.obj] = 1
            return ReturnObject(True)
        else: 
            return ReturnObject(False, "Invalid Person(s)")
    
    def addAmountToPerson(self, word):
        if word.isdigit():
            try:
                self.totals[self.currentPersonToChange] += (int(word) - 1)
            except:
                self.totals[self.currentPersonToChange] = (int(word) - 1)
            return ReturnObject(True)
        else:
            return ReturnObject(False, "Invalid Amount(s)")
                
        
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

def idea_write(idea):
    with open(os.path.abspath('idea.txt'),'a') as f:
        f.write('|||' + idea)
        f.close()

def stat_write(stat):
    with open(os.path.abspath('stat.txt'),'a') as s:
        s.write(stat + '|||')
        s.close()

def update_everyone(request_params, group_id, ulist):
    try:
        group = requests.get('https://api.groupme.com/v3/groups/' +group_id, params = request_params).json()['response']
    except:
        time.sleep(5)
        update_everyone(request_params, group_id, ulist)
        return

    for member in group['members']:
        user = ulist.find(member['user_id'])
        if user.name == 'invalid':
            ulist.add(User(member['user_id'], member['nickname'], member['nickname']))
        else:
            user.nickname = member['nickname']

def members(request_params, group_id):
    "DEPRICATED"
    group = requests.get('https://api.groupme.com/v3/groups/' + group_id, params = request_params).json()['response']
    return group['members']

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", json = post_params)

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id, ulist, post_params, timerlist, red, word_dict, testmode):
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
        time.sleep(5)
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
            if not testmode:
                update_everyone(request_params, group_id, ulist)
            commands(mess, ulist, post_params, timerlist, request_params, group_id, red)
            if not testmode:
                users_write(ulist)
                word_dict.add(mess.sender_id, mess.text)
                word_dict.realness()
            
    if len(message_list) > 0:
        last_write(message_list[0].id)



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


def remove_realness(change_dict, message, ulist, post_params):
    text = 'Not Real. '
    for user in change_dict.keys():
        result = user.adjustRealness(message, 'subtract', ulist, post_params, change_dict[user])
        if (not result.success):
            post_params['text'] = result.obj
            send_message(post_params)
        else:
            text += user.name.capitalize() + ' ' + str(result.obj) + '. '
    if (text != 'Not Real. '):
        return ReturnObject(True, text)
    else:
        return ReturnObject(False)

def add_realness(change_dict, message, ulist, post_params):
    text = 'Very Real. '
    for user in change_dict.keys():
        result = user.adjustRealness(message, 'add', ulist, post_params, change_dict[user])
        if (not result.success):
            post_params['text'] = result.obj
            send_message(post_params)
        else:
            text += user.name.capitalize() + ' ' + str(result.obj) + '. '
    if (text != 'Very Real. '):
        return ReturnObject(True, text)
    else:
        return ReturnObject(False)

def very_real(text, message, ulist, post_params):
    parser = Parser(text, message, ulist)
    result = parser.whoToChange()
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_text = add_realness(result.obj, message, ulist, post_params)
        if (post_text.success):
            post_params['text'] = post_text.obj
            send_message(post_params)
        
def not_real(text, message, ulist, post_params):
    parser = Parser(text, message, ulist)
    result = parser.whoToChange()
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_text = remove_realness(result.obj, message, ulist, post_params)
        if (post_text.success):
            post_params['text'] = post_text.obj
            send_message(post_params)

def clear(ulist, sender_id, post_params):
    result = ulist.clearRealness(sender_id)
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_params['text'] = 'Cleared'
        send_message(post_params)
        
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

                    post_params['text'] = "Ok, 1 " +text[0]+ " ability. That'll last yah " + text[1] + ' days.'
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

def format_all(ulist):
    loci = []
    user_ids = list(ulist.ids.keys())
    for i,person in enumerate(user_ids):
        loci += [[i,i+1]]
    return [{'loci': loci, 'type':'mentions', 'user_ids':user_ids}]

def call_all(message, ulist, post_params):
    
    if (('@all' not in message.text) and ('@everyone' not in message.text)):
        return False
    
    post_params['attachments'] = format_all(ulist)
    post_params['text'] = message.text
    send_message(post_params)
    post_params['attachments'] = []
    return True


def play(ulist, user_id, user_name, user2_id = '', user2_name = '', print_type = 'phone'):
    outcome = play4.play_connect4(user_id, user_name, user2_id, user2_name, print_type)
    if outcome == "win0":
        ulist.find(user_id).add_realness(5)
    elif outcome == "win1":
        ulist.find(user_id).add_realness(5)
        ulist.find(user2_id).subtract_realness(5)
    elif outcome == "win2":
        ulist.find(user2_id).add_realness(5)
        ulist.find(user_id).subtract_realness(5)
        

def joke(post_params, red):
    try:
        text = red.joke()
    except:
        text = "joke"
    post_params['text'] = text
    send_message(post_params)

def toot(post_params, red):
    try:
        text = red.tootz()
    except:
        text = "toot"
    post_params['text'] = text
    send_message(post_params)
    
def meme(post_params, red):
    try:
        text = red.meme().split('||')
    except:
        post_params['text'] = "meme"
        send_message(post_params)
        return
        
    post_params['text'] = text[0]
    try:
        post_params['attachments'] = [{'type': 'image', 'url': text[1]}]
        send_message(post_params)
        post_params['attachments'] = []
    except:
        send_message(post_params)
        
def idea(post_params, text):
    rest = text.split('idea')
    if len(rest) == 1:
        post_params['text'] = "You didn't give me an idea"
        send_message(post_params)
    else:
        idea_write(rest[1])
        

def blue_pill(post_params, red):
    try:
        text = red.blue_pill().split('||')
    except:
        text = ['Trump REEEEEEEEEEEE','','']
    post_params['text'] = text[0] + '\n' + text[1] + '\n' + text[2]
    if ('imgur' in text[2] or 'redd' in text[2]):
        post_params['attachments'] = [{'type': 'image', 'url': text[2]}]
        send_message(post_params)
        post_params['attachments'] = []
    else:
        send_message(post_params)
    
    
def red_pill(post_params, red):
    try:
        text = red.red_pill().split('||')
    except:
        text = ['$hillary REEEEEEEEEEEE','','']
    post_params['text'] = text[0] + '\n' + text[1] + '\n' + text[2]
    if ('imgur' in text[2] or 'redd' in text[2]):
        post_params['attachments'] = [{'type': 'image', 'url': text[2]}]
        send_message(post_params)
        post_params['attachments'] = []
    else:
        send_message(post_params)
        
def games(ulist, text, message, post_params, timerlist):
    sender_id = message.sender_id
    split = text.split(' ')
    length = len(split)
    if len(message.attachments) != 0 and message.attachments[0]['type'] == 'mentions':
        people = message.attachments[0]['user_ids']
        if not split[1].isdigit():
            for user in people:
                user = ulist.find(user)
                timerlist.add(Timer(True, datetime.now() + timedelta(minutes= 60), user, True))
            post_params['text'] = "Games??? T minus 60 minutes"
        else:
            for user in people:
                user = ulist.find(user)
                timerlist.add(Timer(True, datetime.now() + timedelta(minutes= int(split[1])), user, True))
            post_params['text'] = "Games??? T minus " + split[1] + " minutes"
    elif  length > 2 or (length == 2 and not split[1].isdigit()):
        post_params['text'] = "The games command takes a number for how many minutes to wait for people." + "ex. @rb games 60 or @rb games 60 @friendido @friendido2"
        send_message(post_params)
        return
    elif length == 1:
        for user in ulist.ulist:
            if (user.user_id == sender_id): continue
            timerlist.add(Timer(True, datetime.now() + timedelta(minutes= 60), user, True))
        post_params['text'] = "Games??? T minus 60 minutes"
    elif length == 2:
        for user in ulist.ulist:
            if (user.user_id == sender_id): continue
            timerlist.add(Timer(True, datetime.now() + timedelta(minutes= int(split[1])), user, True))
        post_params['text'] = "Games??? T minus " + split[1] + " minutes"
    post_params['attachments'] = format_all(ulist)
    send_message(post_params)
    post_params['attachments'] = []
        
def games_reply(user_id, text, post_params, timerlist):
    if text.startswith("yes"):
        timerlist.games_answer(user_id, True, post_params)
    else:
        timerlist.games_answer(user_id, False, post_params)
            
#checks for last message and runs commands
def commands(message, ulist, post_params, timerlist, request_params, group_id, red):
    fixed_text = message.text.lower().strip()
    if message.text == None:
        return
    elif fixed_text.startswith('here'):
        timerlist.cancel_timer(message.user_id, post_params)
    elif fixed_text.startswith('yes') or fixed_text.startswith('no'):
        games_reply(message.user_id, fixed_text, post_params, timerlist)
    elif call_all(message, ulist, post_params):
        return
    elif (fixed_text == '@rb'):
        helper_main(post_params)
    elif (fixed_text.startswith('@rb ')):
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
                
            elif (text.startswith('reward')):
                ulist.find(message.sender_id).daily_reward(post_params)

            elif (text.startswith('here')):
                timerlist.cancel_timer(message.user_id, post_params)

            elif (text.startswith('shop')):
                shop((text.split('shop')), message, ulist, post_params)
                
            elif (text == 'joke'):
                joke(post_params, red)
                
            elif (text == 'toot'):
                toot(post_params, red)
                
            elif (text == 'meme'):
                meme(post_params, red)
                
            elif (text == 'idea'):
                idea(post_params, text)
            
            elif (text == 'red pill'):
                red_pill(post_params, red)
                
            elif (text == 'blue pill'):
                blue_pill(post_params, red)
                
            elif (text.startswith('games')):
                games(ulist, text, message, post_params, timerlist)

            elif (text.startswith('use')):
                rest = text.split('use')[1].strip().split(' ')
                ulist.find(message.sender_id).use_ability(rest, ulist, message, post_params)
            
            elif (text == 'clear'):
                clear(ulist, message.sender_id, post_params)
            
            elif (text.startswith('play')):
                t = text.split(' ')
                if len(t) == 1 or len(t) == 2:
                    if text.endswith('both'):
                        play(ulist, message.sender_id, message.name, '', '', 'both')
                    elif text.endswith('computer'):
                        play(ulist, message.sender_id, message.name, '', '', 'computer')
                    else:
                        play(ulist, message.sender_id, message.name, '', '', 'phone')
                    return
                elif (message.attachments != [] and message.attachments[0]['type'] == 'mentions'):
                    person = message.attachments[0]['user_ids']
                    if len(person) == 1:
                        if text.endswith('both'):
                            name = ulist.find(person[0]).nickname
                            play(ulist, message.sender_id, message.name, person[0], name, 'both')
                        elif text.endswith('computer'):
                            name = ulist.find(person[0]).nickname
                            play(ulist, message.sender_id, message.name, person[0], name, 'computer')
                        else:
                            name = ulist.find(person[0]).nickname
                            play(ulist, message.sender_id, message.name, person[0], name, 'phone')
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


def run(request_params, post_params, timerlist, group_id, userlist, red, word_dict, testmode):
    while (1 == True):
        read_messages(request_params, group_id, userlist, post_params, timerlist, red, word_dict, testmode)

        timerlist.check(post_params)    

        time.sleep(1)

def startup(testmode = False):
    user_dict = users_load()
    userlist = UserList(user_dict)
    red = Reddit()
    auth = auth_load()
    bot = auth['equipo']
    if testmode:
        bot = auth['test']
    group_id = bot['group_id']
    word_dict = Recorder(group_id, userlist)
    request_params = {'token':auth['token']}
    post_params = {'text':'','bot_id':bot['bot_id'],'attachments':[]}
    timerlist = TimerList()
    text = 'The current realness levels are: \n'
    for user in sorted(userlist.ulist, key=lambda x: x.realness):
        text += user.nickname +': ' + str(user.realness) + '\n'
    print(text)
    run(request_params, post_params, timerlist, group_id, userlist, red, word_dict, testmode)


if __name__ == "__main__":
    startup()
