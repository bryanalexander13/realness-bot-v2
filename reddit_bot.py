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

    def joke(self):
        hot = self.reddit.subreddit('jokes').top(limit = 1000)
        ran = random.randint(0,999)
        
        for i, post in enumerate(hot):
            if i == ran:
                submission = self.reddit.submission(post)
                return submission.title + '\n\n' + submission.selftext
    
    def tootz(self):
        toot = self.reddit.redditor('tootznslootz')
        comments = toot.comments.new(limit = None)
        ran = random.randint(0, 999)
        
        for i, comment in enumerate(comments):
            if i == ran:
                return (comment.body + '\n\n-TootznSlootz')
            
    
    
    
    