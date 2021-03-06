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
import pandas as pd
import plotly
import plotly.graph_objs as go
import traceback
import _thread as thread
import re

class User:
    """Users information"""
    def __init__(self, user_id, name, nickname, realness = 0, abilities = [], protected = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), thornmail = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), permission = 'user', last = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f"), ban = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S.%f")):
        self.user_id = user_id
        self.name = name
        self.nickname = nickname
        self.realness = realness
        self.abilities = abilities
        self.permission = permission
        self.protected = self.datetime_read(protected)
        self.thornmail = self.datetime_read(thornmail)
        self.ban = self.datetime_read(ban)
        self.last = self.datetime_read(last)
        self.switch = {"protect" : "self.protect(ability.val)",
                       "thornmail" : "self.thornmailed(ability.val)",
                       "bomb" : "self.bomb(person, ability.val)"}
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
                "permission": self.permission,
                "last": self.datetime_write(self.last)}


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

    def ban_user(self, length):
        self.ban = datetime.now() + timedelta(hours= length)
    
    def use_ability(self, form, post_params):
        form.removeCommand('use')
        abilities = form.contains(self.switch.keys())
        if len(form.people) > 1:
            post_params['text'] = "I don't know who you're trying to use that on"
            send_message(post_params)
            return
        elif len(form.numbers) != 1:
            post_params['text'] = "I don't know how long your ability lasts for"
            send_message(post_params)
            return
        elif abilities.success and len(abilities.obj) == 1:
            abilities = abilities.obj
            for ability in self.abilities:
                if abilities[0] == ability.type and form.numbers[0] == ability.val:
                    self.use(ability, post_params, form.people)
                    return
            post_params['text'] = "You don't have that ability"
            send_message(post_params)
        else:
            post_params['text'] = "I don't know which ability you want to use"
            send_message(post_params)

    def use(self, ability, post_params, person = []):
        if ability.type == 'bomb':
            if person == []:
                post_params['text'] = "That's not a person"
                send_message(post_params)
                return
            else:
                person = person[0]
        exec(self.switch[ability.type])
        self.remove_ability(ability)
        post_params['text'] = ability.type + " used"
        send_message(post_params)

    def protect(self, time):
        self.protected = datetime.now() + timedelta(days = time)

    def thornmailed(self, time):
        self.thornmail = datetime.now() + timedelta(days = time)

    def bomb(self, person, power):
        person.subtract_realness(multiplier=10*power)

    def daily_reward(self):
        ran = random.randint(0,10000)
        if ran > 100:
            rew = max(min(round((random.gauss(2,1))), 5), 1)
            self.add_realness(rew)
            return ReturnObject(True, {"name": self.nickname, "val": str(rew) + "rp"})
        else:
            ran = random.randint(0,2)
            if ran == 0:
                ab = Ability('protect', max(min(round((random.gauss(3,1))), 3), 1))
            elif ran == 1:
                ab = Ability('thornmail', max(min(round((random.gauss(3,1))), 3), 1))
            elif ran == 2:
                ab = Ability('bomb', max(min(round((random.gauss(3,1))), 3), 1))
            self.add_ability(ab)
            return ReturnObject(True, {"name": self.nickname, "val": ab.type + " " + str(ab.val)})

    def datetime_write(self, date):
        return date.strftime("%Y-%m-%d %H:%M:%S.%f")

    def datetime_read(self, date):
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")

    def ability_write(self):
        return [(i.type, i.val) for i in self.abilities]

    def ability_read(self):
        self.abilities = [Ability(i[0],i[1]) for i in self.abilities]

    def value(self, val):
        return str(self.__dict__()[val])


    def adjustRealness(self, form, reason, post_params, multiplier = 1):
        if (form.message.sender_id == self.user_id):
            return ReturnObject(False, "You can't adjust your own realness")
        elif (multiplier > 3):
            return ReturnObject(False, "You're limited to changing 3 realness at a time")
        elif (reason == 'add'):
            self.add_realness(multiplier)
            return ReturnObject(True, multiplier)
        else:
            if self.thornmail > datetime.now():
                form.ulist.find(form.message.sender_id).realness -= multiplier
                return ReturnObject(False, 'Sorry, ' + self.nickname + ' is protected.')
            elif self.protected > datetime.now():
                return ReturnObject(False, 'Sorry, ' + self.nickname + ' is protected.')
            else:
                for ability in self.abilities:
                    if (ability.type in ["protect", "thornmail"]):
                        self.use(ability, post_params)
                        return self.adjustRealness(form, reason, post_params, multiplier)
                self.subtract_realness(multiplier)
                return ReturnObject(True, multiplier)



class Ability:
    def __init__(self, typ, val):
        self.type = typ
        self.val = val


class UserList:
    def __init__(self, udict):
        try:
            self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected'], i['thornmail'], i['permission'], i['last'], i['ban']) for i in udict]
        except:
            try:
                self.ulist = [User(i['user_id'], i["name"], i['nickname'], i['realness'], i['abilities'], i['protected'], i['thornmail'], i['permission'], i['last']) for i in udict]
            except:
                self.ulist = [User(i['user_id'], i["name"], i['nickname']) for i in udict]
        self.ids = {i.user_id:i for i in self.ulist}
        self.names = {i.name:i for i in self.ulist}
        self.nicknames = {i.nickname:i for i in self.ulist}
        #self.realnesses = {i.user_id:i.realness for i in self.ulist}
        self.peopleFinders = [self.find, self.findByName, self.findByNickname]

    def realnesses(self):
        return {i.user_id:i.realness for i in self.ulist}

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

    def returnAttribute(self, form, attributes, post_params):
        out = ''
        if len(form.people) > 0:
            for user in form.people:
                out += user.nickname + ":\n"
                for att in attributes:
                    out += att + "- " + user.value(att) + "\n"
                out += "\n"
        else:
            out += form.sender.nickname + ":\n"
            for att in attributes:
                out += att + "- " + form.sender.value(att) + "\n"
        post_params['text'] = out
        send_message(post_params)

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
        time.sleep(0.05)

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

    def set_timer(self, form, post_params):
        nonsense = form.findNonsense(['timer'])
        if nonsense.success:
            post_params['text'] = ("I don't understand " + nonsense.obj + "\n" +
                                   "Ex. @rb timer @Employed Degenerate 10 or\n" +
                                   "@rb timer 10")
            send_message(post_params)
            return

        if len(form.numbers) == 1:
            if (form.numbers[0] < 5):
                post_params['text'] = "Timers can only be set for at least 5 minutes"
                send_message(post_params)
                return
            post_params['text'] = ''
            if len(form.people) > 0:
                post_params['text'] += "Timer set for " + str(form.numbers[0]) + " minutes for:"
                for person in form.people:
                    self.add(Timer(True, datetime.now() + timedelta(minutes=form.numbers[0]), person))
                    post_params['text'] += "\n" + person.name
            else:
                self.add(Timer(False, datetime.now() + timedelta(minutes=form.numbers[0]), form.sender))
                post_params['text'] = "Timer set for " + str(form.numbers[0]) + " minutes"
        else:
            post_params['text'] = ("I don't know how long you want that for.\n" +
                                   "Ex. @rb timer @Employed Degenerate 10 or\n" +
                                   "@rb timer 10")
        send_message(post_params)


