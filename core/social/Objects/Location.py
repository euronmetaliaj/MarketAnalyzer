import json
from ..Mongo import Mongo


class Location:
    def __init__(self, _id=None, latitude=None, longitude=None, city=None, country=None):
        self._id = _id
        self._latitude = latitude
        self._longitude = longitude
        self._country = country
        self._city = city

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def country(self):
        return self._country

    @property
    def city(self):
        return self._city

    @staticmethod
    def get_location_by_id(location_id):
        location = Mongo.getLocationsCollection().find_one({'_id': location_id})
        if location:
            return Location.load_from_json(location)
        else:
            return None

    @staticmethod
    def get_location_by_city(city):
        location = Mongo.getLocationsCollection().find_one({'city': city})
        if location:
            return Location.load_from_json(location)
        else:
            return None

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

    @staticmethod
    def get_all_locations():
        results = Mongo.getLocationsCollection().find({})
        locations = []
        for location in results:
            locations.append(location['city'] + ", " + location['country'])
        return locations

    @classmethod
    def load_from_json(cls, values):
        return cls(**values)

    def save(self):
        return Mongo.getLocationsCollection().insert(self.json())