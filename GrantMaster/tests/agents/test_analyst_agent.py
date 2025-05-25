import unittest
from unittest.mock import MagicMock, patch
import sqlite3 # For testing database update failure

# Adjust import paths as necessary based on project structure
from GrantMaster.agents.analyst_agent import node_analyze_opportunities, AnalystAgent
from GrantMaster.core.data_manager import DataManager
from GrantMaster.core.graph_state import GrantMasterState

class TestAnalystAgentNodeFunctions(unittest.TestCase):
    def setUp(self):
        # Common setup for mocks
        self.mock_analyst_agent = MagicMock(spec=AnalystAgent)
        self.mock_data_manager = MagicMock(spec=DataManager)
        
        # Default successful analysis result
        self.sample_analysis_result = {
            "rationale": "Good fit.",
            "suitability_score": 8,
            "status": "analyzed_strong_match"
        }
        # Default grant data from WebSleuth
        self.sample_grant_from_websleuth = {
            "title": "Test Grant", # Matches key used in node_analyze_opportunities
            "grant_title": "Test Grant Alt", # Fallback key
            "funder": "Test Funder",
            "deadline": "2025-12-31",
            "description": "A test grant.",
            "eligibility": "All eligible.",
            "focus_areas": "Testing",
            "raw_research_data": "Raw data."
        }
        self.mock_analyst_agent.analyze_suitability.return_value = self.sample_analysis_result
        self.mock_data_manager.save_grant_opportunity.return_value = 1 # Mock DB ID
        # update_grant_analysis doesn't return anything, so default mock is fine

    def _get_default_state(self, grants=None, org_profile=None, log_messages=None):
        # Helper to create a default state, ensuring all keys are present
        return GrantMasterState(
            extracted_grant_opportunities=grants if grants is not None else [],
            organization_profile=org_profile,
            log_messages=log_messages if log_messages is not None else [],
            research_website_url=None, research_login_credentials=None, authenticated_driver_session=None,
            current_grant_opportunity_id=None, current_grant_details=None, analysis_results=None,
            current_section_name=None, current_draft_content=None, editor_feedback=None,
            iteration_count=0, error_message=None, next_node_to_call=None
        )

    def test_node_analyze_one_grant_success(self):
        initial_grants = [dict(self.sample_grant_from_websleuth)] # Use a copy
        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile={"name": "Test Org"},
            log_messages=["Initial log."]
        )

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.mock_analyst_agent.analyze_suitability.assert_called_once_with(
            initial_grants[0], {"name": "Test Org"}
        )
        
        self.mock_data_manager.save_grant_opportunity.assert_called_once()
        args, kwargs = self.mock_data_manager.save_grant_opportunity.call_args
        self.assertEqual(kwargs['grant_title'], initial_grants[0]['title'])
        self.assertEqual(kwargs['funder'], initial_grants[0]['funder'])
        self.assertEqual(kwargs['deadline'], initial_grants[0]['deadline'])
        self.assertEqual(kwargs['description'], initial_grants[0]['description'])
        self.assertEqual(kwargs['eligibility'], initial_grants[0]['eligibility'])
        self.assertEqual(kwargs['focus_areas'], initial_grants[0]['focus_areas'])
        self.assertEqual(kwargs['raw_research_data'], initial_grants[0]['raw_research_data'])
        self.assertEqual(kwargs['analysis_notes'], self.sample_analysis_result['rationale'])
        self.assertEqual(kwargs['suitability_score'], self.sample_analysis_result['suitability_score'])
        
        self.mock_data_manager.update_grant_analysis.assert_called_once_with(
            grant_id=1, # from save_grant_opportunity mock
            analysis_notes=self.sample_analysis_result['rationale'],
            suitability_score=self.sample_analysis_result['suitability_score'],
            status=self.sample_analysis_result['status']
        )
        
        self.assertEqual(len(result['extracted_grant_opportunities']), 1)
        processed_grant = result['extracted_grant_opportunities'][0]
        self.assertEqual(processed_grant['database_id'], 1)
        self.assertEqual(processed_grant['analysis_rationale'], self.sample_analysis_result['rationale'])
        self.assertEqual(processed_grant['analysis_suitability_score'], self.sample_analysis_result['suitability_score'])
        self.assertEqual(processed_grant['analysis_status'], self.sample_analysis_result['status'])
        self.assertIsNone(result['error_message'])
        self.assertTrue(any("Analysis and saving process complete." in msg for msg in result['log_messages']))
        self.assertTrue(any("Grant 'Test Grant' saved with ID: 1." in msg for msg in result['log_messages']))
        self.assertTrue(any("Analysis status 'analyzed_strong_match' updated for grant ID: 1." in msg for msg in result['log_messages']))

    def test_node_analyze_multiple_grants_success(self):
        grant1 = dict(self.sample_grant_from_websleuth)
        grant2 = dict(self.sample_grant_from_websleuth)
        grant2["title"] = "Test Grant 2"
        initial_grants = [grant1, grant2]
        
        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile={"name": "Test Org"}
        )
        
        self.mock_data_manager.save_grant_opportunity.side_effect = [1, 2] # Return different IDs

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.assertEqual(self.mock_analyst_agent.analyze_suitability.call_count, 2)
        self.assertEqual(self.mock_data_manager.save_grant_opportunity.call_count, 2)
        self.assertEqual(self.mock_data_manager.update_grant_analysis.call_count, 2)

        self.assertEqual(len(result['extracted_grant_opportunities']), 2)
        self.assertEqual(result['extracted_grant_opportunities'][0]['database_id'], 1)
        self.assertEqual(result['extracted_grant_opportunities'][1]['database_id'], 2)
        self.assertIsNone(result['error_message'])
        self.assertTrue(any("2 grants successfully processed" in msg for msg in result['log_messages']))

    def test_node_analyze_no_opportunities(self):
        initial_state = self._get_default_state(
            grants=[],
            org_profile={"name": "Test Org"}
        )

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.mock_analyst_agent.analyze_suitability.assert_not_called()
        self.mock_data_manager.save_grant_opportunity.assert_not_called()
        self.mock_data_manager.update_grant_analysis.assert_not_called()

        self.assertEqual(result['extracted_grant_opportunities'], [])
        self.assertTrue(any("No extracted grant opportunities to analyze." in msg for msg in result['log_messages']))
        self.assertIsNone(result['error_message'])

    def test_node_analyze_missing_org_profile(self):
        initial_grants = [dict(self.sample_grant_from_websleuth)]
        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile=None # Missing org profile
        )

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.mock_analyst_agent.analyze_suitability.assert_not_called()
        self.mock_data_manager.save_grant_opportunity.assert_not_called()
        self.mock_data_manager.update_grant_analysis.assert_not_called()
        
        self.assertEqual(result['error_message'], "Cannot analyze opportunities: Organization profile is missing from state.")
        # Check if the original grants list is passed through in the result
        self.assertEqual(result['extracted_grant_opportunities'], initial_grants)

    def test_node_analyze_analyst_agent_error_one_grant(self):
        grant1 = dict(self.sample_grant_from_websleuth)
        grant1["title"] = "Grant 1 (Fail Analysis)"
        grant2 = dict(self.sample_grant_from_websleuth)
        grant2["title"] = "Grant 2 (Pass Analysis)"
        initial_grants = [grant1, grant2]

        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile={"name": "Test Org"}
        )

        analysis_error_result = {"error": "AI failed"}
        self.mock_analyst_agent.analyze_suitability.side_effect = [analysis_error_result, self.sample_analysis_result]
        # save_grant_opportunity will only be called for the second grant
        self.mock_data_manager.save_grant_opportunity.return_value = 2 

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.assertEqual(self.mock_analyst_agent.analyze_suitability.call_count, 2)
        
        # Save and update should only be called for the second grant
        self.mock_data_manager.save_grant_opportunity.assert_called_once() 
        args_save, kwargs_save = self.mock_data_manager.save_grant_opportunity.call_args
        self.assertEqual(kwargs_save['grant_title'], "Grant 2 (Pass Analysis)")

        self.mock_data_manager.update_grant_analysis.assert_called_once()
        args_update, kwargs_update = self.mock_data_manager.update_grant_analysis.call_args
        self.assertEqual(kwargs_update['grant_id'], 2)

        processed_grant1 = result['extracted_grant_opportunities'][0]
        processed_grant2 = result['extracted_grant_opportunities'][1]

        self.assertEqual(processed_grant1['analysis_error'], "AI failed")
        self.assertNotIn('database_id', processed_grant1)
        
        self.assertEqual(processed_grant2['database_id'], 2)
        self.assertEqual(processed_grant2['analysis_status'], self.sample_analysis_result['status'])
        self.assertNotIn('analysis_error', processed_grant2) # No error for the second grant

        self.assertIsNone(result['error_message'])
        self.assertTrue(any("Analysis failed for grant 'Grant 1 (Fail Analysis)': AI failed" in msg for msg in result['log_messages']))
        self.assertTrue(any("Grant 'Grant 2 (Pass Analysis)' saved with ID: 2." in msg for msg in result['log_messages']))
        self.assertTrue(any("1 grants had issues during processing." in msg for msg in result['log_messages']))

    def test_node_analyze_save_failure_one_grant(self):
        grant1 = dict(self.sample_grant_from_websleuth)
        grant1["title"] = "Grant 1 (Fail Save)"
        grant2 = dict(self.sample_grant_from_websleuth)
        grant2["title"] = "Grant 2 (Pass Save)"
        initial_grants = [grant1, grant2]

        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile={"name": "Test Org"}
        )
        
        # First save fails (returns None), second succeeds (returns ID 2)
        self.mock_data_manager.save_grant_opportunity.side_effect = [None, 2] 

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.assertEqual(self.mock_analyst_agent.analyze_suitability.call_count, 2)
        self.assertEqual(self.mock_data_manager.save_grant_opportunity.call_count, 2)
        
        # update_grant_analysis should only be called for the second grant (which saved successfully)
        self.mock_data_manager.update_grant_analysis.assert_called_once()
        args_update, kwargs_update = self.mock_data_manager.update_grant_analysis.call_args
        self.assertEqual(kwargs_update['grant_id'], 2)

        processed_grant1 = result['extracted_grant_opportunities'][0]
        processed_grant2 = result['extracted_grant_opportunities'][1]

        self.assertEqual(processed_grant1['analysis_error'], "Database save failed")
        self.assertNotIn('database_id', processed_grant1)
        
        self.assertEqual(processed_grant2['database_id'], 2)
        self.assertNotIn('analysis_error', processed_grant2)

        self.assertIsNone(result['error_message'])
        self.assertTrue(any("Failed to save grant 'Grant 1 (Fail Save)' to database." in msg for msg in result['log_messages']))
        self.assertTrue(any("Grant 'Grant 2 (Pass Save)' saved with ID: 2." in msg for msg in result['log_messages']))
        self.assertTrue(any("1 grants had issues during processing." in msg for msg in result['log_messages']))

    def test_node_analyze_update_failure_one_grant(self):
        initial_grants = [dict(self.sample_grant_from_websleuth)]
        initial_state = self._get_default_state(
            grants=initial_grants,
            org_profile={"name": "Test Org"}
        )
        
        self.mock_data_manager.save_grant_opportunity.return_value = 1 # Save succeeds
        db_error_message = "DB update error"
        # Test with generic Exception as sqlite3.Error might not be directly catchable by the node's generic Exception handler in a mock context
        # If node specifically catches sqlite3.Error, then this should be sqlite3.Error
        self.mock_data_manager.update_grant_analysis.side_effect = Exception(db_error_message) 

        result = node_analyze_opportunities(initial_state, self.mock_analyst_agent, self.mock_data_manager)

        self.mock_analyst_agent.analyze_suitability.assert_called_once()
        self.mock_data_manager.save_grant_opportunity.assert_called_once()
        self.mock_data_manager.update_grant_analysis.assert_called_once() # It is called

        processed_grant = result['extracted_grant_opportunities'][0]
        
        # The grant should still have its database_id because save was successful
        self.assertEqual(processed_grant['database_id'], 1)
        
        # The node's current implementation catches the exception from update_grant_analysis within the loop.
        # The analysis fields from the successful analysis are still on the grant.
        # The error is logged, and 'analysis_error' is set on the grant object.
        self.assertEqual(processed_grant['analysis_rationale'], self.sample_analysis_result['rationale'])
        self.assertEqual(processed_grant['analysis_error'], db_error_message)

        self.assertIsNone(result['error_message']) # Node level error is None
        self.assertTrue(any("Grant 'Test Grant' saved with ID: 1." in msg for msg in result['log_messages']))
        # The error message from the exception during update_grant_analysis should be logged.
        # The node logs "Unexpected error processing grant..."
        self.assertTrue(any(f"Unexpected error processing grant 'Test Grant': {db_error_message}" in msg for msg in result['log_messages']))
        # Check the final summary log
        self.assertTrue(any("1 grants had issues during processing." in msg for msg in result['log_messages']))


if __name__ == '__main__':
    unittest.main()
