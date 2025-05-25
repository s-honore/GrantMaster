import functools
import os

from openai import OpenAI
from langgraph.graph import StateGraph, END, START # START might not be used yet, but good to have.

# Project-specific imports
from GrantMaster.core.graph_state import GrantMasterState
from GrantMaster.core.data_manager import DataManager
from GrantMaster.agents.researcher_agent import WebSleuthAgent, node_perform_login, node_research_and_extract
from GrantMaster.agents.analyst_agent import AnalystAgent, node_analyze_opportunities
from GrantMaster.agents.writer_agent import WriterAgent, node_draft_section
from GrantMaster.agents.editor_agent import EditorAgent, node_review_draft

# Consider adding a try-except for dotenv if it's used for API key loading,
# though it's often handled at the application entry point.
# from dotenv import load_dotenv
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
# print("Attempted to load .env file for GraphOrchestrator (if present)")

class GraphOrchestrator:
    def __init__(self, api_key: str): # Modified signature
        self.api_key = api_key # Store api_key

        # Initialize OpenAI client with the passed api_key
        # This client might still be useful if some components expect a client instance
        # rather than an API key directly, or for direct calls if needed.
        self.openai_client = OpenAI(api_key=self.api_key)

        # Initialize DataManager
        self.data_manager = DataManager() # Assumes db_name is default or handled by DataManager

        # Define model names (these could be made configurable or passed in later)
        # Using default values as an example, consistent with some agent defaults.
        research_model_name = "gpt-3.5-turbo" 
        analyst_model_name = "gpt-3.5-turbo"
        writer_model_name = "gpt-3.5-turbo"
        editor_model_name = "gpt-3.5-turbo"

        # Initialize Agents - passing api_key directly as per subtask instructions.
        # This assumes Agent constructors will be updated to accept api_key directly.
        # The variable `self.research_agent` was previously used for WebSleuthAgent.
        self.research_agent = WebSleuthAgent(api_key=self.api_key, model=research_model_name)
        self.analyst_agent = AnalystAgent(api_key=self.api_key, model_name=analyst_model_name)
        self.writer_agent = WriterAgent(api_key=self.api_key, model_name=writer_model_name)
        self.editor_agent = EditorAgent(api_key=self.api_key, model_name=editor_model_name)
        # Note: The prompt did not require changing ResearcherAgent if it exists and differs from WebSleuthAgent.
        # The current code only has self.research_agent assigned to WebSleuthAgent.
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

        # Define the entry point for the graph
        self.workflow.set_entry_point('login')
        print("GraphOrchestrator: Entry point set to 'login'.")

        # Conditional edges after login
        self.workflow.add_conditional_edges(
            'login',
            lambda state: 'research' if state.get('authenticated_driver_session') else 'handle_error',
            {
                'research': 'research',
                'handle_error': 'handle_error'
            }
        )
        print("GraphOrchestrator: Conditional edges added for 'login' node.")

        # Conditional edges after research
        self.workflow.add_conditional_edges(
            'research',
            lambda state: 'analyze_opportunities' if not state.get('error_message') else 'handle_error',
            {
                'analyze_opportunities': 'analyze_opportunities',
                'handle_error': 'handle_error'
            }
        )
        print("GraphOrchestrator: Conditional edges added for 'research' node.")

        # Conditional edges after analyze_opportunities
        # Ensure END is imported: from langgraph.graph import END
        self.workflow.add_conditional_edges(
            'analyze_opportunities',
            lambda state: END if not state.get('error_message') else 'handle_error',
            {
                END: END,
                'handle_error': 'handle_error'
            }
        )
        print("GraphOrchestrator: Conditional edges added for 'analyze_opportunities' node.")

        # Edge from handle_error to END
        self.workflow.add_edge('handle_error', END)
        print("GraphOrchestrator: Edge added from 'handle_error' to END.")

        # Graph is defined but not yet compiled here. Compilation will be a separate step.
        print("GraphOrchestrator: Research pipeline edges defined.")

        # Define edges for the writing/editing loop
        self.workflow.add_edge('draft_section', 'edit_section')
        print("GraphOrchestrator: Edge added from 'draft_section' to 'edit_section'.")

        self.workflow.add_conditional_edges(
            'edit_section',
            self.should_redraft_or_save, # Method defined in the same class
            {
                'draft_section_again': 'draft_section', # Route back to draft_section
                'save_section': 'save_section',
                'handle_error': 'handle_error'
            }
        )
        print("GraphOrchestrator: Conditional edges added for 'edit_section' node using 'should_redraft_or_save'.")

        self.workflow.add_edge('save_section', END) # Ensure END is imported
        print("GraphOrchestrator: Edge added from 'save_section' to END.")
        
        # Compile the graph
        try:
            self.app = self.workflow.compile()
            print("GraphOrchestrator: Workflow compiled successfully.")
        except Exception as e:
            print(f"GraphOrchestrator: CRITICAL - Workflow compilation failed: {e}")
            # import traceback
            # print(traceback.format_exc())
            self.app = None # Ensure self.app is None if compilation fails
            # Depending on desired behavior, could re-raise the exception
            # raise

    def run_research_workflow(self, research_website_url: str, research_login_credentials: dict, organization_profile: dict) -> GrantMasterState:
        """
        Runs the research workflow with the given parameters.
        Initializes the state and invokes the compiled graph.
        """
        initial_state = GrantMasterState(
            organization_profile=organization_profile,
            research_website_url=research_website_url,
            research_login_credentials=research_login_credentials,
            authenticated_driver_session=None,
            extracted_grant_opportunities=[], # Default to empty list
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0, # Initialized to 0
            error_message=None,
            log_messages=['Research workflow started.'], # Initial log message
            next_node_to_call=None
        )

        if not self.app:
            # This check is crucial if graph compilation can fail.
            # Log an error and potentially return an error state or raise exception.
            error_msg = "GraphOrchestrator: Workflow application (self.app) is not compiled or available. Cannot run workflow."
            print(error_msg)
            # Update initial_state to reflect this critical error before returning
            initial_state['error_message'] = error_msg
            initial_state['log_messages'].append(error_msg)
            return initial_state

        print(f"GraphOrchestrator: Invoking research workflow with initial state: {initial_state}")
        
        # Invoke the graph
        # The type checker might complain about final_state_dict not being GrantMasterState directly,
        # but LangGraph's invoke typically returns the state dict.
        final_state_dict = self.app.invoke(initial_state)
        
        print(f"GraphOrchestrator: Research workflow finished. Final state: {final_state_dict}")
        return final_state_dict

    def run_writing_workflow(self, current_grant_details: dict, organization_profile: dict, section_name: str) -> GrantMasterState:
        """
        Runs the writing workflow with the given parameters.
        Initializes the state and invokes the compiled graph.
        """
        initial_state = GrantMasterState(
            organization_profile=organization_profile,
            research_website_url=None, # Not used in writing workflow
            research_login_credentials=None, # Not used in writing workflow
            authenticated_driver_session=None, # Not used directly by writing, but part of state
            extracted_grant_opportunities=[], # Default to empty list
            current_grant_opportunity_id=current_grant_details.get("id") if current_grant_details else None, # Extract if available
            current_grant_details=current_grant_details,
            analysis_results=None, # Typically generated before writing
            current_section_name=section_name,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0, # Initialized to 0 for a new writing task
            error_message=None,
            log_messages=[f'Writing workflow started for section: {section_name}.'], # Initial log
            next_node_to_call='draft_section' # Explicitly set the starting node for writing
        )

        if not self.app:
            error_msg = "GraphOrchestrator: Workflow application (self.app) is not compiled or available. Cannot run writing workflow."
            print(error_msg)
            initial_state['error_message'] = error_msg
            initial_state['log_messages'].append(error_msg)
            return initial_state

        print(f"GraphOrchestrator: Invoking writing workflow with initial state: {initial_state}")
        
        final_state_dict = self.app.invoke(initial_state)
        
        print(f"GraphOrchestrator: Writing workflow finished. Final state: {final_state_dict}")
        return final_state_dict

    def handle_error_node(self, state: GrantMasterState) -> dict:
        """
        Handles errors recorded in the state by logging them.
        The error_message remains in the state for potential inspection
        before the graph typically transitions to END.
        """
        error_message_from_state = state.get('error_message', 'No specific error message provided in state.')
        current_logs = list(state.get('log_messages', []))
        
        # Log the error prominently (e.g., to console)
        print(f"GraphOrchestrator: ERROR ENCOUNTERED - {error_message_from_state}")
        
        # Add the error to the log_messages list in the state
        log_entry = f"ERROR ENCOUNTERED IN GRAPH: {error_message_from_state}"
        current_logs.append(log_entry)
        
        # Return updates: only log_messages is modified.
        # error_message from input state is implicitly passed through if not set here.
        return {
            "log_messages": current_logs
            # By not returning 'error_message': None, we keep the original error in the state.
        }

    def save_section_node(self, state: GrantMasterState) -> dict:
        """
        Saves the current draft section to the database using DataManager.
        Retrieves necessary details from the state.
        """
        current_logs = list(state.get('log_messages', []))
        node_error_message = None

        grant_opp_id = state.get("current_grant_opportunity_id")
        section_name = state.get("current_section_name")
        draft_content = state.get("current_draft_content")
        iteration_count = state.get("iteration_count", 1) # Default to 1 if not set
        editor_feedback = state.get("editor_feedback", "") # Default to empty string

        # Prerequisite checks
        if not grant_opp_id:
            node_error_message = "Save section failed: Missing current_grant_opportunity_id in state."
        elif not section_name:
            node_error_message = "Save section failed: Missing current_section_name in state."
        elif not draft_content: # Assuming empty draft should not be saved
            node_error_message = "Save section failed: Missing or empty current_draft_content in state."

        if node_error_message:
            print(f"GraphOrchestrator.save_section_node: {node_error_message}")
            current_logs.append(node_error_message)
            return {
                "log_messages": current_logs,
                "error_message": node_error_message
            }

        try:
            print(f"GraphOrchestrator.save_section_node: Attempting to save section '{section_name}' for grant ID {grant_opp_id}, version {iteration_count}.")
            db_id = self.data_manager.save_section_draft(
                grant_opportunity_id=grant_opp_id,
                section_name=section_name,
                draft_content=draft_content,
                version=iteration_count,
                feedback=editor_feedback
            )

            if db_id is not None:
                success_log = f"Section '{section_name}' (Version {iteration_count}) saved to database with ID: {db_id} for grant ID {grant_opp_id}."
                print(success_log)
                current_logs.append(success_log)
                # Optionally, clear draft/feedback from state after successful save:
                # return {
                #     "log_messages": current_logs,
                #     "error_message": None,
                #     "current_draft_content": "", # Or None
                #     "editor_feedback": ""       # Or None
                # }
            else:
                node_error_message = f"Failed to save section '{section_name}' (Version {iteration_count}) to database for grant ID {grant_opp_id}. DataManager returned None."
                print(f"GraphOrchestrator.save_section_node: {node_error_message}")
                current_logs.append(node_error_message)
        
        except Exception as e:
            node_error_message = f"Unexpected error in save_section_node for section '{section_name}': {str(e)}"
            print(f"GraphOrchestrator.save_section_node: {node_error_message}")
            current_logs.append(node_error_message)
            # import traceback # For more detailed debugging if needed
            # current_logs.append(traceback.format_exc())


        return {
            "log_messages": current_logs,
            "error_message": node_error_message # Will be None if successful
        }

    # (Future methods like compile_graph, run_graph will be added here)

    def should_redraft_or_save(self, state: GrantMasterState) -> str:
        """
        Determines the next step after an editor's review based on feedback,
        iteration count, and error state.
        """
        print("GraphOrchestrator.should_redraft_or_save: Evaluating state...")
        error_message = state.get('error_message')
        editor_feedback = state.get('editor_feedback', '').lower() # Default to empty string, convert to lower
        iteration_count = state.get('iteration_count', 0) # Default to 0

        # Max iterations for the writing loop (could be made configurable)
        max_iterations = 3 

        if error_message:
            print(f"  Decision: Error found ('{error_message}') -> routing to handle_error")
            return 'handle_error'

        if iteration_count >= max_iterations:
            print(f"  Decision: Max iterations ({max_iterations}) reached -> routing to save_section")
            return 'save_section'

        # Placeholder logic for interpreting feedback
        # More sophisticated NLP/keyword analysis could be used here.
        approval_keywords = ['looks good', 'approved', 'no changes needed', 'ready to save']
        
        requires_redraft = True # Default assumption unless explicit approval
        if any(keyword in editor_feedback for keyword in approval_keywords):
            requires_redraft = False
        
        if not editor_feedback.strip(): # If feedback is empty or just whitespace
             print("  Decision: No substantive editor feedback provided, and not explicitly approved.")
             # Depending on desired flow: could save, or could assume redraft if not explicitly approved.
             # For now, let's be conservative: if no feedback, assume it might need another look or wasn't reviewed properly.
             # However, prompt's "Else (feedback requires redrafting and iterations < max): return 'draft_section_again'"
             # implies that empty feedback without approval keywords also leads to redraft.
             requires_redraft = True 

        if requires_redraft:
            print(f"  Decision: Feedback requires redraft (or feedback empty/not explicitly approved), iterations {iteration_count} < {max_iterations} -> routing to draft_section_again")
            return 'draft_section_again'
        else: # Approved or no redraft needed
            print(f"  Decision: Feedback suggests approval or no redraft needed -> routing to save_section")
            return 'save_section'

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
