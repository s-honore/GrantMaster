# GrantMaster/agents/researcher_agent.py
from openai import OpenAI
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time # For explicit waits if necessary, or for post-login observation
import json # Added for WebSleuthAgent
from GrantMaster.core.graph_state import GrantMasterState # Ensure this import is added at the top of the file
# Consider adding other imports like 'requests' later for actual web interaction.

def perform_website_login(url, username, password, timeout=10):
    # Specific locators for the target website (e.g., grants.gov via Login.gov)
    # These are based on the example https://www.grants.gov/login (which redirects to secure.login.gov)
    # USERNAME_LOCATOR_TYPE = By.NAME 
    # USERNAME_LOCATOR_VALUE = "xoo-el-username" # Example, to be confirmed on actual site
    # PASSWORD_LOCATOR_TYPE = By.NAME
    # PASSWORD_LOCATOR_VALUE = "xoo-el-password" # Example, to be confirmed
    # LOGIN_BUTTON_LOCATOR_TYPE = By.CSS_SELECTOR
    # LOGIN_BUTTON_LOCATOR_VALUE = "button.xoo-el-login-btn" # Example, to be confirmed

    internal_logs = [] # Initialize internal_logs list

    # Commenting out the generic locator lists as per refactoring instructions
    # username_locators = [
    #     (By.ID, 'username'), (By.NAME, 'username'),
    #     (By.ID, 'user'), (By.NAME, 'user'),
    #     (By.ID, 'email'), (By.NAME, 'email'),
    #     (By.ID, 'userid'), (By.NAME, 'userid')
    # ]
    # password_locators = [
    #     (By.ID, 'password'), (By.NAME, 'password'),
    #     (By.ID, 'pass'), (By.NAME, 'pass'),
    #     (By.ID, 'passwd'), (By.NAME, 'passwd')
    # ]
    # login_button_locators = [
    #     (By.ID, 'login_button'), (By.NAME, 'login_button'),
    #     (By.ID, 'signin'), (By.NAME, 'signin'),
    #     (By.XPATH, "//button[contains(translate(., 'LOGIN', 'login'), 'login')]"),
    #     (By.XPATH, "//input[@type='submit' and contains(translate(@value, 'LOGIN', 'login'), 'login')]"),
    #     (By.CSS_SELECTOR, "button[type='submit']"),
    #     (By.ID, 'login'), (By.NAME, 'login')
    # ]

    driver = None
    try:
        internal_logs.append(f"perform_website_login: Attempting to initialize Chrome WebDriver...") # Changed from print
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--log-level=1") # You can adjust log level if needed
        # chrome_options.add_argument("--verbose") # May or may not be supported directly
        # chrome_options.add_argument("--enable-logging=stderr --v=1") # More detailed chrome logging

        # Forcing the browser binary location
        expected_browser_path = "/usr/bin/chromium"
        internal_logs.append(f"perform_website_login: Attempting to set browser binary location to: {expected_browser_path}") # Changed from print
        chrome_options.binary_location = expected_browser_path

        # Use system-installed chromedriver
        system_chromedriver_path = '/usr/bin/chromedriver'
        
        # Reinstate verbose logging for chromedriver service
        service_args = ['--verbose', '--log-path=/tmp/chromedriver.log']
        internal_logs.append(f"perform_website_login: Initializing ChromeService with system chromedriver path: {system_chromedriver_path} and service_args: {service_args}") # Changed from print
        service = ChromeService(executable_path=system_chromedriver_path, service_args=service_args)
        
        internal_logs.append("perform_website_login: Attempting to start webdriver.Chrome with specified service and options...") # Changed from print
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        internal_logs.append(f"perform_website_login: WebDriver initialized. Navigating to URL: {url}")
        driver.get(url)
        internal_logs.append(f"perform_website_login: Successfully navigated to URL: {url}")
        wait = WebDriverWait(driver, timeout)

        # Click the "Kom indenfor" login trigger button to open the popup
        LOGIN_TRIGGER_BUTTON_LOCATOR = (By.CSS_SELECTOR, "a.xoo-el-login-tgr")
        internal_logs.append(f"perform_website_login: Looking for login trigger button: {LOGIN_TRIGGER_BUTTON_LOCATOR[1]}")
        try:
            login_trigger_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(LOGIN_TRIGGER_BUTTON_LOCATOR)
            )
            internal_logs.append("perform_website_login: Login trigger button found. Clicking it to open popup.")
            login_trigger_button.click()
            internal_logs.append("perform_website_login: Login trigger button clicked. Pausing for popup to appear.")
            time.sleep(1.5) # Give a moment for the popup to start loading
        except TimeoutException:
            error_detail = f"TimeoutException: Could not find or click the 'Kom indenfor' login trigger button with locator {LOGIN_TRIGGER_BUTTON_LOCATOR}."
            internal_logs.append(f"perform_website_login: ERROR: {error_detail}")
            # The main try-except block of perform_website_login will handle driver.quit() and returning (None, internal_logs)
            raise # Re-raise the TimeoutException to be caught by the outer handler.
        except Exception as e_trigger: # Catch other potential errors during trigger click
            error_detail = f"Error clicking login trigger button {LOGIN_TRIGGER_BUTTON_LOCATOR}: {type(e_trigger).__name__} - {str(e_trigger)}"
            internal_logs.append(f"perform_website_login: ERROR: {error_detail}")
            raise # Re-raise to be caught by the outer handler

        # Find and fill username in the popup
        username_locator = (By.NAME, "xoo-el-username")
        internal_logs.append(f"perform_website_login: Attempting to find username field in popup with locator: {username_locator}")
        try:
            username_field = wait.until(EC.presence_of_element_located(username_locator))
            internal_logs.append(f"perform_website_login: Found username field in popup with locator: {username_locator}")
        except TimeoutException:
            internal_logs.append(f"perform_website_login: Timeout waiting for username field in popup with locator: {username_locator}")
            raise NoSuchElementException(f"Could not find username field in popup with locator {username_locator} within timeout {timeout}s.")
        
        internal_logs.append(f"perform_website_login: Sending username '{username}' to popup field.")
        username_field.send_keys(username)
        time.sleep(0.5) # Pause after sending keys
        internal_logs.append("perform_website_login: Username sent to popup field.")

        # Find and fill password in the popup
        password_locator = (By.NAME, "xoo-el-password")
        internal_logs.append(f"perform_website_login: Attempting to find password field in popup with locator: {password_locator}")
        try:
            # Using the main 'wait' object which uses the function's 'timeout' parameter.
            password_field = wait.until(EC.presence_of_element_located(password_locator))
            internal_logs.append(f"perform_website_login: Found password field in popup with locator: {password_locator}")
        except TimeoutException:
            internal_logs.append(f"perform_website_login: Timeout waiting for password field in popup with locator: {password_locator}")
            raise NoSuchElementException(f"Could not find password field in popup with locator {password_locator} within timeout {timeout}s.")

        internal_logs.append("perform_website_login: Sending password to popup field...")
        password_field.send_keys(password)
        time.sleep(0.5) # Pause after sending keys
        internal_logs.append("perform_website_login: Password sent to popup field.")

        # Find and click login button in the popup
        login_button_locator = (By.CSS_SELECTOR, "button.xoo-el-login-btn")
        internal_logs.append(f"perform_website_login: Attempting to find login button in popup with locator: {login_button_locator}")
        try:
            login_button = wait.until(EC.element_to_be_clickable(login_button_locator))
            internal_logs.append(f"perform_website_login: Found login button in popup with locator: {login_button_locator}")
        except TimeoutException:
            internal_logs.append(f"perform_website_login: Timeout waiting for login button in popup with locator: {login_button_locator} or it was not clickable.")
            raise NoSuchElementException(f"Could not find login button in popup with locator {login_button_locator} or it was not clickable within timeout {timeout}s.")
        
        internal_logs.append(f"perform_website_login: Attempting to click login button in popup with locator {login_button_locator}")
        login_button.click()
        # time.sleep(3) is already part of the post-login check, so it's effectively after the click.
        internal_logs.append("perform_website_login: Login button in popup click action performed.")

        # Post-login check (placeholder - very basic)
        # A more robust check would be to wait for a specific element that appears only after login,
        # or to check if the URL changes to a dashboard/account page.
        time.sleep(3) # Wait for page to potentially redirect/load
        
        current_url = driver.current_url
        if "login" in current_url.lower() or url == current_url: # Simple check if URL still looks like a login page
            # This check is very basic. Many sites redirect to login on failure.
            # A more reliable check is needed, e.g., looking for error messages or specific post-login elements.
            internal_logs.append(f"perform_website_login: Post-login check: Current URL ({current_url}) might indicate login failure or no redirect.")
            # Consider checking for common error messages here if possible
            # error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
            # if any("invalid" in msg.text.lower() for msg in error_messages if msg.is_displayed()):
            #     internal_logs.append("perform_website_login: Login error message detected on page.")
            #     raise Exception("Login failed: Error message detected on page.")

        internal_logs.append(f"perform_website_login: Login attempt to {url} seems successful. Current URL: {driver.current_url}")
        return driver, internal_logs

    except TimeoutException as e:
        # Note: Specific timeout context (e.g. "waiting for username") is logged within the try-except blocks for element finding.
        # This top-level TimeoutException might occur if driver.get(url) times out, or other WebDriverWait calls not caught by more specific handlers.
        internal_logs.append(f"perform_website_login: ERROR: A timeout occurred during login process. Details: {e}")
        if driver:
            internal_logs.append("perform_website_login: Quitting driver due to TimeoutException.")
            driver.quit()
        return None, internal_logs
    except NoSuchElementException as e:
        # Specific context for NoSuchElementException is logged before raising it (e.g. "Username field not found").
        # This top-level handler catches it if not handled more specifically or re-raised.
        internal_logs.append(f"perform_website_login: ERROR: Could not find a required login element. Details: {e}")
        if driver:
            internal_logs.append("perform_website_login: Quitting driver due to NoSuchElementException.")
            driver.quit()
        return None, internal_logs
    except Exception as e:
        internal_logs.append(f"perform_website_login: ERROR: An unexpected error occurred: {type(e).__name__} - {e}")
        if driver:
            internal_logs.append("perform_website_login: Quitting driver due to unexpected exception.")
            driver.quit()
        return None, internal_logs

