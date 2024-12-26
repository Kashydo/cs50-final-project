import os
import base64
from flask import Flask, flash, redirect, render_template, request, session, g
from flask_session import Session
from config import ProdConfig, DevConfig
from psycopg2 import connect
from psycopg2.extras import DictCursor
from os import environ
from flask_bcrypt import generate_password_hash, check_password_hash
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

@app.before_request
def before_request():
    g.nonce = base64.b64encode(os.urandom(16)).decode('utf-8')

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' https://cdn.jsdelivr.net 'nonce-{g.nonce}'; "
        f"style-src 'self' https://cdn.jsdelivr.net; "
        f"style-src-elem 'self' https://cdn.jsdelivr.net; "
        f"img-src 'self' data:; "
        f"font-src 'self' https://cdn.jsdelivr.net; "
    )
    return response

# Testowa trasa
@app.route('/')
def index():
    with conn.cursor(cursor_factory=DictCursor) as cur:
        games = queries.get_games(cur)
    return render_template("index.html", games=games, nonce=g.nonce)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    GET:
        Renders the registration form.
    POST:
        Processes the registration form:
        - Validates the presence of username, email, password, and password confirmation.
        - Checks if the password and confirmation match.
        - Hashes the password.
        - Checks if the username already exists in the database.
        - Adds the new user to the database.
        - Commits the transaction.
        - Redirects to the login page upon successful registration.
    Returns:
        - Renders the registration form with error messages if validation fails or an exception occurs.
        - Redirects to the login page upon successful registration.
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
    This function clears the current session and processes the login request.
    If the request method is GET, it renders the login page.
    If the request method is POST, it validates the user credentials and logs the user in.
    Returns:
        The rendered template for the login page or preferences page, or a redirect to the home page.
    Raises:
        Exception: If there is an error during the login process.
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
                session["user"] = {
                    "id": user["id"],
                    "name": user["name"],
                    "gm": gm
                }

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
    This function handles both GET and POST requests for user preferences.
    - For GET requests, it renders the preferences form.
    - For POST requests, it processes the submitted preferences form.
    POST request processing:
    1. Retrieves the user ID from the session.
    2. Checks if the user ID is valid; if not, redirects to the home page with an error message.
    3. Retrieves the list of selected roles from the form.
    4. Checks if any preferences were selected; if not, re-renders the preferences form with an error message.
    5. Updates the user's preferences in the database based on the selected roles.
    6. Commits the changes to the database and flashes a success message.
    7. Handles any exceptions by flashing an error message and redirecting to the home page.
    Returns:
        - For GET requests: Renders the preferences form.
        - For POST requests: Redirects to the home page after processing the form.
    """

    if request.method == 'GET':
        return render_template("preferences.html")
    if request.method == 'POST':
        user = session.get("user")["id"]
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
                if 'gm' in preferences:
                    print("gm")
                    queries.add_gm(cur, user)
                queries.update_preferences_questionary(cur, user)
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
    Renders the profile page for the logged-in user.
    This function retrieves the user's profile information from the database
    and checks their player and game master (GM) status. If the user is not
    found or an error occurs during the retrieval process, appropriate error
    messages are flashed, and the user is redirected to the home page.
    Returns:
        Response: Renders the profile page with the user's profile information or redirects to the home page with an error message.
    """

    user = session.get("user")["id"]
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
    """
    Handle the posting of a new game.
    This function handles both GET and POST requests for posting a new game.
    - For GET requests, it retrieves the available game systems and renders the "post_game.html" template.
    - For POST requests, it processes the form data to add a new game to the database.
    Returns:
        - For GET requests:
            - Redirects to the home page with an error message if the user is not logged in.
            - Renders the "post_game.html" template with the available game systems.
        - For POST requests:
            - Redirects to the home page with an error message if the user is not logged in.
            - Renders the "post_game.html" template with an error message if any required form field is missing.
            - Adds the new game to the database and redirects to the home page with a success message.
            - Redirects to the home page with an error message if there is an exception during the database operation.

    """
    if request.method == 'GET':
        print("GET")
        if check_and_flash_if_none(session.get("user"), "Brak użytkownika"):
            return redirect("/", error="Brak użytkownika")
        with conn.cursor(cursor_factory=DictCursor) as cur:
            try:
                systems = queries.get_systems(cur)
                print("get game systems")
                for system in systems:
                    print(system["title"])
            except Exception as e:
                print(f"Exception occurred: {e}")
                flash("Błąd pobierania systemów gier", "error")
                return redirect("/", error="Błąd pobierania systemów gier")
        return render_template("post_game.html", systems=systems)
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
                print(f"{title}, {session.get("user")["id"]}, {players}, {system}, {description}")
                queries.add_game(cur, session.get("user")["id"], title, players, system, description)
                conn.commit()
                flash("Dodano grę", "success")
            except Exception as e:
                flash("Błąd dodawania gry", "error")
                return redirect("/", error="Błąd dodawania gry")
        return redirect("/")


if __name__ == '__main__':
    app.run()