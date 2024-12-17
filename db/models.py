def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            hash VARCHAR(128) NOT NULL,
            filled_preferences BOOLEAN NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

      

        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY REFERENCES users(id)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS gms (
                user_id INTEGER PRIMARY KEY REFERENCES users(id)
            );   
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS systems (
                id SERIAL PRIMARY KEY,
                title VARCHAR(120) UNIQUE NOT NULL,
                abbreviation VARCHAR(20)
                );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS games_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(120) NOT NULL,
                system_id INTEGER REFERENCES systems(id),
                max_players INTEGER NOT NULL,
                description TEXT,
                gm_id INTEGER REFERENCES users(id)      
            );
        """)


        conn.commit()