class WebSleuthAgent:
    def __init__(self, api_key: str, model="gpt-3.5-turbo"): # Modified signature
        self.api_key = api_key # Store api_key if needed, or use directly
        self.openai_client = OpenAI(api_key=self.api_key) # Initialize client
        self.model = model
        # Max characters for page source to feed to LLM (to avoid excessive token usage)
        # This is a very rough limit, actual token limits are more complex.
        self.max_page_source_chars = 15000 # Approx 3k-4k tokens, well within 16k gpt-3.5-turbo context
        # The print statement in __init__ remains as it's for agent initialization, not per-run logging.
        print(f"WebSleuthAgent initialized with model: {self.model}")

    def research_and_extract(self, driver, research_task_description):
        ws_internal_logs = []
        ws_internal_logs.append(f"WebSleuthAgent: Starting research and extraction. Task: '{research_task_description}'")
        try:
            page_source = driver.page_source
            ws_internal_logs.append(f"WebSleuthAgent: Page source obtained (length: {len(page_source)} chars).")
        except Exception as e:
            ws_internal_logs.append(f"WebSleuthAgent ERROR: Could not get page source from driver: {e}")
            return [], ws_internal_logs

        if len(page_source) > self.max_page_source_chars:
            ws_internal_logs.append(f"WebSleuthAgent WARNING: Page source is too long ({len(page_source)} chars). Truncating to {self.max_page_source_chars} chars.")
            page_source = page_source[:self.max_page_source_chars]

        prompt = f"""
        You are an expert AI assistant tasked with extracting grant information from a given web page's source code.
        The user's specific research task is: "{research_task_description}"

        Please analyze the following HTML page source and extract all grant opportunities that match the research task.
        For each grant, provide the following details if available:
        - title: The title of the grant.
        - funder: The organization funding the grant.
        - deadline: The application deadline (try to format as YYYY-MM-DD if possible, otherwise as found).
        - description: A brief description of the grant.
        - eligibility: Key eligibility criteria.
        - focus_areas: The main areas or topics the grant supports.

        Return the information as a JSON list of objects. Each object should represent one grant.
        Example of a single JSON object:
        {{
            "title": "Example Grant Title",
            "funder": "Example Funder Name",
            "deadline": "2024-12-31",
            "description": "This is a sample description of the grant.",
            "eligibility": "Non-profit organizations in the education sector.",
            "focus_areas": "STEM Education, Literacy Programs"
        }}

        If no grants matching the task are found, or if the page source does not seem to contain grant information, return an empty list [].
        Ensure your output is only the JSON list, with no introductory text or explanations.

        Page Source to analyze:
        ---
        {page_source}
        ---
        """
        ws_internal_logs.append(f"WebSleuthAgent: Sending prompt to LLM (task: '{research_task_description}', HTML source length: {len(page_source)}).")
        # ws_internal_logs.append(f"WebSleuthAgent: Full prompt (excluding HTML source for brevity): {prompt.split('Page Source to analyze:')[0]}...") # Optional: Log part of the prompt

        try:
            completion = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI assistant that extracts grant information from web page content and returns it as a valid JSON list of objects, where each object has keys: title, funder, deadline, description, eligibility, focus_areas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0, # Lower temperature for more deterministic output in extraction tasks
                # response_format={ "type": "json_object" } # Requires GPT-4 Turbo or newer, good for ensuring JSON
            )
            response_content = completion.choices[0].message.content
            ws_internal_logs.append("WebSleuthAgent: Received response from OpenAI API.")
            ws_internal_logs.append(f"WebSleuthAgent: Raw LLM response snippet (first 500 chars): {response_content[:500]}")

        except Exception as e:
            ws_internal_logs.append(f"WebSleuthAgent ERROR: OpenAI API call failed: {e}")
            return [], ws_internal_logs

        try:
            # The response might be a string that looks like a JSON list.
            # Sometimes LLMs wrap JSON in ```json ... ```, try to strip that if present.
            if response_content.strip().startswith("```json"):
                response_content = response_content.strip()[7:-3].strip()
            elif response_content.strip().startswith("```"): # Generic code block
                 response_content = response_content.strip()[3:-3].strip()

            extracted_grants = json.loads(response_content)
            if not isinstance(extracted_grants, list):
                ws_internal_logs.append(f"WebSleuthAgent WARNING: LLM response was valid JSON but not a list. Type: {type(extracted_grants)}. Returning as a single item list if it's a dict, else empty.")
                if isinstance(extracted_grants, dict): # Check if it's a dictionary
                     return [extracted_grants], ws_internal_logs # Wrap a single dict in a list
                return [], ws_internal_logs # Or handle as error / return empty list
            
            ws_internal_logs.append(f"WebSleuthAgent: Successfully parsed JSON response. Found {len(extracted_grants)} item(s).")
            return extracted_grants, ws_internal_logs
        except json.JSONDecodeError as e:
            ws_internal_logs.append(f"WebSleuthAgent ERROR: Failed to decode JSON from OpenAI response: {e}")
            ws_internal_logs.append(f"WebSleuthAgent: ERROR - Failed to decode JSON. Problematic snippet: {response_content[:500]}")
            return [], ws_internal_logs
        except Exception as e:
            ws_internal_logs.append(f"WebSleuthAgent ERROR: An unexpected error occurred during JSON parsing or handling: {e}")
            return [], ws_internal_logs

