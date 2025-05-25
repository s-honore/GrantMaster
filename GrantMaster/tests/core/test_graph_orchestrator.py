import unittest
from unittest.mock import MagicMock, patch
import os # For OPENAI_API_KEY

# Adjust import paths as necessary
from GrantMaster.core.graph_orchestrator import GraphOrchestrator
from GrantMaster.core.graph_state import GrantMasterState
from GrantMaster.core.data_manager import DataManager 
# Agents are not directly tested here but are part of GraphOrchestrator init

class TestGraphOrchestratorNodes(unittest.TestCase):
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}) # Mock API key for init
    def setUp(self):
        self.mock_data_manager_instance = MagicMock(spec=DataManager)
        
        self.data_manager_patch = patch('GrantMaster.core.graph_orchestrator.DataManager', return_value=self.mock_data_manager_instance)
        self.mock_data_manager_constructor = self.data_manager_patch.start()

        self.orchestrator = GraphOrchestrator()

        self.base_state_dict = {
            "current_grant_opportunity_id": 1,
            "current_section_name": "Project Narrative",
            "current_draft_content": "This is the final draft.",
            "iteration_count": 3,
            "editor_feedback": "Looks good.",
            "log_messages": ["Initial log."],
            "error_message": None,
            # Fill other GrantMasterState fields with None or defaults
            "organization_profile": None, "research_website_url": None, 
            "research_login_credentials": None, "authenticated_driver_session": None, 
            "extracted_grant_opportunities": None, "current_grant_details": None,
            "analysis_results": None, "specific_instructions": None, "next_node_to_call": None
        }
    
    def tearDown(self):
        self.data_manager_patch.stop()

    def get_state(self, **kwargs):
        state_data = {**self.base_state_dict, **kwargs}
        # Ensure all keys from GrantMasterState are present
        all_keys = {k: None for k in GrantMasterState.__annotations__}
        all_keys.update(state_data)
        return GrantMasterState(**all_keys)

    # --- Tests for save_section_node ---
    def test_save_section_node_success(self):
        self.mock_data_manager_instance.save_section_draft.return_value = 123 # mock DB ID
        state = self.get_state()
        
        result = self.orchestrator.save_section_node(state)
        
        self.mock_data_manager_instance.save_section_draft.assert_called_once_with(
            grant_opportunity_id=state['current_grant_opportunity_id'],
            section_name=state['current_section_name'],
            draft_content=state['current_draft_content'],
            version=state['iteration_count'],
            feedback=state['editor_feedback']
        )
        self.assertIsNone(result['error_message'])
        self.assertTrue(any("Section 'Project Narrative' (Version 3) saved to database with ID: 123" in msg for msg in result['log_messages']))

    def test_save_section_node_missing_grant_id(self):
        state = self.get_state(current_grant_opportunity_id=None)
        
        result = self.orchestrator.save_section_node(state)
        
        self.mock_data_manager_instance.save_section_draft.assert_not_called()
        self.assertIn("Missing current_grant_opportunity_id", result['error_message'])

    def test_save_section_node_missing_section_name(self):
        state = self.get_state(current_section_name=None)
        
        result = self.orchestrator.save_section_node(state)
        
        self.mock_data_manager_instance.save_section_draft.assert_not_called()
        self.assertIn("Missing current_section_name", result['error_message'])

    def test_save_section_node_missing_draft_content(self):
        # Test with None
        state_none = self.get_state(current_draft_content=None)
        result_none = self.orchestrator.save_section_node(state_none)
        self.mock_data_manager_instance.save_section_draft.assert_not_called()
        self.assertIn("Missing or empty current_draft_content", result_none['error_message'])
        
        # Reset mock for next call if needed, though not strictly necessary here as it wasn't called
        self.mock_data_manager_instance.save_section_draft.reset_mock() 

        # Test with empty string
        state_empty = self.get_state(current_draft_content="")
        result_empty = self.orchestrator.save_section_node(state_empty)
        self.mock_data_manager_instance.save_section_draft.assert_not_called()
        self.assertIn("Missing or empty current_draft_content", result_empty['error_message'])

    def test_save_section_node_db_failure(self):
        self.mock_data_manager_instance.save_section_draft.return_value = None
        state = self.get_state()
        
        result = self.orchestrator.save_section_node(state)
        
        self.mock_data_manager_instance.save_section_draft.assert_called_once()
        self.assertIn("Failed to save section", result['error_message'])
        self.assertIn("DataManager returned None", result['error_message'])

    # --- Tests for handle_error_node ---
    def test_handle_error_node_with_error(self):
        state = self.get_state(error_message="Something went wrong!")
        
        result = self.orchestrator.handle_error_node(state)
        
        self.assertTrue(any("ERROR ENCOUNTERED IN GRAPH: Something went wrong!" in msg for msg in result['log_messages']))
        # Check that error_message from input state is preserved.
        # The node itself only returns {"log_messages": ...}, so the original state's error_message persists
        # by nature of how StateGraph updates state (merges returned dict).
        # So, result from node call won't have error_message, but if we were to check full state after node, it would.
        # For testing the node's direct output:
        self.assertNotIn('error_message', result) # The node does not return error_message: None

    def test_handle_error_node_no_error_in_state(self):
        state = self.get_state(error_message=None) # Explicitly None
        
        result = self.orchestrator.handle_error_node(state)
        
        self.assertTrue(any("ERROR ENCOUNTERED IN GRAPH: No specific error message provided in state." in msg for msg in result['log_messages']))
        self.assertNotIn('error_message', result) # The node does not return error_message: None

    # --- Tests for should_redraft_or_save ---
    def test_should_redraft_or_save_error_message(self):
        state = self.get_state(error_message="Critical failure in prior node")
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'handle_error')

    def test_should_redraft_or_save_max_iterations(self):
        # Test at max_iterations
        state_at_max = self.get_state(iteration_count=3, editor_feedback="Needs changes", error_message=None)
        decision_at_max = self.orchestrator.should_redraft_or_save(state_at_max)
        self.assertEqual(decision_at_max, 'save_section')

        # Test above max_iterations
        state_above_max = self.get_state(iteration_count=4, editor_feedback="Still needs changes", error_message=None)
        decision_above_max = self.orchestrator.should_redraft_or_save(state_above_max)
        self.assertEqual(decision_above_max, 'save_section')

    def test_should_redraft_or_save_approval_looks_good(self):
        state = self.get_state(editor_feedback="This draft looks good!", iteration_count=1, error_message=None)
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'save_section')

    def test_should_redraft_or_save_approval_approved_case_insensitive(self):
        state = self.get_state(editor_feedback="Consider this APPROVED.", iteration_count=1, error_message=None)
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'save_section')

    def test_should_redraft_or_save_needs_redraft(self):
        state = self.get_state(editor_feedback="Needs major revisions.", iteration_count=1, error_message=None)
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'draft_section_again')

    def test_should_redraft_or_save_empty_feedback(self):
        state = self.get_state(editor_feedback="", iteration_count=1, error_message=None)
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'draft_section_again')
        
    def test_should_redraft_or_save_whitespace_feedback(self):
        state = self.get_state(editor_feedback="   ", iteration_count=1, error_message=None)
        decision = self.orchestrator.should_redraft_or_save(state)
        self.assertEqual(decision, 'draft_section_again')

    # --- Test for Graph Compilation ---
    def test_graph_orchestrator_compilation(self):
        # setUp already initializes self.orchestrator and thus compiles the graph
        self.assertIsNotNone(self.orchestrator.app, "Graph compilation should result in a non-None app object.")
        # Langchain's compiled graphs are instances of `CompiledGraph` which is a `Runnable`.
        # Runnables have an `invoke` method.
        self.assertTrue(callable(self.orchestrator.app.invoke), "Compiled app should have a callable 'invoke' method.")
        # Could also check for 'stream' if that's intended for use:
        # self.assertTrue(callable(self.orchestrator.app.stream), "Compiled app should have a callable 'stream' method.")

if __name__ == '__main__':
    unittest.main()
