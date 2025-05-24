import streamlit as st
import os
from dotenv import load_dotenv

# Assuming core and agents are subdirectories of GrantMaster where app.py resides,
# or that GrantMaster is in PYTHONPATH.
# If app.py is in GrantMaster/, and core/ and agents/ are also in GrantMaster/
# then these imports should work.
from core.orchestrator import Orchestrator
from core.data_manager import DataManager # Though Orchestrator creates its own, it's good for type hints or direct use if ever needed.
from agents.researcher_agent import WebSleuthAgent # WebSleuthAgent is in researcher_agent.py
from agents.analyst_agent import AnalystAgent
from agents.writer_agent import WriterAgent
from agents.editor_agent import EditorAgent

# --- Page Config (should be the first Streamlit command) ---
st.set_page_config(page_title="GrantMaster AI", layout="wide")

# --- Load Environment Variables ---
# Assuming app.py is in the GrantMaster project root alongside .env
# If .env is in GrantMaster/ and app.py is also in GrantMaster/, this is direct.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env') 
# More robust: if __file__ is not defined (e.g. in some streamlit cloud setups from zip)
# dotenv_path = os.path.join(os.getcwd(), '.env') 

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    # print(f"Loaded .env from {dotenv_path}") # For debugging
else:
    # Fallback for environments where .env might be in CWD or already loaded
    load_dotenv() 
    # print("Attempted to load .env from default location or environment.") # For debugging

# Check for API Key after attempting to load .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("CRITICAL ERROR: OPENAI_API_KEY not found. "
             "Please ensure a .env file with your OPENAI_API_KEY is in the project root directory (GrantMaster/.env). "
             "The application cannot proceed without it.")
    # print("OPENAI_API_KEY not found after .env load attempts.") # For debugging
    st.stop()
# else:
    # print("OPENAI_API_KEY loaded successfully for app.py.") # For debugging


# --- Initialize Orchestrator and Agents ---
# Orchestrator's __init__ handles its own DataManager and OpenAI client setup.
# It also loads .env internally, but loading here ensures Streamlit has early access if needed
# and provides a clear stop point if the key isn't found for the app itself.
orchestrator = None
research_agent = None
analysis_agent = None
writing_agent = None
review_agent = None # For EditorAgent

try:
    # db_name can be configured here if needed, e.g. for different environments
    # orchestrator = Orchestrator(db_name='grantmaster_prod.db') 
    orchestrator = Orchestrator() # Uses default 'grantmaster.db' and loads API key
    
    if not orchestrator.openai_client:
        # This check is important because Orchestrator's __init__ might fail to create openai_client
        # if the API key wasn't found by its internal dotenv loading.
        st.error("CRITICAL ERROR: OpenAI client not initialized in Orchestrator. "
                 "This usually means the OPENAI_API_KEY was not accessible to the Orchestrator. "
                 "Ensure your .env file is correctly placed and formatted.")
        # print("Orchestrator's OpenAI client is None after Orchestrator init.") # For debugging
        st.stop()

    # Initialize agents with the OpenAI client from the Orchestrator
    research_agent = WebSleuthAgent(openai_client=orchestrator.openai_client)
    analysis_agent = AnalystAgent(openai_client=orchestrator.openai_client)
    writing_agent = WriterAgent(openai_client=orchestrator.openai_client)
    review_agent = EditorAgent(openai_client=orchestrator.openai_client)

    # Register agents with the Orchestrator
    orchestrator.register_researcher(research_agent)
    orchestrator.register_analyst(analysis_agent)
    orchestrator.register_writer(writing_agent)
    orchestrator.register_editor(review_agent) # 'review_agent' is the attribute name in Orchestrator

    # print("Orchestrator and all agents initialized and registered successfully.") # For debugging
    # st.success("GrantMaster AI system initialized successfully!") # Optional: early success message

except ValueError as ve: # Catch ValueError from Orchestrator if API key is missing
    st.error(f"Initialization Error: {ve}. Please check your OPENAI_API_KEY setup in the .env file.")
    # print(f"ValueError during Orchestrator/Agent init: {ve}") # For debugging
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during system initialization: {e}")
    # import traceback # For debugging
    # print(f"Unexpected error during Orchestrator/Agent init: {e}
# {traceback.format_exc()}") # For debugging
    st.stop()

