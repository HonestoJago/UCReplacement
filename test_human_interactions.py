# test_human_interactions.py
"""
Human-like interaction tests for the stealth browser.
Tests realistic typing, clicking, and form interactions.
"""
import logging
import os
import time
import random
from dotenv import load_dotenv

# Selenium imports for human-like interactions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment variables from .env file
load_dotenv()

# -----------------------------------------------------------------
# 1️⃣  Logging configuration
# -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# -----------------------------------------------------------------
# 2️⃣  Import from our stealth package
# -----------------------------------------------------------------
from my_stealth.driver_factory import get_driver
# Note: No cookie imports needed - persistent profiles handle cookies automatically

# -----------------------------------------------------------------
# 3️⃣  Environment-based configuration
# -----------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Get Brave user data directory from environment variable, fallback to BASE_DIR if not set
BRAVE_USER_DATA_DIR = os.getenv("BRAVE_USER_DATA_DIR", BASE_DIR)
if not os.path.isabs(BRAVE_USER_DATA_DIR):
    BRAVE_USER_DATA_DIR = os.path.join(BASE_DIR, BRAVE_USER_DATA_DIR)

# Get Brave profile name from environment variable, fallback to "Default" if not set  
BRAVE_PROFILE_NAME = os.getenv("BRAVE_PROFILE_NAME", "Default")
PROFILE_DIR = os.path.join(BRAVE_USER_DATA_DIR, BRAVE_PROFILE_NAME)

# Create the profile directory if it doesn't exist
os.makedirs(PROFILE_DIR, exist_ok=True)

BRAVE_VERSION = os.getenv("BRAVE_VERSION", "139")
# Note: No COOKIES_JSON needed - persistent profiles handle cookies automatically

log.info(f"Using Brave user data directory: {BRAVE_USER_DATA_DIR}")
log.info(f"Using Brave profile name: {BRAVE_PROFILE_NAME}")

# -----------------------------------------------------------------
# 4️⃣  Human-like interaction utilities
# -----------------------------------------------------------------

def human_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> None:
    """
    Create a realistic human-like delay with slight randomization.
    Uses normal distribution around the mean for more natural timing.
    """
    mean = (min_sec + max_sec) / 2.0
    sigma = (max_sec - min_sec) / 6.0  # 99.7% of values within min-max range
    delay = max(min_sec, min(max_sec, random.gauss(mean, sigma)))
    time.sleep(delay)

def human_type(element, text: str, typing_speed: float = 0.1) -> None:
    """
    Type text character by character with human-like timing variations.
    
    Args:
        element: WebElement to type into
        text: Text to type
        typing_speed: Base delay between characters (seconds)
    """
    log.info(f"Typing text: '{text}' with human-like timing")
    
    for char in text:
        element.send_keys(char)
        
        # Add realistic typing variations
        if char == ' ':
            # Slightly longer pause after spaces
            delay = random.uniform(typing_speed * 1.5, typing_speed * 3.0)
        elif char in '.,!?;:':
            # Pause after punctuation
            delay = random.uniform(typing_speed * 2.0, typing_speed * 4.0)
        else:
            # Normal character typing speed with variation
            delay = random.uniform(typing_speed * 0.5, typing_speed * 2.0)
        
        time.sleep(delay)

def human_click(driver, element) -> None:
    """
    Perform a human-like click with mouse movement.
    """
    log.info("Performing human-like click")
    
    # Move to element first (creates more realistic behavior)
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.pause(random.uniform(0.1, 0.3))  # Brief pause before clicking
    actions.click()
    actions.perform()
    
    # Small delay after click
    human_delay(0.2, 0.5)

