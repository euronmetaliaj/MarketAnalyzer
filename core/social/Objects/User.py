from core.social.Mongo import Mongo
import ast
import facebook
import threading
from core.social.Objects.Education import Education
from core.social.Objects.Comment import Comment
from core.social.Objects.Mini import Post
from core.social.Objects.Page import Page
from core.social.Objects.Location import Location
from .PageEval import PageEval
from ..configurations import Config
from collections import defaultdict
from time import sleep
from .Page import Page


class User(object):
    def __init__(self, **kwargs):
        post_fields = ['id', 'bio', 'birthday', 'birthday', 'email', 'favorite_teams', 'first_name',
                       'gender', 'hometown', 'inspirational_people', 'languages', 'last_name', 'name', 'political',
                       'relationship_status', 'religion', 'timezone', 'verified', 'website', 'work', 'education',
                       'location', 'posts']
        for key, value in kwargs.iteritems():
            if key in post_fields:
                setattr(self, key, value)

    # @property
    # def location(self):
    #     return self.location
    #
    # @location.setter
    # def location(self, value):
    #     self.location = value

    @staticmethod
    def load_from_facebook(id, location=None):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')
        user = graph.get_object(id)

        us = User(**user)
        for x in us.load_posts():
            x.save()

        # If user provides location via facebook
        if 'location' in us.__dict__:
            # Check if the location is in database
            result = Location.get_location_by_id(us.location['id'])
            # If the location is not in database, add it. Else skip
            if result is None:
                # Get location from facebook
                location = graph.get_object(us.location['id'])['location']
                # Add it to database
                Location(_id=us.location['id'], city=location['city'], country=location['country'],
                         latitude=location['latitude'], longitude=location['longitude']).save()

        else:
            # If user provides the location via browser
            if location is not None:
                us.location = {'name': location['city'] + ', ' + location['country']}
                # Check if the location is in database
                result = Location.get_location_by_city(location['city'])
                # If it is not in database, save it. Else skip
                if result is None:
                    Location(city=location['city'], country=location['country'],
                             latitude=location['latitude'], longitude=location['longitude']).save()

        return us

    @staticmethod
    def load_from_db(id):
        user = Mongo.getUserCollection().find_one({"_id": id})
        if user:
            return User(**user)
        else:
            return None

    def load_posts_db(self):
        ps = []
        posts = Mongo.getPostCollection().find(ids = self.posts)
        for x in posts:
            ps.append(Post(**x))
        return ps

    def load_posts(self):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')
        comm = []
        comments = graph.get_connections(id=self.id, connection_name='posts')
        for x in comments['data']:
            comm.append(Post(**x))
        return comm

    def load_posts_id(self):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')
        comm = []
        comments = graph.get_connections(id='me', connection_name='posts')

        for x in comments['data']:
            comm.append(x['id'])
        return comm

    # Redundant
    def evaluate_pages(self):
        graph = facebook.GraphAPI(access_token=Config.api_key, version='2.2')

        # Get pages
        pages = graph.get_connections(id=self.id, connection_name='likes', limit=1000)
        for page in pages['data']:
            PageThread(page_id=page['id'], user_id=self.id).start()

        # If there are more pages, repeat procedure
        while 'paging' in pages:
            pages = graph.get_connections(id=self.id, connection_name='likes',
                                          after=pages['paging']['cursors']['after'], limit=1000)
            for page in pages['data']:
                PageThread(page_id=page['id'], user_id=self.id).start()

    def evaluate_pages_extreme(self):
        graph = facebook.GraphAPI(access_token=Config.api_key, version='2.2')

        # Get pages
        while True:
            try:
                pages = graph.get_connections(id=self.id, connection_name='likes', limit=100)
                break

            except facebook.GraphAPIError:
                sleep(900)  # Sleep for 15 minutes
                continue  # Retry

            except:
                continue

        for page in pages['data']:
            PageThreadExtreme(page_id=page['id']).start()

        # If there are more pages, repeat procedure
        while 'paging' in pages:
            # Keep looping until request is successful
            while True:
                try:
                    pages = graph.get_connections(id=self.id, connection_name='likes',
                                                  after=pages['paging']['cursors']['after'], limit=100)
                    break

                except facebook.GraphAPIError:
                    sleep(1200)     # Sleep for 15 minutes
                    continue        # Retry

                except:
                    continue

            for page in pages['data']:
                PageThreadExtreme(page_id=page['id']).start()

    def get_education(self):
        edu = []
        for x in self.education:
            edu.append(Education.Education(**x))
        return edu

    def get_evaluations(self):
        return PageEval.get_user_evaluations(self.id)

    def json(self):
        json_res = {}
        for key, value in self.__dict__.items():
            if value:
                json_res[key] = value
                if key == 'id':
                    json_res['_id'] = value
        return json_res

    def save(self):
        return Mongo.getUserCollection().insert(self.json())

    @staticmethod
    def evaluate_page(page_id):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')

        print ("Now in page " + page_id)
        points_per_user = defaultdict(int)
        post_skipped = 0  # Number of posts skipped
        threshold = 10000  # Max number of likes allowed

        # Get last 30 posts of the page
        while True:
            try:
                page_posts = graph.get_connections(id=page_id, connection_name='posts', limit=30)
            except facebook.GraphAPIError:
                print ("Retrying...")
                sleep(5)
                continue

        for post in page_posts['data']:
            print ("Now in post " + str(post['id']))

            # Get likes for each post
            likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000, summary=True)

            # If the post needs to be skipped
            if likes['summary']['total_count'] > threshold and post_skipped < 2:
                print("Post skipped")
                post_skipped += 1
                continue

            # Otherwise, if the post is accepted, set the number of posts skipped to 0
            post_skipped = 0

            # Add likes to the dict
            for like in likes['data']:
                points_per_user[like['id']] += 1

            # If a like wasn't found and there are more likes, repeat
            while 'paging' in likes and 'next' in likes['paging']:
                likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000,
                                              after=likes['paging']['cursors']['after'])
                for like in likes['data']:
                    points_per_user[like['id']] += 1

            print ("Now checking comments")
            # Get comments for each post
            comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500)
            for comment in comments['data']:
                points_per_user[comment['from']['id']] += 3

            # If there are more comments, check them too
            while 'paging' in comments and 'next' in comments['paging']:
                comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500,
                                                 after=comments['paging']['cursors']['after'])
                for comment in comments['data']:
                    points_per_user[comment['from']['id']] += 3

        PageEval(_id=page_id, points=points_per_user).save()

        print("Finished Successfully: " + str(points_per_user))

    def index_all_pages(self):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')

        # Index 50 pages
        pages = graph.get_connections(id=self.id, connection_name='likes', limit=100)
        for page in pages['data']:
            Page.load_from_facebook(page['id']).index_page_logic()

        # If there are more pages, index them too
        while 'paging' in pages and 'next' in pages['paging']:
            pages = graph.get_connections(id=self.id, connection_name='likes', limit=100,
                                          after=pages['paging']['cursors']['after'])
            for page in pages['data']:
                Page.load_from_facebook(page['id']).index_page_logic()

