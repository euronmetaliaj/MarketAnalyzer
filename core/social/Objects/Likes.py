import core.social.Mongo
import core.social.Objects.User
import json


class Likes:
    def __init__(self, id=None, user_name=None):
        self._id = id
        self.user_name = user_name

    def __repr__(self):
        return json.dumps(self.json())

    def __str__(self):
        return json.dumps(self.json())

    def json(self):
        json_res = {}
        for key, value in self.__dict__.items():
            if value:
                json_res[key] = value
        return json_res