class ResearcherAgent:
    def __init__(self, openai_client):
        self.openai_client = openai_client
        print("ResearcherAgent initialized.")
        # Potentially load specific configurations or tools for research

    def perform_research(self, website_url, login_credentials=None):
        # Placeholder for actual web login, browsing, and information extraction
        # This will eventually use Selenium/Requests and then OpenAI for summarization/extraction
        print(f"ResearcherAgent: Simulating research on {website_url} (login: {login_credentials is not None})...")
        
        # In a real scenario, this would involve web interaction and AI processing.
        # For now, let's return something similar to what the Orchestrator's mock expects.
        mock_extracted_data = [
            {'grant_title': 'Researched Grant Alpha', 'funder': 'Live Funder Inc.', 'deadline': '2026-01-15', 'description': 'Description from REAL research agent for Grant Alpha.', 'eligibility': 'Open to all registered non-profits.', 'focus_areas': 'AI Ethics, Community Development', 'raw_research_data': 'Extensive notes compiled from website content, FAQs, and linked PDF documents for Grant Alpha.'},
            {'grant_title': 'Researched Grant Beta', 'funder': 'Web Data Funder LLC', 'deadline': '2026-02-20', 'description': 'Another detailed description from REAL research agent for Grant Beta.', 'eligibility': 'US-based educational institutions.', 'focus_areas': 'Data Science, Online Learning Platforms', 'raw_research_data': 'Data snippets, terms of service, and application guidelines for Grant Beta.'}
        ]
        print(f"ResearcherAgent: Mock research complete, returning {len(mock_extracted_data)} item(s).")
        return mock_extracted_data

