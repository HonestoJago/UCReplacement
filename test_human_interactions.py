# test_human_interactions.py
"""
Human-like interaction tests for the stealth browser using Enhanced Elements.

MAJOR REFACTOR: This file has been updated to use my_stealth's Enhanced Elements
system instead of custom ActionChains-based interactions.

KEY CHANGES:
1. Replaced ActionChains with JavaScript-based methods to avoid Chrome's shadow DOM conflicts
2. All element interactions now use enhanced methods (click_safe, type_human, hover)
3. Enhanced elements automatically handle window sizing and Chrome inspection issues
4. More reliable and stealthy than ActionChains which trigger Chrome's visual feedback

BENEFITS OF REFACTOR:
- Eliminates "Cannot take screenshot with 0 width" errors
- Avoids "no such shadow root" conflicts with Chrome's internal UI
- Uses JavaScript events that are indistinguishable from real user interactions
- Maintains human-like timing while being more reliable
- Automatic fallbacks for different browsers and configurations

Tests realistic typing, clicking, and form interactions with enhanced stealth.
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
import my_stealth as uc
from my_stealth import enhance_driver_elements, EnhancedWebElement
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
    Type text using enhanced elements' JavaScript-based typing method.
    
    REFACTOR: Replaced custom character-by-character typing with our enhanced
    elements' type_human() method which uses JavaScript events to avoid
    Chrome's shadow DOM conflicts while maintaining human-like characteristics.
    
    Args:
        element: EnhancedWebElement to type into
        text: Text to type
        typing_speed: Base delay between characters (seconds)
    """
    log.info(f"Typing text: '{text}' with enhanced human-like typing")
    
    # Use our enhanced element's JavaScript-based typing with realistic mistakes
    element.type_human(text, typing_speed=typing_speed, mistakes=True)

def human_click(driver, element) -> None:
    """
    Perform a human-like click using enhanced elements' JavaScript-based method.
    
    REFACTOR: Replaced ActionChains-based clicking (which triggers Chrome's
    visual feedback systems) with our enhanced elements' click_safe() method
    that uses JavaScript execution to avoid shadow DOM conflicts.
    """
    log.info("Performing enhanced human-like click")
    
    # Use our enhanced element's JavaScript-based clicking
    # This includes natural timing and avoids Chrome's screenshot/inspection systems
    element.click_safe(pause_before=random.uniform(0.1, 0.3), 
                      pause_after=random.uniform(0.2, 0.5))

def wait_and_find(driver, by, value, timeout=10):
    """
    Wait for element to be present and return enhanced element.
    
    REFACTOR: Now returns EnhancedWebElement instead of regular WebElement.
    This ensures all found elements automatically have our JavaScript-based
    interaction methods (click_safe, type_human, hover, etc.) available.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        # Note: Don't manually wrap with EnhancedWebElement here since driver
        # is already enhanced via enhance_driver_elements() - it returns enhanced elements automatically
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
    
    # If a restored tab put us on an unexpected page, redirect
    try:
        current = driver.current_url
    except Exception:
        current = "about:blank"

    if not current.startswith("https://www.google."):
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
    
    # Always navigate explicitly – session restore may have left us elsewhere
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
    """Test 3: Natural mouse movements and hovering using enhanced elements"""
    log.info("🖱️ TEST 3: Enhanced Mouse Movement Test")
    
    driver.get("https://www.google.com")
    human_delay(2.0, 3.0)
    
    try:
        # Find multiple elements to hover over using enhanced elements
        # REFACTOR: driver.find_elements now returns EnhancedWebElement automatically
        links = driver.find_elements(By.TAG_NAME, "a")[:5]  # First 5 links
        
        if links:
            for i, link in enumerate(links):
                log.info(f"Hovering over link {i+1} with enhanced JavaScript method")
                
                # REFACTOR: Use enhanced element's JavaScript-based hover method
                # This avoids ActionChains and Chrome's visual feedback systems
                link.hover(duration=random.uniform(0.5, 1.5))
                
                human_delay(0.8, 1.5)
            
            log.info("✅ Enhanced mouse movement test completed")
            return True
        else:
            log.warning("❌ No links found for mouse movement test")
            return False
            
    except Exception as e:
        log.error(f"❌ Enhanced mouse movement test failed: {e}")
        return False

# -----------------------------------------------------------------
# 5️⃣⁺  Stealth-specific verification (CDC variables)
# -----------------------------------------------------------------

def test_cdc_variables_absence(driver):
    """Test 4: Ensure no `cdc_*` variables are present (patch verification)

    This directly checks the *core* promise of the binary patcher: that the
    notorious JavaScript variables injected by vanilla ChromeDriver (e.g.
    ``window.cdc_adoQpoasnfa76pfcZLmcfl_Array``) are **absent**.  A failure
    here means the driver was *not* patched correctly and therefore much more
    likely to be detected by anti-bot defences.
    """
    log.info("🔒 TEST 4: CDC Variable Absence Verification")

    # Use a completely blank page to avoid site-specific scripts interfering
    driver.get("about:blank")

    # Gather keys on *window* and *document* objects that start with 'cdc_' or '$cdc_'
    cdc_window = driver.execute_script("return Object.keys(window).filter(k => k.startsWith('cdc_'));")
    cdc_document = driver.execute_script("return Object.keys(document).filter(k => k.startsWith('$cdc_'));")

    if not cdc_window and not cdc_document:
        log.info("✅ No CDC variables detected – patch confirmed")
        return True

    log.warning("❌ Detected CDC variables! window:%s document:%s", cdc_window, cdc_document)
    return False

# -----------------------------------------------------------------
# 6️⃣  Main test runner
# -----------------------------------------------------------------

def main() -> None:
    """Run all human-like interaction tests"""
    log.info("🚀 Starting Human-like Interaction Tests")
    
    # Create stealth driver with enhanced elements - always visible for maximum stealth
    driver = uc.Chrome(
        profile_path=BRAVE_USER_DATA_DIR,
        profile_name=BRAVE_PROFILE_NAME,
        maximise=True,
    )
    
    # REFACTOR: Enable enhanced elements for JavaScript-based interactions
    # This replaces ActionChains with shadow DOM-safe JavaScript methods
    enhance_driver_elements(driver)
    log.info("Enhanced elements enabled - all interactions now use JavaScript methods")

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
        human_delay(3.0, 5.0)

        # NEW – verify binary patch actually removed CDC variables
        test_results['cdc_variables_absence'] = test_cdc_variables_absence(driver)
        
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
