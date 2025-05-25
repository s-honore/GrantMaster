import functools
import os

from openai import OpenAI
from langgraph.graph import StateGraph, END, START # START might not be used yet, but good to have.

# Project-specific imports
from .graph_state import GrantMasterState
from .data_manager import DataManager
from ..agents.researcher_agent import WebSleuthAgent, node_perform_login, node_research_and_extract
from ..agents.analyst_agent import AnalystAgent, node_analyze_opportunities
from ..agents.writer_agent import WriterAgent, node_draft_section
from ..agents.editor_agent import EditorAgent, node_review_draft

# Consider adding a try-except for dotenv if it's used for API key loading,
# though it's often handled at the application entry point.
# from dotenv import load_dotenv
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
# print("Attempted to load .env file for GraphOrchestrator (if present)")

class GraphOrchestrator:
    def __init__(self):
        # Initialize OpenAI client
        # It's good practice to ensure the API key is actually found.
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("WARNING: OPENAI_API_KEY environment variable not found. OpenAI dependent agents may fail.")
            # Depending on strictness, could raise an error:
            # raise ValueError("OPENAI_API_KEY not found. Please set the environment variable.")
        self.openai_client = OpenAI(api_key=openai_api_key)

        # Initialize DataManager
        self.data_manager = DataManager() # Assumes db_name is default or handled by DataManager

        # Initialize Agents
        self.research_agent = WebSleuthAgent(openai_client=self.openai_client)
        self.analyst_agent = AnalystAgent(openai_client=self.openai_client)
        self.writer_agent = WriterAgent(openai_client=self.openai_client)
        self.editor_agent = EditorAgent(openai_client=self.openai_client)
        print("GraphOrchestrator: All agents and DataManager initialized.")

        # Create StateGraph
        self.workflow = StateGraph(GrantMasterState)
        print("GraphOrchestrator: StateGraph initialized.")

        # Add nodes to the workflow
        # Using functools.partial to bind agent/manager instances to node functions
        
        # Note: node_perform_login was defined without requiring an agent instance.
        # If it were a method of WebSleuthAgent, it would need partial(self.research_agent.node_perform_login_method, ...)
        self.workflow.add_node('login', node_perform_login) 
        
        self.workflow.add_node('research', 
                               functools.partial(node_research_and_extract, agent=self.research_agent))
        
        self.workflow.add_node('analyze_opportunities', 
                               functools.partial(node_analyze_opportunities, 
                                                 agent=self.analyst_agent, 
                                                 data_manager=self.data_manager))
        
        self.workflow.add_node('draft_section', 
                               functools.partial(node_draft_section, agent=self.writer_agent))
        
        self.workflow.add_node('edit_section', # 'edit_section' was used in prompt, but node is node_review_draft
                               functools.partial(node_review_draft, agent=self.editor_agent))

        # Placeholder for save_section_node (to be defined more fully later)
        self.workflow.add_node('save_section', self.save_section_node)
        
        self.workflow.add_node('handle_error', self.handle_error_node)
        print("GraphOrchestrator: All nodes added to the workflow.")

    def handle_error_node(self, state: GrantMasterState) -> dict:
        """
        Handles errors recorded in the state.
        Logs the error and clears it from the state.
        """
        error_message = state.get('error_message', 'No specific error message found in state.')
        current_logs = list(state.get('log_messages', []))
        
        error_log_message = f"GraphOrchestrator: Error handled - {error_message}"
        print(error_log_message)
        current_logs.append(error_log_message)
        
        # Return state updates
        return {
            "log_messages": current_logs,
            "error_message": None # Clear the error message after handling
        }

    def save_section_node(self, state: GrantMasterState) -> dict:
        """
        Placeholder node for saving a drafted section.
        (Actual implementation will be defined based on a future prompt)
        """
        section_name = state.get('current_section_name', 'Unknown Section')
        current_logs = list(state.get('log_messages', []))
        
        save_log_message = f"GraphOrchestrator: save_section_node called for section '{section_name}'. Not yet implemented."
        print(save_log_message)
        current_logs.append(save_log_message)
        
        # No actual state changes related to saving yet
        return {
            "log_messages": current_logs
        }

    # (Future methods like compile_graph, run_graph will be added here)

# (This should be at the very end of the file, after GraphOrchestrator class definition)
if __name__ == '__main__':
    print("Attempting to initialize GraphOrchestrator for smoke test...")
    
    # Attempt to load .env file if OPENAI_API_KEY is not already in environment
    # This is primarily for direct execution of this script.
    # In a full app, .env loading is usually handled at the entry point.
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not found in environment, attempting to load from .env file...")
        try:
            from dotenv import load_dotenv
            # Assuming .env is in GrantMaster project root, and this file is in GrantMaster/core
            dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(dotenv_path):
                load_dotenv(dotenv_path=dotenv_path)
                print(f".env file loaded from {os.path.abspath(dotenv_path)}")
            else:
                print(f".env file not found at {os.path.abspath(dotenv_path)}")
            
            # Check again if API key is now available
            if not os.getenv("OPENAI_API_KEY"):
                print("ERROR: OPENAI_API_KEY still not found after attempting to load .env. Orchestrator may not function correctly.")
            else:
                print("OPENAI_API_KEY found after loading .env.")
        except ImportError:
            print("dotenv package not installed. Skipping .env load attempt. Ensure OPENAI_API_KEY is set in environment.")
        except Exception as e:
            print(f"An error occurred during .env loading: {e}")

    try:
        orchestrator = GraphOrchestrator()
        print("GraphOrchestrator initialized successfully.")
        # Future steps would involve compiling and running the graph here for testing.
        # For now, just initialization is tested by this block.
    except Exception as e:
        print(f"Failed to initialize GraphOrchestrator: {e}")
        import traceback
        traceback.print_exc()