class StatEvaluator:
    def __init__(self, group_id):
        self.group_id = group_id
        self.word_dict = self.readDict()
        self.person_stats = defaultdict(lambda: defaultdict(int))
        self.total_stats = defaultdict(int)
        self.common = self.readCommon()

    def readDict(self):
        try:
            with open(os.path.abspath('word_'+self.group_id+'.json'),'r') as s:
                file = s.readlines()
                word_dict = json.loads(file[0])
                s.close()
            return word_dict
        except:
            return {}

    def readCommon(self):
        with open(os.path.abspath('common.txt'),'r') as s:
            file = s.readlines()
            word_dict = [word.strip('\n').lower().translate(''.maketrans("","",string.punctuation)) for word in file]
            s.close()
        return word_dict

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

    def mostCommonWordForEachPerson(self, ulist):
        out = []
        for user in ulist.ulist:
            person_dict = self.person_stats[user.user_id]
            max_val = sorted(zip(person_dict.values(), person_dict.keys()))[::-1]
            for item in max_val:
                if item[1] in self.common: continue
                out += [(user.nickname, item)]
                break
        return out

    def mostCommonWordForPerson(self, user, top):
        out = []
        person_dict = self.person_stats[user.user_id]
        max_val = sorted(zip(person_dict.values(), person_dict.keys()))[::-1]
        for item in max_val:
            if top <= 0:
                break
            if item[1] in self.common: continue
            out += [item]
            top -= 1
        return [(user.nickname, out)]

    def mostCommonWordForAll(self, top):
        out = []
        max_val = sorted(zip(self.total_stats.values(), self.total_stats.keys()))[::-1]
        for item in max_val:
            if top <= 0:
                break
            if item[1] in self.common: continue
            out += [item]
            top -= 1
        return out


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
        self.realness_stat[str(datetime.now())] = self.ulist.realnesses()
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
            with open(os.path.abspath('word_'+self.group_id+'.json'),'r', encoding='utf8', errors='ignore') as s:
                file = s.readlines()
                self.word_dict = json.loads(file[0])
                s.close()
        except:
            self.read_dict()



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
        self.type = None
        self.user_ids = None
        self.loci = None
        self.url = None
        self.poll_id = None
        for item in self.attachments:
            self.type = item['type']
            if self.type == 'mentions':
                self.user_ids = item['user_ids']
                self.loci = item['loci']
            elif self.type == 'image':
                self.url = item['url']
            elif self.type == 'poll':
                self.poll_id = item['poll_id']
            else:
                return


    def count_likes(self):
        return len(self.liked)

class ReturnObject:
    def __init__(self, success = False, obj = None):
        self.success = success
        self.obj = obj


class Parser():
    def __init__(self, form):
        self.text = form.text
        self.message = form.message
        self.ulist = form.ulist
        self.split = []
        self.numbers = []
        self.totals = {}
        self.currentPersonToChange = None
        self.max = 3

    def whoToChange(self):
        validate = self.valid_command()
        if (not validate.success):
            return validate
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
        if self.message.type != 'mentions':
            self.text = self.message.text[3:].lower().strip()
            self.split = self.text.split(' ')[2:]
            return
        user_ids = self.message.attachments[0]['user_ids'][::-1]
        locations = self.message.attachments[0]['loci'][::-1]
        for ind, user in enumerate(user_ids):
            person = self.ulist.find(user)
            replacement = person.name
            location = locations[ind]
            self.message.text = self.message.text[0:location[0]] + replacement + self.message.text[location[0] + location[1]:]
        self.text = self.message.text[3:].lower().strip()
        self.split = self.text.split(' ')[2:]

    def formatForRecorder(self):
        if self.message.type == 'mentions':
            user_ids = self.message.attachments[0]['user_ids'][::-1]
            locations = self.message.attachments[0]['loci'][::-1]
            for ind, user in enumerate(user_ids):
                person = self.ulist.find(user)
                replacement = person.name
                location = locations[ind]
                self.message.text = self.message.text[0:location[0]] + replacement + self.message.text[location[0] + location[1]:]
        if len(self.message.text) > 3 and self.message.text[:3] == '@rb':
            self.text = self.message.text[3:].lower().strip()
        else:
            self.text = self.message.text.lower().strip()

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

