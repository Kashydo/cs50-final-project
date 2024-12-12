import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, flash
from flask_bcrypt import generate_password_hash, check_password_hash



def check_user_exist(cur, username):
    cur.execute("SELECT * FROM users WHERE name = %s", (username,))
    user = cur.fetchone()
    if user:
        return user
    return None

def check_user_password(cur, column, user, password):
    cur.execute(f"SELECT * FROM users WHERE {column} = %s", (user,))
    user = cur.fetchone()
    if user and check_password_hash(user["hash"], password):
        return user
    return None

def add_user(cur, username, email, hash):
        cur.execute(
            "INSERT INTO users (name, email, hash, filled_preferences) VALUES (%s, %s, %s, False)",
            (username, email, hash))

def add_player(cur, user):
    cur.execute(
        "INSERT INTO players (user_id) VALUES (%s)",
        (user,),
    )
def add_gm(cur, user):
    cur.execute(
        "INSERT INTO gms (user_id) VALUES (%s)",
        (user,),
    )

def update_prefences_questionary(cur, user):
    cur.execute(
        "UPDATE users SET filled_preferences = True WHERE id = %s",
        (user,),
    )

def get_user_profile(cur, user):
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user,))
    user= cur.fetchone()
    if user:
        return user
    return None

def get_user_player_status(cur, user):
    cur.execute("SELECT * FROM players WHERE user_id = %s", (user,))
    if cur.fetchone():
        return True
    return False
def get_user_gm_status(cur, user):
    cur.execute("SELECT * FROM gms WHERE user_id = %s", (user,))
    if cur.fetchone():
        return True
    return False