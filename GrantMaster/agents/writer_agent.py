from openai import OpenAI
import os # For __main__ block, to load .env

from GrantMaster.core.graph_state import GrantMasterState
# WriterAgent class is defined in the same file.

class WriterAgent:
    def __init__(self, api_key: str, model_name="gpt-4o"): # Modified signature, kept gpt-4o as it was specific
        self.api_key = api_key # Store api_key if needed
        self.openai_client = OpenAI(api_key=self.api_key) # Initialize client
        self.model_name = model_name # Using model_name for consistency
        print(f"WriterAgent initialized with model: {self.model_name}")

    def draft_section(self, grant_opportunity_details, org_profile, section_name, specific_instructions=''):
        print(f"WriterAgent: Drafting section '{section_name}' for grant '{grant_opportunity_details.get('grant_title', 'N/A')}'...")

        # Constructing a detailed context string for the prompt
        grant_context = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in grant_opportunity_details.items()])
        org_context = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in org_profile.items()])

        prompt = f"""
        You are an expert AI grant writer assistant. Your task is to draft a specific section of a grant proposal.

        **Grant Opportunity Details:**
        ---
        {grant_context}
        ---

        **Organization Profile:**
        ---
        {org_context}
        ---

        **Section to Draft:** {section_name}

        **Specific Instructions (if any):** {specific_instructions if specific_instructions else "None provided. Please adhere to general best practices for this section."}

        **Task:**
        Please draft the content for the "{section_name}" section of this grant proposal.
        - Adhere to common grant writing best practices: be clear, concise, persuasive, and directly address the requirements typically expected for this section.
        - Ensure the tone is professional and appropriate for a grant application.
        - If specific instructions were provided above, incorporate them carefully into your draft.
        - The output should be ONLY the drafted text for the section, suitable for direct inclusion in a grant proposal document. Do not include any introductory phrases like "Here is the draft:" or any concluding remarks.

        Begin drafting the "{section_name}" now:
        """

        print(f"WriterAgent: Sending request to OpenAI API for section '{section_name}'.")
        try:
            completion = self.openai_client.chat.completions.create(
                model=self.model_name, # Using self.model_name
                messages=[
                    {"role": "system", "content": "You are an expert AI grant writer. Your task is to draft high-quality content for specific grant proposal sections based on provided context and instructions. Output only the drafted text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6, # Slightly higher temperature for more natural writing, but still controlled.
                # max_tokens can be set if needed, but usually not required for drafting single sections.
            )
            drafted_text = completion.choices[0].message.content
            print(f"WriterAgent: Received draft for section '{section_name}' from OpenAI API.")
            # Basic cleanup: strip leading/trailing whitespace
            return drafted_text.strip() if drafted_text else ""
            
        except Exception as e:
            print(f"WriterAgent ERROR: OpenAI API call failed for section '{section_name}': {e}")
            return f"// Error generating draft for {section_name}: {e} //"

if __name__ == '__main__':
    # Example Usage (requires OPENAI_API_KEY in .env in the project root: GrantMaster/.env)
    
    # Construct the path to the .env file relative to this script's location
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    from dotenv import load_dotenv # Local import for testing

    if os.path.exists(dotenv_path):
        print(f"Loading .env file from: {os.path.abspath(dotenv_path)}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print(f"Warning: .env file not found at {os.path.abspath(dotenv_path)}. Attempting to load from default location or environment.")
        load_dotenv() 

    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure a .env file with OPENAI_API_KEY=YOUR_API_KEY_HERE exists in the GrantMaster project root directory.")
    else:
        print("OpenAI API Key loaded successfully for WriterAgent test.")
        try:
            client = OpenAI(api_key=api_key)
            print("OpenAI client initialized for WriterAgent test.")
            
            writer = WriterAgent(openai_client=client) # Uses default gpt-4o

            # Mock data for testing
            mock_grant_details = {
                'grant_title': 'Youth Empowerment Program Grant',
                'funder': 'Global Children Fund',
                'deadline': '2025-03-01',
                'description': 'Funds programs aimed at providing skills training and mentorship for at-risk youth aged 16-24.',
                'eligibility': 'Non-profit organizations with proven experience in youth development. Must operate in designated urban areas.',
                'focus_areas': 'Youth Development, Skills Training, Mentorship, Urban Renewal'
            }

            mock_org_profile_data = {
                'name': 'City Youth Connect',
                'mission': 'To empower at-risk urban youth by providing them with essential life skills, educational support, and positive mentorship experiences.',
                'projects': 'After-school tutoring, vocational workshops (coding, culinary arts), summer leadership camp.',
                'needs': 'Expansion of vocational workshops to include green jobs training; more volunteer mentors.',
                'target_demographics': 'At-risk youth aged 16-24 in downtown Metropolis.'
            }
            
            section_to_draft = "Needs Statement"
            # section_to_draft = "Project Description"
            # section_to_draft = "Organizational Background"


            specific_instructions_for_draft = "Emphasize the urgency due to recent local economic shifts impacting youth employment. Highlight specific statistics if possible (though the AI won't have live data, it can frame the need for them)."
            
            print(f"\n--- Running WriterAgent.draft_section() DEMO for section: '{section_to_draft}' ---")
            
            drafted_content = writer.draft_section(
                mock_grant_details,
                mock_org_profile_data,
                section_to_draft,
                specific_instructions_for_draft
            )
            
            print(f"\n--- WriterAgent Draft for '{section_to_draft}' ---")
            if drafted_content and not drafted_content.startswith("// Error"):
                print(drafted_content)
            else:
                print(f"Could not generate draft or an error occurred: {drafted_content}")
            print(f"--- End of WriterAgent DEMO for '{section_to_draft}' ---")

            # Example of drafting another section without specific instructions
            section_to_draft_2 = "Project Goals and Objectives"
            print(f"\n--- Running WriterAgent.draft_section() DEMO for section: '{section_to_draft_2}' (no specific instructions) ---")
            drafted_content_2 = writer.draft_section(
                mock_grant_details,
                mock_org_profile_data,
                section_to_draft_2
            )
            print(f"\n--- WriterAgent Draft for '{section_to_draft_2}' ---")
            if drafted_content_2 and not drafted_content_2.startswith("// Error"):
                print(drafted_content_2)
            else:
                print(f"Could not generate draft or an error occurred: {drafted_content_2}")
            print(f"--- End of WriterAgent DEMO for '{section_to_draft_2}' ---")


        except Exception as e:
            print(f"An error occurred during WriterAgent demo setup or execution: {e}")
            import traceback
            traceback.print_exc()

def node_draft_section(state: GrantMasterState, agent: WriterAgent) -> dict:
    """
    LangGraph node to draft a specific grant section using WriterAgent.
    It incorporates grant details, organization profile, section name,
    and any available editor feedback or specific instructions from the state.
    Updates state with the draft, iteration count, and logs.
    """
    print("Attempting node_draft_section...")
    log_messages = list(state.get("log_messages", []))

    current_grant_details = state.get("current_grant_details")
    organization_profile = state.get("organization_profile")
    current_section_name = state.get("current_section_name")
    editor_feedback = state.get("editor_feedback") # Optional
    specific_instructions_from_state = state.get("specific_instructions") # Optional

    if not current_grant_details or not organization_profile or not current_section_name:
        error_message = "Cannot draft section: Missing current_grant_details, organization_profile, or current_section_name in state."
        print(error_message)
        log_messages.append(error_message)
        return {
            "error_message": error_message,
            "log_messages": log_messages,
            "current_draft_content": "", # Ensure key exists
            "iteration_count": state.get("iteration_count", 0) # Pass through iteration count
        }

    # Combine editor_feedback and specific_instructions from state to pass to the agent
    combined_instructions = ""
    if specific_instructions_from_state:
        combined_instructions += specific_instructions_from_state
    if editor_feedback:
        if combined_instructions: # Add a separator if specific_instructions already exist
            combined_instructions += "\n\n--- Previous Editor Feedback ---\n"
        combined_instructions += editor_feedback
    
    if not combined_instructions:
        combined_instructions = '' # Ensure it's an empty string if nothing was provided

    new_iteration_count = state.get('iteration_count', 0) + 1
    node_error_message = None
    draft_text = ""

    try:
        print(f"Calling WriterAgent.draft_section for section: '{current_section_name}', Iteration: {new_iteration_count}")
        draft_text = agent.draft_section(
            grant_opportunity_details=current_grant_details,
            org_profile=organization_profile,
            section_name=current_section_name,
            specific_instructions=combined_instructions
        )

        if draft_text.startswith("// Error"):
            agent_error = f"WriterAgent failed to draft section '{current_section_name}': {draft_text}"
            print(agent_error)
            log_messages.append(agent_error)
            node_error_message = agent_error # Set node error from agent error
            draft_text = "" # Clear draft text on agent error
        else:
            log_messages.append(f"Drafted section (Iteration {new_iteration_count}): {current_section_name}.")
            # Clear editor_feedback from state if it was successfully incorporated
            # This is a choice: do we want to clear it here or let the graph logic handle it?
            # For now, let's assume this node is responsible for clearing it after use.
            # However, returning it as None in the output dict is how state is changed.
            # The prompt doesn't explicitly say to clear editor_feedback, so we won't add it to output dict.
            # If it needs to be cleared, the graph would route to a state update node or this node would return 'editor_feedback': None.

    except Exception as e:
        unexpected_error = f"Unexpected error in node_draft_section for '{current_section_name}': {str(e)}"
        print(unexpected_error)
        log_messages.append(unexpected_error)
        node_error_message = unexpected_error
        draft_text = "" # Clear draft text on unexpected error

    return {
        "current_draft_content": draft_text,
        "iteration_count": new_iteration_count,
        "log_messages": log_messages,
        "error_message": node_error_message
        # If editor_feedback needs to be cleared, add: 'editor_feedback': None
    }