# Redundant
class PageThread(threading.Thread):
    def __init__(self, page_id, user_id):
        threading.Thread.__init__(self)
        self.page_id = page_id
        self.user_id = user_id

    def run(self):
        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')

        print ("Now in page " + self.page_id)
        like_count = 0
        comment_count = 0
        # Get last 30 posts of the page
        page_posts = graph.get_connections(id=self.page_id, connection_name='posts', limit=30)
        for post in page_posts['data']:
            print ("Now in post " + str(post['id']))
            like_flag = False
            # Get likes for each post
            likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000)
            for like in likes['data']:
                if like['id'] == self.user_id:
                    like_count += 1
                    like_flag = True  # Don't get the other likes of this post
                    break

            # If a like wasn't found and there are more likes, repeat
            while not like_flag and 'paging' in likes and 'next' in likes['paging']:
                likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000,
                                              after=likes['paging']['cursors']['after'])
                for like in likes['data']:
                    if like['id'] == self.user_id:
                        like_count += 1
                        like_flag = True  # Don't get the other likes of this post
                        break

            print ("Now checking comments")
            # Get comments for each post
            comments = graph.get_connections(id=post['id'], connection_name='comments', limit=1000)
            for comment in comments['data']:
                if comment['from']['id'] == self.user_id:
                    comment_count += 1

            # If there are more comments, check them too
            while 'paging' in comments and 'next' in comments['paging']:
                comments = graph.get_connections(id=post['id'], connection_name='comments', limit=1000,
                                                 after=comments['paging']['cursors']['after'])
                for comment in comments['data']:
                    if comment['from']['id'] == self.user_id:
                        comment_count += 1

        points = like_count + comment_count * 3
        PageEval.add_points(self.user_id, self.page_id, points)

        print("Finished Successfully: " + str(points))


