# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from core.social.Mongo import Mongo
import facebook
from core.social.Objects.Mini import Post
from core.social.Objects.Comment import Comment
from core.social.Objects.Likes import Likes
from core.social.Objects.CategoryList import CategoryList
from core.social.Objects.Location import Location
from core.social.configurations import Config
import re

import six

# import core.social.Objects.rake

import json
import ast
from collections import defaultdict

class Page:
    def __init__(self, **kwargs):
        post_fields = ["about", "founded", "_id", "id", "category", "category_list", "checkins", "likes", "link",
                       "location", "name", "products", "talking_about_count", "were_here_count", "description"]

        for key, value in kwargs.iteritems():
            if key in post_fields:
                setattr(self, key, value)

    def __repr__(self):
        return str(self.__dict__)

    @property
    def id(self):
        return self._id

    def get_categories(self):
        json_r = {}
        if "category" in self.__dict__:
            if type(self.category) is unicode:
                json_r.update({"Main_Category": self.category})
                # json_r.update({"Main_Category:":CategoryList(**(self.category))})
        if "category_list" in self.__dict__:
            if self.category_list :
                json_r.update({"Sub_Categories": []})
                for x in self.category_list:
                    json_r["Sub_Categories"].append(x['name'])
        return json_r

    def get_location(self):
        if "location" in self.__dict__:
            return Location(**ast.literal_eval(self.location))

    @staticmethod
    def demo(**kwargs):
        for key, value in kwargs.iteritems():
            print(str(key) + "---------->" + str(value))

    @staticmethod
    def load_from_db(id):
        page = Mongo.Mongo.getPagesCollection().find_one({'_id': id})
        # print ast.literal_eval(str(page))
        return Page(**page)

    @staticmethod
    def load_from_facebook(id):
        graph = facebook.GraphAPI(
            access_token=config.Config.api_key,
            version='2.2')
        page = graph.get_object(id)
        # print page
        return Page(**page)

    def json(self):
        json_res = {}
        for key, value in self.__dict__.items():
            if value:
                try:
                    json_res[key] = str(value)
                except:
                    json_res[key] = str(value.encode('ascii', 'ignore'))

        if "id" in json_res.keys():
            id = json_res.pop("id")
            json_res['_id'] = id
        return json_res

    def save(self):
        json_res = self.json()
        print(Mongo.getPagesCollection().insert(json_res))

    @classmethod
    def load_from_json(cls, values):
        return cls(**values)

    def index_page_logic(self):
        rake_object = rake.Rake(config.Config.stoppath, max_words_length=2)
        text = ""
        if "description" in self.__dict__.keys():
            text += self.description
        if "about" in self.__dict__.keys():
            text += self.about
        print(text)
        one = text.encode('utf-8').replace("ë", 'e')
        one = one.replace("$", 'dollar')
        keywords = rake_object.run(one)
        print(keywords)
        json_repr = {"_id":self.id,"name":self.name}
        json_repr.update(self.get_categories())
        json_repr.update({"keywords":{}})
        for index, x in enumerate(keywords):
            json_repr['keywords'].update({x[0]: x[1]})
        if Mongo.getPageIndex().insert(json_repr):
            return True
        else:
            return False

    @staticmethod
    def get_categories_and_subcategories():
        pages = Mongo.getPageIndex().find({})
        subcategories_points = defaultdict(int)

        for page in pages:
            if 'Sub_Categories' in page.keys():
                for subcategory in page['Sub_Categories']:
                    subcategories_points[page['Main_Category'] + " - " + subcategory] += 1

        subcategories = {}
        counter = 0

        for subcategory, _ in sorted(subcategories_points.items(), key=lambda x: x[1], reverse=True):
            if counter < 5:
                subcategories[subcategory] = True
            else:
                subcategories[subcategory] = False
            counter += 1

        return subcategories
