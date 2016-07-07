import json
import threading
from core.social.Mongo import Mongo
import pymongo
import User
from collections import defaultdict
import time

class PageEval:
    def __init__(self, _id=None, points={}):
        self._id = _id
        self._points = points

    def __repr__(self):
        return json.dumps(self.json())

    def __str__(self):
        return json.dumps(self.json())

    @property
    def id(self):
        return str(self._id)

    @property
    def points(self):
        return self._points

    @property
    def sorted_points(self):
        return list(sorted(self._points.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def add_points(user_id, page_id, points):
        Mongo.getPageEvalCollection().update_one({'page_id': page_id},
                                                 {'$set': {'points.' + user_id: points}}, upsert=True)
        return True

    @staticmethod
    def get_points(user_id, page_id):
        eval = Mongo.getPageEvalCollection().find_one({"page_id": page_id})
        if eval:
            return eval['points'][user_id]
        else:
            return None

    @staticmethod
    def get_page_evaluations(page_id):
        eval = Mongo.getPageEvalCollection().find_one({"_id": page_id})
        if eval:
            return PageEval.load_from_json(eval)
        else:
            return None

    @staticmethod
    def get_user_evaluations(user_id):
        evals = Mongo.getPageEvalCollection().find({'points.' + user_id: {'$exists': 'true'}})
        evaluations = {}
        for eval in evals:
            evaluations[eval['page_id']] = eval['points'][user_id]
        return evaluations

    @staticmethod
    def get_filtered_evaluations(category=None, subcategory=None, keywords=None, location=None):
        # If category, subcategory and keywords are given
        if keywords is not None:
            keywords_filter = []
            for keyword in keywords:
                keywords_filter.append({"keywords." + keyword: {'$exists': 'true'}})
            pages = Mongo.getPageIndex().find(
                {'$and': [{'Main_Category': category}, {'Sub_Categories': subcategory}, {'$or': keywords_filter}]}
            )

        # If category and subcategory is given
        elif subcategory is not None:
            pages = Mongo.getPageIndex().find(
                {'$and': [{'Main_Category': category}, {'Sub_Categories': subcategory}]}
            )
        # If only the category is given
        elif category is not None:
            pages = Mongo.getPageIndex().find({'Main_Category': category})

        else:
            pages = Mongo.getPageIndex().find({})

        # for page in pages:
        #     print page['name']

        # If there are no pages matching the results
        if pages.count() == 0:
            return None

        print "Pages count: " + str(pages.count())

        users_points = defaultdict(int)
        # Get all users and calculate total points
        for page in pages:
            page_evaluations = PageEval.get_page_evaluations(page['_id'])

            # If the page evaluation exists
            if page_evaluations is not None:
                for user_id, points in page_evaluations.points.iteritems():
                    users_points[user_id] += points

        print (len(users_points))

        users = []

        start_time = time.time()

        # Filter by location
        if location is not None:
            for user_id, points in users_points.iteritems():
                user = User.User.load_from_db(user_id)

                # If the user doesn't exist in the database, skip
                if user is None:
                    continue

                # If the location matches, add the user to the list
                if user.location['name'] == location:  # Get only the name of the city out of the location
                    users.append((user, points))

        if location is None:
            for user_id, points in users_points.iteritems():
                user = User.User.load_from_db(user_id)

                # If the user doesn't exist in the database, skip
                if user is None:
                    continue

                users.append((user, points))

        print('Time: ' + str(time.time() - start_time))

        return users

    def json(self):
        json_res = {'_id': self.id, 'points': self.points}
        return json_res

    @classmethod
    def load_from_json(cls, values):
        return cls(**values)

    def save(self):
        try:
            json_res = self.json()
            Mongo.getPageEvalCollection().insert(json_res)
            return True

        except pymongo.errors.OperationFailure as e:
            print (e.code)
            print (e.details)
            return False

