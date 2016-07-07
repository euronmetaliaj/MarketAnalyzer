
import json

class Education:

    def __init__(self, **kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)


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