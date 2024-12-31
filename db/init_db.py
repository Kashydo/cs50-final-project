from os import environ
from psycopg2 import connect
from config import DevConfig, ProdConfig
from models import create_tables

env = environ.get('FLASK_ENV', 'development')

if env == 'production':
    config = ProdConfig
else:  # Domyślnie development
    config = DevConfig

# Połączenie z bazą danych
try:
    conn = connect(
        dbname=config.DBNAME,
        user= config.DBUSER,
        password= config.DBPASS,
        host= config.DBHOST,
        port= config.DBPORT,
    )
    print("Połączono z bazą danych!")
    create_tables(conn)
    print("Utworzono tabele")
except Exception as e:
    print(f"Błąd połączenia z bazą danych: {e}")
    raise