# --- Streamlit UI Starts Here ---
st.title("GrantMaster AI")

# Ensure orchestrator is initialized before using it for UI state or actions
if orchestrator and orchestrator.data_manager:
    st.header("Organization Profile")

    # Attempt to load existing profile to pre-fill fields
    # Initialize with empty strings if no profile exists or an error occurs
    profile_data = {}
    try:
        retrieved_profile = orchestrator.data_manager.get_organization_profile()
        if retrieved_profile:
            profile_data = retrieved_profile
            # print("Loaded existing organization profile for UI.") # For debugging
        # else:
            # print("No existing organization profile found, UI will use default values.") # For debugging
    except Exception as e:
        st.warning(f"Could not load existing organization profile: {e}. Using default empty values.")
        # print(f"Error loading organization profile for UI: {e}") # For debugging
        # This might happen if the DB isn't initialized yet or there's a connection issue.

    # Use st.session_state to better manage form state if needed, especially for complex forms.
    # For this simple form, direct use of default_value in widgets is often okay.
    # However, to ensure edits persist if other parts of app cause reruns before saving,
    # session_state is more robust. Let's initialize if not set.

    if 'org_name' not in st.session_state:
        st.session_state.org_name = profile_data.get('name', '')
    if 'org_mission' not in st.session_state:
        st.session_state.org_mission = profile_data.get('mission', '')
    if 'org_projects' not in st.session_state:
        st.session_state.org_projects = profile_data.get('projects', '')
    if 'org_needs' not in st.session_state:
        st.session_state.org_needs = profile_data.get('needs', '')
    if 'org_target_demographics' not in st.session_state:
        st.session_state.org_target_demographics = profile_data.get('target_demographics', '')

    # Create text input/area for each profile field, using session_state for values
    # This allows values to be edited and persist across reruns until "Save Profile" is clicked.
    st.session_state.org_name = st.text_input(
        "Organization Name", 
        value=st.session_state.org_name
    )
    st.session_state.org_mission = st.text_area(
        "Mission Statement", 
        value=st.session_state.org_mission, 
        height=100
    )
    st.session_state.org_projects = st.text_area(
        "Key Projects/Programs", 
        value=st.session_state.org_projects, 
        height=150,
        help="Briefly describe 2-3 key projects or programs."
    )
    st.session_state.org_needs = st.text_area(
        "Current Needs/Challenges", 
        value=st.session_state.org_needs, 
        height=150,
        help="What are the primary needs or challenges your organization is currently facing that grants could address?"
    )
    st.session_state.org_target_demographics = st.text_area(
        "Target Demographics", 
        value=st.session_state.org_target_demographics, 
        height=100,
        help="Describe the primary population(s) your organization serves."
    )

    if st.button("Save Profile"):
        if not st.session_state.org_name.strip(): # Basic validation
            st.error("Organization Name is required to save the profile.")
        else:
            try:
                # Call save_organization_profile using the orchestrator's data_manager
                orchestrator.data_manager.save_organization_profile(
                    name=st.session_state.org_name,
                    mission=st.session_state.org_mission,
                    projects=st.session_state.org_projects,
                    needs=st.session_state.org_needs,
                    target_demographics=st.session_state.org_target_demographics
                )
                st.success("Organization profile saved successfully!")
                # print("Organization profile saved via UI button.") # For debugging
                # Optionally, could clear/update session_state here if needed,
                # but get_organization_profile will reload it on next full interaction.
            except Exception as e:
                st.error(f"Failed to save organization profile: {e}")
                # import traceback # For debugging
                # print(f"Error saving profile from UI: {e}
# {traceback.format_exc()}") # For debugging
else:
    st.info("System is initializing or an error occurred. Orchestrator not available for UI rendering.")
    # print("Orchestrator or its data_manager is None when trying to render UI.") # For debugging

# Add a divider for visual separation before any future sections
st.divider()

