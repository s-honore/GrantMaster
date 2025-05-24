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

    def save_organization_profile(self, name, mission, projects, needs, target_demographics):
        """
        Saves the organization profile. Deletes any existing profile and inserts the new one.
        """
        try:
            self.cursor.execute("DELETE FROM organization_profile")
            self.cursor.execute('''
                INSERT INTO organization_profile (name, mission, projects, needs, target_demographics)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, mission, projects, needs, target_demographics))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error in save_organization_profile: {e}")
            # Optionally, re-raise the exception or handle it as appropriate
            # raise

    def get_organization_profile(self):
        """
        Retrieves the organization profile from the database.
        Returns a dictionary representing the profile, or None if not found.
        """
        try:
            self.cursor.execute("SELECT id, name, mission, projects, needs, target_demographics FROM organization_profile LIMIT 1")
            row = self.cursor.fetchone()
            if row:
                # Get column names from cursor.description
                column_names = [description[0] for description in self.cursor.description]
                # Create a dictionary
                profile_dict = dict(zip(column_names, row))
                return profile_dict
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_organization_profile: {e}")
            # Optionally, re-raise the exception or handle it as appropriate
            # raise
            return None

    def save_grant_opportunity(self, grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data='', analysis_notes='', suitability_score=None):
        """
        Saves a new grant opportunity to the database.
        Returns the ID of the newly inserted row.
        """
        try:
            self.cursor.execute('''
                INSERT INTO grant_opportunities (grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data, analysis_notes, suitability_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data, analysis_notes, suitability_score))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in save_grant_opportunity: {e}")
            # raise
            return None

    def update_grant_analysis(self, grant_id, analysis_notes, suitability_score, status):
        """
        Updates the analysis fields for a specific grant opportunity.
        """
        try:
            self.cursor.execute('''
                UPDATE grant_opportunities
                SET analysis_notes = ?, suitability_score = ?, status = ?
                WHERE id = ?
            ''', (analysis_notes, suitability_score, status, grant_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error in update_grant_analysis: {e}")
            # raise

    def get_grant_opportunity(self, grant_id):
        """
        Retrieves a specific grant opportunity by its ID.
        Returns a dictionary or None.
        """
        try:
            self.cursor.execute("SELECT * FROM grant_opportunities WHERE id = ?", (grant_id,))
            row = self.cursor.fetchone()
            if row:
                column_names = [description[0] for description in self.cursor.description]
                return dict(zip(column_names, row))
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_grant_opportunity: {e}")
            # raise
            return None

    def get_all_grant_opportunities(self, status_filter=None):
        """
        Retrieves all grant opportunities, optionally filtered by status.
        Returns a list of dictionaries.
        """
        try:
            query = "SELECT * FROM grant_opportunities"
            params = []
            if status_filter:
                query += " WHERE status = ?"
                params.append(status_filter)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            opportunities = []
            if rows:
                column_names = [description[0] for description in self.cursor.description]
                for row in rows:
                    opportunities.append(dict(zip(column_names, row)))
            return opportunities
        except sqlite3.Error as e:
            print(f"Database error in get_all_grant_opportunities: {e}")
            # raise
            return []

    def save_section_draft(self, grant_opportunity_id, section_name, draft_content, version=1, feedback=''):
        """
        Saves a new grant application section draft to the database.
        Returns the ID of the newly inserted row.
        """
        try:
            self.cursor.execute('''
                INSERT INTO grant_application_sections (grant_opportunity_id, section_name, draft_content, version, feedback)
                VALUES (?, ?, ?, ?, ?)
            ''', (grant_opportunity_id, section_name, draft_content, version, feedback))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in save_section_draft: {e}")
            # raise
            return None

    def get_section_draft(self, grant_opportunity_id, section_name, version=None):
        """
        Retrieves a specific section draft, or the latest version if version is None.
        Returns a dictionary or None.
        """
        try:
            query = "SELECT * FROM grant_application_sections WHERE grant_opportunity_id = ? AND section_name = ?"
            params = [grant_opportunity_id, section_name]
            
            if version is not None:
                query += " AND version = ?"
                params.append(version)
            else:
                query += " ORDER BY version DESC LIMIT 1"
                
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            
            if row:
                column_names = [description[0] for description in self.cursor.description]
                return dict(zip(column_names, row))
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_section_draft: {e}")
            # raise
            return None

    def get_all_sections_for_grant(self, grant_opportunity_id):
        """
        Retrieves the latest version of all unique sections for a given grant opportunity.
        Returns a list of dictionaries.
        """
        try:
            # Using the suggested SQL pattern to get the latest version of each section
            query = """
                SELECT t1.* 
                FROM grant_application_sections t1
                WHERE t1.version = (
                    SELECT MAX(t2.version) 
                    FROM grant_application_sections t2 
                    WHERE t2.grant_opportunity_id = t1.grant_opportunity_id 
                    AND t2.section_name = t1.section_name
                )
                AND t1.grant_opportunity_id = ?
            """
            self.cursor.execute(query, (grant_opportunity_id,))
            rows = self.cursor.fetchall()
            sections = []
            if rows:
                column_names = [description[0] for description in self.cursor.description]
                for row in rows:
                    sections.append(dict(zip(column_names, row)))
            return sections
        except sqlite3.Error as e:
            print(f"Database error in get_all_sections_for_grant: {e}")
            # raise
            return []

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
