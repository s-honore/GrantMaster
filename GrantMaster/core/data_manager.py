import sqlite3

def initialize_database(db_name='grantmaster.db'):
    """
    Initializes the SQLite database and creates necessary tables if they don't exist.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create organization_profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organization_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            details TEXT
        )
    ''')

    # Create grant_opportunities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grant_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            funder TEXT,
            deadline TEXT,
            description TEXT,
            link TEXT UNIQUE
        )
    ''')

    # Create grant_templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grant_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            content TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
    print("Database initialized successfully.")