# Ensure orchestrator is available before attempting to add more UI
if orchestrator and orchestrator.data_manager:
    st.header("Grant Research")

    # Use unique keys for inputs in different sections if names are similar
    # or ensure session state for these is handled distinctly if needed.
    # For simple text_inputs, unique keys prevent widget ID collisions.
    st.session_state.research_url = st.text_input(
        "Website URL", 
        value=st.session_state.get('research_url', "http://mockgrants.example.com"), # Pre-fill with example
        key="research_url_input" # Explicit key
    )
    st.session_state.research_username = st.text_input(
        "Username (if applicable)", 
        value=st.session_state.get('research_username', "mock_user"), # Pre-fill
        key="research_username_input"
    )
    st.session_state.research_password = st.text_input(
        "Password (if applicable)", 
        type="password", 
        value=st.session_state.get('research_password', "mock_pass"), # Pre-fill
        key="research_password_input"
    )

    # The button and its logic will be detailed in the next subtask (step 2 of the plan).
    # For now, just adding the button placeholder.
    if st.button("Start Research", key="start_research_button"):
        # Validate inputs
        if not st.session_state.research_url.strip():
            st.warning("Please enter a Website URL to start research.")
            st.stop() # Stop execution for this callback if URL is missing

        # Retrieve organization profile
        org_profile = None
        # This check for orchestrator and data_manager is already done before the header
        # but good to be defensive if this code block were ever moved.
        if orchestrator and orchestrator.data_manager: 
            try:
                org_profile = orchestrator.data_manager.get_organization_profile()
            except Exception as e:
                st.error(f"Error fetching organization profile: {e}")
                st.stop()
        
        if not org_profile or not org_profile.get('name'): # Check if profile exists and has a name
            st.error("Organization Profile is not set or is incomplete. Please save a complete Organization Profile first.")
            st.stop()

        # If inputs and profile are valid, proceed with the research pipeline
        st.info(f"Starting research for URL: {st.session_state.research_url}")
        login_credentials = {
            # Ensure these session_state keys match the keys used in st.text_input
            "username": st.session_state.research_username_input, 
            "password": st.session_state.research_password_input
        }

        with st.spinner("Performing research and analysis... This may take a few moments. Please wait."):
            try:
                # Call the orchestrator's research pipeline
                # This is a blocking call. Streamlit will show the spinner until it's done.
                orchestrator.run_research_pipeline(
                    st.session_state.research_url_input, # Use the key from st.text_input
                    login_credentials
                )
                st.session_state.research_pipeline_completed = True # Flag to display results
                st.session_state.research_error = None # Clear any previous error
                
                # ADD THIS MOCK LOG CREATION:
                mock_research_log = [
                    f"Called Orchestrator's run_research_pipeline (actual log to be implemented in Orchestrator).",
                    f"Input URL: {st.session_state.research_url}", # Using research_url as research_url_input might not be in session_state here if not set by text_input yet
                    "Simulated call to WebSleuth agent for website content extraction.",
                    "Simulated processing of extracted content.",
                    "Looping through potential grants identified:",
                    "  - Simulated call to OpportunityMatcher agent for Grant Alpha.",
                    "  - Simulated saving/updating Grant Alpha via DataManager.",
                    "  - Simulated call to OpportunityMatcher agent for Grant Beta.",
                    "  - Simulated saving/updating Grant Beta via DataManager."
                ]
                st.session_state.research_process_log = mock_research_log
                # print("Mock research process log created.") # For debugging
                # print("Research pipeline completed successfully via UI.") # For debugging
                
            except Exception as e:
                st.error(f"An error occurred during the research pipeline: {e}")
                st.session_state.research_pipeline_completed = False
                st.session_state.research_error = str(e)
                # import traceback # For debugging
                # print(f"Error in research pipeline from UI: {e}