class PageThreadExtreme(threading.Thread):
    def __init__(self, page_id):
        threading.Thread.__init__(self)
        self.page_id = page_id

    def run(self):
        if PageEval.get_page_evaluations(self.page_id) is not None:
            print("------------------------ PAGE EVAL EXISTS --------------------")
            return

        graph = facebook.GraphAPI(
            access_token=Config.api_key,
            version='2.2')

        print ("Now in page " + self.page_id)
        points_per_user = defaultdict(int)
        post_skipped = 0        # Number of posts skipped
        threshold = 10000      # Max number of likes allowed

        # Get last 30 posts of the page
        while True:
            try:
                page_posts = graph.get_connections(id=self.page_id, connection_name='posts', limit=30)
                break

            except facebook.GraphAPIError:
                sleep(900)  # Sleep for 15 minutes
                continue  # Retry

            except:
                pass

        for post in page_posts['data']:
            print ("Now in post " + str(post['id']))

            # Get likes for each post
            try:
                likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000, summary=True)
                print("----------------------------------------------------------------------------------")
                print("----------------------------------------------------------------------------------")
                print("----------------------------- ACTIVE THREADS: %s ---------------------------------" % threading.activeCount())
                print("----------------------------------------------------------------------------------")
                print("----------------------------------------------------------------------------------")

            except facebook.GraphAPIError:
                sleep(900)  # Sleep for 15 minutes
                continue  # Retry

            except:
                continue

            # If the post needs to be skipped
            if likes['summary']['total_count'] > threshold and post_skipped < 2:
                post_skipped += 1
                continue

            # Otherwise, if the post is accepted, set the number of posts skipped to 0
            post_skipped = 0

            # Add likes to the dict
            for like in likes['data']:
                points_per_user[like['id']] += 2

            # If there are more likes, repeat
            while 'paging' in likes and 'next' in likes['paging']:
                while True:
                    try:
                        likes = graph.get_connections(id=post['id'], connection_name='likes', limit=1000,
                                                      after=likes['paging']['cursors']['after'])
                        for like in likes['data']:
                            points_per_user[like['id']] += 2
                        break

                    except facebook.GraphAPIError:
                        sleep(900)  # Sleep for 15 minutes
                        continue    # Retry

                    except:
                        continue



            print ("Now checking comments")
            # Get comments for each post

            try:
                comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500)

            except facebook.GraphAPIError:
                sleep(900)  # Sleep for 15 minutes
                continue  # Retry

            except:
                continue

            for comment in comments['data']:
                points_per_user[comment['from']['id']] += 3

            # If there are more comments, check them too
            while 'paging' in comments and 'next' in comments['paging']:
                while True:
                    try:
                        comments = graph.get_connections(id=post['id'], connection_name='comments', limit=500,
                                                         after=comments['paging']['cursors']['after'])
                        for comment in comments['data']:
                            points_per_user[comment['from']['id']] += 3

                    except facebook.GraphAPIError:
                        sleep(900)  # Sleep for 15 minutes
                        continue  # Retry

                    except:
                        continue

        PageEval(_id=self.page_id, points=dict(points_per_user)).save()

        print("Finished Successfully: " + str(points_per_user))
