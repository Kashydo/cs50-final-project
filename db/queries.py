import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, flash
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime



def check_user_exist(cur, username):
    """
    Check if a user exists in the database.
    Args:
        cur (cursor): The database cursor to execute the query.
        username (str): The username to check for existence.
    Returns:
        tuple or None: Returns the user record as a tuple if the user exists, otherwise returns None.
    """

    cur.execute("SELECT * FROM users WHERE name = %s", (username,))
    user = cur.fetchone()
    if user:
        return user
    return None

def check_user_password(cur, column, user, hash):
    """
    Check if the provided user and hash match a record in the database.
    Args:
        cur (cursor): The database cursor to execute the query.
        column (str): The column name to search for the user.
        user (str): The user identifier to search for.
        hash (str): The hash to verify against the stored hash.
    Returns:
        dict or None: The user record if the hash matches, otherwise None.
    """
    cur.execute(f"SELECT * FROM users WHERE {column} = %s", (user,))
    user = cur.fetchone()
    if user and check_password_hash(user["hash"], hash):
        return user
    return None

def add_user(cur, username, email, hash):
    """
    Adds a new user to the database.
    Args:
        cur (cursor): The database cursor to execute the SQL command.
        username (str): The username of the new user.
        email (str): The email address of the new user.
        hash (str): The hashed password of the new user.
    Returns:
        None
    """
    timestamp = datetime.now()
    cur.execute(
        "INSERT INTO users (name, email, hash, filled_preferences, registered_at, last_login) VALUES (%s, %s, %s, False, %s , %s)",
        (username, email, hash, timestamp, timestamp))

def add_player(cur, user):
    """
    Adds a new player to the players table in the database.
    Args:
        cur (cursor): The database cursor to execute the SQL command.
        user (int): The user ID of the player to be added.
    Returns:
        None
    """

    cur.execute(
        "INSERT INTO players (user_id) VALUES (%s)",
        (user,),
    )

def add_gm(cur, user):
    """
    Adds a new game master (GM) to the database.
    Parameters:
    cur (cursor): The database cursor to execute the SQL command.
    user (int): The user ID of the game master to be added.
    Returns:
    None
    """

    cur.execute(
        "INSERT INTO gms (user_id) VALUES (%s)",
        (user,),
    )

def update_preferences_questionary(cur, user):
    """
    Updates the user's preferences questionnaire status to filled in the database.
    Args:
        cur (cursor): The database cursor to execute the SQL command.
        user (int): The ID of the user whose preferences questionnaire status is to be updated.
    Returns:
        None
    """

    cur.execute(
        "UPDATE users SET filled_preferences = True WHERE id = %s",
        (user,),
    )

def get_user_profile(cur, user):
    """
    Retrieve the user profile from the database.
    Args:
        cur (cursor): The database cursor to execute the query.
        user (int): The ID of the user whose profile is to be retrieved.
    Returns:
        tuple: A tuple containing the user's id, name, and email if the user is found.
        None: If the user is not found in the database.
    """
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user,))
    user= cur.fetchone()
    if user:
        return user
    return None

def get_user_player_status(cur, user):
    """
    Check if a user exists in the players table.
    Args:
        cur (cursor): A database cursor object to execute the SQL query.
        user (int): The user ID to check in the players table.
    Returns:
        bool: True if the user exists in the players table, False otherwise.
    """

    cur.execute("SELECT * FROM players WHERE user_id = %s", (user,))
    if cur.fetchone():
        return True
    return False

def get_user_gm_status(cur, user):
    """
    Check if a user has GM (Game Master) status.
    Args:
        cur (cursor): A database cursor object used to execute SQL queries.
        user (int): The user ID to check for GM status.
    Returns:
        bool: True if the user has GM status, False otherwise.
    """
    

    cur.execute("SELECT * FROM gms WHERE user_id = %s", (user,))
    if cur.fetchone():
        return True
    return False

def add_game(cur, user, title, max_players, game_system, description):
    """
    Adds a new game post to the database.
    Parameters:
    cur (cursor): The database cursor to execute the query.
    gm (int): The id of the game master (GM) creating the post.
    title (str): The title of the game.
    max_players (int): The maximum number of players allowed in the game.
    system _id (int): The game system id.
    description (str): A brief description of the game.
    Returns:
    None
    """

    cur.execute("INSERT INTO games_posts (title, system_id, max_players, description, gm_id) "
                "VALUES (%s, %s, %s, %s, %s)", (title, game_system, max_players, description, user))
                    
def get_games(cur):
    """
    Fetches all records from the 'games_posts' table.
    Args:
        cur: The database cursor to execute the query.
    Returns:
        list: A list of tuples containing all records from the 'games_posts' table.
    """

    cur.execute("SELECT * FROM games_posts")
    return cur.fetchall()

def update_last_login(cur, user_id):
    """
    Updates the last login timestamp for a user in the database.
    Args:
        cur: The database cursor to execute the query.
        user_id: The ID of the user whose last login timestamp is to be updated.
    Returns:
        None
    """

    cur.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                (datetime.now(), user_id))

def get_systems(cur):
    """
    Retrieve all records from the 'systems' table.
    Args:
        cur: The database cursor to execute the query.
    Returns:
        list: A list of tuples containing all records from the 'systems' table.
    """
    cur.execute("SELECT * FROM systems")
    return cur.fetchall()

def get_game_by_id(cur, id):
    cur.execute("SELECT * FROM games_posts WHERE id = %s", (id,))
    game= cur.fetchone()
    if game:
        columns = [desc[0] for desc in cur.description]
        game_dict = dict(zip(columns, game))
        return game_dict
    return None