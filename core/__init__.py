
import logging
import atexit
from apscheduler.scheduler import Scheduler

from .configurations import config_by_name
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mongoalchemy import MongoAlchemy
from logging.handlers import RotatingFileHandler
from flask.ext.pymongo import PyMongo

# Configure Mongo Database
mongo = PyMongo()
# Enable Debug Extension Toolbar
toolbar = DebugToolbarExtension()

cron = Scheduler(daemon= True)
cron.start()

atexit.register(lambda: cron.shutdown(wait=False))
# Configure authentication
login_manager = LoginManager()
login_manager.session_protection='strong'
login_manager.login_view = 'auth.login'

handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)


def create_app(config_name):
    """
    Create the flask application
    :param config_name:dev for development ,prod for production
    :return:flask application
    """
    app = Flask(__name__)

    app.logger.addHandler(handler)

    app.config.from_object(configurations.config_by_name[config_name])

    # Login Handler
    login_manager.init_app(app)

    mongo.init_app(app)

    # Enable Debug Toolbar
    # toolbar.init_app(app)


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
