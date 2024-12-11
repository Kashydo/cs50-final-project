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
        print("POST")
        username = request.form.get("username")
        if not username:
            flash("Brak nazwy użytkownika", "error")
            return render_template("register.html", error="Brak nazwy użytkownika")
        email = request.form.get("email")
        if not email:
            flash("Brak adresu email", "error")
            return render_template("register.html", error="Brak adresu email")
        password = request.form.get("password")
        if not password:
            flash("Brak hasła", "error")
            return render_template("register.html", error="Brak hasła")
        confirmation = request.form.get("confirmation")
        if not confirmation:
            flash("Brak potwierdzenia hasła", "error")
            return render_template("register.html", error="Brak potwierdzenia hasła")
        if password != confirmation:
            flash("Hasła nie są zgodne", "error")
            return render_template("register.html", error="Hasła nie są zgodne")
        hash= generate_password_hash(password).decode('utf-8')
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE name = %s OR email=%s", (username, email)) 
                if cur.fetchone():
                    flash("Użytkownik już istnieje", "error")
                    return render_template("register.html", error="Użytkownik już istnieje")
                cur.execute(
                    "INSERT INTO users (name, email, hash) VALUES (%s, %s, %s)",
                    (username, email, hash),
                )
                conn.commit()
                flash("Dodano użytkownika", "success")
        except Exception as e:
            flash("Błąd dodawania użytkownika", "error")
            return render_template("register.html", error="Błąd dodawania użytkownika")
        return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        user = request.form.get("user")
        if not user:
            flash("Brak nazwy użytkownika lub maila", "error")
            return render_template("login.html", error="Brak nazwy użytkownika lub maila")
        if "@" in user:
            column = "email"
        else:
            column = "name"
        password = request.form.get("password")
        if not password:
            flash("Brak hasła", "error")
            return render_template("login.html", error="Brak hasła")
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(f"SELECT * FROM users WHERE {column} = %s", (user,))
                user = cur.fetchone()
                if not user:
                    flash("Niepoprawne dane", "error")
                    return render_template("login.html", error="Niepoprawne dane")
                if not check_password_hash(user["hash"], password):
                    flash("Niepoprawne dane", "error")
                    return render_template("login.html", error="Niepoprawne dane")
                session["user"] = user
                flash("Zalogowano", "success")
        except Exception as e:
            flash("Błąd logowania", "error")
            return render_template("login.html", error="Błąd logowania")
        return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

if __name__ == '__main__':
    app.run()