# {traceback.format_exc()}") # For debugging

    # The display of results will be handled in the next step/subtask,
    # potentially checking st.session_state.research_pipeline_completed.
    # For now, this subtask focuses on the button click logic and pipeline execution.
    # The st.divider() and placeholder for "Grant Writing" section should remain after this block.

    if 'research_pipeline_completed' in st.session_state:
        if st.session_state.research_pipeline_completed:
            st.success("Research pipeline completed successfully!") # Moved here to be above results
            
            # Fetch and display analyzed grants
            try:
                if orchestrator and orchestrator.data_manager:
                    all_grants = orchestrator.data_manager.get_all_grant_opportunities()
                    # The research_pipeline mock sets status like 'analyzed_strong_match', 'analyzed_needs_review'
                    analyzed_grants = [g for g in all_grants if g.get('status', '').startswith('analyzed_')]

                    if not analyzed_grants and all_grants:
                        st.info("No grants with a status starting 'analyzed_' found. "
                                "Displaying all grants returned by the research pipeline for review (mock data may not have 'analyzed' status yet).")
                        # This fallback is useful if the mock pipeline doesn't perfectly set the 'analyzed' status
                        # or if we want to see all results during development.
                        # In production, might only show strictly 'analyzed_' grants.
                        analyzed_grants_to_display = all_grants
                    elif not analyzed_grants:
                        st.info("No grants were found or analyzed by the research pipeline.")
                        analyzed_grants_to_display = []
                    else:
                        analyzed_grants_to_display = analyzed_grants
                    
                    if analyzed_grants_to_display:
                        st.subheader("Research Results: Identified & Analyzed Grants")
                        for i, grant in enumerate(analyzed_grants_to_display):
                            st.markdown(f"---") # Visual separator for each grant
                            st.markdown(f"#### {i+1}. {grant.get('grant_title', 'N/A')}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Funder:** {grant.get('funder', 'N/A')}")
                                st.markdown(f"**Deadline:** {grant.get('deadline', 'N/A')}")
                            with col2:
                                st.markdown(f"**Suitability Score:** {grant.get('suitability_score', 'N/A')}/10")
                                st.markdown(f"**Status:** {grant.get('status', 'N/A')}")
                            
                            st.markdown(f"**Rationale/Analysis Notes:** {grant.get('analysis_notes', 'N/A')}")

                            with st.expander("View Full Grant Details"):
                                st.markdown(f"**Description:** {grant.get('description', 'N/A')}")
                                st.markdown(f"**Eligibility:** {grant.get('eligibility', 'N/A')}")
                                st.markdown(f"**Focus Areas:** {grant.get('focus_areas', 'N/A')}")
                                if grant.get('link'):
                                    st.markdown(f"**Link:** {grant.get('link')}")
                                if grant.get('raw_research_data'):
                                    st.text_area("Raw Research Data", value=grant.get('raw_research_data'), height=150, disabled=True, key=f"raw_data_{grant.get('id', i)}")
                else:
                    st.warning("Orchestrator or DataManager is not available to fetch grant results.")
            
            except Exception as e:
                st.error(f"Error displaying grant opportunities: {e}")
                # import traceback # For debugging
                # print(f"Error displaying results: {e}
