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

    def _mock_grantscribe_draft(self, grant_details, org_profile, section_name):
        """
        Internal mock method to simulate draft generation by a GrantScribe agent.
        """
        grant_title = grant_details.get('grant_title', 'Unknown Grant')
        org_name = org_profile.get('name', 'Unknown Org')
        print(f"[Orchestrator LOG] Called _mock_grantscribe_draft for section '{section_name}' of grant '{grant_title}'")
        return f"This is a generated draft for section '{section_name}' regarding grant '{grant_title}', considering the organization '{org_name}'."

    def _mock_refinebot_review(self, draft_content):
        """
        Internal mock method to simulate draft review by a RefineBot agent.
        """
        print(f"[Orchestrator LOG] Called _mock_refinebot_review for draft starting with: '{draft_content[:75]}...'")
        # Attempt to extract section name if it's in the format 'section 'section_name''
        try:
            extracted_section_name = draft_content.split("'")[1] if "'" in draft_content else "the specified section"
        except IndexError:
            extracted_section_name = "the specified section (could not extract)"
        return f"Mock RefineBot feedback: The draft looks promising. Consider elaborating on impact metrics. The section on '{extracted_section_name}' is a good start."

    def run_research_pipeline(self, website_url, login_credentials):
        """
        Orchestrates the research and initial analysis of grant opportunities.
        Returns a structured process log.
        """
        process_log = []
        print(f"[Orchestrator LOG] Starting run_research_pipeline for URL: {website_url}")
        process_log.append({'step': "Pipeline Start", 'detail': f"Research pipeline initiated for URL: {website_url}."})

        # 1. Get Organization Profile
        org_profile = None
        try:
            process_log.append({'step': "Organization Profile Retrieval", 'detail': "Attempting to fetch profile."})
            org_profile = self.data_manager.get_organization_profile()
            if not org_profile:
                msg = "No organization profile found. Aborting research pipeline."
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': "Organization Profile Retrieval", 'detail': msg, 'status': 'Error'})
                return process_log
            
            org_name = org_profile.get('name', 'N/A')
            print(f"[Orchestrator LOG] Organization profile '{org_name}' retrieved.")
            process_log.append({'step': "Organization Profile Retrieval", 
                                'detail': f"Organization profile '{org_name}' retrieved successfully.", 'status': 'Success'})
        except Exception as e:
            msg = f"Failed to retrieve organization profile: {e}"
            print(f"[Orchestrator ERROR] {msg}")
            process_log.append({'step': "Organization Profile Retrieval", 'detail': msg, 'status': 'Error'})
            return process_log

        # 2. Call WebSleuth (Mock)
        extracted_grants = []
        process_log.append({'step': "Web Research (Mock)", 'detail': f"Calling _mock_websleuth_research for URL: {website_url}."})
        try:
            extracted_grants = self._mock_websleuth_research(website_url, login_credentials)
            print(f"[Orchestrator LOG] _mock_websleuth_research returned {len(extracted_grants)} grants.")
            process_log.append({'step': "Web Research (Mock)", 
                                'detail': f"_mock_websleuth_research executed.",
                                'output_summary': f"Returned {len(extracted_grants)} grant(s).",
                                'status': 'Success'})
        except Exception as e:
            msg = f"Error in _mock_websleuth_research: {e}"
            print(f"[Orchestrator ERROR] {msg}")
            process_log.append({'step': "Web Research (Mock)", 'detail': msg, 'status': 'Error'})
            # Continue to log completion, extracted_grants will be empty.

        # 3. Process Each Grant
        if not extracted_grants:
             process_log.append({'step': "Grant Processing", 'detail': "No grants extracted from web research to process."})
        else:
            process_log.append({'step': "Grant Processing", 'detail': f"Starting processing for {len(extracted_grants)} extracted grant(s)."})

        for i, grant_data in enumerate(extracted_grants):
            grant_id = None
            analysis_result = None
            grant_title_for_log = grant_data.get('grant_title', f'Unknown Title (Grant {i+1})')
            process_log.append({'step': f"Processing Grant: {grant_title_for_log}", 'detail': "Starting individual grant processing."})

            # 3.a Save Grant Opportunity
            try:
                grant_id = self.data_manager.save_grant_opportunity(**grant_data)
                print(f"[Orchestrator LOG] Saved grant '{grant_title_for_log}' with ID: {grant_id}.")
                process_log.append({'step': f"Save Grant: {grant_title_for_log}", 
                                    'detail': f"Saved grant with ID: {grant_id}.", 
                                    'status': 'Success',
                                    'grant_id': grant_id})
            except Exception as e:
                msg = f"Error saving grant '{grant_title_for_log}': {e}"
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': f"Save Grant: {grant_title_for_log}", 'detail': msg, 'status': 'Error'})
                continue # Continue to the next grant if saving fails

            # 3.b Analyze Suitability (Mock)
            if grant_id is not None:
                process_log.append({'step': f"Analyze Suitability: {grant_title_for_log}", 
                                    'detail': f"Calling _mock_opportunitymatcher_analyze for grant ID {grant_id}."})
                try:
                    analysis_result = self._mock_opportunitymatcher_analyze(grant_data, org_profile)
                    print(f"[Orchestrator LOG] Analysis for grant ID {grant_id}: {analysis_result}")
                    process_log.append({'step': f"Analyze Suitability: {grant_title_for_log}", 
                                        'detail': "Analysis complete.", 
                                        'output_summary': f"Score: {analysis_result.get('suitability_score')}, Status: {analysis_result.get('status')}",
                                        'status': 'Success'})
                except Exception as e:
                    msg = f"Error analyzing grant ID {grant_id}: {e}"
                    print(f"[Orchestrator ERROR] {msg}")
                    process_log.append({'step': f"Analyze Suitability: {grant_title_for_log}", 'detail': msg, 'status': 'Error'})
                    # analysis_result remains None

            # 3.c Update Grant Analysis
            if grant_id is not None and analysis_result is not None:
                process_log.append({'step': f"Update Grant Analysis: {grant_title_for_log}", 
                                    'detail': f"Attempting to update analysis in DB for grant ID {grant_id}."})
                try:
                    self.data_manager.update_grant_analysis(
                        grant_id,
                        analysis_result['analysis_notes'],
                        analysis_result['suitability_score'],
                        analysis_result['status']
                    )
                    print(f"[Orchestrator LOG] Updated analysis for grant ID {grant_id}.")
                    process_log.append({'step': f"Update Grant Analysis: {grant_title_for_log}", 
                                        'detail': "Successfully updated analysis in database.", 
                                        'status': 'Success'})
                except Exception as e:
                    msg = f"Error updating analysis for grant ID {grant_id}: {e}"
                    print(f"[Orchestrator ERROR] {msg}")
                    process_log.append({'step': f"Update Grant Analysis: {grant_title_for_log}", 'detail': msg, 'status': 'Error'})
            elif grant_id is not None and analysis_result is None:
                 process_log.append({'step': f"Update Grant Analysis: {grant_title_for_log}", 
                                    'detail': "Skipped updating analysis due to prior analysis error.", 'status': 'Skipped'})
        
        print("[Orchestrator LOG] run_research_pipeline completed.")
        process_log.append({'step': "Pipeline End", 'detail': "Research pipeline finished."})
        return process_log

    def run_writing_pipeline(self, grant_id, section_name, specific_instructions=''):
        """
        Orchestrates the writing and review pipeline for a specific grant section.
        Returns a structured process log.
        """
        process_log = []
        log_msg_start = f"Starting run_writing_pipeline for grant ID: {grant_id}, section: '{section_name}'"
        print(f"[Orchestrator LOG] {log_msg_start}")
        process_log.append({'step': "Pipeline Start", 'detail': log_msg_start, 'grant_id': grant_id, 'section_name': section_name})

        if specific_instructions:
            process_log.append({'step': "Input Parameters", 'detail': f"Specific instructions provided: '{specific_instructions}'"})
        else:
            process_log.append({'step': "Input Parameters", 'detail': "No specific instructions provided."})

        # 1. Get Grant Details
        grant_details = None
        process_log.append({'step': "Grant Details Retrieval", 'detail': f"Attempting to fetch grant ID: {grant_id}."})
        try:
            grant_details = self.data_manager.get_grant_opportunity(grant_id)
            if not grant_details:
                msg = f"Grant with ID {grant_id} not found. Aborting writing pipeline."
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': "Grant Details Retrieval", 'detail': msg, 'status': 'Error'})
                return process_log
            
            grant_title = grant_details.get('grant_title', 'N/A')
            print(f"[Orchestrator LOG] Retrieved grant details for '{grant_title}'.")
            process_log.append({'step': "Grant Details Retrieval", 
                                'detail': f"Retrieved grant details for '{grant_title}'.", 
                                'status': 'Success'})
        except Exception as e:
            msg = f"Failed to retrieve grant details for ID {grant_id}: {e}"
            print(f"[Orchestrator ERROR] {msg}")
            process_log.append({'step': "Grant Details Retrieval", 'detail': msg, 'status': 'Error'})
            return process_log

        # 2. Get Organization Profile
        org_profile = None
        process_log.append({'step': "Organization Profile Retrieval", 'detail': "Attempting to fetch organization profile."})
        try:
            org_profile = self.data_manager.get_organization_profile()
            if not org_profile:
                msg = f"Organization profile not found. Aborting writing pipeline."
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': "Organization Profile Retrieval", 'detail': msg, 'status': 'Error'})
                return process_log
            
            org_name = org_profile.get('name', 'N/A')
            print(f"[Orchestrator LOG] Retrieved organization profile: '{org_name}'.")
            process_log.append({'step': "Organization Profile Retrieval", 
                                'detail': f"Retrieved organization profile: '{org_name}'.", 
                                'status': 'Success'})
        except Exception as e:
            msg = f"Failed to retrieve organization profile: {e}"
            print(f"[Orchestrator ERROR] {msg}")
            process_log.append({'step': "Organization Profile Retrieval", 'detail': msg, 'status': 'Error'})
            return process_log

        # 3. Draft Section (Mock)
        draft_content = None
        log_draft_step = f"Drafting Section (Mock GrantScribe): {section_name}"
        process_log.append({'step': log_draft_step, 
                            'detail': f"Calling _mock_grantscribe_draft. Instructions: '{specific_instructions if specific_instructions else 'None'}'"})
        try:
            # Note: _mock_grantscribe_draft currently doesn't use specific_instructions, but we log that it was passed.
            draft_content = self._mock_grantscribe_draft(grant_details, org_profile, section_name)
            print(f"[Orchestrator LOG] Draft for section '{section_name}': '{draft_content[:100]}...'")
            process_log.append({'step': log_draft_step, 
                                'detail': "Draft content generated.", 
                                'output_summary': f"Draft length: {len(draft_content)} chars.",
                                'status': 'Success'})
        except Exception as e:
            msg = f"Error in _mock_grantscribe_draft for section '{section_name}': {e}"
            print(f"[Orchestrator ERROR] {msg}")
            process_log.append({'step': log_draft_step, 'detail': msg, 'status': 'Error'})
            # draft_content remains None, proceed to save what we have (which might be nothing) or log pipeline end.

        # 4. Review Draft (Mock)
        feedback = None
        log_review_step = f"Reviewing Draft (Mock RefineBot): {section_name}"
        if draft_content is not None:
            process_log.append({'step': log_review_step, 'detail': "Calling _mock_refinebot_review."})
            try:
                feedback = self._mock_refinebot_review(draft_content)
                print(f"[Orchestrator LOG] Feedback for section '{section_name}': '{feedback}'")
                process_log.append({'step': log_review_step, 
                                    'detail': "Feedback generated.",
                                    'output_summary': f"Feedback length: {len(feedback)} chars.",
                                    'status': 'Success'})
            except Exception as e:
                msg = f"Error in _mock_refinebot_review for section '{section_name}': {e}"
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': log_review_step, 'detail': msg, 'status': 'Error'})
                # feedback remains None
        else:
            feedback = "No draft content to review due to prior error." # As per instruction
            print(f"[Orchestrator LOG] Section '{section_name}': {feedback}")
            process_log.append({'step': log_review_step, 'detail': feedback, 'status': 'Skipped'})

        # 5. Save Section Draft
        log_save_step = f"Saving Section Draft: {section_name}"
        if draft_content is not None:
            process_log.append({'step': log_save_step, 'detail': f"Attempting to save draft for grant ID {grant_id}."})
            try:
                self.data_manager.save_section_draft(
                    grant_opportunity_id=grant_id,
                    section_name=section_name,
                    draft_content=draft_content,
                    version=1,  # Assuming version 1 for this initial draft
                    feedback=feedback if feedback else '' # Ensure feedback is not None
                )
                print(f"[Orchestrator LOG] Saved draft for section '{section_name}' of grant ID {grant_id} with feedback.")
                process_log.append({'step': log_save_step, 
                                    'detail': "Successfully saved draft and feedback to database.", 
                                    'status': 'Success'})
            except Exception as e:
                msg = f"Error saving draft for section '{section_name}', grant ID {grant_id}: {e}"
                print(f"[Orchestrator ERROR] {msg}")
                process_log.append({'step': log_save_step, 'detail': msg, 'status': 'Error'})
        else:
            process_log.append({'step': log_save_step, 
                                'detail': "Skipped saving draft as no content was generated due to prior error.", 
                                'status': 'Skipped'})
        
        print(f"[Orchestrator LOG] run_writing_pipeline for grant ID {grant_id}, section '{section_name}' completed.")
        process_log.append({'step': "Pipeline End", 'detail': "Writing pipeline finished."})
        return process_log

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

        # --- Preparing for Writing Pipeline DEMO ---
        print("\n--- Preparing for Writing Pipeline DEMO ---")
        test_grant_id_for_writing = None
        # all_grants_after_pipeline is already available from the verification step above
        if all_grants_after_pipeline:
            test_grant_id_for_writing = all_grants_after_pipeline[0]['id'] # Get ID of the first grant
            print(f"Using grant ID {test_grant_id_for_writing} ('{all_grants_after_pipeline[0]['grant_title']}') for writing pipeline demo.")
        else:
            print("No grants found from research pipeline to use for writing pipeline demo. Skipping.")

        if test_grant_id_for_writing:
            print("\n--- Running Writing Pipeline DEMO ---")
            orchestrator.run_writing_pipeline(
                grant_id=test_grant_id_for_writing,
                section_name="Project Narrative" # Example section name
            )
            print("--- Writing Pipeline DEMO Finished ---\n")

            # Optional: Verify section draft was saved
            print("\n--- Verifying Section Draft in DB after writing pipeline ---")
            # Use dm_setup to check the database directly
            section_drafts = dm_setup.get_all_sections_for_grant(test_grant_id_for_writing)
            if section_drafts:
                found_draft = False
                for draft in section_drafts:
                    if draft['section_name'] == "Project Narrative":
                        print(f"  Found draft for section '{draft['section_name']}': '{draft['draft_content'][:50]}...' (v{draft['version']})")
                        print(f"    Feedback: {draft['feedback']}")
                        found_draft = True
                        break
                if not found_draft:
                    print(f"  Draft for section 'Project Narrative' not found for grant ID {test_grant_id_for_writing}.")
            else:
                print(f"  No sections found for grant ID {test_grant_id_for_writing}.")
            print("--- Section Verification Finished ---\n")
        
        # The original start_grant_application_flow call can be removed or adapted.
        # For this subtask, focusing on run_writing_pipeline, so I'll comment it out.
        # print("Retrieving org profile and a specific grant for start_grant_application_flow demo...")
        # org_profile_for_flow = dm_setup.get_organization_profile() 
        # processed_grants = dm_setup.get_all_grant_opportunities()
        # grant_opp_for_flow = None
        # if processed_grants:
        #     for g in processed_grants:
        #         if g.get('grant_title') == 'Mock Grant Alpha':
        #             grant_opp_for_flow = g
        #             break
        #     if not grant_opp_for_flow: 
        #         grant_opp_for_flow = processed_grants[0]
        # 
        # if org_profile_for_flow and grant_opp_for_flow:
        #     print(f"Organization profile and grant '{grant_opp_for_flow.get('grant_title')}' loaded for start_grant_application_flow.")
        #     orchestrator.start_grant_application_flow(org_profile_for_flow, grant_opp_for_flow)
        #     print("Orchestrator start_grant_application_flow initiated.")
        # else:
        #     print("ERROR: Failed to retrieve org profile or a suitable grant opportunity for start_grant_application_flow demo.")

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
