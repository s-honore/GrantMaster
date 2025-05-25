import sys
import os

# Get the directory of the currently running script (app.py)
# In Streamlit Cloud, this will be something like /mount/src/grantmaster/GrantMaster/
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory of current_script_dir
# This should be /mount/src/grantmaster/, which is the root containing the GrantMaster package
project_root = os.path.dirname(current_script_dir)

# Add project_root to the beginning of sys.path if it's not already there
# This allows Python to find the 'GrantMaster' package
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Existing imports should now work ---
# (The rest of the file content should follow this block)
import streamlit as st
import os
from dotenv import load_dotenv

# Assuming core and agents are subdirectories of GrantMaster where app.py resides,
# or that GrantMaster is in PYTHONPATH.
# If app.py is in GrantMaster/, and core/ and agents/ are also in GrantMaster/
# then these imports should work.
from GrantMaster.core.graph_orchestrator import GraphOrchestrator
from GrantMaster.core.data_manager import DataManager # Though Orchestrator creates its own, it's good for type hints or direct use if ever needed.

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

# --- Initialize GraphOrchestrator ---
if 'graph_orchestrator' not in st.session_state:
    try:
        st.session_state.graph_orchestrator = GraphOrchestrator()
        st.success("GraphOrchestrator initialized successfully!") 
        # print("GraphOrchestrator initialized and stored in session state.") # For debugging
    except Exception as e:
        st.error(f"CRITICAL ERROR: Failed to initialize GraphOrchestrator: {e}")
        # import traceback # For debugging
        # print(f"Critical error initializing GraphOrchestrator: {e}\n{traceback.format_exc()}") # For debugging
        st.stop() # Stop the app if GraphOrchestrator fails to initialize

# Ensure it's available for use
graph_orchestrator = st.session_state.graph_orchestrator
if not graph_orchestrator:
    # This case should ideally be caught by the st.stop() above, but as a fallback:
    st.error("GraphOrchestrator not available. The application cannot continue.")
    st.stop()

# --- Streamlit UI Starts Here ---
st.title("GrantMaster AI")

