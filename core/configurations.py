
class Config(object):
    """
    Base class to change Config Details for the application
    """

    """
    Flask Main Configurations
    """
    DEBUG = True
    SECRET_KEY = 'KOD'
    TESTING = False
    DEBUG_TB_INTERCEPT_REDIRECTS = True
    MONGO_DBNAME='social_prod'
    threaded=True

class ProductionConfig(Config):
    """
    These settings apply to the application if the applications is
    in the production Phase
    """
    DEBUG = False

class DevelopmentConfig(Config):
    """
    These settings apply to the application if the applications is
    in the Development Phase.If you are a developer you should choose these
    settings
    """
    DEBUG = True

config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)