class Formatter:
    def __init__(self, message, ulist):
        self.message = message
        self.text = message.text.lower().strip()
        self.sender = ulist.find(message.sender_id)
        self.ulist = ulist
        self.split = self.text.split(' ')
        self.people = []
        self.numbers = []

    def replaceMentions(self):
        if self.message.type != 'mentions':
            return
        mentions = sorted(zip( self.message.loci, self.message.user_ids))[::-1]
        mentions = self.removeDuplicates(mentions)
        for mention in mentions:
            person = self.ulist.find(mention[1])
            replacement = person.name
            location = mention[0]
            self.text = self.text[0:location[0]].strip() + ' ' + replacement + ' ' + self.text[location[0] + location[1]:].strip()
        self.split = self.text.split(' ')

    def removeDuplicates(self, mentions):
        seen = []
        for mention in mentions:
            if mention not in seen:
                seen += [mention]
        return seen

    def removeAllPeople(self):
        self.replaceMentions()
        self.removePeople()

    def removePeople(self):
        words = []
        for word in self.split:
            person = self.ulist.findPerson(word).obj
            if person != None:
                self.people += [person]
                words += [word]
        for word in words:
            self.split.remove(word)
        self.text = ' '.join(self.split)

    def removeBotCall(self):
        if self.text.startswith('@rb'):
            self.text = self.text.split('@rb')[1].lower().strip()
            self.split = self.text.split(' ')
        else:
            return

    def removeCommand(self, command):
        if self.text.startswith(command):
            self.text = self.text.split(command)[1].lower().strip()
            self.split = self.text.split(' ')
        else:
            return

    def containsNonsense(self, words):
        for word in self.split:
            if( not word.isdigit() and word not in words):
                return True
        return False

    def findNonsense(self, words):
        for word in self.split:
            if( not word.isdigit() and word not in words):
                return ReturnObject(True, word)
        return ReturnObject(False)

    def removeNonsense(self, words):
        toRemove = []
        for word in self.split:
            if( not word.isdigit() and word not in words):
                toRemove += [word]
        for word in toRemove:
            self.split.remove()
        self.text = ' '.join(self.split)

    def findNumbers(self):
        for word in self.split:
            if word.isdigit():
                self.numbers += [int(word)]

    def contains(self, words):
        con = []
        for word in self.split:
            if word in words:
                con += [word]
        if len(con) > 0:
            return ReturnObject(True, con)
        else:
            return ReturnObject(False)

class Group:
    def __init__(self, dic):
        self.creator = dic['creator']
        self.group = dic['group']

    def __dict__(self):
        return {'creator':self.creator, 'group':self.group}


class Groups:

    def __init__(self, testmode):
        self.testmode = testmode
        self.group_dict = {}
        self.readGroups()

    def readGroups(self):
        try:
            with open(os.path.abspath('groups.json'),'r') as s:
                file = s.readlines()
                read_dict = json.loads(file[0])
                for item in read_dict:
                    self.group_dict[item] = Group(read_dict[item])
                s.close()
        except Exception:
            print(traceback.format_exc())
            time.sleep(5)
            return self.readGroups()

    def writeGroups(self):
        if self.testmode:
            return
        write_dict = {}
        for item in self.group_dict:
            write_dict[item] = self.group_dict[item].__dict__()
        try:
            with open(os.path.abspath('groups.json'),'w') as s:
                s.write(json.dumps(write_dict))
                s.close()
        except Exception:
            print(traceback.format_exc())
            time.sleep(5)
            return self.writeGroups()

    def addToAll(self, person):
        self.group_dict['all'].group += [person]
        self.writeGroups()

    def addGroup(self, group_name, group):
        if group_name in self.group_dict:
            return False
        else:
            self.group_dict[group_name] = group
            return True

    def makeGroup(self, form):
        ids = []
        for user in set(form.people):
            ids += [user.user_id]
        return self.addGroup(form.split[0], Group({"creator":form.sender.user_id, "group":ids}))

    def createGroup(self, form, post_params):
        form.removeCommand('make group')
        form.removeCommand('makegroup')
        form.removeCommand('add group')
        form.removeCommand('addgroup')
        if len(form.split) > 1:
            post_params['text'] = 'Groups can only a one word name'
            send_message(post_params)
        elif len(form.split) < 1 or form.split == ['']:
            post_params['text'] = "You didn't tell me a group to make"
            send_message(post_params)
        elif len(form.people) == 0:
            post_params['text'] = "You didn't tell me any people to add"
            send_message(post_params)
        else:
            if self.makeGroup(form):
                self.writeGroups()
                post_params['text'] = 'Made new group ' + form.split[0]
                send_message(post_params)
            else:
                post_params['text'] = 'That group already exists'
                send_message(post_params)

    def addPeople(self, form, group):
        people = self.group_dict[group].group
        for person in set(form.people):
            people += [person.user_id]
        self.group_dict[group].group = people

    def addToGroup(self, form, post_params):
        form.removeCommand('add to group')
        form.removeCommand('add to')
        if len(form.split) > 1:
            post_params['text'] = 'Groups can only a one word name'
            send_message(post_params)
        elif len(form.split) < 1 or form.split == ['']:
            post_params['text'] = "You didn't tell me a group to add to"
            send_message(post_params)
        elif len(form.people) == 0:
            post_params['text'] = "You didn't tell me any people to add"
            send_message(post_params)
        elif form.split[0] not in self.group_dict:
            post_params['text'] = "That is not a group. To make a new group, use @rb make group"
            send_message(post_params)
        elif form.sender.user_id != self.group_dict[form.split[0]].creator:
            post_params['text'] = "Only the creator of the group can add to it"
            send_message(post_params)
        else:
            self.addPeople(form, form.split[0])
            self.writeGroups()
            post_params['text'] = "Added to group " + form.split[0]
            send_message(post_params)

    def findPeople(self, group, ulist):
        people = self.group_dict[group].group
        names = ''
        for person in people:
            names += ulist.find(person).nickname + ', '
        return names[:-2]

    def peopleInGroup(self, form, ulist, post_params):
        form.removeCommand('people')
        if len(form.split) > 1:
            post_params['text'] = 'Groups can only a one word name'
            send_message(post_params)
        elif len(form.split) < 1 or form.split == ['']:
            post_params['text'] = "You didn't tell me a group to print"
            send_message(post_params)
        elif form.split[0] not in self.group_dict:
            post_params['text'] = "That is not a group"
            send_message(post_params)
        else:
            people = self.findPeople(form.split[0], ulist)
            post_params['text'] = form.split[0] + " contains: " + people
            send_message(post_params)

    def findAllGroups(self):
        all_groups = ''
        for group in self.group_dict:
            all_groups += group + ', '
        return all_groups[:-2]

    def findGroups(self, post_params):
        groups = self.findAllGroups()
        post_params['text'] = 'The groups are: ' + groups
        send_message(post_params)

    def findGroup(self, key):
        if key in self.group_dict:
            return ReturnObject(True, self.group_dict[key])
        else:
            return ReturnObject(False)

    def findMentions(self, text):
        return re.findall(r'@\w+', text)

    def findIds(self, text):
        mentions = self.findMentions(text)
        ids = []
        for mention in mentions:
            group = self.findGroup(mention[1:])
            if group.success:
                ids += group.obj.group
        return ids

    def formMentions(self, form, ulist):
        text = form.text
        ids = self.findIds(text)
        if ids == []:
            return ReturnObject(False)
        loci = []
        user_ids = []
        for person in ids:
            loci += [[0,1]]
            user_ids += [person]
        return ReturnObject(True, [{'loci': loci, 'type':'mentions', 'user_ids':user_ids}])

    def sendMention(self, form, ulist, post_params):
        mentions = self.formMentions(form, ulist)
        if mentions.success:
            post_params['attachments'] = mentions.obj
            post_params['text'] = form.message.text
            send_message(post_params)
            post_params['attachments'] = []
            return True
        else:
            return False

    def removeGroup(self, key):
        del self.group_dict[key]

    def removePeopleFromGroup(self, key, id_list):
        people = self.group_dict[key].group
        for user_id in id_list:
            try:
                people.remove(user_id)
            except:
                continue
        self.group_dict[key].group = people

    def retrieveGroup(self, form):
        return form.contains(self.group_dict.keys())

    def remove(self, form, post_params):
        key = self.retrieveGroup(form)
        if not key.success:
            post_params['text'] = "You didn't give me a group"
            send_message(post_params)
            return
        key = key.obj
        if len(key) > 1:
            post_params['text'] = "Only one group at a time"
            send_message(post_params)
            return
        key = key[0]
        if form.sender.user_id != self.group_dict[key].creator:
            post_params['text'] = "Only the creator can modify the group"
            send_message(post_params)
            return
        if len(form.people) == 0:
            self.removeGroup(key)
            post_params['text'] = key + " has been removed"
            send_message(post_params)
            return
        id_list = [person.user_id for person in form.people]
        self.removePeopleFromGroup(key, id_list)
        post_params['text'] = "Removed members"
        send_message(post_params)


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

