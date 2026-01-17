import sqlite3

def get_connection():
    return sqlite3.connect("gaze_data.db")


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gaze_data (
        gaze_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        direction TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS calibration_data (
    calibration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    direction TEXT,
    eye_x REAL,
    eye_y REAL,
    is_valid INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")


    conn.commit()
    conn.close()


def insert_user(name, age):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        (name, age)
    )

    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def start_session(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sessions (user_id, start_time) VALUES (?, CURRENT_TIMESTAMP)",
        (user_id,)
    )

    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def insert_gaze_data(session_id, direction):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO gaze_data (session_id, direction) VALUES (?, ?)",
        (session_id, direction)
    )

    conn.commit()
    conn.close()
def insert_calibration_data(user_id, direction, eye_x, eye_y, is_valid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO calibration_data 
    (user_id, direction, eye_x, eye_y, is_valid)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, direction, eye_x, eye_y, is_valid))

    conn.commit()
    conn.close()


# Run once to create tables
if __name__ == "__main__":
    create_tables()
    print("Database & tables ready")

