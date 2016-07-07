import core.social.Objects.User
from ..Mongo import Mongo
import facebook
# from .User import User
from .Comment import Comment
from .Likes import Likes
from ..configurations import Config
import re

import json
import ast


class Post:
    def __init__(self, **kwargs):
        post_fields = ["created_time", "_id", "id", "updated_time", "likes", "message", "status_type", "comments"]

        for key, value in kwargs.iteritems():
            if key in post_fields:
                setattr(self, key, value)

    def __repr__(self):
        return str(self.__dict__)

    @property
    def id(self):
        return self._id

    @property
    def likes(self):
        return self.likes

    @likes.setter
    def likes(self, value):
        self.likes = value

    def get_all_likes(self):
        likes = []
        if type(self.likes) is dict:
            for x in self.likes['data']:
                likes.append(Likes(id=x['id'], user_name=x['name']))
        else :
            for x in ast.literal_eval(self.likes)['data']:
                likes.append(Likes(id=x['id'], user_name=x['name']))
        return likes

    def get_comments(self):
        comments = []
        if 'comments' in self.__dict__:
            for x in ast.literal_eval(self.comments)['data']:
                comments.append(Comment(id= x['id'], user=x['from'], like_count=x['like_count'], created_time=x['created_time'],
                                        message=x['message'], user_likes=x['user_likes']))
        return comments

    @staticmethod
    def demo(**kwargs):
        for key, value in kwargs.iteritems():
            print (str(key) + "---------->" + str(value))

    @staticmethod
    def load_from_db(id):
        post = Mongo.getPostCollection().find_one({'_id': id})
        # print ast.literal_eval(str(post))
        return Post(**post)

    @staticmethod
    def load_from_facebook(id):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')
        post = graph.get_object(id)
        # print post
        return Post(**post)

    def json(self):
        json_res = {}
        for key, value in self.__dict__.items():
            if value:
                try:
                    json_res[key] = str(value)
                except :
                    json_res[key] = str(value.encode('ascii', 'ignore'))

        if "id" in json_res.keys():
            id = json_res.pop("id")
            json_res['_id'] = id
        return json_res

    def load_user(self):
        return User.load_user(self.user)

    def save(self):
        json_res = self.json()
        Mongo.getPostCollection().insert(json_res)

    @classmethod
    def load_from_json(cls, values):
        return cls(**values)

    @staticmethod
    def load_post(id):
        record = Mongo.getPostCollection().find_one({'_id': id})
        print (record)
        if not record:
            return None
        return Post.load_from_json(record)