def read_auth():
    with open(os.path.abspath('bot_auth.json'),'r') as auth:
        file = auth.readlines()
        data = json.loads(file[0])
        return data
    
def general_data_load():
    with open(os.path.abspath('general_data.json'),'r') as gen:
        file = gen.readlines()
        data = json.loads(file[0])
        return data
    
def general_data_write(genral_data):
    """Writes last message id to last.json.
    :param str last_message: last message id"""
    with open(os.path.abspath('general_data.json'),'w') as gen:
        gen.write(json.dumps(genral_data))
        gen.close()
    

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

def update_everyone(request_params, group_id, ulist, groups):
    try:
        group = requests.get('https://api.groupme.com/v3/groups/' +group_id, params = request_params).json()['response']
    except:
        time.sleep(5)
        update_everyone(request_params, group_id, ulist, groups)
        return

    for member in group['members']:
        user = ulist.find(member['user_id'])
        if user.name == 'invalid':
            ulist.add(User(member['user_id'], member['nickname'], member['nickname']))
            groups.addToAll(member['user_id'])
        else:
            user.nickname = member['nickname']

def members(request_params, group_id):
    "DEPRICATED"
    group = requests.get('https://api.groupme.com/v3/groups/' + group_id, params = request_params).json()['response']
    return group['members']

def upload_image(request_params, filename=None,ImageData=None):
    """Uploads image file or image data (binary) to GroupMe Image Service.  Returns url."""
    if filename is not None:
        with open(os.path.abspath(filename), 'rb') as pic:
            ImageData = pic.read()
    url = requests.post('https://image.groupme.com/pictures', params=request_params , data=ImageData).json()['payload']['url']
    return url

def send_message(post_params):
    """Sends message to group.
    :param dict post_params: bot_id, text required"""
    requests.post("https://api.groupme.com/v3/bots/post", json = post_params)

def parse_message(request_params, group_id, ulist, post_params, timerlist, red, word_dict, groups, testmode, mess):
    if not testmode:
        update_everyone(request_params, group_id, ulist, groups)
    commands(mess, ulist, post_params, timerlist, request_params, group_id, red, groups)
    if not testmode and mess.text is not None:
        users_write(ulist)
        form = Formatter(mess, ulist)
        form.replaceMentions()
        form.removeBotCall()
        word_dict.add(mess.sender_id, form.text)
        word_dict.realness()

#reads messages and creates message_list of Message objects
def read_messages(request_params, group_id, ulist, post_params, timerlist, red, word_dict, groups, testmode):
    """Reads in messages from GroupMe API through requests.get().
    Converts messages into Message objects. Filters system and bot messages.
    Updates ulist with update method of UserList.  Calls commands().  Calls
    last_write().
    :param dict request_params: dictionary of token
    :param str group_id: group id
    :param UserList ulist: user list of User objects
    :return list: list of Message objects"""
    try:
        try:
            response_messages = requests.get('https://api.groupme.com/v3/groups/{}/messages'.format(group_id), params = request_params).json()['response']['messages']
        except:
            print('connection problem')
            time.sleep(5)
            read_messages(request_params, group_id, ulist, post_params, timerlist, red, word_dict, groups, testmode)
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
                thread.start_new_thread(parse_message, (request_params, group_id, ulist, post_params, timerlist, red, word_dict, groups, testmode, mess))
                #parse_message(request_params, group_id, ulist, post_params, timerlist, red, word_dict, groups, testmode, mess)
    except Exception:
        print(traceback.format_exc())
        post_params['text'] = "Sorry, something went wrong. Try again, it could just have been a read failure."
        send_message(post_params)
        time.sleep(5)

    if len(message_list) > 0:
        last_write(message_list[0].id)