def node_perform_login(state: GrantMasterState) -> dict:
    """
    LangGraph node to perform website login using credentials from the state.
    Updates the state with the authenticated driver session or an error message.
    """
    print("Attempting node_perform_login...") # This print is outside perform_website_login, so it remains.
    raw_url = state.get("research_website_url")
    credentials = state.get("research_login_credentials")
    log_messages = list(state.get("log_messages", [])) # Initialize log_messages

    if not raw_url: # Check for raw_url specifically
        error_message = "Login failed: research_website_url not found in state."
        print(error_message) # This print is outside perform_website_login, so it remains.
        log_messages.append(error_message)
        return {
            "error_message": error_message,
            "authenticated_driver_session": None,
            "log_messages": log_messages,
        }

    if not credentials: # Keep existing credentials check
        error_message = "Login failed: research_login_credentials not found in state."
        return {
            "error_message": error_message,
            "authenticated_driver_session": None,
            "log_messages": log_messages,
        }
    
    # Scheme checking for raw_url
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        url_for_login_function = f"https://{raw_url}"
        log_message = f"URL scheme missing, prepended 'https://'. Original: '{raw_url}', Used: '{url_for_login_function}'"
        print(log_message) # This print is outside perform_website_login, so it remains.
        log_messages.append(log_message)
    else:
        url_for_login_function = raw_url
        log_message = f"Attempting login with provided URL: {url_for_login_function}"
        print(log_message) # This print is outside perform_website_login, so it remains.
        log_messages.append(log_message)

    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        error_message = "Login failed: Username or password not found in research_login_credentials."
        print(error_message) # This print is outside perform_website_login, so it remains.
        log_messages.append(error_message)
        return {
            "error_message": error_message,
            "authenticated_driver_session": None,
            "log_messages": log_messages,
        }

    driver = None # Initialize driver to None before the try block
    internal_login_logs = [] # Initialize for perform_website_login's logs
    try:
        # Assuming perform_website_login is defined in the same file
        driver, internal_login_logs = perform_website_login(url_for_login_function, username, password) # Capture logs
        log_messages.extend(internal_login_logs) # Append internal logs to the main log_messages list

        if driver:
            success_message = f"Login successful to {url_for_login_function}."
            print(success_message) # This print is outside perform_website_login, so it remains.
            log_messages.append(success_message)
            return {
                "authenticated_driver_session": driver,
                "log_messages": log_messages,
                "error_message": None, # Explicitly set error_message to None on success
            }
        else:
            # perform_website_login now returns its logs, which have been appended.
            # The error message here should reflect that perform_website_login indicated failure.
            failure_message = f"Login attempt to {url_for_login_function} failed internally (driver not returned). See appended logs for details from perform_website_login."
            print(failure_message) # This print is outside perform_website_login, so it remains.
            log_messages.append(failure_message)
            return {
                "error_message": f"Login failed for {url_for_login_function}. Driver not returned by perform_website_login. Check appended logs.",
                "authenticated_driver_session": None,
                "log_messages": log_messages,
            }
    except Exception as e:
        error_detail = f"An unexpected error occurred in node_perform_login while calling or processing result from perform_website_login for {url_for_login_function}: {type(e).__name__} - {str(e)}"
        print(error_detail) # This print is outside perform_website_login, so it remains.
        log_messages.extend(internal_login_logs) # Ensure any partial logs from perform_website_login are added
        log_messages.append(error_detail)
        if driver: # If driver was assigned (meaning perform_website_login was successful before this outer exception)
            print("Quitting driver due to an error in node_perform_login after successful login function call.") # This print is outside perform_website_login
            driver.quit()
        return {
            "error_message": error_detail, # Use the more detailed error message
            "authenticated_driver_session": None,
            "log_messages": log_messages,
        }

