from openai import OpenAI
import json
import os # For __main__ block, to load .env

class AnalystAgent:
    def __init__(self, openai_client, model="gpt-3.5-turbo"):
        self.openai_client = openai_client
        self.model = model
        print(f"AnalystAgent initialized with model: {self.model}")

    def analyze_suitability(self, grant_info_dict, org_profile_dict):
        print(f"AnalystAgent: Analyzing suitability for grant '{grant_info_dict.get('grant_title', 'N/A')}'...")

        prompt = f"""
        You are an expert AI assistant specializing in grant proposal analysis.
        Your task is to assess the suitability of a specific grant opportunity for an organization.

        Organization Profile:
        ---
        Name: {org_profile_dict.get('name', 'N/A')}
        Mission: {org_profile_dict.get('mission', 'N/A')}
        Projects: {org_profile_dict.get('projects', 'N/A')}
        Needs: {org_profile_dict.get('needs', 'N/A')}
        Target Demographics: {org_profile_dict.get('target_demographics', 'N/A')}
        ---

        Grant Opportunity Information:
        ---
        Title: {grant_info_dict.get('grant_title', grant_info_dict.get('title', 'N/A'))}
        Funder: {grant_info_dict.get('funder', 'N/A')}
        Deadline: {grant_info_dict.get('deadline', 'N/A')}
        Description: {grant_info_dict.get('description', 'N/A')}
        Eligibility: {grant_info_dict.get('eligibility', 'N/A')}
        Focus Areas: {grant_info_dict.get('focus_areas', 'N/A')}
        ---

        Based on the provided organization profile and grant opportunity information, please perform the following:
        1.  Analyze the alignment between the grant's focus areas, eligibility criteria, and description, and the organization's mission, current projects, stated needs, and target demographics.
        2.  Provide a brief textual rationale for your analysis (e.g., why it's a good fit, a partial fit, or a poor fit).
        3.  Provide a suitability score on a scale of 1 to 10 (where 1 is a very poor fit and 10 is an excellent fit). The score should be an integer.
        4.  Determine a status based on your analysis. Suggested statuses: 'analyzed_strong_match', 'analyzed_good_match', 'analyzed_partial_match', 'analyzed_poor_match', 'analyzed_needs_further_review'.

        Return your analysis as a single JSON object with the following keys:
        - "rationale": (string) Your textual rationale.
        - "suitability_score": (integer) The score from 1 to 10.
        - "status": (string) One of the suggested status values.

        Example JSON output:
        {{
            "rationale": "The grant's focus on renewable energy aligns well with the organization's mission and recent projects in solar technology. Eligibility criteria are also met.",
            "suitability_score": 8,
            "status": "analyzed_strong_match"
        }}

        Ensure your output is ONLY the JSON object, with no introductory text or explanations.
        """

        print("AnalystAgent: Sending request to OpenAI API...")
        try:
            # For newer models (gpt-4-1106-preview, gpt-3.5-turbo-1106 and later)
            # response_format_param = {{ "type": "json_object" }}
            # For older models, rely on prompt engineering for JSON.
            response_format_param = None 
            if "1106" in self.model or "gpt-4" in self.model: # Basic check if model might support json_object mode
                 response_format_param = {{ "type": "json_object" }}


            completion_args = {{
                "model": self.model,
                "messages": [
                    {{"role": "system", "content": "You are an expert AI that analyzes grant suitability and returns analysis in a specific JSON format."}},
                    {{"role": "user", "content": prompt}}
                ],
                "temperature": 0.1, # Lower temperature for more factual and less "creative" analysis
            }}
            if response_format_param:
                completion_args["response_format"] = response_format_param
            
            completion = self.openai_client.chat.completions.create(**completion_args)
            response_content = completion.choices[0].message.content
            print("AnalystAgent: Received response from OpenAI API.")
        except Exception as e:
            print(f"AnalystAgent ERROR: OpenAI API call failed: {e}")
            return {{"error": "OpenAI API call failed", "details": str(e)}}

        print(f"AnalystAgent: Raw API Response Content snippet: {response_content[:500]}...")
        try:
            if response_content.strip().startswith("```json"):
                response_content = response_content.strip()[7:-3].strip()
            elif response_content.strip().startswith("```"):
                response_content = response_content.strip()[3:-3].strip()
            
            analysis_result = json.loads(response_content)

            # Validate structure
            required_keys = ["rationale", "suitability_score", "status"]
            if not all(key in analysis_result for key in required_keys):
                print(f"AnalystAgent ERROR: Response JSON missing one or more required keys: {required_keys}")
                return {{"error": "Response JSON missing required keys", "response": analysis_result}}
            
            if not isinstance(analysis_result["suitability_score"], int) or \
               not (1 <= analysis_result["suitability_score"] <= 10):
                print(f"AnalystAgent ERROR: Suitability score is not an integer between 1 and 10. Score: {analysis_result['suitability_score']}")
                # Attempt to coerce or cap, or just flag
                try:
                    score = int(analysis_result["suitability_score"])
                    analysis_result["suitability_score"] = max(1, min(10, score))
                    print(f"AnalystAgent WARNING: Coerced suitability_score to {analysis_result['suitability_score']}")
                except ValueError:
                     return {{"error": "Invalid suitability_score format", "score_value": analysis_result.get("suitability_score") }}


            print(f"AnalystAgent: Successfully parsed and validated JSON response.")
            return analysis_result
            
        except json.JSONDecodeError as e:
            print(f"AnalystAgent ERROR: Failed to decode JSON from OpenAI response: {e}")
            print(f"Problematic response content snippet: {response_content[:500]}")
            return {{"error": "Failed to decode JSON response", "response_snippet": response_content[:500]}}
        except Exception as e:
            print(f"AnalystAgent ERROR: An unexpected error occurred during JSON parsing or validation: {e}")
            return {{"error": "Unexpected error processing response", "details": str(e)}}

