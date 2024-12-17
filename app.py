from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from config import ProdConfig, DevConfig
from psycopg2 import connect
from psycopg2.extras import DictCursor
from os import environ
from flask_bcrypt import generate_password_hash 
from helpers import login_required, check_and_flash_if_none
import db.queries as queries
from datetime import datetime

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
    with conn.cursor(cursor_factory=DictCursor) as cur:
        games = queries.get_games(cur)
    return render_template("index.html", games=games)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.

    Returns:
        - On GET: Renders the registration form.
        - On POST: 
            - If any form field is missing or invalid, re-renders the registration form with an error message.
            - If the username already exists, re-renders the registration form with an error message.
            - If registration is successful, redirects to the login page.

    Raises:
        Exception: If there is an error adding the user to the database.
    """
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        print("POST")
        username = request.form.get("username")
        if check_and_flash_if_none(username, "Brak nazwy użytkownika"):
            return render_template("register.html", error="Brak nazwy użytkownika")
        email = request.form.get("email")
        if check_and_flash_if_none(email, "Brak maila"):
            return render_template("register.html", error="Brak maila")
        password = request.form.get("password")
        if check_and_flash_if_none(password, "Brak hasła"):
            return render_template("register.html", error="Brak hasła")
        confirmation = request.form.get("confirmation")
        if check_and_flash_if_none(confirmation, "Brak potwierdzenia hasła"):
            return render_template("register.html", error="Brak potwierdzenia hasła")
        if password != confirmation:
            flash("Hasła nie są zgodne", "error")
            return render_template("register.html", error="Hasła nie są zgodne")
        hash= generate_password_hash(password).decode('utf-8')
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if queries.check_user_exist(cur, username):
                    flash("Użytkownik już istnieje", "error")
                    return render_template("register.html", error="Użytkownik już istnieje")
                queries.add_user(cur, username, email, hash)
                print("User added to db")
            conn.commit()
            print("User saved")
            flash("Dodano użytkownika", "success")
        except Exception as e:
            print(f"Exception occurred: {e}")
            flash("Błąd dodawania użytkownika", "error")
            return render_template("register.html", error="Błąd dodawania użytkownika")
        return redirect("/login")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    This function clears the current session and processes login requests.

    GET:
        Renders the login page.

    POST:
        - Retrieves the username/email and password from the form.
        - Validates the presence of username/email and password.
        - Determines whether the user input is an email or username.
        - Checks the user's credentials against the database.
        - If credentials are invalid, flashes an error message and re-renders the login page.
        - If credentials are valid, sets the user ID in the session and flashes a success message.
        - Redirects to the home page if user preferences are filled, otherwise renders the preferences page.

    """
    session.clear()
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        user = request.form.get("user")
        if check_and_flash_if_none(user, "Brak nazwy użytkownika lub maila"):
            return render_template("login.html", error="Brak nazwy użytkownika lub maila")
        if "@" in user:
            column = "email"
        else:
            column = "name"
        password = request.form.get("password")
        if check_and_flash_if_none(password, "Brak hasła"):
            return render_template("login.html", error="Brak hasła")
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                user = queries.check_user_password(cur, column, user, password)
                check_and_flash_if_none(user, "Niepoprawne dane")
                player = False
                gm = False
                if queries.get_user_profile(cur, user["id"]):
                    player = True
                if queries.get_user_gm_status(cur, user['id']):
                    gm = True
                session["user_id"] = user['id']
                session["name"] = user['name']
                session["gm"] = gm
                session["player"] = player
                queries.update_last_login(cur, user['id'])
                conn.commit
                flash("Zalogowano", "success")
        except Exception as e:
            flash("Błąd logowania", "error")
            return render_template("login.html", error="Błąd logowania")
        if user["filled_preferences"]:
            return redirect("/")
        return render_template("preferences.html")

