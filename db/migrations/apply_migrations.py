import os
from psycopg2 import connect, OperationalError
from config import ProdConfig, DevConfig
from os import environ

# Wybór konfiguracji
env = environ.get('FLASK_ENV', 'development')

if env == 'production':
    config = ProdConfig
else:  # Domyślnie development
    config = DevConfig

def connect_db():
    try:
        conn = connect(
            dbname=config.DBNAME,
            user=config.DBUSER,
            password=config.DBPASS,
            host=config.DBHOST,
            port=config.DBPORT,
        )
        print("Połączono z bazą danych!")
        return conn
    except OperationalError as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        raise

def apply_migrations(conn):
    with conn.cursor() as cur:
        # Keep track of applied migrations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL
            );
        """)
        conn.commit()

        # Get list of applied migrations
        cur.execute("SELECT filename FROM migrations;")
        applied_migrations = {row[0] for row in cur.fetchall()}

        # Apply new migrations
        migration_dir = os.path.dirname(os.path.abspath(__file__))
        migration_files = sorted(f for f in os.listdir(migration_dir) if f.endswith('.sql'))
        print(f"Found migration files: {migration_files}")
        for filename in migration_files:
            if filename not in applied_migrations:
                print(f"Applying migration: {filename}")
                with open(os.path.join(migration_dir, filename), 'r') as f:
                    sql = f.read()
                    cur.execute(sql)
                    cur.execute("INSERT INTO migrations (filename) VALUES (%s);", (filename,))
                    conn.commit()
                    print(f"Applied migration: {filename}")
  

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    conn = connect_db()
    apply_migrations(conn)
    conn.close()