def wait_and_find(driver, by, value, timeout=10):
    """
    Wait for element to be present and return it.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        log.error(f"Element not found: {by}={value} within {timeout} seconds")
        return None

# -----------------------------------------------------------------
# 5️⃣  Test functions
# -----------------------------------------------------------------

def test_google_search(driver):
    """Test 1: Basic Google search with human-like typing"""
    log.info("🔍 TEST 1: Google Search with Human-like Typing")
    
    # Navigate to Google
    driver.get("https://www.google.com")
    human_delay(2.0, 3.0)
    
    # Find the search box
    search_box = wait_and_find(driver, By.NAME, "q")
    if not search_box:
        log.error("Could not find Google search box")
        return False
    
    # Clear any existing text and type search query
    search_box.clear()
    human_delay(0.5, 1.0)
    
    search_query = "python selenium automation tutorial"
    human_type(search_box, search_query, typing_speed=0.15)
    
    # Pause before hitting enter (human behavior)
    human_delay(1.0, 2.0)
    
    # Press Enter to search
    search_box.send_keys(Keys.RETURN)
    
    # Wait for results
    human_delay(2.0, 4.0)
    
    # Verify we got search results
    try:
        results = driver.find_elements(By.CSS_SELECTOR, "h3")
        if results:
            log.info(f"✅ Search successful! Found {len(results)} result headers")
            return True
        else:
            log.warning("❌ No search results found")
            return False
    except Exception as e:
        log.error(f"❌ Error checking search results: {e}")
        return False

def test_form_interaction(driver):
    """Test 2: Form interaction with realistic behavior"""
    log.info("📝 TEST 2: Form Interaction Test")
    
    # Navigate to a simple form page (using HTML form generator)
    driver.get("https://www.w3schools.com/html/tryit.asp?filename=tryhtml_form_submit")
    human_delay(3.0, 5.0)
    
    try:
        # Switch to the result iframe where the form is
        iframe = wait_and_find(driver, By.ID, "iframeResult", timeout=10)
        if iframe:
            driver.switch_to.frame(iframe)
            log.info("Switched to form iframe")
        
        # Find form elements
        first_name = wait_and_find(driver, By.NAME, "fname")
        last_name = wait_and_find(driver, By.NAME, "lname")
        
        if first_name and last_name:
            # Fill first name
            log.info("Filling first name field")
            human_click(driver, first_name)
            human_type(first_name, "John", typing_speed=0.12)
            
            # Tab to next field (more human-like than clicking)
            human_delay(0.5, 1.0)
            first_name.send_keys(Keys.TAB)
            
            # Fill last name
            log.info("Filling last name field")
            human_delay(0.3, 0.8)
            human_type(last_name, "Doe", typing_speed=0.14)
            
            # Find and click submit button
            submit_btn = wait_and_find(driver, By.CSS_SELECTOR, "input[type='submit']")
            if submit_btn:
                human_delay(1.0, 2.0)  # Think before submitting
                human_click(driver, submit_btn)
                log.info("✅ Form submitted successfully!")
                
                # Wait to see result
                human_delay(2.0, 3.0)
                return True
            else:
                log.warning("❌ Could not find submit button")
                return False
        else:
            log.warning("❌ Could not find form fields")
            return False
            
    except Exception as e:
        log.error(f"❌ Form interaction failed: {e}")
        return False
    finally:
        # Switch back to default content
        driver.switch_to.default_content()

def test_mouse_movements(driver):
    """Test 3: Natural mouse movements and hovering"""
    log.info("🖱️ TEST 3: Mouse Movement Test")
    
    driver.get("https://www.google.com")
    human_delay(2.0, 3.0)
    
    try:
        # Find multiple elements to hover over
        links = driver.find_elements(By.TAG_NAME, "a")[:5]  # First 5 links
        
        if links:
            actions = ActionChains(driver)
            
            for i, link in enumerate(links):
                log.info(f"Hovering over link {i+1}")
                
                # Move to element with a natural pause
                actions.move_to_element(link)
                actions.pause(random.uniform(0.5, 1.5))
                actions.perform()
                
                # Reset actions for next iteration
                actions = ActionChains(driver)
                
                human_delay(0.8, 1.5)
            
            log.info("✅ Mouse movement test completed")
            return True
        else:
            log.warning("❌ No links found for mouse movement test")
            return False
            
    except Exception as e:
        log.error(f"❌ Mouse movement test failed: {e}")
        return False

# -----------------------------------------------------------------
# 6️⃣  Main test runner
# -----------------------------------------------------------------

def main() -> None:
    """Run all human-like interaction tests"""
    log.info("🚀 Starting Human-like Interaction Tests")
    
    # Create stealth driver
    driver = get_driver(
        headless=False,
        profile_path=BRAVE_USER_DATA_DIR,
        profile_name=BRAVE_PROFILE_NAME,
        maximise=True,
    )

    # Verify stealth is working first
    driver.get("about:blank")
    is_stealth = driver.execute_script("return navigator.webdriver === undefined;")
    log.info(f"Navigator.webdriver hidden: {is_stealth}")

    # Note: Using persistent Brave profile - cookies, login sessions, and browsing 
    # data are automatically available from your real browser profile!

    # Test results tracking
    test_results = {}
    
    try:
        # Run tests
        test_results['google_search'] = test_google_search(driver)
        human_delay(3.0, 5.0)  # Pause between tests
        
        test_results['form_interaction'] = test_form_interaction(driver)
        human_delay(3.0, 5.0)
        
        test_results['mouse_movements'] = test_mouse_movements(driver)
        
        # Summary
        log.info("\n" + "="*50)
        log.info("TEST RESULTS SUMMARY:")
        log.info("="*50)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            log.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        passed = sum(test_results.values())
        total = len(test_results)
        log.info(f"\nOverall: {passed}/{total} tests passed")
        
        # Note: No need to save cookies manually - persistent Brave profile 
        # automatically saves all browsing data, cookies, and session state!
        log.info("All browsing data automatically saved to persistent Brave profile")
        
    except Exception as e:
        log.error(f"Test execution failed: {e}")
    finally:
        input("\n>>> Press ENTER to close the browser … ")
        driver.quit()
        log.info("Tests completed.")

if __name__ == "__main__":
    main()
