from ..Mongo import Mongo

# import social.Objects.User
import json


class Comment:
    def __init__(self, **kwargs):
        values = ['_id', 'id', 'created_time', 'user', 'message', 'like_count', 'user_likes']
        for key, value in kwargs.items():
            if key in values:
                setattr(self, key, value)

    def json(self):
        json_res = {}
        for key, value in self.__dict__.items():
            if value:
                json_res[key] = value
        return json_res

    def __str__(self):
        return json.dumps(self.json())

    def __repr__(self):
        return json.dumps(self.json())
