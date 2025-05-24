import unittest
from unittest.mock import patch, MagicMock

# Adjust import path based on actual file structure
# Assuming GrantMaster is the project root and in PYTHONPATH
from GrantMaster.agents.researcher_agent import node_perform_login
from GrantMaster.core.graph_state import GrantMasterState

class TestResearcherAgentNodeFunctions(unittest.TestCase):

    @patch('GrantMaster.agents.researcher_agent.perform_website_login')
    def test_node_perform_login_success(self, mock_perform_login):
        # Arrange
        mock_driver = MagicMock()
        mock_perform_login.return_value = mock_driver
        
        initial_state = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials={"username": "user", "password": "pw"},
            log_messages=["Initial log."],
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0, # Ensure this is int
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state = node_perform_login(initial_state)

        # Assert
        mock_perform_login.assert_called_once_with("http://example.com/login", "user", "pw")
        self.assertEqual(result_state["authenticated_driver_session"], mock_driver)
        self.assertIsNone(result_state["error_message"])
        self.assertEqual(len(result_state["log_messages"]), 2)
        self.assertIn("Initial log.", result_state["log_messages"])
        self.assertTrue(any("Login successful" in msg for msg in result_state["log_messages"]))

    @patch('GrantMaster.agents.researcher_agent.perform_website_login')
    def test_node_perform_login_failure_driver(self, mock_perform_login):
        # Arrange
        mock_perform_login.return_value = None
        
        initial_state = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials={"username": "user", "password": "pw"},
            log_messages=["Initial failure log."],
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state = node_perform_login(initial_state)

        # Assert
        mock_perform_login.assert_called_once_with("http://example.com/login", "user", "pw")
        self.assertIsNone(result_state["authenticated_driver_session"])
        self.assertIsNotNone(result_state["error_message"])
        self.assertTrue("Login failed" in result_state["error_message"])
        self.assertEqual(len(result_state["log_messages"]), 2)
        self.assertIn("Initial failure log.", result_state["log_messages"])
        self.assertTrue(any("Login attempt failed" in msg for msg in result_state["log_messages"]))

    def test_node_perform_login_missing_url(self):
        # Arrange
        initial_state = GrantMasterState(
            research_website_url=None, # Missing URL
            research_login_credentials={"username": "user", "password": "pw"},
            log_messages=[],
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state = node_perform_login(initial_state)

        # Assert
        self.assertIsNone(result_state["authenticated_driver_session"])
        self.assertIsNotNone(result_state["error_message"])
        self.assertIn("research_website_url or research_login_credentials not found", result_state["error_message"])
        self.assertTrue(any("research_website_url or research_login_credentials not found" in msg for msg in result_state["log_messages"]))

    def test_node_perform_login_missing_credentials(self):
        # Arrange
        initial_state = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials=None, # Missing credentials
            log_messages=[],
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state = node_perform_login(initial_state)

        # Assert
        self.assertIsNone(result_state["authenticated_driver_session"])
        self.assertIsNotNone(result_state["error_message"])
        self.assertIn("research_website_url or research_login_credentials not found", result_state["error_message"])
        self.assertTrue(any("research_website_url or research_login_credentials not found" in msg for msg in result_state["log_messages"]))

    def test_node_perform_login_missing_username(self):
        # Arrange
        initial_state = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials={"password": "pw"}, # Missing username
            log_messages=[],
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state = node_perform_login(initial_state)

        # Assert
        self.assertIsNone(result_state["authenticated_driver_session"])
        self.assertIsNotNone(result_state["error_message"])
        self.assertIn("Username or password not found", result_state["error_message"])
        self.assertTrue(any("Username or password not found" in msg for msg in result_state["log_messages"]))

    @patch('GrantMaster.agents.researcher_agent.perform_website_login')
    def test_node_perform_login_success_empty_initial_logs(self, mock_perform_login):
        # Arrange
        mock_driver = MagicMock()
        mock_perform_login.return_value = mock_driver
        
        # Test with log_messages key missing
        initial_state_missing_key = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials={"username": "user", "password": "pw"},
            # log_messages key is intentionally missing
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )
        
        # Act
        result_state_missing = node_perform_login(initial_state_missing_key)

        # Assert
        mock_perform_login.assert_called_with("http://example.com/login", "user", "pw") # Called again
        self.assertEqual(result_state_missing["authenticated_driver_session"], mock_driver)
        self.assertIsNone(result_state_missing["error_message"])
        self.assertIsInstance(result_state_missing["log_messages"], list)
        self.assertEqual(len(result_state_missing["log_messages"]), 1)
        self.assertTrue(any("Login successful" in msg for msg in result_state_missing["log_messages"]))

        # Test with log_messages key present but set to None
        mock_perform_login.reset_mock() # Reset mock for the next call
        initial_state_none_key = GrantMasterState(
            research_website_url="http://example.com/login",
            research_login_credentials={"username": "user", "password": "pw"},
            log_messages=None, # log_messages is None
            organization_profile=None,
            authenticated_driver_session=None,
            extracted_grant_opportunities=None,
            current_grant_opportunity_id=None,
            current_grant_details=None,
            analysis_results=None,
            current_section_name=None,
            current_draft_content=None,
            editor_feedback=None,
            iteration_count=0,
            error_message=None,
            next_node_to_call=None
        )

        # Act
        result_state_none = node_perform_login(initial_state_none_key)

        # Assert
        mock_perform_login.assert_called_once_with("http://example.com/login", "user", "pw")
        self.assertEqual(result_state_none["authenticated_driver_session"], mock_driver)
        self.assertIsNone(result_state_none["error_message"])
        self.assertIsInstance(result_state_none["log_messages"], list)
        self.assertEqual(len(result_state_none["log_messages"]), 1)
        self.assertTrue(any("Login successful" in msg for msg in result_state_none["log_messages"]))

if __name__ == '__main__':
    unittest.main()