# {traceback.format_exc()}") # For debugging

        elif st.session_state.get('research_error'): # Check if there was an error flagged
            # The error message from the pipeline execution is already displayed by st.error()
            # This block is if we want to add more info or keep the error message persistent
            # st.error(f"Research pipeline failed: {st.session_state.research_error}") # Redundant if already shown
            pass # Error already shown by the button logic's try-except block

        # Clean up session state flags for next run, if desired, or keep them for inspection
        # For example, could add a "Clear Results" button that resets these:
        # if st.button("Clear Research Results"):
        #     st.session_state.research_pipeline_completed = False
        #     st.session_state.research_error = None
        #     st.rerun()

    # --- Display Process Log (Grant Research) ---
    # This should be placed after the results of the research pipeline are displayed.
    if 'research_process_log' in st.session_state and st.session_state.research_process_log:
        with st.expander("Process Log & Reasoning (Grant Research)", expanded=False):
            for log_entry in st.session_state.research_process_log:
                if isinstance(log_entry, tuple) and len(log_entry) == 2:
                    st.markdown(f"**{log_entry[0]}:** {log_entry[1]}")
                elif isinstance(log_entry, dict):
                    st.markdown(f"**{log_entry.get('step','Log')}:** {log_entry.get('detail','N/A')}")
                    if log_entry.get('output_summary'):
                         st.caption(f"Output: {log_entry.get('output_summary')}")
                else:
                    st.text(str(log_entry))
            if st.button("Clear Research Log", key="clear_research_log_button"):
                st.session_state.research_process_log = []
                st.rerun()

    # The main st.divider() for the "Grant Research" section should be after this result display logic.

    # Add another divider for visual separation before any future sections
    st.divider()

    # Placeholder for "Grant Writing" section if it comes next
    # st.header("Grant Application Writing")
    # ...

    # Ensure orchestrator is available before attempting to add more UI
    # This check is repeated for modularity, though the outer 'if' already covers it.
    # If orchestrator and orchestrator.data_manager: (This line is part of the provided code, let's use it)
    st.header("Grant Application Writing")

    # --- Grant Selection Dropdown ---
    analyzed_grants_for_writing = []
    grant_options = {"Select a grant...": None} # Default option

    try:
        all_grants = orchestrator.data_manager.get_all_grant_opportunities()
        if all_grants:
            # Filter for grants that have been through some analysis
            # (status starts with 'analyzed_' or has a suitability_score)
            analyzed_grants_for_writing = [
                g for g in all_grants if g.get('status', '').startswith('analyzed_') or g.get('suitability_score') is not None
            ]
            if analyzed_grants_for_writing:
                for grant in analyzed_grants_for_writing:
                    option_label = f"{grant.get('grant_title', 'Untitled Grant')} (ID: {grant.get('id')}, Score: {grant.get('suitability_score', 'N/A')})"
                    grant_options[option_label] = grant.get('id')
            # else:
                # st.info("No analyzed grants available to select for writing. Please run the research pipeline first or ensure grants are analyzed.")
    except Exception as e:
        st.error(f"Error loading grants for writing selection: {e}")
        # print(f"Error loading grants for writing UI: {e}") # For debugging
    
    # Use session state to hold the currently selected option string to avoid losing it on reruns
    # when other parts of the app might trigger a rerun.
    if 'selected_grant_option_writing' not in st.session_state:
        st.session_state.selected_grant_option_writing = "Select a grant..."

    # Update selected_grant_option_writing when user changes selection in selectbox
    # The actual grant ID will be derived from this option string when needed.
    st.session_state.selected_grant_option_writing = st.selectbox(
        "Choose an Analyzed Grant to Work On:",
        options=list(grant_options.keys()), # Pass list of keys (labels)
        key="writing_grant_select_sb", # Unique key for the selectbox widget
        index=0 # Default to "Select a grant..."
    )
    
    # Derive selected_grant_id based on the selected option label
    # selected_grant_id_for_writing = grant_options.get(st.session_state.selected_grant_option_writing)


    # --- Section Name Input ---
    if 'section_name_to_draft' not in st.session_state:
        st.session_state.section_name_to_draft = "Needs Statement" # Default example

    st.session_state.section_name_to_draft = st.text_input(
        "Section Name to Draft",
        value=st.session_state.section_name_to_draft,
        placeholder="e.g., Needs Statement, Project Description",
        key="writing_section_name_input" # Unique key
    )
    
    # --- Specific Instructions (Optional) ---
    if 'specific_instructions_for_draft' not in st.session_state:
        st.session_state.specific_instructions_for_draft = "" # Default example

    st.session_state.specific_instructions_for_draft = st.text_area(
        "Specific Instructions for this Section (Optional)",
        value=st.session_state.specific_instructions_for_draft,
        placeholder="e.g., Emphasize community impact, target audience is XYZ foundation...",
        height=100,
        key="writing_specific_instructions_input" # Unique key
    )


    # The button and its logic will be detailed in the next subtask (step 2 of the plan).
    # --- Draft Section Button ---
    if st.button("Draft Section", key="draft_section_button"):
        # Derive selected_grant_id from the session state holding the option string
        selected_grant_id_for_writing = grant_options.get(st.session_state.selected_grant_option_writing)

        if not selected_grant_id_for_writing:
            st.warning("Please select a grant to work on.")
            st.stop()
        
        if not st.session_state.section_name_to_draft.strip():
            st.warning("Please enter a section name to draft.")
            st.stop()

        st.info(f"Drafting section: '{st.session_state.section_name_to_draft}' for grant ID: {selected_grant_id_for_writing}")
        with st.spinner(f"Drafting section '{st.session_state.section_name_to_draft}'... This may take a few moments. Please wait."):
            try:
                # Call the orchestrator's writing pipeline
                # For now, this pipeline doesn't return a log. We'll simulate one.
                orchestrator.run_writing_pipeline(
                    selected_grant_id_for_writing,
                    st.session_state.section_name_to_draft,
                    st.session_state.specific_instructions_for_draft # Pass specific instructions
                )
                
                # Simulate process log for now (Phase 1)
                mock_writing_log = [
                    f"Called Orchestrator's run_writing_pipeline (actual log to be implemented in Orchestrator).",
                    f"Input: Grant ID {selected_grant_id_for_writing}, Section: '{st.session_state.section_name_to_draft}'",
                    f"Specific Instructions: '{st.session_state.specific_instructions_for_draft if st.session_state.specific_instructions_for_draft else 'None'}'",
                    "Simulated call to GrantScribe agent for drafting.",
                    "Simulated call to RefineBot agent for initial feedback (if any was part of mock).",
                    "Section draft and any initial feedback saved by DataManager."
                ]
                st.session_state.writing_process_log = mock_writing_log
                
                # Fetch the latest draft to display it
                # The run_writing_pipeline saves the draft, so we fetch it here.
                # The get_section_draft method should ideally get the latest version by default.
                drafted_section_info = orchestrator.data_manager.get_section_draft(
                    grant_opportunity_id=selected_grant_id_for_writing,
                    section_name=st.session_state.section_name_to_draft
                    # version=None # To get the latest
                )
                st.session_state.current_draft_info = drafted_section_info # Store for display
                st.session_state.drafting_completed = True # Flag for display logic
                st.session_state.drafting_error = None

                # print(f"Drafting pipeline completed via UI. Fetched draft: {drafted_section_info is not None}") # For debugging

            except Exception as e:
                st.error(f"An error occurred during the drafting pipeline: {e}")
                st.session_state.drafting_completed = False
                st.session_state.drafting_error = str(e)
                st.session_state.current_draft_info = None
                st.session_state.writing_process_log = [f"Error during drafting: {e}"]
                # import traceback # For debugging
                # print(f"Error in writing pipeline from UI: {e}