# Make sure WebSleuthAgent class definition is available above this function.
# GrantMasterState should already be imported from ..core.graph_state

def node_research_and_extract(state: GrantMasterState, agent: WebSleuthAgent) -> dict:
    """
    LangGraph node to perform research and extraction using WebSleuthAgent.
    Updates state with extracted grant opportunities or an error message.
    The 'agent' parameter (WebSleuthAgent instance) will be partially applied
    when this node is added to the graph.
    """
    print("Attempting node_research_and_extract...")
    authenticated_driver = state.get("authenticated_driver_session")
    # Use a default research task if not provided in the state
    research_task_description = state.get('current_research_task_description', 'Find relevant grant opportunities')
    
    log_messages = list(state.get("log_messages", []))
    ws_logs = [] # Initialize to capture logs from WebSleuthAgent

    # This code assumes authenticated_driver and log_messages are already defined.
    # If authenticated_driver could be None here, wrap this in an 'if authenticated_driver:' block.
    
    if authenticated_driver: # Added this check for safety
        try:
            current_url = authenticated_driver.current_url
            page_title = authenticated_driver.title
            log_messages.append(f"Research node: Authenticated driver. Current URL: {current_url}, Title: {page_title}")

            page_html_snippet = authenticated_driver.page_source[:500] # Get first 500 chars
            log_messages.append(f"Research node: Page source snippet (first 500 chars): {page_html_snippet}")

        except Exception as e_pageinfo:
            error_detail = f"Error getting initial page info in research node: {type(e_pageinfo).__name__} - {str(e_pageinfo)}"
            log_messages.append(f"Research node: ERROR: {error_detail}")
            # Depending on desired behavior, you might choose to not proceed if this fails.
            # For now, just log and let subsequent steps attempt execution.
    else:
        log_messages.append("Research node: Authenticated driver not found. Skipping initial page logging.")