def helper_main(post_params, page = 1):
    """Sends message of all commands.
    :param dict post_params: text, bot_id required"""
    header = "These are the following commands:\n"
    pages = [
            ("not real [@mention]\n"
              "very real [@mention]\n"
              "help [#page|command]\n"
              "timer [@mention] [time]\n"
              "@all|@everyone\n"
              "word [names] [number]\n"),

            ("shop [item] [time]\n"
             "use [ability] [time] [@mention]\n"
             "reward\n"
             "games [@mention] [time]\n"
             "[@mention] [stat]\n"
             "play [@mention] [computer|phone|both]\n"),

             ("ranking\n"
              "toot\n"
              "red pill\n"
              "blue pill\n"
              "meme\n"
              "joke\n")
            ]
    max_page = len(pages)
    page = (page - 1)%max_page
    tail = "page " + str(page + 1) + "/" + str(max_page)

    post_params['text'] = header + pages[page] + tail
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

        elif (reason[0] == "very"):
            post_params['text'] = ("The very real command is used to reward a user for their excess of realness\n" +
                      "Example: @rb very real Carter")

        elif (reason[0] == "ranking"):
            post_params['text'] = ("The ranking command shows how real everyone is\n" +
                      "Example: @rb ranking")

        elif (reason[0] == "timer"):
            post_params['text'] = ("Set a timer in minutes so people aren't late\n" +
                      "Example: @rb timer @LusciousBuck 10")

        elif (reason[0] == 'shop'):
            post_params['text'] = ("Shop for radical abilities dude\n" +
                      "Example: @rb shop protect 10")

        elif (reason[0] == 'use'):
            post_params['text'] = ("Use your radical abilities dude\n" +
                      "Example: @rb use protect 10")

        elif (reason[0] == 'toot'):
            post_params['text'] = ("Gives a random comment made by Carter on Reddit\n" +
                      "Example: @rb toot")

        elif (reason[0] == 'meme'):
            post_params['text'] = ("Gives a random meme from r/dankmemes\n" +
                      "Example: @rb meme")

        elif (reason[0] == 'joke'):
            post_params['text'] = ("Gives a random joke from r/jokes\n" +
                      "Example: @rb joke")

        elif (reason[0] == 'bluepill' or reason[0] == 'blue_pill'):
            post_params['text'] = ("Gives a random post from r/esist\n" +
                      "Example: @rb blue_pill")

        elif (reason[0] == 'redpill' or reason[0] == 'red_pill'):
            post_params['text'] = ("Gives a random post from r/the_donald\n" +
                      "Example: @rb red_pill")

        elif (reason[0] == 'games'):
            post_params['text'] = ("Sets a timer that rewards and punishes people for playing games.\n"
                       "You can leave out the @mentions to send the message to everyone.\n"
                       "You can also leave out the time and it will default to 60 minutes.\n"
                       "Example: @rb games @friendido 100")

        elif (reason[0] == 'play'):
            post_params['text'] = ("Play connect four against a bot or friend for 5rp.\n"
                       "To play against a bot, leave out the @mentions.\n"
                       "There are 2 board displays: phone and computer.\n"
                       "You can also say both to have both displays.\n"
                       "Examples: @rb play @friendido phone\n"
                       "@rb play")

        elif (reason[0] == 'reddit'):
            post_params['text'] = ("There are 5 reddit commands:\n\n"
                       "toot\n"
                       "meme\n"
                       "joke\n"
                       "red_pill\n"
                       "blue_pill\n")

        elif (reason[0] == 'word'):
            post_params['text'] = ("There are 3 uses for word:\n\n"
                       "word [#number] \n(shows top # of words for the group)\n"
                       "word [names] [#number] \n(shows top # of words for each person mentioned)\n"
                       "word \n(shows top word for each person)")

        elif (reason[0] == 'stats' or reason[0] == 'stat'):
            post_params['text'] = ("There are six stats to lookup:\n\n" +
                       "name\n" +
                       "nickname\n" +
                       "realness\n" +
                       "abilities\n" +
                       "protected")

        elif (reason[0] == 'ability' or reason[0] == 'abilities'):
            post_params['text'] = ("There are three abilities to lookup:\n\n" +
                       "protect\n" +
                       "thornmail\n" +
                       "bomb")

        elif (reason[0] == 'help'):
            post_params['text'] = ("The help command has 3 uses:\n\n" +
                      "help [command]: find info on how to call commands and what they do\n\n" +
                      "help shop [item]: find info on abilities in the shop\n\n" +
                      "help ability [ability]: find info on what abilities do")
        elif (reason[0].isdigit()):
            helper_main(post_params, int(reason[0]))
            return
        else:
            helper_main(post_params)
            return
    elif (len(reason) == 2):
        if (reason[0] == 'shop'):
            if (reason[1] == 'protect'):
                post_params['text'] = ("The protect ability is 10rp per day")
            elif (reason[1] == 'thornmail'):
                post_params['text'] = ("The thornmail ability is 15rp per day")
            elif (reason[1] == 'bomb'):
                post_params['text'] = ("The bomb ability is 10rp for 10 damage")
            else:
                post_params['text'] = ("Sorry, that's not an ability for sale"
                           "Did you want protect, thornmail, or bomb?")

        elif (reason[0] == 'ability'):
            if (reason[1] == 'protect'):
                post_params['text'] = ("The protect ability protects you from losing rp")
            elif (reason[1] == 'thornmail'):
                post_params['text'] = ("The thornmail ability protects you from losing rp and punishes the attacker")
            elif (reason[1] == 'bomb'):
                post_params['text'] = ("The bomb ability does massive damage to others")
            else:
                post_params['text'] = ("Sorry, that's not an ability.\n"
                           "Did you want protect, thornmail, or bomb?")

        elif (reason[0] == 'very' and reason[1] == 'real'):
            post_params['text'] = ("The very real command is used to reward a user for their excess of realness\n" +
                      "Example: @rb very real Carter")

        elif (reason[0] == 'not' and reason[1] == 'real'):
            post_params['text'] = ("The not real command is used to shame a user for their lack of realness\n" +
                      "Example: @rb not real Carter")

        elif (reason[0] == 'red' and reason[1] == 'pill'):
            post_params['text'] = ("Gives a random post from r/the_donald\n" +
                      "Example: @rb red pill")

        elif (reason[0] == 'blue' or reason[0] == 'pill'):
            post_params['text'] = ("Gives a random post from r/esist\n" +
                      "Example: @rb blue pill")
        else:
            helper_main(post_params)
            return
    else:
        helper_main(post_params)
        return
    send_message(post_params)