# {traceback.format_exc()}") # For debugging

    # The display of the draft and the process log will be handled in the next subtask (Step 3 of Phase 1).
    # The st.divider() for this section should be AFTER the display logic.

    # --- Display Drafted Section and Feedback ---
    if 'drafting_completed' in st.session_state:
        if st.session_state.drafting_completed and st.session_state.get('current_draft_info'):
            draft_info = st.session_state.current_draft_info
            st.subheader(f"Drafted Section: {draft_info.get('section_name', 'N/A')}")
            
            st.markdown("**Draft Content:**")
            st.text_area(
                label="Current Draft", # Label made more generic
                value=draft_info.get('draft_content', 'No content available.'), 
                height=300, 
                disabled=True, # Display only, not for editing here
                key=f"draft_display_{draft_info.get('id', 'new')}" # Unique key
            )
            
            if draft_info.get('feedback'):
                st.markdown("**Feedback on this Draft:**")
                st.text_area(
                    label="Feedback", # Label for feedback
                    value=draft_info.get('feedback'), 
                    height=100, 
                    disabled=True,
                    key=f"feedback_display_{draft_info.get('id', 'new')}" # Unique key
                )
            # else:
                # st.info("No feedback recorded for this draft version yet.")

        elif st.session_state.get('drafting_error'):
            # Error message is already displayed by the button logic's try-except block.
            # This space could be used for more detailed error info if needed.
            pass

    # --- Display Process Log (Grant Writing) ---
    if 'writing_process_log' in st.session_state and st.session_state.writing_process_log:
        with st.expander("Process Log & Reasoning (Grant Writing)", expanded=False):
            for log_entry in st.session_state.writing_process_log:
                if isinstance(log_entry, tuple) and len(log_entry) == 2: # For (step, detail) tuples
                    st.markdown(f"**{log_entry[0]}:** {log_entry[1]}")
                elif isinstance(log_entry, dict): # For more structured logs
                    st.markdown(f"**{log_entry.get('step','Log')}:** {log_entry.get('detail','N/A')}")
                    if log_entry.get('output_summary'):
                         st.caption(f"Output: {log_entry.get('output_summary')}")
                else: # Default to string
                    st.text(str(log_entry))
            # Button to clear the log for this section
            if st.button("Clear Writing Log", key="clear_writing_log_button"):
                st.session_state.writing_process_log = []
                st.session_state.current_draft_info = None # Also clear draft from view
                st.session_state.drafting_completed = False
                st.rerun()

    # Add another divider for visual separation
    st.divider()
else:
    # This else might be redundant if the app stops earlier when orchestrator is not available,
    # but good for safety if more UI sections are added that don't depend on orchestrator.
    st.warning("Grant Research section cannot be displayed as the system is not fully initialized.")
