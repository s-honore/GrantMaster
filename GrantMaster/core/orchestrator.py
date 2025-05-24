import os
from dotenv import load_dotenv
from openai import OpenAI
from data_manager import DataManager # Assumes data_manager.py is in the same directory (core)

class Orchestrator:
    def __init__(self, db_name='grantmaster.db'):
        self.data_manager = DataManager(db_name=db_name)
        
        # Placeholder agent attributes
        self.research_agent = None
        self.analysis_agent = None
        self.writing_agent = None
        self.review_agent = None
        
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
            
        self.openai_client = OpenAI(api_key=api_key)
        print("Orchestrator and OpenAI client initialized successfully.")

    def register_researcher(self, researcher_agent):
        """Registers the researcher agent."""
        self.research_agent = researcher_agent
        print(f"Researcher agent {type(researcher_agent).__name__} registered.")

    def register_analyst(self, analyst_agent):
        """Registers the analyst agent."""
        self.analysis_agent = analyst_agent
        print(f"Analyst agent {type(analyst_agent).__name__} registered.")

    def register_writer(self, writer_agent):
        """Registers the writer agent."""
        self.writing_agent = writer_agent
        print(f"Writer agent {type(writer_agent).__name__} registered.")

    def register_editor(self, editor_agent):
        """Registers the editor agent (as review_agent)."""
        self.review_agent = editor_agent
        print(f"Editor agent {type(editor_agent).__name__} registered as review_agent.")

    def start_grant_application_flow(self, organization_profile, grant_opportunity):
        # Placeholder for workflow logic
        print(f"Starting grant application flow for grant ID: {grant_opportunity.get('id')} - {grant_opportunity.get('grant_title')}")
        print(f"Organization: {organization_profile.get('name')}")
        # Example: identify sections needed based on grant_opportunity details
        # Example: coordinate with an 'AnalysisAgent' or 'WritingAgent'
        pass

if __name__ == '__main__':
    # This block is for example usage and basic testing of the Orchestrator.
    # It uses a dedicated test database to avoid conflicts with main/development data.

    # 1. Define Dummy Agent Classes
    class DummyResearchAgent:
        def __init__(self, name="Researcher"):
            self.name = name
            print(f"Dummy {self.name} initialized.")

    class DummyAnalysisAgent:
        def __init__(self, name="Analyst"):
            self.name = name
            print(f"Dummy {self.name} initialized.")

    class DummyWritingAgent:
        def __init__(self, name="Writer"):
            self.name = name
            print(f"Dummy {self.name} initialized.")

    class DummyReviewAgent: # For the 'editor' role
        def __init__(self, name="Editor/Reviewer"):
            self.name = name
            print(f"Dummy {self.name} initialized.")

    db_name_for_test = 'test_orchestrator_main.db'
    dm_setup = None  # Initialize to None for cleanup in finally block

    try:
        print(f"Setting up DataManager for test data setup with '{db_name_for_test}'...")
        dm_setup = DataManager(db_name=db_name_for_test)

        print(f"Initializing Orchestrator with its DataManager pointed to '{db_name_for_test}'...")
        # Note: OPENAI_API_KEY must be set in .env or environment for Orchestrator to init successfully.
        orchestrator = Orchestrator(db_name=db_name_for_test)

        # 2. Instantiate and Register Dummy Agents
        print("\nRegistering dummy agents...")
        researcher = DummyResearchAgent()
        orchestrator.register_researcher(researcher)

        analyst = DummyAnalysisAgent()
        orchestrator.register_analyst(analyst)

        writer = DummyWritingAgent()
        orchestrator.register_writer(writer)

        editor = DummyReviewAgent() # Corresponds to self.review_agent
        orchestrator.register_editor(editor)
        print("Dummy agents registered.\n")

        # Populate with dummy data for testing the flow using dm_setup
        print("Saving dummy organization profile using dm_setup...")
        dm_setup.save_organization_profile(
            name="Test Org for Orchestrator Main",
            mission="To test orchestration with a dedicated test DB.",
            projects="Various test projects under main test.",
            needs="More testing with dedicated DB.",
            target_demographics="Test users for main test."
        )
        org_profile = dm_setup.get_organization_profile()

        print("Saving dummy grant opportunity using dm_setup...")
        grant_id = dm_setup.save_grant_opportunity(
            grant_title="Orchestrator Main Test Grant",
            funder="Test Funder Main",
            deadline="2025-01-15",
            description="A grant to test the orchestrator with its own test DB.",
            eligibility="All testers in main test.",
            focus_areas="Testing, Orchestration, Main DB"
        )
        grant_opp = dm_setup.get_grant_opportunity(grant_id)

        if org_profile and grant_opp:
            print("Organization profile and grant opportunity loaded for testing.")
            orchestrator.start_grant_application_flow(org_profile, grant_opp)
            print("Orchestrator flow initiated with test database.")
        else:
            print("ERROR: Failed to retrieve organization profile or grant opportunity for testing.")
            if not org_profile:
                print("Organization profile was None.")
            if not grant_opp:
                print(f"Grant opportunity was None (tried to fetch ID: {grant_id}).")

    except ValueError as ve: # Catching the specific ValueError from Orchestrator's __init__ (e.g., API key missing)
        print(f"Configuration error during Orchestrator testing: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during Orchestrator testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up the test database
        if dm_setup and dm_setup.conn: # Check if dm_setup was initialized and connection exists
            print(f"Closing connection to '{db_name_for_test}' used by dm_setup...")
            dm_setup.close_connection()
        
        # The Orchestrator's DataManager connection (orchestrator.data_manager.conn)
        # will be the same as dm_setup.conn if db_name_for_test was used for both.
        # DataManager.close_connection() handles if conn is already None.
        # If Orchestrator was initialized with a different db_name, its connection should be closed separately.
        # However, in this setup, orchestrator.data_manager is dm_setup or uses the same db_name.
        # If orchestrator was created and its data_manager is different, that's a more complex scenario.
        # For now, assume orchestrator.data_manager.close_connection() is covered if it's the same as dm_setup.
        # If orchestrator might have its own connection that is different, we'd need:
        # if 'orchestrator' in locals() and orchestrator.data_manager and orchestrator.data_manager.conn:
        #    orchestrator.data_manager.close_connection()
        # But this is redundant if db_name_for_test is used for Orchestrator.

        if os.path.exists(db_name_for_test):
            print(f"Removing test database '{db_name_for_test}'...")
            os.remove(db_name_for_test)
            print(f"Test database '{db_name_for_test}' removed.")
        else:
            print(f"Test database '{db_name_for_test}' not found, no need to remove.")
