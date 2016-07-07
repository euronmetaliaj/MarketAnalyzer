import json


class CategoryList:
    def __init__(self, id=None, name=None):
        self._id = id
        self.name = name

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
