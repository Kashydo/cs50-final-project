from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from config import ProdConfig, DevConfig
from psycopg2 import connect
from psycopg2.extras import DictCursor
from os import environ
from flask_bcrypt import generate_password_hash, check_password_hash

# Wybór konfiguracji
env = environ.get('FLASK_ENV', 'development')

# Tworzenie aplikacji Flask
app = Flask(__name__)

if env == 'production':
    app.config.from_object(ProdConfig)
else:  # Domyślnie development
    app.config.from_object(DevConfig)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Testowa trasa
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        username = request.form.get("username")
        if not username:
            return render_template("register.html", error="Brak nazwy użytkownika")
        password = request.form.get("password")
        if not password:
            return render_template("register.html", error="Brak hasła")
        confirmation = request.form.get("confirmation")
        if not confirmation:
            return render_template("register.html", error="Brak potwierdzenia hasła")
        if password != confirmation:
            return render_template("register.html", error="Hasła nie są zgodne")
        hash= generate_password_hash(password).decode('utf-8')
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    "INSERT INTO users (username, hash) VALUES (%s, %s)",
                    (username, hash),
                )
                conn.commit()
        except Exception as e:
            print(f"Błąd dodawania użytkownika: {e}")
            return render_template("register.html", error="Błąd dodawania użytkownika")
        return redirect("/")

if __name__ == '__main__':
    app.run()