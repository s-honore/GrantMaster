from data_manager import DataManager # Assumes data_manager.py is in the same directory (core)

class Orchestrator:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        # Initialize other agents or components here later
        print("Orchestrator initialized.")

    def start_grant_application_flow(self, organization_profile, grant_opportunity):
        # Placeholder for workflow logic
        print(f"Starting grant application flow for grant ID: {grant_opportunity.get('id')} - {grant_opportunity.get('grant_title')}")
        print(f"Organization: {organization_profile.get('name')}")
        # Example: identify sections needed based on grant_opportunity details
        # Example: coordinate with an 'AnalysisAgent' or 'WritingAgent'
        pass

if __name__ == '__main__':
    # This block is for example usage and basic testing of the Orchestrator.
    # It should use a distinct test database to avoid conflicts with main data.
    
    db_name_for_orchestrator_test = 'test_orchestrator.db'
    dm = None  # Initialize dm to None for cleanup in finally block

    try:
        print(f"Setting up DataManager with '{db_name_for_orchestrator_test}' for Orchestrator testing...")
        dm = DataManager(db_name=db_name_for_orchestrator_test)

        # Populate with dummy data for testing the flow
        print("Saving dummy organization profile...")
        dm.save_organization_profile(
            name="Test Org for Orchestrator",
            mission="To test orchestration.",
            projects="Various test projects.",
            needs="More testing.",
            target_demographics="Test users."
        )
        org_profile = dm.get_organization_profile()

        print("Saving dummy grant opportunity...")
        grant_id = dm.save_grant_opportunity(
            grant_title="Orchestrator Test Grant",
            funder="Test Funder",
            deadline="2025-01-01",
            description="A grant to test the orchestrator.",
            eligibility="All testers.",
            focus_areas="Testing, Orchestration"
        )
        grant_opp = dm.get_grant_opportunity(grant_id)

        if org_profile and grant_opp:
            print("Organization profile and grant opportunity loaded for testing.")
            orchestrator = Orchestrator(data_manager=dm)
            orchestrator.start_grant_application_flow(org_profile, grant_opp)
            print("Orchestrator flow initiated.")
        else:
            print("ERROR: Failed to retrieve organization profile or grant opportunity for testing.")
            if not org_profile:
                print("Organization profile was None.")
            if not grant_opp:
                print(f"Grant opportunity was None (tried to fetch ID: {grant_id}).")

    except Exception as e:
        print(f"An error occurred during Orchestrator testing: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up the test database
        import os
        if dm:
            print(f"Closing connection to '{db_name_for_orchestrator_test}'...")
            dm.close_connection()
        
        if os.path.exists(db_name_for_orchestrator_test):
            print(f"Removing test database '{db_name_for_orchestrator_test}'...")
            os.remove(db_name_for_orchestrator_test)
            print(f"Test database '{db_name_for_orchestrator_test}' removed.")
        else:
            print(f"Test database '{db_name_for_orchestrator_test}' not found, no need to remove.")
