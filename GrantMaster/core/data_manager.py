import sqlite3

class DataManager:
    def __init__(self, db_name='grantmaster.db'):
        """
        Initializes the DataManager and stores the database name.
        Table creation will be handled by _create_tables, now responsible for its own connection.
        """
        self.db_name = db_name
        self._create_tables()

    def _create_tables(self):
        """
        Creates the necessary tables in the database if they don't already exist.
        Manages its own database connection.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            # Create organization_profile table
            cursor.execute('''
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
            cursor.execute('''
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grant_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT,
                    content TEXT,
                    usage_notes TEXT
                )
            ''')

            # Create grant_application_sections table
            cursor.execute('''
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
            conn.commit()
            print("DataManager: Tables checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Database error in _create_tables: {e}")
            # This method is critical for startup, so perhaps re-raise or handle more gracefully
        finally:
            if conn:
                conn.close()

    def save_organization_profile(self, name, mission, projects, needs, target_demographics):
        """
        Saves the organization profile. Deletes any existing profile and inserts the new one.
        Returns True on success, False on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM organization_profile")
            cursor.execute('''
                INSERT INTO organization_profile (name, mission, projects, needs, target_demographics)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, mission, projects, needs, target_demographics))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in save_organization_profile: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_organization_profile(self):
        """
        Retrieves the organization profile from the database.
        Returns a dictionary representing the profile, or None if not found or on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, mission, projects, needs, target_demographics FROM organization_profile LIMIT 1")
            row = cursor.fetchone()
            if row:
                column_names = [description[0] for description in cursor.description]
                profile_dict = dict(zip(column_names, row))
                return profile_dict
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_organization_profile: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def save_grant_opportunity(self, grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data='', analysis_notes='', suitability_score=None):
        """
        Saves a new grant opportunity to the database.
        Returns the ID of the newly inserted row, or None on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO grant_opportunities (grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data, analysis_notes, suitability_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data, analysis_notes, suitability_score))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in save_grant_opportunity: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_grant_analysis(self, grant_id, analysis_notes, suitability_score, status):
        """
        Updates the analysis fields for a specific grant opportunity.
        Returns True on success, False on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE grant_opportunities
                SET analysis_notes = ?, suitability_score = ?, status = ?
                WHERE id = ?
            ''', (analysis_notes, suitability_score, status, grant_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error in update_grant_analysis: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_grant_opportunity(self, grant_id):
        """
        Retrieves a specific grant opportunity by its ID.
        Returns a dictionary or None on error or if not found.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM grant_opportunities WHERE id = ?", (grant_id,))
            row = cursor.fetchone()
            if row:
                column_names = [description[0] for description in cursor.description]
                return dict(zip(column_names, row))
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_grant_opportunity: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_grant_opportunities(self, status_filter=None):
        """
        Retrieves all grant opportunities, optionally filtered by status.
        Returns a list of dictionaries, or an empty list on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            query = "SELECT * FROM grant_opportunities"
            params = []
            if status_filter:
                query += " WHERE status = ?"
                params.append(status_filter)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            opportunities = []
            if rows:
                column_names = [description[0] for description in cursor.description]
                for row in rows:
                    opportunities.append(dict(zip(column_names, row)))
            return opportunities
        except sqlite3.Error as e:
            print(f"Database error in get_all_grant_opportunities: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def save_section_draft(self, grant_opportunity_id, section_name, draft_content, version=1, feedback=''):
        """
        Saves a new grant application section draft to the database.
        Returns the ID of the newly inserted row, or None on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO grant_application_sections (grant_opportunity_id, section_name, draft_content, version, feedback)
                VALUES (?, ?, ?, ?, ?)
            ''', (grant_opportunity_id, section_name, draft_content, version, feedback))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in save_section_draft: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_section_draft(self, grant_opportunity_id, section_name, version=None):
        """
        Retrieves a specific section draft, or the latest version if version is None.
        Returns a dictionary or None on error or if not found.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            query = "SELECT * FROM grant_application_sections WHERE grant_opportunity_id = ? AND section_name = ?"
            params = [grant_opportunity_id, section_name]
            
            if version is not None:
                query += " AND version = ?"
                params.append(version)
            else:
                query += " ORDER BY version DESC LIMIT 1"
                
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                column_names = [description[0] for description in cursor.description]
                return dict(zip(column_names, row))
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error in get_section_draft: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all_sections_for_grant(self, grant_opportunity_id):
        """
        Retrieves the latest version of all unique sections for a given grant opportunity.
        Returns a list of dictionaries, or an empty list on error.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
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
            cursor.execute(query, (grant_opportunity_id,))
            rows = cursor.fetchall()
            sections = []
            if rows:
                column_names = [description[0] for description in cursor.description]
                for row in rows:
                    sections.append(dict(zip(column_names, row)))
            return sections
        except sqlite3.Error as e:
            print(f"Database error in get_all_sections_for_grant: {e}")
            return []
        finally:
            if conn:
                conn.close()

# Example usage (optional, can be removed or commented out for production)
if __name__ == '__main__':
    # This is for testing purposes, to ensure the DataManager initializes correctly
    # and creates the database and tables.
    # In a real application, you would import DataManager and instantiate it where needed.
    try:
        db_manager = DataManager(db_name='test_grantmaster.db') # This will call _create_tables
        print("DataManager initialized with 'test_grantmaster.db'. Tables should be checked/created.")
        
        # Example: Save and retrieve organization profile
        profile_saved = db_manager.save_organization_profile("Test Org", "To test things", "Testing", "More tests", "Testers")
        if profile_saved:
            print("Organization profile saved successfully.")
            profile = db_manager.get_organization_profile()
            if profile:
                print(f"Retrieved profile: {profile['name']}")
            else:
                print("Failed to retrieve profile after saving.")
        else:
            print("Failed to save organization profile.")

        # Add more specific tests for other methods if needed
        # For instance, listing tables still requires a direct connection for that specific test.
        # This is a test-specific action, not part of DataManager's public API.
        conn_test = None
        try:
            conn_test = sqlite3.connect('test_grantmaster.db')
            cursor_test = conn_test.cursor()
            cursor_test.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor_test.fetchall()
            print("Tables found in test_grantmaster.db:", tables)
        except sqlite3.Error as e:
            print(f"Error accessing test_grantmaster.db directly for table listing: {e}")
        finally:
            if conn_test:
                conn_test.close()
                print("Test connection for table listing closed.")

    except Exception as e:
        print(f"An error occurred in __main__ test: {e}")
    
    # It's good practice to clean up the test database if you create one
    import os
    if os.path.exists('test_grantmaster.db'):
        os.remove('test_grantmaster.db')
        print("Test database 'test_grantmaster.db' removed.")