# Ensure graph_orchestrator is initialized before using it for UI state or actions
if graph_orchestrator and graph_orchestrator.data_manager:
    st.header("Organization Profile")

    # Attempt to load existing profile to pre-fill fields
    # Initialize with empty strings if no profile exists or an error occurs
    profile_data = {}
    try:
        retrieved_profile = graph_orchestrator.data_manager.get_organization_profile()
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
                # Call save_organization_profile using the graph_orchestrator's data_manager
                graph_orchestrator.data_manager.save_organization_profile(
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
    st.info("System is initializing or an error occurred. GraphOrchestrator not available for UI rendering.")
    # print("GraphOrchestrator or its data_manager is None when trying to render UI.") # For debugging

# Add a divider for visual separation before any future sections
st.divider()

# Ensure graph_orchestrator is available before attempting to add more UI
if graph_orchestrator and graph_orchestrator.data_manager:
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
        # This check for graph_orchestrator and data_manager is already done before the header
        # but good to be defensive if this code block were ever moved.
        if graph_orchestrator and graph_orchestrator.data_manager: 
            try:
                org_profile = graph_orchestrator.data_manager.get_organization_profile()
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

        # Ensure org_profile is not None and contains essential data before proceeding
        if org_profile and org_profile.get('name'):
            with st.spinner("Performing research... This may take some time."):
                try:
                    # Access graph_orchestrator from session_state
                    current_graph_orchestrator = st.session_state.graph_orchestrator
                    
                    final_state_dict = current_graph_orchestrator.run_research_workflow(
                        research_website_url=st.session_state.research_url_input, # type: ignore
                        research_login_credentials=login_credentials,
                        organization_profile=org_profile
                    )
                    st.session_state.research_workflow_state = final_state_dict
                    # print("Research workflow finished. Final state stored.") # For debugging
                    
                    # Error message from the workflow itself is displayed here
                    if final_state_dict.get('error_message'):
                        st.error(f"Research workflow completed with an error: {final_state_dict['error_message']}")
                    else:
                        st.success("Research workflow completed successfully!")

                except Exception as e:
                    st.error(f"An unexpected error occurred while running the research workflow: {e}")
                    # Ensure state is set with error info for consistent display
                    st.session_state.research_workflow_state = {
                        "error_message": str(e), 
                        "log_messages": [f"Application error during research workflow: {str(e)}"], 
                        "extracted_grant_opportunities": []
                    }
                    # import traceback # For debugging
                    # print(f"Exception in app.py calling research workflow: {e}\n{traceback.format_exc()}") # For debugging
        # else: # This else was for the org_profile check, which is now implicitly handled by the outer structure
             # The initial error for missing/incomplete org_profile is already handled before this block.
             # st.error("Organization Profile is not set or incomplete. Please save it first.") # This line is moved up

    # --- Display logic (outside button click, uses st.session_state.research_workflow_state) ---
    if 'research_workflow_state' in st.session_state:
        state = st.session_state.research_workflow_state
        
        # Display Error if any from the workflow itself 
        # This is mostly handled by the button logic's st.error, but kept if state is set by other means
        # or if we want to ensure it's always checked when state exists.
        # However, to avoid duplicate messages, we rely on the button click's error reporting.
        # If state.get('error_message') and not already_shown_error_from_button_click:
        #    st.error(f"Workflow Error: {state.get('error_message')}")
    
        # Display Extracted Grant Opportunities
        opportunities = state.get('extracted_grant_opportunities', [])
        if opportunities:
            st.subheader("Research Results: Identified Grant Opportunities")
            for i, grant in enumerate(opportunities): # Ensure grant is a dictionary
                st.markdown(f"---") # Visual separator for each grant
                title = grant.get('grant_title', 'N/A') if isinstance(grant, dict) else 'Invalid grant format'
                st.markdown(f"#### {i+1}. {title}")
                
                if isinstance(grant, dict):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Funder:** {grant.get('funder', 'N/A')}")
                        st.markdown(f"**Deadline:** {grant.get('deadline', 'N/A')}")
                    with col2:
                        st.markdown(f"**Suitability Score:** {grant.get('suitability_score', 'N/A')}/10")
                        st.markdown(f"**Status:** {grant.get('status', 'Pending Analysis')}")
                    
                    if grant.get('analysis_notes'):
                        st.markdown(f"**Rationale/Analysis Notes:** {grant.get('analysis_notes', 'N/A')}")

                    with st.expander("View Full Grant Details"):
                        st.markdown(f"**Description:** {grant.get('description', 'N/A')}")
                        st.markdown(f"**Eligibility:** {grant.get('eligibility_criteria', 'N/A')}")
                        st.markdown(f"**Focus Areas:** {grant.get('focus_areas', 'N/A')}")
                        if grant.get('website_link'):
                            st.markdown(f"**Link:** {grant.get('website_link')}")
                        # Consider if 'raw_research_data' is useful here or too verbose
                        # if grant.get('raw_research_data'):
                        #     st.text_area("Raw Research Data", value=grant.get('raw_research_data'), height=150, disabled=True, key=f"raw_data_state_{grant.get('grant_id', i if isinstance(grant, dict) else str(i))}")
                else:
                    st.warning("An item in extracted opportunities was not in the expected format.")

        elif not state.get('error_message'): # Only show if no error and no opps
            st.info("Research workflow completed, but no grant opportunities were extracted or returned.")

        # Display Log Messages
        with st.expander("View Research Process Log", expanded=False):
            log_messages = state.get('log_messages', [])
            if log_messages:
                for entry in log_messages:
                    st.text(entry) 
            else:
                st.info("No log messages available for this research run.")
        
        # Button to clear the current research results and log
        if st.button("Clear Research Results & Log", key="clear_research_state_button"):
            if 'research_workflow_state' in st.session_state:
                del st.session_state.research_workflow_state
            st.rerun()

    # Add another divider for visual separation before any future sections
    st.divider()

    # Placeholder for "Grant Writing" section if it comes next
    # st.header("Grant Application Writing")
    # ...

    # Ensure graph_orchestrator is available before attempting to add more UI
    # This check is repeated for modularity, though the outer 'if' already covers it.
    # If graph_orchestrator and graph_orchestrator.data_manager: (This line is part of the provided code, let's use it)
    st.header("Grant Application Writing")

    # --- Grant Selection Dropdown ---
    analyzed_grants_for_writing = []
    grant_options = {"Select a grant...": None} # Default option

    try:
        all_grants = graph_orchestrator.data_manager.get_all_grant_opportunities()
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
        # Access graph_orchestrator from session_state
        current_graph_orchestrator = st.session_state.graph_orchestrator # Use a different variable name to avoid conflict with global graph_orchestrator

        # Fetch Organization Profile
        org_profile = None
        try:
            org_profile = current_graph_orchestrator.data_manager.get_organization_profile()
            if not org_profile or not org_profile.get('name'):
                st.error("Organization Profile is not set or is incomplete. Please save it first.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching organization profile: {e}")
            st.stop()

        # Fetch Current Grant Details
        current_grant_details = None
        try:
            current_grant_details = current_graph_orchestrator.data_manager.get_grant_opportunity_by_id(selected_grant_id_for_writing)
            if not current_grant_details:
                st.error(f"Could not retrieve details for grant ID: {selected_grant_id_for_writing}.")
                st.stop()
        except Exception as e:
            st.error(f"Error fetching grant details: {e}")
            st.stop()
        
        # Proceed if all inputs are valid
        if org_profile and current_grant_details: # This check is somewhat redundant due to st.stop() above but good for clarity
            section_name_to_draft_val = st.session_state.section_name_to_draft # Capture value before spinner
            with st.spinner(f"Running writing workflow for section '{section_name_to_draft_val}'..."):
                try:
                    final_state_dict = current_graph_orchestrator.run_writing_workflow(
                        current_grant_details=current_grant_details,
                        organization_profile=org_profile,
                        section_name=section_name_to_draft_val
                    )
                    st.session_state.writing_workflow_state = final_state_dict
                    # print("Writing workflow finished. Final state stored.") # For debugging

                    if final_state_dict.get('error_message'):
                        st.error(f"Writing workflow completed with an error: {final_state_dict['error_message']}")
                    else:
                        st.success("Writing workflow completed successfully!")

                except Exception as e:
                    st.error(f"An unexpected error occurred while running the writing workflow: {e}")
                    st.session_state.writing_workflow_state = {
                        "error_message": str(e), 
                        "log_messages": [f"App.py error: {str(e)}"], 
                        "current_draft_content": "", 
                        "editor_feedback": ""
                    }
                    # import traceback # For debugging
                    # print(f"Exception in app.py calling writing workflow: {e}\n{traceback.format_exc()}") # For debugging

    # --- Display logic (outside button click, uses st.session_state.writing_workflow_state) ---
    if 'writing_workflow_state' in st.session_state:
        state = st.session_state.writing_workflow_state
        
        # Display Draft Content
        # Use section name from state if available, otherwise fallback to the one from input field
        section_name_display = state.get('current_section_name', st.session_state.get('section_name_to_draft', 'N/A'))
        st.subheader(f"Output for Section: {section_name_display}") 
        
        draft_content = state.get('current_draft_content', '')
        st.text_area(
            label="Draft Content",
            value=draft_content if draft_content else "No draft content available from workflow.",
            height=300,
            disabled=True, # Display only
            key="writing_draft_display_new"
        )

        # Display Editor Feedback
        editor_feedback = state.get('editor_feedback', '')
        if editor_feedback: # Only show if feedback exists
            st.markdown("**Editor Feedback:**")
            st.text_area(
                label="Feedback on this Draft", # Label is clear enough without repeating "Editor"
                value=editor_feedback,
                height=100,
                disabled=True,
                key="writing_feedback_display_new"
            )
        # else: (No need to explicitly say "no feedback" if the section isn't shown)

        # Display Log Messages
        # expanded=True makes the log visible by default after running.
        with st.expander("View Writing Process Log", expanded=True): 
            log_messages = state.get('log_messages', [])
            if log_messages:
                for entry in log_messages:
                    st.text(entry) # Or st.markdown for richer text
            else:
                st.info("No log messages available for this writing run.")
        
        # Button to clear the current writing results and log
        if st.button("Clear Writing Results & Log", key="clear_writing_state_button"):
            if 'writing_workflow_state' in st.session_state:
                del st.session_state.writing_workflow_state
            st.rerun()
        
        # Display Error (if any) from the workflow (already handled by button logic, but can be repeated for safety)
        # error_msg_from_state = state.get('error_message')
        # if error_msg_from_state:
        #    st.error(f"Workflow Error (from state): {error_msg_from_state}")

    # Add another divider for visual separation
    st.divider()
else:
    # This else might be redundant if the app stops earlier when orchestrator is not available,
    # but good for safety if more UI sections are added that don't depend on orchestrator.
    st.warning("Grant Research section cannot be displayed as the system is not fully initialized.")
