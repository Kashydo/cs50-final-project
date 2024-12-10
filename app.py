from flask import Flask, jsonify
from config import ProdConfig, DevConfig
from psycopg2 import connect
from psycopg2.extras import DictCursor
from os import environ

# Wybór konfiguracji
env = environ.get('FLASK_ENV', 'development')

# Tworzenie aplikacji Flask
app = Flask(__name__)

if env == 'production':
    app.config.from_object(ProdConfig)
else:  # Domyślnie development
    app.config.from_object(DevConfig)


# Połączenie z bazą danych
try:
    conn = connect(
        dbname=app.config["DBNAME"],
        user=app.config["DBUSER"],
        password=app.config["DBPASS"],
        host=app.config["DBHOST"],
        port=app.config["DBPORT"],
    )
    print("Połączono z bazą danych!")
except Exception as e:
    print(f"Błąd połączenia z bazą danych: {e}")
    raise

# Testowa trasa
@app.route('/')
def hello_world():
    try:
        with conn.cursor(cursor_factory=DictCursor) as db:
            db.execute('SELECT * FROM users;')
            result = db.fetchall()
            return jsonify([dict(row) for row in result])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
