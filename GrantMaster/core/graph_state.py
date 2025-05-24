from typing import Any, List, Optional, TypedDict

class GrantMasterState(TypedDict):
    organization_profile: Optional[dict]
    research_website_url: Optional[str]
    research_login_credentials: Optional[dict]  # e.g., {'username': '...', 'password': '...'}
    authenticated_driver_session: Optional[Any] # To hold the Selenium driver
    extracted_grant_opportunities: Optional[List[dict]]
    current_grant_opportunity_id: Optional[int]
    current_grant_details: Optional[dict]
    analysis_results: Optional[dict]
    current_section_name: Optional[str]
    current_draft_content: Optional[str]
    editor_feedback: Optional[str]
    iteration_count: int  # Initialized to 0 in graph creation
    error_message: Optional[str]
    log_messages: List[str]  # Initialized to an empty list in graph creation
    next_node_to_call: Optional[str]
