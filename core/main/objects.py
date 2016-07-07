from queue import Queue
from threading import Thread
import facebook
from ..social.Objects.User import User

queue1 = Queue()        # queue used for users that have provided token
queue2 = Queue()        # queue used to evaluate pages later


class Thread1(Thread):
    """Thread used to get user likes and posts"""
    def __init__(self, token):
        Thread.__init__(self)
        self.token = token

    def run(self):
        graph = facebook.GraphAPI(
            access_token=self.token,
            version='2.2')

        pages = graph.get_connections(id='me', connection_name='likes')

        queue2.put(Thread2(pages))
        # get likes and posts


class Thread2(Thread):
    """Thread used to evaluate pages."""
    def __init__(self, pages):
        Thread.__init__(self)
        self.pages = pages

    def run(self):
        print(self.pages)
        # evaluate pages

while True:
    if not queue1.empty():
        queue1.get().run()

    else:
        queue2.get().run()
