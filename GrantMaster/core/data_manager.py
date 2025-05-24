import sqlite3

class DataManager:
    def __init__(self, db_name='grantmaster.db'):
        """
        Initializes the DataManager, connects to the database, and creates tables.
        """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        Creates the necessary tables in the database if they don't already exist.
        """
        # Create organization_profile table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                mission TEXT,
                projects TEXT,
                needs TEXT,
                target_demographics TEXT
            )
        ''')

        # Create grant_opportunities table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grant_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grant_title TEXT,
                funder TEXT,
                deadline DATE,
                description TEXT,
                eligibility TEXT,
                focus_areas TEXT,
                raw_research_data TEXT,
                analysis_notes TEXT,
                suitability_score REAL,
                status TEXT DEFAULT 'identified'
            )
        ''')

        # Create grant_templates table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grant_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT,
                content TEXT,
                usage_notes TEXT
            )
        ''')

        # Create grant_application_sections table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grant_application_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grant_opportunity_id INTEGER,
                section_name TEXT,
                draft_content TEXT,
                version INTEGER,
                feedback TEXT,
                FOREIGN KEY(grant_opportunity_id) REFERENCES grant_opportunities(id)
            )
        ''')

        self.conn.commit()

    def close_connection(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()

# Example usage (optional, can be removed or commented out for production)
if __name__ == '__main__':
    # This is for testing purposes, to ensure the DataManager initializes correctly
    # and creates the database and tables.
    # In a real application, you would import DataManager and instantiate it where needed.
    try:
        db_manager = DataManager(db_name='test_grantmaster.db')
        print("Database 'test_grantmaster.db' initialized and tables created successfully.")
        
        # You could add further checks here, e.g., listing tables
        db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = db_manager.cursor.fetchall()
        print("Tables found:", tables)
        
        db_manager.close_connection()
        print("Database connection closed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # It's good practice to clean up the test database if you create one
    import os
    if os.path.exists('test_grantmaster.db'):
        os.remove('test_grantmaster.db')
        print("Test database 'test_grantmaster.db' removed.")
