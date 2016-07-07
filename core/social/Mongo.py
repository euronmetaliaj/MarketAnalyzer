import pymongo
from core.social.configurations import Config
from pymongo import MongoClient

client = MongoClient(Config.database_host, Config.mongo_port)
db = client[Config.database]

class Mongo:

    @staticmethod
    def getPostCollection():
        return db[Config.post_collection]


    @staticmethod
    def getPageIndex():
        # client = MongoClient(Config.database_host, Config.mongo_port)
        # db = client[Config.database]
        return db[Config.page_indexation]

    @staticmethod
    def getUserCollection():
        # client = MongoClient(Config.database_host, Config.mongo_port)
        # db = client[Config.database]
        return db[Config.user_collection]

    @staticmethod
    def getPagesCollection():
        # client = MongoClient(Config.database_host, Config.mongo_port)
        # db = client[Config.database]
        return db[Config.page_collection]

    @staticmethod
    def getPageEvalCollection():
        # client = MongoClient(Config.database_host, Config.mongo_port)
        # db = client[Config.database]
        return db[Config.page_eval_collection]

    @staticmethod
    def getLocationsCollection():
        # client = MongoClient(Config.database_host, Config.mongo_port)
        # db = client[Config.database]
        return db[Config.location_collection]