def remove_realness(change_dict, form, post_params):
    text = 'Not Real. '
    for user in change_dict.keys():
        result = user.adjustRealness(form, 'subtract', post_params, change_dict[user])
        if (not result.success):
            post_params['text'] = result.obj
            send_message(post_params)
        else:
            text += user.name.capitalize() + ' ' + str(result.obj) + '. '
    if (text != 'Not Real. '):
        return ReturnObject(True, text)
    else:
        return ReturnObject(False)

def add_realness(change_dict, form, post_params):
    text = 'Very Real. '
    for user in change_dict.keys():
        result = user.adjustRealness(form, 'add', post_params, change_dict[user])
        if (not result.success):
            post_params['text'] = result.obj
            send_message(post_params)
        else:
            text += user.name.capitalize() + ' ' + str(result.obj) + '. '
    if (text != 'Very Real. '):
        return ReturnObject(True, text)
    else:
        return ReturnObject(False)

def very_real(person, form, post_params):
    parser = Parser(form)
    result = parser.whoToChange()
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_text = add_realness(result.obj, form, post_params)
        if (post_text.success):
            post_params['text'] = post_text.obj
            send_message(post_params)
        person.last = datetime.now()


def not_real(person, form, post_params):
    
    parser = Parser(form)
    result = parser.whoToChange()
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_text = remove_realness(result.obj, form, post_params)
        if (post_text.success):
            post_params['text'] = post_text.obj
            send_message(post_params)
        person.last = datetime.now()

def change_realness(reason, form, post_params):
    person = form.ulist.find(form.message.sender_id)
    if person.ban > datetime.now():
        post_params['text'] = "Sorry, you are banned for " + str(person.ban - datetime.now()) + " hours"
        send_message(post_params)
        return
    if person.last > (datetime.now() - timedelta(minutes=30)):
        post_params['text'] = "Sorry, you can only use this once every 30 minutes. You have " + str((person.last + timedelta(minutes=30)) - datetime.now()) + " minutes left"
        send_message(post_params)
        return
    if reason == 'not':
        not_real(person, form, post_params)
    else:
        very_real(person, form, post_params)
        
def ban(form, post_params):
    if (form.sender.permission != 'admin'):
        post_params['text'] = 'Sorry, only admins can use that ability'
        send_message(post_params)
        return
    if (len(form.people) < 1):
        post_params['text'] = 'Please give a person'
        send_message(post_params)
        return
    if (len(form.people) > 1):
        post_params['text'] = 'Sorry, only one person at a time'
        send_message(post_params)
        return
    if (len(form.numbers) < 1):
        post_params['text'] = 'Please give a time duration'
        send_message(post_params)
        return
    if (len(form.numbers) > 1):
        post_params['text'] = 'Please give only one number'
        send_message(post_params)
        return
    form.removeCommand('ban')
    nonsense = form.findNonsense([])
    if nonsense.success:
        post_params['text'] = "I don't understand " + nonsense.obj
        send_message(post_params)
        return
    form.people[0].ban_user(form.numbers[0])
    post_params['text'] = form.people[0].nickname + ' is banned for ' + str(form.numbers[0]) + ' hours'
    send_message(post_params)
        
        
def clear(form, post_params):
    result = form.ulist.clearRealness(form.sender.user_id)
    if (not result.success):
        post_params['text'] = result.obj
        send_message(post_params)
    else:
        post_params['text'] = 'Cleared'
        send_message(post_params)

def shop(form, post_params):
    items = ['protect', 'bomb', 'thornmail']
    nonsense = form.findNonsense(items + ['shop'])
    if nonsense.success:
        post_params['text'] = ("I don't understand " + nonsense.obj + "\n" +
                               "Ex. @rb shop protect 10")
        send_message(post_params)

    form.removeCommand('shop')
    product = form.contains(items)
    if (product.success and len(product.obj) == 1):
        person = form.sender
        numbers = form.numbers
        if (len(numbers) == 1):
            if product.obj[0] in ['protect', 'bomb']:
                if person.realness >= 10 * int(numbers[0]):
                    person.add_ability(Ability(product.obj[0], int(numbers[0])))
                    person.realness -= 10 * int(numbers[0])

                    post_params['text'] = "Ok, 1 " +product.obj[0]+ " ability."
                    send_message(post_params)
                else:
                    post_params['text'] = 'Fuck off peasant.'
                    send_message(post_params)
            elif product.obj[0] in ['thornmail']:
                if person.realness >= 15 * int(numbers[0]):
                    person.add_ability(Ability(product.obj[0], int(numbers[0])))
                    person.realness -= 15 * int(numbers[0])

                    post_params['text'] = "Ok, 1 " +product.obj[0]+ " ability. That'll last yah " + str(numbers[0]) + ' days.'
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
        post_params['text'] = "I don't know what ability you want"
        send_message(post_params)

def play(ulist, user_id, user_name, user2_id = '', user2_name = '', print_type = 'phone'):
    play4.play_connect4(user_id, user_name, user2_id, user2_name, print_type)

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

