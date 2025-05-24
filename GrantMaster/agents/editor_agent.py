from openai import OpenAI
import os # For __main__ block, to load .env

class EditorAgent:
    def __init__(self, openai_client, model="gpt-4o"): # Using a capable model for review
        self.openai_client = openai_client
        self.model = model
        print(f"EditorAgent initialized with model: {self.model}")

    def review_draft(self, draft_text, section_name, grant_guidelines_summary=''):
        print(f"EditorAgent: Reviewing draft for section '{section_name}'...")

        guidelines_content = "No specific grant guidelines summary was provided."
        if grant_guidelines_summary:
            guidelines_content = f"Relevant Grant Guidelines Summary:\n---\n{grant_guidelines_summary}\n---"

        prompt = f"""
        You are an expert AI grant editor. Your task is to critically review a draft for a specific grant proposal section and provide actionable feedback.

        **Section Name:** {section_name}

        **Draft Text to Review:**
        ---
        {draft_text}
        ---

        **Contextual Information (if provided):**
        {guidelines_content}

        **Review Instructions:**
        Please review the draft text for the "{section_name}" based on the following criteria:
        1.  **Clarity and Conciseness:** Is the language clear, direct, and free of jargon where possible? Are there any run-on sentences or overly complex phrases?
        2.  **Coherence and Flow:** Do the ideas flow logically? Is there a clear structure within the section?
        3.  **Grammar and Spelling:** Are there any grammatical errors, typos, or punctuation mistakes?
        4.  **Persuasiveness and Impact:** Is the writing compelling? Does it effectively make its case or convey the necessary information to the funder?
        5.  **Adherence to Guidelines (if provided):** Does the draft seem to align with the (optional) grant guidelines summary provided above? Highlight any potential misalignments.

        **Output Requirements:**
        - Provide your feedback as a list of specific, actionable points or a summarized critique.
        - Focus on what can be improved and how. Be constructive.
        - **Do NOT rewrite the entire section.** Your role is to provide feedback on the existing draft.
        - The output should be ONLY the feedback text. Do not include any introductory phrases like "Here is the feedback:" or any concluding remarks.

        Begin your review of the "{section_name}" draft now:
        """

        print(f"EditorAgent: Sending request to OpenAI API for review of section '{section_name}'.")
        try:
            completion = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI grant editor. Your task is to provide critical and actionable feedback on a grant section draft based on provided criteria. Do not rewrite the draft; only provide feedback points or a summarized critique."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4, # A moderate temperature for insightful but focused feedback
            )
            feedback_text = completion.choices[0].message.content
            print(f"EditorAgent: Received feedback for section '{section_name}' from OpenAI API.")
            # Basic cleanup: strip leading/trailing whitespace
            return feedback_text.strip() if feedback_text else ""
            
        except Exception as e:
            print(f"EditorAgent ERROR: OpenAI API call failed for review of section '{section_name}': {e}")
            return f"// Error generating review for {section_name}: {e} //"

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
        print("OpenAI API Key loaded successfully for EditorAgent test.")
        try:
            client = OpenAI(api_key=api_key)
            print("OpenAI client initialized for EditorAgent test.")
            
            editor = EditorAgent(openai_client=client) # Uses default gpt-4o

            # Mock data for testing
            mock_section_name = "Project Impact and Evaluation"
            mock_draft = """
            Our project aims to make a big difference. We will see many positive changes. 
            The outcomes are expected to be significant for the community. We will track progress 
            using surveys and also by counting how many people attend our workshops. This data 
            will show our success. The project's impact is very good and helps everyone lots.
            We think this is a good plan for evaluation.
            """
            
            mock_guidelines = """
            - Evaluation section must clearly define SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound).
            - Detail specific metrics that will be tracked for each objective.
            - Describe data collection methods and frequency.
            - Explain how results will be analyzed and disseminated.
            - Address potential challenges in evaluation and mitigation strategies.
            """
            
            print(f"\n--- Running EditorAgent.review_draft() DEMO for section: '{mock_section_name}' (with guidelines) ---")
            
            feedback_with_guidelines = editor.review_draft(
                mock_draft,
                mock_section_name,
                mock_guidelines
            )
            
            print(f"\n--- EditorAgent Feedback for '{mock_section_name}' (with guidelines) ---")
            if feedback_with_guidelines and not feedback_with_guidelines.startswith("// Error"):
                print(feedback_with_guidelines)
            else:
                print(f"Could not generate feedback or an error occurred: {feedback_with_guidelines}")
            print(f"--- End of EditorAgent DEMO for '{mock_section_name}' ---")

            # Example of reviewing without specific guidelines
            mock_section_name_2 = "Organizational Capacity"
            mock_draft_2 = "We are a good team. Our organization has experience. We can do this project well. We have strong leaders and good staff."
            
            print(f"\n--- Running EditorAgent.review_draft() DEMO for section: '{mock_section_name_2}' (no guidelines) ---")
            feedback_no_guidelines = editor.review_draft(
                mock_draft_2,
                mock_section_name_2
            )
            print(f"\n--- EditorAgent Feedback for '{mock_section_name_2}' (no guidelines) ---")
            if feedback_no_guidelines and not feedback_no_guidelines.startswith("// Error"):
                print(feedback_no_guidelines)
            else:
                print(f"Could not generate feedback or an error occurred: {feedback_no_guidelines}")
            print(f"--- End of EditorAgent DEMO for '{mock_section_name_2}' ---")

        except Exception as e:
            print(f"An error occurred during EditorAgent demo setup or execution: {e}")
            import traceback
            traceback.print_exc()
