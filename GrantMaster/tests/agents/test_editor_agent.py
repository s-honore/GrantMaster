import unittest
from unittest.mock import MagicMock, patch

# Adjust import paths as necessary
from GrantMaster.agents.editor_agent import node_review_draft, EditorAgent
from GrantMaster.core.graph_state import GrantMasterState

class TestEditorAgentNodeFunctions(unittest.TestCase):
    def setUp(self):
        self.mock_editor_agent = MagicMock(spec=EditorAgent)
        self.mock_editor_agent.review_draft.return_value = "This is excellent feedback." # Default success

        self.base_state_dict = {
            "current_draft_content": "This is a draft.",
            "current_section_name": "Introduction",
            "current_grant_details": {"guidelines": "Follow these guidelines closely."}, # Example with guidelines
            "log_messages": ["Initial log."],
            # Fill other GrantMasterState fields with None or defaults
            "organization_profile": None, "research_website_url": None, 
            "research_login_credentials": None, "authenticated_driver_session": None, 
            "extracted_grant_opportunities": None, "current_grant_opportunity_id": None,
            "analysis_results": None, "editor_feedback": None, 
            "iteration_count": 0, "error_message": None, "next_node_to_call": None,
            "specific_instructions": None
        }

    def get_state(self, **kwargs):
        state_data = {**self.base_state_dict, **kwargs}
        return GrantMasterState(**state_data)

    def test_node_review_draft_success(self):
        # Test with no specific guidelines passed to agent, uses default empty string
        state = self.get_state(current_grant_details={}) # Clear guidelines for this test
        
        result = node_review_draft(state, self.mock_editor_agent)

        self.mock_editor_agent.review_draft.assert_called_once_with(
            draft_text=self.base_state_dict['current_draft_content'],
            section_name=self.base_state_dict['current_section_name'],
            grant_guidelines_summary="" 
        )
        self.assertEqual(result['editor_feedback'], "This is excellent feedback.")
        self.assertIsNone(result['error_message'])
        self.assertTrue(any(f"Feedback received for section: {self.base_state_dict['current_section_name']}" in msg for msg in result['log_messages']))

    def test_node_review_draft_with_guidelines(self):
        state = self.get_state() # Uses default setUp with current_grant_details containing 'guidelines'
        
        result = node_review_draft(state, self.mock_editor_agent)

        self.mock_editor_agent.review_draft.assert_called_once_with(
            draft_text=self.base_state_dict['current_draft_content'],
            section_name=self.base_state_dict['current_section_name'],
            grant_guidelines_summary="Follow these guidelines closely."
        )
        self.assertEqual(result['editor_feedback'], "This is excellent feedback.")
        self.assertIsNone(result['error_message'])
        self.assertTrue(any(f"Feedback received for section: {self.base_state_dict['current_section_name']}" in msg for msg in result['log_messages']))

    def test_node_review_draft_with_alternative_guideline_key(self):
        state = self.get_state(current_grant_details={"guidelines_summary": "Alternative guidelines."})
        
        result = node_review_draft(state, self.mock_editor_agent)

        self.mock_editor_agent.review_draft.assert_called_once_with(
            draft_text=self.base_state_dict['current_draft_content'],
            section_name=self.base_state_dict['current_section_name'],
            grant_guidelines_summary="Alternative guidelines."
        )
        self.assertEqual(result['editor_feedback'], "This is excellent feedback.")
        self.assertIsNone(result['error_message'])

    def test_node_review_draft_missing_draft_content(self):
        state = self.get_state(current_draft_content=None)
        
        result = node_review_draft(state, self.mock_editor_agent)
        
        self.mock_editor_agent.review_draft.assert_not_called()
        self.assertIn("Missing current_draft_content", result['error_message'])
        self.assertEqual(result['editor_feedback'], "")

    def test_node_review_draft_empty_draft_content(self):
        state = self.get_state(current_draft_content="")
        
        result = node_review_draft(state, self.mock_editor_agent)
        
        self.mock_editor_agent.review_draft.assert_not_called()
        self.assertIn("Missing current_draft_content in state or content is empty", result['error_message'])
        self.assertEqual(result['editor_feedback'], "")

    def test_node_review_draft_missing_section_name(self):
        state = self.get_state(current_section_name=None)
        
        result = node_review_draft(state, self.mock_editor_agent)
        
        self.mock_editor_agent.review_draft.assert_not_called()
        self.assertIn("Missing current_section_name", result['error_message'])
        self.assertEqual(result['editor_feedback'], "")

    def test_node_review_draft_agent_failure(self):
        self.mock_editor_agent.review_draft.return_value = "// Error: Could not review //"
        state = self.get_state()
        
        result = node_review_draft(state, self.mock_editor_agent)
        
        self.mock_editor_agent.review_draft.assert_called_once()
        self.assertIn("EditorAgent failed to review section 'Introduction': // Error: Could not review //", result['error_message'])
        self.assertEqual(result['editor_feedback'], "")

    def test_node_review_draft_agent_raises_exception(self):
        self.mock_editor_agent.review_draft.side_effect = Exception("Editor exploded")
        state = self.get_state()
        
        result = node_review_draft(state, self.mock_editor_agent)
        
        self.mock_editor_agent.review_draft.assert_called_once()
        self.assertIn("Unexpected error in node_review_draft for 'Introduction': Editor exploded", result['error_message'])
        self.assertEqual(result['editor_feedback'], "")

if __name__ == '__main__':
    unittest.main()