if __name__ == '__main__':
    # Example Usage (requires OPENAI_API_KEY in .env in the project root: GrantMaster/.env)
    
    # Construct the path to the .env file relative to this script's location
    # GrantMaster/agents/analyst_agent.py -> GrantMaster/.env means going up one level.
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    # Local import for dotenv as it's only needed when script is run directly
    from dotenv import load_dotenv

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
        print("OpenAI API Key loaded successfully for AnalystAgent test.")
        try:
            # Ensure OpenAI client is initialized here for the test
            client = OpenAI(api_key=api_key)
            print("OpenAI client initialized for AnalystAgent test.")
            
            analyst = AnalystAgent(openai_client=client) # Uses default gpt-3.5-turbo

            # Mock data for testing
            mock_grant_info = {
                'grant_title': 'Community Health Initiative Grant',
                'funder': 'National Wellness Foundation',
                'deadline': '2024-10-15',
                'description': 'Supports projects that promote community health and wellness through education, outreach, and direct services. Priority given to underserved populations.',
                'eligibility': 'Registered 501(c)(3) non-profit organizations with at least 2 years of operation. Must serve target county X.',
                'focus_areas': 'Community Health, Wellness Programs, Health Education, Underserved Populations'
            }

            mock_org_profile = {
                'name': 'Local Action Group for Health',
                'mission': 'To improve the health and well-being of residents in county X through accessible programs and advocacy.',
                'projects': 'Mobile health clinic, nutrition workshops, annual health fair.',
                'needs': 'Funding for expanding mobile clinic services and developing new mental health awareness programs.',
                'target_demographics': 'Low-income families, seniors, and at-risk youth in county X.'
            }
            
            print("\n--- Running AnalystAgent.analyze_suitability() DEMO ---")
            analysis_output = analyst.analyze_suitability(mock_grant_info, mock_org_profile)
            
            print("\n--- AnalystAgent Results ---")
            if analysis_output and not analysis_output.get("error"):
                print(f"  Rationale: {analysis_output.get('rationale')}")
                print(f"  Suitability Score: {analysis_output.get('suitability_score')}")
                print(f"  Status: {analysis_output.get('status')}")
            elif analysis_output and analysis_output.get("error"):
                print(f"  Error during analysis: {analysis_output.get('error')}")
                if analysis_output.get('details'):
                    print(f"    Details: {analysis_output.get('details')}")
                if analysis_output.get('response_snippet'):
                    print(f"    Response Snippet: {analysis_output.get('response_snippet')}")
            else:
                print("  No analysis output or an unexpected empty response was received.")
            print("--- End of AnalystAgent DEMO ---")
            
        except Exception as e:
            print(f"An error occurred during AnalystAgent demo setup or execution: {e}")
            import traceback
            traceback.print_exc()