# The rest of the function (e.g., checking if authenticated_driver is truly None for error returns, calling agent.research_and_extract) follows.
    if not authenticated_driver:
        error_message = "Cannot research, not logged in."
        # print(error_message) # Original print, now handled by log_messages
        log_messages.append(f"Research node: ERROR - {error_message}") # More consistent logging
        return {
            "error_message": error_message,
            "extracted_grant_opportunities": [], # Ensure this key is present
            "log_messages": log_messages,
        }

    try:
        log_messages.append(f"Research node: Calling WebSleuthAgent.research_and_extract with task: '{research_task_description}'")
        # Assuming 'agent' is an instance of WebSleuthAgent passed in
        results_list, ws_logs = agent.research_and_extract(authenticated_driver, research_task_description)
        log_messages.extend(ws_logs) # Append logs from WebSleuthAgent
        
        # research_and_extract returns ([], ws_logs) on error or if nothing found.
        # The internal logs of research_and_extract will indicate if an error occurred.
        
        success_message = f"Research node: WebSleuthAgent finished. Found {len(results_list)} potential opportunities."
        # print(success_message) # Original print, now handled by log_messages
        log_messages.append(success_message)
        
        return {
            "extracted_grant_opportunities": results_list,
            "log_messages": log_messages,
            "error_message": None, # Explicitly set to None on successful execution path
        }
    except Exception as e:
        # This handles unexpected errors within the node function itself,
        # potentially during the call to research_and_extract or if it raises an unexpected exception.
        error_message = f"An unexpected error occurred in node_research_and_extract: {type(e).__name__} - {str(e)}"
        # print(error_message) # Original print, now handled by log_messages
        log_messages.extend(ws_logs) # Append any logs that might have been returned before exception
        log_messages.append(f"Research node: ERROR - {error_message}")
        return {
            "extracted_grant_opportunities": [],
            "log_messages": log_messages,
            "error_message": error_message,
        }

