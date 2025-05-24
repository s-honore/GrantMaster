# GrantMaster/agents/researcher_agent.py
from openai import OpenAI
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time # For explicit waits if necessary, or for post-login observation
# Consider adding other imports like 'requests' later for actual web interaction.

def perform_website_login(url, username, password, timeout=10):
    # Common locators for login elements
    # (These might need to be configurable or more sophisticated later)
    username_locators = [
        (By.ID, 'username'), (By.NAME, 'username'),
        (By.ID, 'user'), (By.NAME, 'user'),
        (By.ID, 'email'), (By.NAME, 'email'),
        (By.ID, 'userid'), (By.NAME, 'userid')
    ]
    password_locators = [
        (By.ID, 'password'), (By.NAME, 'password'),
        (By.ID, 'pass'), (By.NAME, 'pass'),
        (By.ID, 'passwd'), (By.NAME, 'passwd')
    ]
    # More specific button locators might be needed for different sites
    # e.g., (By.XPATH, "//button[contains(text(),'Login')]") or (By.CSS_SELECTOR, "button[type='submit']")
    login_button_locators = [
        (By.ID, 'login_button'), (By.NAME, 'login_button'),
        (By.ID, 'signin'), (By.NAME, 'signin'),
        (By.XPATH, "//button[contains(translate(., 'LOGIN', 'login'), 'login')]"), # Case-insensitive text search
        (By.XPATH, "//input[@type='submit' and contains(translate(@value, 'LOGIN', 'login'), 'login')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.ID, 'login'), (By.NAME, 'login')
    ]

    driver = None
    try:
        print(f"Attempting to initialize Chrome WebDriver...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        print(f"WebDriver initialized. Navigating to login page: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, timeout)

        # Find and fill username
        username_field = None
        for by, value in username_locators:
            try:
                username_field = wait.until(EC.presence_of_element_located((by, value)))
                if username_field:
                    print(f"Found username field with {by}: {value}")
                    break
            except TimeoutException:
                print(f"Username field not found with {by}: {value} within timeout.")
                continue
        if not username_field:
            raise NoSuchElementException("Could not find username field with any common locators.")
        username_field.send_keys(username)
        print("Username entered.")

        # Find and fill password
        password_field = None
        for by, value in password_locators:
            try:
                # Re-wait for password field, it might appear after username interaction
                password_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located((by, value))) # Shorter timeout for subsequent fields
                if password_field:
                    print(f"Found password field with {by}: {value}")
                    break
            except TimeoutException:
                print(f"Password field not found with {by}: {value} within timeout.")
                continue
        if not password_field:
            raise NoSuchElementException("Could not find password field with any common locators.")
        password_field.send_keys(password)
        print("Password entered.")

        # Find and click login button
        login_button = None
        for by, value in login_button_locators:
            try:
                login_button = wait.until(EC.element_to_be_clickable((by, value)))
                if login_button:
                    print(f"Found login button with {by}: {value}")
                    break
            except TimeoutException:
                print(f"Login button not found with {by}: {value} or not clickable.")
                continue
        if not login_button:
            raise NoSuchElementException("Could not find login button with any common locators or it was not clickable.")
        
        print("Attempting to click login button...")
        login_button.click()
        print("Login button clicked.")

        # Post-login check (placeholder - very basic)
        # A more robust check would be to wait for a specific element that appears only after login,
        # or to check if the URL changes to a dashboard/account page.
        time.sleep(3) # Wait for page to potentially redirect/load
        
        current_url = driver.current_url
        if "login" in current_url.lower() or url == current_url: # Simple check if URL still looks like a login page
            # This check is very basic. Many sites redirect to login on failure.
            # A more reliable check is needed, e.g., looking for error messages or specific post-login elements.
            print(f"Post-login check: Current URL ({current_url}) might indicate login failure or no redirect.")
            # Consider checking for common error messages here if possible
            # error_messages = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
            # if any("invalid" in msg.text.lower() for msg in error_messages if msg.is_displayed()):
            #     print("Login error message detected on page.")
            #     raise Exception("Login failed: Error message detected on page.")

        print(f"Login attempt to {url} seems successful. Current URL: {driver.current_url}")
        return driver

    except TimeoutException as e:
        print(f"Login failed: A timeout occurred while waiting for an element. {e}")
        if driver:
            driver.quit()
        return None
    except NoSuchElementException as e:
        print(f"Login failed: Could not find a required login element. {e}")
        if driver:
            driver.quit()
        return None
    except Exception as e:
        print(f"Login failed: An unexpected error occurred: {e}")
        if driver:
            driver.quit()
        return None

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
            
        except Exception as e:
            print(f"An error occurred during ResearcherAgent demo: {e}")
            import traceback
            traceback.print_exc()