def games(form, post_params, timerlist):
    nonsense = form.findNonsense(['games'])
    if nonsense.success:
        post_params['text'] = ("I don't understand " + nonsense.obj + "\n" +
                               "Ex. @rb games @Employed Degenerate 10 or\n" +
                               "@rb games")
        send_message(post_params)

    people = []
    if len(form.people) > 0:
        people = form.people
    else:
        people = form.ulist.ulist
    numbers = form.numbers
    if len(numbers) == 1:
        for user in people:
            if (user.user_id == form.sender.user_id): continue
            timerlist.add(Timer(True, datetime.now() + timedelta(minutes= numbers[0]), user, True))
        post_params['text'] = "Games??? T minus "+str(numbers[0])+" minutes"

    elif len(numbers) == 0:
        for user in people:
            if (user.user_id == form.sender.user_id): continue
            timerlist.add(Timer(True, datetime.now() + timedelta(minutes= 60), user, True))
        post_params['text'] = "Games??? T minus 60 minutes"

    else:
        post_params['text'] = ("I don't know how long you want that for.\n" +
                               "Ex. @rb games @Employed Degenerate 10 or\n" +
                               "@rb games")
        send_message(post_params)
        return
    post_params['attachments'] = [{'loci': [[0,5] for person in people], 'type':'mentions', 'user_ids':[person.user_id for person in people]}]
    send_message(post_params)
    post_params['attachments'] = []

def games_reply(user_id, text, post_params, timerlist, answer):
    if answer == "yes":
        timerlist.games_answer(user_id, True, post_params)
    else:
        timerlist.games_answer(user_id, False, post_params)

def evaluate(post_params, form, group_id):
    if len(form.numbers) > 1:
        post_params['text'] = "Too many numbers, just 1 please."
        send_message(post_params)
        return
    nonsense = form.findNonsense(['word', 'words'])
    if nonsense.success:
        post_params['text'] = ("I don't understand " + nonsense.obj + "\n" +
                               "Ex. @rb word @Employed Degenerate 10 or\n" +
                               "@rb word")
        send_message(post_params)
    if len(form.people) == 0 and len(form.numbers) == 0:
        evaluator = StatEvaluator(group_id)
        evaluator.evaluate(form.ulist)
        word_list = evaluator.mostCommonWordForEachPerson(form.ulist)
        post_params['text'] = ''
        for word in word_list:
            post_params['text'] += word[0] + ": " + word[1][1] + "\n"
        send_message(post_params)
    elif len(form.numbers) == 1:
        if len(form.people) > 0:
            evaluator = StatEvaluator(group_id)
            evaluator.evaluate(form.ulist)
            word_list = []
            for user in form.people:
                word_list += evaluator.mostCommonWordForPerson(user, form.numbers[0])
            post_params['text'] = ''
            for word in word_list:
                post_params['text'] += word[0] + ":\n"
                for tup in word[1]:
                    post_params['text'] += tup[1] + '  ' + str(tup[0]) + "\n"
                post_params['text'] += "\n"
            send_message(post_params)
        else:
            evaluator = StatEvaluator(group_id)
            evaluator.evaluate(form.ulist)
            word_list = evaluator.mostCommonWordForAll(int(form.numbers[0]))
            post_params['text'] = ''
            for word in word_list:
                post_params['text'] += word[1] + "  " + str(word[0])  +  "\n"
            send_message(post_params)
    else:
        evaluator = StatEvaluator(group_id)
        evaluator.evaluate(form.ulist)
        word_list = []
        for user in form.people:
            word_list += evaluator.mostCommonWordForPerson(user, 10)
        post_params['text'] = ''
        for word in word_list:
            post_params['text'] += word[0] + ":\n"
            for tup in word[1]:
                post_params['text'] += tup[1] + '  ' + str(tup[0]) + "\n"
            post_params['text'] += "\n"
        send_message(post_params)

def create_graph(userlist, request_params, post_params):
    df = pd.read_json(os.path.abspath('realness_stat.json'), orient='records').transpose().groupby(pd.Grouper(freq='d')).last()
    data=[]
    for column in df.columns:
        obj = go.Scatter(x=df.index,
                    y=df[column],
                    mode='lines',
                    name=userlist.find(str(column)).nickname)
        data.append(obj)
    layout = go.Layout(title='Realness',
                        xaxis=dict(title='Date',
                                    gridcolor='rgb(255,255,255)',
                                    tickmode="auto",
                                    nticks=20,
                                    ticks="inside",
                                    range=[str(datetime.date(df.index[0])),
                                            str(datetime.date(df.index[-1]+pd.DateOffset(1)))]),
                        yaxis=dict(title='Realness Level',
                                    gridcolor='rgb(255,255,255)',
                                    showgrid=True,
                                    showticklabels=True,
                                    zeroline=True,
                                    rangemode='tozero',
                                    tickmode="auto",
                                    ticks="inside",
                                    tickcolor='rgb(0,0,0)'),
                        showlegend=True,

                        legend=dict(orientation='h',
                                y=1.15,
                                x=0,),
                        plot_bgcolor='rgb(229,229,229)',
                        paper_bgcolor='rgb(255,255,255)')

    fig = go.Figure(data=data,layout=layout)
    ImageData = plotly.plotly.image.get(fig,'png')
    imgurl = upload_image(request_params, ImageData=ImageData)
    post_params['text'] = 'GRAPH REEEEEEEEEEEEEE'
    post_params['attachments'] = [{"type":"image","url":imgurl}]
    send_message(post_params)
    post_params['attachments']=[]

def reee(post_params):
    """Returns angry frog gif"""
    post_params['text'] = 'REEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE'
    post_params['attachments']=[{"type":"image","url":"https://i.groupme.com/828x828.gif.0587229f90fa489187bdc94f3d74d231.large"}]
    send_message(post_params)
    post_params['attachments']=[]

def weed(post_params):
    """Sends MAD MUSK with WEED"""
    post_params['text']=[]
    post_params['attachments']=[{"type":"image","url":"https://i.groupme.com/480x270.gif.37dd89552d064e3c83c7e4213eb9229a"}]
    send_message(post_params)
    post_params['attachments']=[]

def play_game(form, post_params):
    nonsense = form.findNonsense(['play', 'phone', 'computer', 'both'])
    if nonsense.success:
        post_params['text'] = ("I don't understand " + nonsense.obj + "\n" +
                               "Ex. @rb play @Employed Degenerate or\n" +
                               "@rb play")
        send_message(post_params)

    player2 = ''
    player2_name = ''
    player1 = form.sender.user_id
    player1_name = form.sender.nickname
    if len(form.people) > 1:
        post_params['text'] = "You can only play 1 person at a time"
        send_message(post_params)
        return
    if len(form.people) == 1:
        player2 = form.people[0].user_id
        player2_name = form.people[0].nickname
    mode = form.contains(['phone', 'computer', 'both'])
    if mode.success:
        if len(mode.obj) > 1:
            post_params['text'] = "I don't know which mode you want, just use one."
            send_message(post_params)
            return
        mode = mode.obj[0]
    else:
        mode = 'phone'

    play(form.ulist, player1, player1_name, player2, player2_name, mode)
    