if __name__ == '__main__':
    # Example Usage (requires OPENAI_API_KEY in .env in the project root: GrantMaster/.env)
    from dotenv import load_dotenv

    # Construct the path to the .env file relative to this script's location
    # agents/researcher_agent.py -> GrantMaster/.env means going up one level.
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    if os.path.exists(dotenv_path):
        print(f"Loading .env file from: {os.path.abspath(dotenv_path)}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print(f"Warning: .env file not found at {os.path.abspath(dotenv_path)}. Attempting to load from default location or environment.")
        # Fallback, try loading without specifying path (might pick up if CWD is project root)
        load_dotenv() 

    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure a .env file with OPENAI_API_KEY=YOUR_API_KEY_HERE exists in the GrantMaster project root directory.")
    else:
        print("OpenAI API Key loaded successfully.")
        try:
            client = OpenAI(api_key=api_key)
            print("OpenAI client initialized.")
            
            researcher = ResearcherAgent(openai_client=client)
            
            # Example: Using a mock URL for now
            print("\n--- Running ResearcherAgent.perform_research() DEMO ---")
            results = researcher.perform_research(
                website_url="http://mock-grant-portal.example.com",
                login_credentials={"user": "test_user", "pass": "test_pass"}
            )
            print("\n--- ResearcherAgent Results ---")
            if results:
                for item in results:
                    print(f"  Title: {item.get('grant_title')}, Funder: {item.get('funder')}, Deadline: {item.get('deadline')}")
            else:
                print("  No results returned from researcher.")
            print("--- End of ResearcherAgent Results ---")

            # ... (after existing ResearcherAgent demo)

            print("\n--- Testing perform_website_login ---")
            # Note: Using a public test site. Replace with other sites for more specific testing if needed.
            # This site is for web scraping practice and has a simple login form.
            # http://quotes.toscrape.com/login uses username/password: user/user or admin/admin
            # However, its login fields might not match the generic locators perfectly.
            # Let's use a more generic placeholder URL for now to test the locator logic and error handling.
            # If you have a specific public test login page with known simple IDs, use that.
            
            # Test case 1: A site known to fail or a placeholder (to test error handling)
            print("\nTest Case 1: Placeholder URL (expects failure or robust error handling)")
            test_login_url_fail = "http://nonexistentgrantportal.example.com/login"
            # test_login_url_fail = "http://quotes.toscrape.com/login" # A real site to try
            test_username_fail = "testuser"
            test_password_fail = "testpassword"
            
            authenticated_driver_fail = perform_website_login(test_login_url_fail, test_username_fail, test_password_fail)
            
            if authenticated_driver_fail:
                print(f"Login to {test_login_url_fail} reported as successful. Current URL: {authenticated_driver_fail.current_url}")
                print(f"Page title: {authenticated_driver_fail.title}")
                authenticated_driver_fail.quit()
                print("Browser closed after successful login test (Test Case 1).")
            else:
                print(f"Login failed or was skipped for {test_login_url_fail}, as expected for this test case.")
            
            # Test case 2: (Optional) A real site if one is known and suitable
            # print("\nTest Case 2: Attempt with quotes.toscrape.com/login")
            # test_login_url_real = "http://quotes.toscrape.com/login"
            # # This site's fields are 'username' and 'password', button is input type=submit value=Login
            # # Default locators should find these. Credentials are 'user'/'user' or 'admin'/'admin'
            # authenticated_driver_real = perform_website_login(test_login_url_real, "user", "user")
            # if authenticated_driver_real:
            #     print(f"Login to {test_login_url_real} reported as successful. Current URL: {authenticated_driver_real.current_url}")
            #     # Check for a known post-login element, e.g., a logout link
            #     try:
            #         logout_link = WebDriverWait(authenticated_driver_real, 5).until(
            #             EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/logout')]"))
            #         )
            #         print("Logout link found, confirming successful login.")
            #     except TimeoutException:
            #         print("Logout link not found. Login might not have been fully successful or page structure changed.")
            #     authenticated_driver_real.quit()
            #     print("Browser closed after login test (Test Case 2).")
            # else:
            #     print(f"Login failed for {test_login_url_real}.")

            print("--- Finished testing perform_website_login ---")

            # ... (after existing tests for perform_website_login)

            print("\n--- Testing WebSleuthAgent with Mock Driver ---")

            class MockSeleniumDriver:
                def __init__(self, page_source_content=""):
                    self.page_source = page_source_content
                    print("MockSeleniumDriver initialized.")

                def quit(self):
                    print("MockSeleniumDriver quit() called.")

            # Sample HTML-like content with grant information
            mock_html_content = """
            <html><body>
                <h1>Grant Opportunities</h1>
                <div class="grant-item">
                    <h2>Environmental Research Grant</h2>
                    <p>Funder: Green Future Foundation</p>
                    <p>Deadline: 2024-12-31</p>
                    <p>Description: Supports research into renewable energy sources.</p>
                    <p>Eligibility: Accredited research institutions.</p>
                    <p>Focus Areas: Renewable Energy, Climate Change</p>
                </div>
                <div class="grant-item">
                    <h2>Community Art Project Grant</h2>
                    <p>Funder: Creative Collective</p>
                    <p>Deadline: 2024-11-15</p>
                    <p>Description: Funds community-based art projects.</p>
                    <p>Eligibility: Local artists and community groups.</p>
                    <p>Focus Areas: Public Art, Community Engagement</p>
                </div>
                <div class="other-info">
                    <p>This is not a grant. Just some other text.</p>
                </div>
                <div class="grant-item">
                    <h2>Tech Innovation Challenge - No Deadline Info</h2>
                    <p>Funder: Innovate Hub</p>
                    <p>Description: For groundbreaking tech solutions. Eligibility: Startups and SMEs.</p>
                    <p>Focus Areas: AI, SaaS, Fintech</p>
                </div>
            </body></html>
            """

            mock_driver = MockSeleniumDriver(page_source_content=mock_html_content)
            
            # Ensure 'client' (OpenAI client) is available from the earlier part of __main__
            if 'client' in locals() and client is not None:
                websleuth = WebSleuthAgent(openai_client=client)
                
                research_task = "Extract all available grant opportunities."
                print(f"WebSleuthAgent: Calling research_and_extract with task: '{research_task}'")
                
                extracted_data = websleuth.research_and_extract(mock_driver, research_task)
                
                print("\n--- WebSleuthAgent Mock Test Results ---")
                if extracted_data:
                    for i, grant in enumerate(extracted_data):
                        print(f"Grant {i+1}:")
                        for key, value in grant.items():
                            print(f"  {key}: {value}")
                else:
                    print("No data extracted by WebSleuthAgent in mock test, or an error occurred.")
                
                mock_driver.quit() # Call quit on the mock driver
            else:
                print("WebSleuthAgent Test: OpenAI client not available. Skipping.")
            
            print("--- Finished testing WebSleuthAgent ---")
            
        except Exception as e:
            print(f"An error occurred during ResearcherAgent demo: {e}")
            import traceback
            traceback.print_exc()