@app.route('/logout')
def logout():
    """
    Logs out the current user by clearing the session and redirecting to the home page.
    Returns:
        Response: A redirect response to the home page ("/").
    """

    session.clear()
    return redirect("/")

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """
    Handle user preferences for roles.
    Returns:
        - On GET: Renders the preferences.html template.
        - On POST: Redirects to the home page with a success or error message.
    Raises:
        - Redirects to the home page with an error message if the user is not found in the session.
        - Renders the preferences.html template with an error message if no preferences are selected.
        - Redirects to the home page with an error message if there is an exception during database operations.
    """
    if request.method == 'GET':
        return render_template("preferences.html")
    if request.method == 'POST':
        user = session.get("user")
        print(user)
        if check_and_flash_if_none(user, "Brak użytkownika"):
            return redirect("/", error="Brak użytkownika")
        preferences = request.form.getlist("roles")
        print(preferences)
        if check_and_flash_if_none(preferences, "Brak preferencji"):
            return render_template("preferences.html", error="Brak preferencji")
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if 'player' in preferences:
                    print("player")
                    queries.add_player(cur, user)
                    filled_preferences = True
                if 'gm' in preferences:
                    print("gm")
                    queries.add_gm(cur, user)
                    filled_preferences = True
                queries.update_prefences_questionary(cur, user)
                print("filled_preferences")
                conn.commit()
                flash("Wypełniono ankiete", "success")
        except Exception as e:
            flash("Błąd uzupełniania preferencji", "error")
            return redirect("/", error="Błąd preferencji")
        return redirect("/")

@app.route('/profile')
@login_required
def profile():
    """
    Route for displaying the user's profile.
    This route is protected by the @login_required decorator, ensuring that only logged-in users can access it.
    Returns:
        A rendered template of the user's profile if the user is found in the session and the database.
        Redirects to the home page with an error message if the user is not found or if there is an error fetching the user data.
    Raises:
        Exception: If there is an error while fetching the user data from the database.
    """
    user = session.get("user")
    if check_and_flash_if_none(user, "Brak użytkownika"):
        return redirect("/", error="Brak użytkownika")
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            user_profile = queries.get_user_profile(cur, user)
            check_and_flash_if_none(user_profile, "Brak użytkownika")
            user_profile = dict(user_profile)
            if queries.get_user_player_status(cur, user):
               user_profile["player"] = True
            else:
                user_profile["player"] = False    
            if queries.get_user_gm_status(cur, user):
                user_profile["gm"] = True
            else:
                user_profile["gm"] = False
            return render_template("profile.html", user= user_profile)
    except Exception as e:
        flash("Błąd pobierania użytkownika", "error")
        return redirect("/", error="Błąd pobierania użytkownika")
    return render_template("profile.html")
    
@app.route('/post_game', methods=['GET', 'POST'])
@login_required
def post_game():
    if request.method == 'GET':
        print("GET")
        if check_and_flash_if_none(session.get("user"), "Brak użytkownika"):
            return redirect("/", error="Brak użytkownika")
        return render_template("post_game.html")
    if request.method == 'POST':
        print("POST")
        if check_and_flash_if_none(session.get("user"), "Brak użytkownika"):
            return redirect("/", error="Brak użytkownika")
        title = request.form.get("title")
        if check_and_flash_if_none(title, "Brak tytułu"):
            return render_template("post_game.html", error="Brak tytułu")
        system = request.form.get("system")
        if check_and_flash_if_none(system, "Brak systemu"):
            return render_template("post_game.html", error="Brak systemu")
        players = request.form.get("players")
        if check_and_flash_if_none(players, "Brak liczby graczy"):
            return render_template("post_game.html", error="Brak liczby graczy")
        description = request.form.get("description")

        with conn.cursor(cursor_factory=DictCursor) as cur:
            try:
                print("try to add game")
                queries.add_game(cur, session.get("user"), title, players, system, description)
                conn.commit()
                flash("Dodano grę", "success")
            except Exception as e:
                flash("Błąd dodawania gry", "error")
                return redirect("/", error="Błąd dodawania gry")
        return redirect("/")


if __name__ == '__main__':
    app.run()