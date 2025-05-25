import unittest
from unittest.mock import MagicMock, patch

from GrantMaster.agents.writer_agent import node_draft_section, WriterAgent
from GrantMaster.core.graph_state import GrantMasterState

class TestWriterAgentNodeFunctions(unittest.TestCase):
    def setUp(self):
        self.mock_writer_agent = MagicMock(spec=WriterAgent)
        self.mock_writer_agent.draft_section.return_value = "Successful draft text." # Default success

        self.base_state_dict = {
            "organization_profile": {"name": "Test Org"},
            "research_website_url": None,
            "research_login_credentials": None,
            "authenticated_driver_session": None,
            "extracted_grant_opportunities": None,
            "current_grant_opportunity_id": None,
            "current_grant_details": {"title": "Test Grant Detail"}, # This is the one used by the node
            "analysis_results": None,
            "current_section_name": "Introduction",
            "current_draft_content": None,
            "editor_feedback": None,
            "iteration_count": 0,
            "error_message": None,
            "log_messages": ["Initial log."],
            "next_node_to_call": None,
            "specific_instructions": None # Added this based on node_draft_section's use of state.get("specific_instructions")
        }

    def get_state(self, **kwargs):
        state_data = {**self.base_state_dict, **kwargs}
        # Ensure all keys for GrantMasterState are present
        # TypedDict is strict, so all keys must be provided.
        # The base_state_dict should cover all keys.
        return GrantMasterState(**state_data)

    def test_node_draft_section_success_first_draft(self):
        state = self.get_state() 
        
        result = node_draft_section(state, self.mock_writer_agent)

        self.mock_writer_agent.draft_section.assert_called_once_with(
            grant_opportunity_details=self.base_state_dict['current_grant_details'],
            org_profile=self.base_state_dict['organization_profile'],
            section_name=self.base_state_dict['current_section_name'],
            specific_instructions="" 
        )
        self.assertEqual(result['current_draft_content'], "Successful draft text.")
        self.assertEqual(result['iteration_count'], 1)
        self.assertIsNone(result['error_message'])
        self.assertTrue(any("Drafted section (Iteration 1): Introduction." in msg for msg in result['log_messages']))

    def test_node_draft_section_with_editor_feedback(self):
        state = self.get_state(editor_feedback="Use more keywords.")
        
        result = node_draft_section(state, self.mock_writer_agent)

        self.mock_writer_agent.draft_section.assert_called_once_with(
            grant_opportunity_details=self.base_state_dict['current_grant_details'],
            org_profile=self.base_state_dict['organization_profile'],
            section_name=self.base_state_dict['current_section_name'],
            specific_instructions="Use more keywords."
        )
        self.assertEqual(result['current_draft_content'], "Successful draft text.")
        self.assertEqual(result['iteration_count'], 1)
        self.assertIsNone(result['error_message'])

    def test_node_draft_section_with_specific_instructions(self):
        state = self.get_state(specific_instructions="Focus on impact.")
        
        result = node_draft_section(state, self.mock_writer_agent)

        self.mock_writer_agent.draft_section.assert_called_once_with(
            grant_opportunity_details=self.base_state_dict['current_grant_details'],
            org_profile=self.base_state_dict['organization_profile'],
            section_name=self.base_state_dict['current_section_name'],
            specific_instructions="Focus on impact."
        )
        self.assertEqual(result['current_draft_content'], "Successful draft text.")
        self.assertEqual(result['iteration_count'], 1)

    def test_node_draft_section_with_both_feedback_and_instructions(self):
        state = self.get_state(editor_feedback="Review grammar.", specific_instructions="Keep it concise.")
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        expected_combined_instructions = "Keep it concise.\n\n--- Previous Editor Feedback ---\nReview grammar."
        self.mock_writer_agent.draft_section.assert_called_once_with(
            grant_opportunity_details=self.base_state_dict['current_grant_details'],
            org_profile=self.base_state_dict['organization_profile'],
            section_name=self.base_state_dict['current_section_name'],
            specific_instructions=expected_combined_instructions
        )
        self.assertEqual(result['current_draft_content'], "Successful draft text.")
        self.assertEqual(result['iteration_count'], 1)

    def test_node_draft_section_missing_grant_details(self):
        state = self.get_state(current_grant_details=None)
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.mock_writer_agent.draft_section.assert_not_called()
        self.assertIn("Missing current_grant_details", result['error_message'])
        self.assertEqual(result['current_draft_content'], "")
        self.assertEqual(result['iteration_count'], 0) # Iteration count from input state

    def test_node_draft_section_missing_org_profile(self):
        state = self.get_state(organization_profile=None)
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.mock_writer_agent.draft_section.assert_not_called()
        self.assertIn("Missing organization_profile", result['error_message'])
        self.assertEqual(result['current_draft_content'], "")
        self.assertEqual(result['iteration_count'], 0)

    def test_node_draft_section_missing_section_name(self):
        state = self.get_state(current_section_name=None)
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.mock_writer_agent.draft_section.assert_not_called()
        self.assertIn("Missing current_section_name", result['error_message'])
        self.assertEqual(result['current_draft_content'], "")
        self.assertEqual(result['iteration_count'], 0)

    def test_node_draft_section_agent_failure(self):
        self.mock_writer_agent.draft_section.return_value = "// Error: AI hiccup //"
        state = self.get_state()
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.mock_writer_agent.draft_section.assert_called_once()
        self.assertIn("WriterAgent failed to draft section 'Introduction': // Error: AI hiccup //", result['error_message'])
        self.assertEqual(result['current_draft_content'], "")
        self.assertEqual(result['iteration_count'], 1) # Attempt was made

    def test_node_draft_section_iteration_increment(self):
        state = self.get_state(iteration_count=3)
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.assertEqual(result['iteration_count'], 4)
        self.assertEqual(result['current_draft_content'], "Successful draft text.") # Ensure it still drafts
        self.assertIsNone(result['error_message'])

    def test_node_draft_section_agent_raises_exception(self):
        self.mock_writer_agent.draft_section.side_effect = Exception("Agent exploded")
        state = self.get_state()
        
        result = node_draft_section(state, self.mock_writer_agent)
        
        self.mock_writer_agent.draft_section.assert_called_once()
        self.assertIn("Unexpected error in node_draft_section for 'Introduction': Agent exploded", result['error_message'])
        self.assertEqual(result['current_draft_content'], "")
        self.assertEqual(result['iteration_count'], 1)

if __name__ == '__main__':
    unittest.main()