def daily_reward(ulist, post_params):
    text = ''
    gen = general_data_load()
    reward = datetime.strptime(gen['reward'], "%Y-%m-%d %H:%M:%S.%f")
    if (reward.date() >= datetime.now().date()):
        timeleft = str(datetime.combine((datetime.now() + timedelta(days=1)).date(),datetime.min.time()) - datetime.now()).split('.')[0].split(':')
        text = 'Time until next reward: ' + timeleft[0] + 'h ' + timeleft[1] + 'm ' + timeleft[2] + 's\n'
    else:
        for person in ulist.ulist:
            reward = person.daily_reward()
            text += reward.obj['name'] + ": " + reward.obj['val'] + "\n"
        gen['reward'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        general_data_write(gen)
        
    post_params['text'] = text
    send_message(post_params)
    

#checks for last message and runs commands
def commands(message, ulist, post_params, timerlist, request_params, group_id, red, groups):
    if message.text == None:
        return
    form = Formatter(message, ulist)
    text = form.text
    if 'reee' in text:
        reee(post_params)
    if any(x in text for x in ['weed','dwl','W E E D']):
        weed(post_params)
    if 'here' in text:
        timerlist.cancel_timer(message.user_id, post_params)
    elif any(word in form.split for word in ['yes','yah','yeah', 'yea', 'ya']):
        games_reply(message.user_id, text, post_params, timerlist, 'yes')
    elif any(word in form.split for word in ['no','nah','nope']):
        games_reply(message.user_id, text, post_params, timerlist, 'no')
    elif groups.sendMention(form, ulist, post_params):
        return
    elif (text == '@rb'):
        helper_main(post_params)
    elif (text.startswith('@rb ')):

            form.replaceMentions()
            form.removeBotCall()

            text = form.text

            #do not completely remove people references in text for these
            #Position of the references are important
            if text.startswith('very real'):
                change_realness('very', form, post_params)
                return

            elif text.startswith('not real'):
                change_realness('not', form, post_params)
                return

            #remove mentions first, allows for less f-ups
            form.removePeople()
            form.findNumbers()
            text = form.text
            if text in ['ranking', 'rankings', 'r']:
                ulist.ranking(post_params)

            elif text.startswith('timer'):
                timerlist.set_timer(form, post_params)

            elif (text.startswith("help")):
                helper_specific(post_params, text)

            elif (text.startswith('reward') and len(form.people) == 0):
                daily_reward(ulist, post_params)

            elif (text.startswith('here')):
                timerlist.cancel_timer(message.user_id, post_params)

            elif (text.startswith('shop')):
                shop(form, post_params)

            elif (text == 'joke'):
                joke(post_params, red)

            elif (text == 'toot'):
                toot(post_params, red)

            elif (text == 'meme'):
                meme(post_params, red)

            elif ('idea' in text):
                idea(post_params, text)

            elif (text in ['red pill', 'redpill', 'red_pill']):
                red_pill(post_params, red)

            elif (text in ['blue pill', 'bluepill', 'blue_pill']):
                blue_pill(post_params, red)

            elif (text.startswith('games')):
                games(form, post_params, timerlist)

            elif (text.startswith('word') or text.startswith('words')):
                evaluate(post_params, form, group_id)

            elif (text.startswith('use')):
                form.sender.use_ability(form, post_params)

            elif (text == 'clear'):
                clear(form, post_params)
                
            elif (text.startswith('ban')):
                ban(form, post_params)

            elif (text.startswith('play')):
                play_game(form, post_params)

            elif (text == 'graph'):
                create_graph(ulist, request_params, post_params)

            elif (text.startswith('add group') or text.startswith('addgroup') or text.startswith('make group') or text.startswith('makegroup')):
                groups.createGroup(form, post_params)

            elif (text.startswith('add to group') or text.startswith('add to')):
                groups.addToGroup(form, post_params)

            elif (text.startswith('people')):
                groups.peopleInGroup(form, ulist, post_params)

            elif (text == 'groups'):
                groups.findGroups(post_params)

            elif (text.startswith('remove') or text.startswith('delete')):
                groups.remove(form, post_params)

            else:
                attributes = form.contains(form.sender.properties)
                if attributes.success:
                    form.ulist.returnAttribute(form, attributes.obj, post_params)
                else:
                    helper_main(post_params)


def run(request_params, post_params, timerlist, group_id, userlist, red, word_dict, groups, testmode):
    while (1 == True):
        read_messages(request_params, group_id, userlist, post_params, timerlist, red, word_dict, groups, testmode)

        timerlist.check(post_params)

        time.sleep(1)


def startup(testmode = False, shouldrun = True):
    user_dict = users_load()
    userlist = UserList(user_dict)
    red = Reddit()
    auth = auth_load()
    bot_auth = read_auth()
    bot = auth['equipo']
    if testmode:
        bot = auth['test']
    group_id = bot['group_id']
    word_dict = Recorder(group_id, userlist)
    groups = Groups(testmode)
    request_params = {'token':auth['token']}
    post_params = {'text':'','bot_id':bot['bot_id'],'attachments':[]}
    timerlist = TimerList()
    plotly.tools.set_credentials_file(username=bot_auth['plotlyuser'],api_key=bot_auth['plotlykey'])
    plotly.tools.set_config_file(world_readable=False,
                                 sharing='private')
    text = 'The current realness levels are: \n'
    for user in sorted(userlist.ulist, key=lambda x: x.realness):
        text += user.nickname +': ' + str(user.realness) + '\n'
    print(text)
    if shouldrun:
        run(request_params, post_params, timerlist, group_id, userlist, red, word_dict, groups, testmode)


if __name__ == "__main__":
    startup()
