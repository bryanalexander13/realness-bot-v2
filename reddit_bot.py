# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 17:58:45 2018

@author: Alexander
"""
import praw
import json
import os
import random

class Reddit:
    def __init__(self):
        app_id, app_secret = self.read_auth()

        self.reddit = praw.Reddit(client_id= app_id,
                             client_secret= app_secret,
                             user_agent='Gets Data')

    def read_auth(self):
        with open(os.path.abspath('bot_auth.json'),'r') as auth:
            file = auth.readlines()
            data = json.loads(file[0])
            auth.close()
            return data["app_id"], data["app_secret"]

    def read_comments(self):
        with open(os.path.abspath('val.json'),'r') as f:
            file = f.readlines()
            comments = json.loads(file[0])
            f.close()
            return comments

    def joke(self):
        top = self.reddit.subreddit('jokes').top('all', limit = 1000)
        ran = random.randint(0,999)
        
        for i, post in enumerate(top):
            if i == ran:
                return post.title + '\n\n' + post.selftext
    
    def meme(self):
        top = self.reddit.subreddit('dankmemes').top('all', limit = 1000)
        ran = random.randint(0,999)
        for i, post in enumerate(top):
            if i == ran:
                return post.title + '||' + post.url
    
    def tootz(self):
        try:
            toot = self.reddit.redditor('tootznslootz')
            comments = toot.comments.new(limit = None)
        except:
            comments = self.read_comments()["comments"]
        ran = random.randint(0, 999)
        
        for i, comment in enumerate(comments):
            if i == ran:
                return (comment.body + '\n\n-TootznSlootz')    
    
        print('uh, oh', ran)
    