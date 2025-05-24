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

# Placeholder for future UI sections
# st.header("Research Grant Opportunities")
# ...
