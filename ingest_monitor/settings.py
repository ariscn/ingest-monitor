from os import environ
from os.path import abspath, dirname#, join


class Base(object):
    # BASE_DIR = dirname(dirname(abspath(__file__)))
    DATABASE = {
        'name': environ['MONITOR_DB'],
        'engine': 'SqliteDatabase',
    }
    SECRET_KEY = environ['MONITOR_SECRET']


class Dev(Base):
    DEBUG = True
    DEBUG_TB_ENABLED = True
    ASSETS_DEBUG = True
    # TODO make manage:Server respect SERVER_NAME = '127.0.0.1:8000'


settings = {
    'dev': Dev,
    'prod': Base
}
