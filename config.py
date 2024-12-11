from os import environ, path
from dotenv import load_dotenv

env = environ.get('FLASK_ENV', 'development')  
dotenv_path = path.join(
    './environment/production' if env == 'production' else './environment/development',
    '.env'
)
load_dotenv(dotenv_path)


class Config:
    SECRET_KEY = environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"


class ProdConfig(Config):
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    DBNAME=environ.get('DBNAME')
    DBUSER=environ.get('DBUSER')
    DBPASS=environ.get('DBPASS')
    DBHOST=environ.get('DBHOST')   
    DBPORT=int(environ.get("DBPORT"))
   


class DevConfig(Config):
    """Konfiguracja developerska."""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    DBNAME=environ.get('DBNAME')
    DBUSER=environ.get('DBUSER')
    DBPASS=environ.get('DBPASS')
    DBHOST=environ.get('DBHOST')   
    DBPORT=int(environ.get("DBPORT"))