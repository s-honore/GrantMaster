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

    def _mock_websleuth_research(self, website_url, login_credentials):
        """
        Internal mock method to simulate web research by an agent.
        """
        print(f"[Orchestrator LOG] Called _mock_websleuth_research with URL: {website_url}")
        # login_credentials are not used in this mock but are part of the signature
        return [
            {'grant_title': 'Mock Grant Alpha', 'funder': 'Funder X', 'deadline': '2025-10-31', 'description': 'Alpha grant description.', 'eligibility': 'All eligible.', 'focus_areas': 'Testing, Mocking', 'raw_research_data': 'Some raw text for Alpha.'},
            {'grant_title': 'Mock Grant Beta', 'funder': 'Funder Y', 'deadline': '2025-11-30', 'description': 'Beta grant description.', 'eligibility': 'Specific criteria.', 'focus_areas': 'Development, AI', 'raw_research_data': 'Some raw text for Beta.'}
        ]

    def _mock_opportunitymatcher_analyze(self, grant_info, org_profile):
        """
        Internal mock method to simulate grant opportunity analysis by an agent.
        """
        grant_title = grant_info.get('grant_title', '')
        org_name = org_profile.get('name', 'Unknown Org')
        print(f"[Orchestrator LOG] Called _mock_opportunitymatcher_analyze for grant: {grant_title} and org: {org_name}")
        
        if "Alpha" in grant_title:
            return {'analysis_notes': 'This seems like a strong match for Alpha grant.', 'suitability_score': 0.90, 'status': 'analyzed_strong_match'}
        else:
            return {'analysis_notes': 'Further review needed for this grant.', 'suitability_score': 0.65, 'status': 'analyzed_needs_review'}

    def run_research_pipeline(self, website_url, login_credentials):
        """
        Orchestrates the research and initial analysis of grant opportunities.
        """
        print(f"[Orchestrator LOG] Starting run_research_pipeline for URL: {website_url}")

        # 1. Get Organization Profile
        try:
            org_profile = self.data_manager.get_organization_profile()
            if not org_profile:
                print("[Orchestrator ERROR] No organization profile found. Aborting research pipeline.")
                return
            print(f"[Orchestrator LOG] Organization profile '{org_profile.get('name', 'N/A')}' retrieved.")
        except Exception as e:
            print(f"[Orchestrator ERROR] Failed to retrieve organization profile: {e}")
            return

        # 2. Call WebSleuth (Mock)
        extracted_grants = []
        try:
            extracted_grants = self._mock_websleuth_research(website_url, login_credentials)
            print(f"[Orchestrator LOG] _mock_websleuth_research returned {len(extracted_grants)} grants.")
        except Exception as e:
            print(f"[Orchestrator ERROR] Error in _mock_websleuth_research: {e}")
            # extracted_grants remains an empty list, so the loop below won't run.
            # Depending on desired behavior, could return here or ensure pipeline completion log still runs.
            # For now, let it proceed to log completion.

        # 3. Process Each Grant
        for grant_data in extracted_grants:
            grant_id = None
            analysis_result = None
            grant_title_for_log = grant_data.get('grant_title', 'Unknown Title')

            # 3.a Save Grant Opportunity
            try:
                # Ensure all necessary keys are present, with defaults for optional ones if not in grant_data
                # save_grant_opportunity expects: grant_title, funder, deadline, description, eligibility, focus_areas, 
                #                                 raw_research_data='', analysis_notes='', suitability_score=None
                # The mock provides: grant_title, funder, deadline, description, eligibility, focus_areas, raw_research_data
                # So, this should work directly.
                grant_id = self.data_manager.save_grant_opportunity(**grant_data)
                print(f"[Orchestrator LOG] Saved grant '{grant_title_for_log}' with ID: {grant_id}.")
            except Exception as e:
                print(f"[Orchestrator ERROR] Error saving grant '{grant_title_for_log}': {e}")
                # Continue to the next grant if saving fails
                continue 

            # 3.b Analyze Suitability (Mock) - only if saving was successful
            if grant_id is not None:
                try:
                    analysis_result = self._mock_opportunitymatcher_analyze(grant_data, org_profile)
                    print(f"[Orchestrator LOG] Analysis for grant ID {grant_id}: {analysis_result}")
                except Exception as e:
                    print(f"[Orchestrator ERROR] Error analyzing grant ID {grant_id}: {e}")
                    # analysis_result remains None

            # 3.c Update Grant Analysis - only if saving and analysis were successful
            if grant_id is not None and analysis_result is not None:
                try:
                    self.data_manager.update_grant_analysis(
                        grant_id,
                        analysis_result['analysis_notes'],
                        analysis_result['suitability_score'],
                        analysis_result['status']
                    )
                    print(f"[Orchestrator LOG] Updated analysis for grant ID {grant_id}.")
                except Exception as e:
                    print(f"[Orchestrator ERROR] Error updating analysis for grant ID {grant_id}: {e}")
        
        print("[Orchestrator LOG] run_research_pipeline completed.")

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
        # This organization profile will be used by the run_research_pipeline
        print("Saving dummy organization profile using dm_setup...")
        dm_setup.save_organization_profile(
            name="Test Org for Orchestrator Main",
            mission="To test orchestration with a dedicated test DB.",
            projects="Various test projects under main test.",
            needs="More testing with dedicated DB.",
            target_demographics="Test users for main test."
        )
        # org_profile = dm_setup.get_organization_profile() # Retrieved inside run_research_pipeline

        # Call run_research_pipeline
        print("\n--- Running Research Pipeline DEMO ---")
        orchestrator.run_research_pipeline(
            website_url="http://mockgrants.example.com",
            login_credentials={"user": "mock_user", "pass": "mock_pass"}
        )
        print("--- Research Pipeline DEMO Finished ---\n")

        # Verify data (Optional but good for testing)
        print("\n--- Verifying Grants in DB after pipeline ---")
        all_grants_after_pipeline = dm_setup.get_all_grant_opportunities()
        if all_grants_after_pipeline:
            for grant in all_grants_after_pipeline:
                print(f"  Grant: {grant.get('grant_title')}, Status: {grant.get('status')}, Score: {grant.get('suitability_score')}")
        else:
            print("  No grants found in DB after pipeline.")
        print("--- Verification Finished ---\n")

        # The original start_grant_application_flow call can be kept for other testing
        # or removed if this __main__ is now focused on run_research_pipeline.
        # For now, let's retrieve a specific grant (e.g., one of the mock ones)
        # and the org profile again for start_grant_application_flow, if it's still to be tested.

        print("Retrieving org profile and a specific grant for start_grant_application_flow demo...")
        org_profile_for_flow = dm_setup.get_organization_profile() # Re-fetch for clarity
        
        # Attempt to get one of the grants processed by the pipeline
        # Assuming 'Mock Grant Alpha' was processed and saved.
        # We need its ID. The pipeline saves it. Let's try to fetch by title if DataManager had such a method,
        # or just fetch all and pick one. For simplicity, fetch all and try to use the first one.
        
        processed_grants = dm_setup.get_all_grant_opportunities()
        grant_opp_for_flow = None
        if processed_grants:
            # Try to find "Mock Grant Alpha" specifically if it has a known status or details
            for g in processed_grants:
                if g.get('grant_title') == 'Mock Grant Alpha':
                    grant_opp_for_flow = g
                    break
            if not grant_opp_for_flow: # Fallback to first grant if Alpha not found
                grant_opp_for_flow = processed_grants[0]
        
        if org_profile_for_flow and grant_opp_for_flow:
            print(f"Organization profile and grant '{grant_opp_for_flow.get('grant_title')}' loaded for start_grant_application_flow.")
            orchestrator.start_grant_application_flow(org_profile_for_flow, grant_opp_for_flow)
            print("Orchestrator start_grant_application_flow initiated.")
        else:
            print("ERROR: Failed to retrieve org profile or a suitable grant opportunity for start_grant_application_flow demo.")
            if not org_profile_for_flow:
                print("Org profile for flow was None.")
            if not grant_opp_for_flow:
                print("Grant opp for flow was None.")

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
