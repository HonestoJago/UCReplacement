import os
import time
import logging
import re
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from game.core import GamePhase
from configs.sites import SITE_CONFIGS
from utils.js_monitor import check_session_expired_flag
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database.session_state import session_state

import platform
from pathlib import Path
from typing import Optional
from selenium.webdriver.chrome.webdriver import WebDriver

# Import our stealth package
import my_stealth as uc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Windows registry import for version detection
if os.name == 'nt':
    try:
        import winreg
    except ImportError:
        winreg = None

"""
The _high5_last_phase variable has an interesting history in this codebase:

Originally, it was used as a state-tracking mechanism to handle empty or missing status text
in the High5 game. The previous approach was to:
1. Store the last known valid game phase
2. Return this stored phase whenever we couldn't read the current status text
3. This was problematic because it could lead to the bot acting on stale state information

We've since improved the approach to:
1. Actively wait up to 20 seconds for a valid status message to appear
2. Only return actual, current game states
3. Default to WAITING only after we've tried and failed to get a valid state

This variable is now only used in setup.py to track the initial game state when the bot starts.
This helps ensure we begin operation with a known, valid state, but we no longer use it for
ongoing state management.
"""

# Global variable only used for initial state tracking in setup.py
_high5_last_phase = None

def find_brave_browser() -> Optional[str]:
    """
    Cross-platform Brave browser detection with comprehensive fallbacks.
    
    Returns the path to Brave executable if found, None otherwise.
    Prioritizes environment variable override, then checks standard locations.
    """
    # Check environment variable first (allows user override)
    env_path = os.getenv("BRAVE_BINARY_PATH")
    if env_path and os.path.exists(env_path):
        log.info(f"Using Brave from environment variable: {env_path}")
        return env_path
    
    system = platform.system()
    
    if system == "Windows":
        # Windows paths in order of likelihood
        possible_paths = [
            # User installation (most common)
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
            # System-wide installations
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            # Using environment variables for robustness
            os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]
    else:  # Linux and other Unix-like systems
        possible_paths = [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/opt/brave.com/brave/brave-browser",
            "/snap/brave/current/usr/bin/brave",  # Snap package
            "/var/lib/flatpak/exports/bin/com.brave.Browser",  # Flatpak
            os.path.expanduser("~/.local/bin/brave-browser"),  # User local install
        ]
    
    # Check each path
    for path in possible_paths:
        if os.path.exists(path):
            log.info(f"Found Brave browser at: {path}")
            return path
    
    log.warning("Brave browser not found at any standard location")
    log.info("Tip: Set BRAVE_BINARY_PATH environment variable to specify custom Brave location")
    return None


def get_profile_config() -> tuple[str, str]:
    """
    Get Brave profile configuration from environment or sensible defaults.
    
    Returns (user_data_dir, profile_name) tuple.
    """
    # Check environment variables first
    user_data_dir = os.getenv("BRAVE_USER_DATA_DIR")
    profile_name = os.getenv("BRAVE_PROFILE_NAME", "Default")
    
    if user_data_dir:
        # Expand user path if needed
        user_data_dir = os.path.expanduser(user_data_dir)
        log.info(f"Using Brave profile from environment: {user_data_dir}/{profile_name}")
        return user_data_dir, profile_name
    
    # Determine default Brave profile location by platform
    system = platform.system()
    
    if system == "Windows":
        default_data_dir = os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\User Data")
    elif system == "Darwin":  # macOS
        default_data_dir = os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")
    else:  # Linux
        default_data_dir = os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
    
    log.info(f"Using default Brave profile: {default_data_dir}/{profile_name}")
    return default_data_dir, profile_name


def create_brave_driver(
    *,
    headless: bool = False,
    profile_path: Optional[str] = None,
    profile_name: Optional[str] = None,
    maximize: bool = True,
    enable_stealth: bool = True,
    **kwargs
) -> WebDriver:
    """
    Create a stealth Brave WebDriver instance with automatic configuration.
    
    This is a drop-in replacement for undetected-chromedriver that provides:
    - Automatic Brave browser detection
    - Persistent profile support
    - Enhanced stealth capabilities
    - Simplified configuration
    
    Parameters
    ----------
    headless : bool, default False
        Run browser in headless mode
    profile_path : str, optional
        Custom path to user data directory. If provided, overrides environment config.
    profile_name : str, optional
        Profile directory name within user data dir. Defaults to "Default".
    maximize : bool, default True
        Maximize browser window on startup
    enable_stealth : bool, default True
        Enable stealth patches (disable for debugging)
    **kwargs
        Additional arguments passed to create_stealth_driver
    
    Returns
    -------
    WebDriver
        Configured Brave WebDriver instance
        
    Raises
    ------
    FileNotFoundError
        If Brave browser cannot be found
    Exception
        If driver creation fails
        
    Examples
    --------
    Basic usage:
    >>> driver = create_brave_driver()
    >>> driver.get("https://example.com")
    
    With custom profile:
    >>> driver = create_brave_driver(
    ...     profile_path="./bot_profiles/session1",
    ...     profile_name="BotProfile"
    ... )
    
    Headless mode:
    >>> driver = create_brave_driver(headless=True)
    """
    try:
        log.info("🚀 Configuring Brave WebDriver with my_stealth...")
        
        # Find Brave browser executable
        brave_path = find_brave_browser()
        if not brave_path:
            error_msg = (
                "CRITICAL ERROR: Brave browser not found!\n"
                "Please install Brave browser or set BRAVE_BINARY_PATH environment variable.\n"
                "Download from: https://brave.com/"
            )
            log.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Configure profile settings
        if profile_path:
            # Use custom profile path
            user_data_dir = os.path.expanduser(profile_path)
            profile_dir_name = profile_name or "Default"
            log.info(f"Using custom profile: {user_data_dir}/{profile_dir_name}")
        else:
            # Use environment or default profile configuration
            user_data_dir, profile_dir_name = get_profile_config()
        
        # Ensure profile directory exists
        Path(user_data_dir).mkdir(parents=True, exist_ok=True)
        
        # Create stealth driver with our configuration
        driver = uc.create_driver(
            headless=headless,
            profile_path=user_data_dir,
            profile_name=profile_dir_name,
            binary_path=brave_path,
            maximise=maximize,
            enable_stealth=enable_stealth,
            **kwargs
        )
        
        log.info("✅ Brave WebDriver configured successfully!")
        
        # Verify stealth is working
        if enable_stealth:
            try:
                driver.get("about:blank")
                webdriver_hidden = driver.execute_script("return navigator.webdriver === undefined;")
                log.info(f"Stealth status: navigator.webdriver hidden = {webdriver_hidden}")
            except Exception as e:
                log.warning(f"Could not verify stealth status: {e}")
        
        return driver
        
    except Exception as e:
        log.error(f"Failed to configure Brave WebDriver: {e}")
        raise


def create_brave_driver_uc_compatible(
    options=None,
    use_subprocess=True,
    version_main=None,
    **kwargs
) -> WebDriver:
    """
    UC-compatible interface for easy migration from undetected-chromedriver.
    
    This provides the same interface as uc.Chrome() for drop-in replacement.
    Many UC-specific parameters are ignored since my_stealth handles them automatically.
    
    Parameters
    ----------
    options : ChromeOptions, optional
        Chrome options (many settings auto-configured by my_stealth)
    use_subprocess : bool, optional
        Ignored - my_stealth handles process management automatically
    version_main : int, optional
        Ignored - my_stealth handles version detection automatically
    **kwargs
        Additional arguments (most UC-specific ones are ignored)
    
    Returns
    -------
    WebDriver
        Configured Brave WebDriver instance
        
    Examples
    --------
    Direct UC replacement:
    >>> # Old UC code:
    >>> # driver = uc.Chrome(options=options, use_subprocess=True)
    >>> 
    >>> # New my_stealth code:
    >>> driver = create_brave_driver_uc_compatible(options=options)
    """
    log.info("🔄 Creating Brave driver with UC-compatible interface...")
    
    # Extract useful settings from UC options if provided
    headless = False
    if options:
        args = getattr(options, '_arguments', [])
        headless = any('--headless' in arg for arg in args)
        
        # Log ignored UC-specific arguments for awareness
        ignored_args = [arg for arg in args if any(pattern in arg for pattern in [
            '--disable-blink-features=AutomationControlled',  # We handle this
            '--disable-infobars',  # We handle this
            '--user-data-dir',  # We handle this via profile_path
            '--profile-directory'  # We handle this via profile_name
        ])]
        if ignored_args:
            log.info(f"Note: Some UC options are auto-handled by my_stealth: {ignored_args}")
    
    # Use our simplified interface
    return create_brave_driver(
        headless=headless,
        maximize=True,
        enable_stealth=True
    )


# Convenience aliases for different use cases
def get_brave_driver(**kwargs) -> WebDriver:
    """Alias for create_brave_driver - matches naming from test files."""
    return create_brave_driver(**kwargs)


def configure_chrome_driver(**kwargs) -> WebDriver:
    """
    Drop-in replacement for the original configure_chrome_driver function.
    Now uses my_stealth instead of UC with much simpler configuration.
    """
    return create_brave_driver(**kwargs)


# Example usage and testing
if __name__ == "__main__":
    """
    Example usage demonstrating the driver configuration.
    """
    import time
    
    log.info("🧪 Testing Brave driver configuration...")
    
    try:
        # Test basic driver creation
        driver = create_brave_driver(maximize=True)
        
        # Quick functionality test
        log.info("Testing basic navigation...")
        driver.get("https://www.google.com")
        time.sleep(2)
        
        # Verify stealth
        webdriver_status = driver.execute_script("return navigator.webdriver;")
        log.info(f"navigator.webdriver = {webdriver_status} (should be undefined)")
        
        # Test search functionality
        try:
            search_box = driver.find_element("name", "q")
            search_box.send_keys("my_stealth package test")
            search_box.submit()
            time.sleep(3)
            log.info("✅ Basic functionality test passed!")
        except Exception as e:
            log.warning(f"Search test failed (non-critical): {e}")
        
        log.info("🎉 Brave driver test completed successfully!")
        
    except Exception as e:
        log.error(f"❌ Driver test failed: {e}")
        raise
    finally:
        try:
            driver.quit()
            log.info("🧹 Driver closed cleanly")
        except:
            pass


def wait_for_element(driver, data_locator, is_test_attr=False, timeout=10):
    """Wait for an element to be present and visible using data-locator or data-test."""
    try:
        attr = "data-test" if is_test_attr else "data-locator"
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'[{attr}="{data_locator}"]'))
        )
        return element
    except Exception as e:
        logging.error(f"Failed to find element with {attr}={data_locator}: {str(e)}")
        return None

def get_game_phase_js(driver):
    """
    Determine the current game phase using Selenium.
    Returns: Tuple of (GamePhase enum value, found_buttons or None)
    For High5 games, waits up to 10 seconds for a valid status message before defaulting to WAITING.
    """
    # Get site configuration at the start
    site = os.getenv('SITE', 'mcluck').lower()
    config = SITE_CONFIGS.get(site)
    # Determine game type, default to 'gravity' if config not found or type missing
    game_type = config.get('game_type', 'gravity') if config else 'gravity'
    
    try:
        # Check if we're using High5 (limitless)
        if game_type == 'limitless': # Check game_type instead of site == 'high5'
            # First check for session expiration
            try:
                if check_session_expired_flag(driver):
                    logging.warning("Session expiration detected in game phase check")
                    return None, None  # Signal to break out of any loops
            except Exception as e:
                logging.debug(f"Error checking session expiration: {str(e)}")
            
            # logging.debug("Checking High5 game phase...")
            
            # Ensure we're in the game iframe
            driver.switch_to.default_content()
            try:
                WebDriverWait(driver, 1).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "game-iframe"))
                )
            except Exception as e:
                logging.debug(f"Error switching to game frame in phase check: {str(e)}")
                return GamePhase.WAITING, None
            
            def wait_for_valid_status(driver):
                """Wait for a valid status message to appear"""
                try:
                    status_element = driver.find_element(By.CSS_SELECTOR, '.status-text.ui-text-shadow-dark-strong')
                    if not status_element:
                        return None
                        
                    status_text = status_element.text.strip().upper()
                    if not status_text:
                        return None
                        
                    # Return the status text if it's one we recognize
                    if status_text in [
                        "PLACE YOUR PLAY",
                        "WAITING FOR PLAYER SEAT ACTIONS",
                        "WAITING FOR DEALER CARDS",
                        "WAITING FOR PLAYER CARDS",
                        "SHOWING WINNERS"
                    ]:
                        return status_text
                    return None
                except:
                    return None
            
            try:
                # Wait up to 5 seconds for a valid status message
                status_text = WebDriverWait(driver, 10).until(wait_for_valid_status)
                
                # Map status text to game phases
                # BETTING PHASE: When it's time for the player to place their bet
                if status_text == "PLACE YOUR PLAY":
                    return GamePhase.BETTING, None
                
                # Check for clickable action buttons first
                action_buttons = ['hit', 'stand', 'double', 'split']
                action_states = []
                
                # Create a combined selector for all action buttons
                combined_selector = ', '.join([
                    f'.hit-stand-actions-panel .{button}-icon[data-action="{button}"]' 
                    for button in action_buttons
                ])
                
                # ACTION PHASE: Either buttons are clickable or status indicates player action
                try:
                    # Wait for any action button to become clickable (1 second timeout)
                    WebDriverWait(driver, 1).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, combined_selector))
                    )
                    
                    # If we get here, at least one button is clickable, now check state of all buttons
                    for button in action_buttons:
                        selector = f'.hit-stand-actions-panel .{button}-icon[data-action="{button}"]'
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        is_enabled = elements and elements[0].is_displayed() and elements[0].is_enabled()
                        action_states.append(is_enabled)
                        
                    return GamePhase.ACTION, action_states
                except:
                    # If no buttons are clickable, check the status text
                    if status_text == "WAITING FOR PLAYER SEAT ACTIONS":
                        return GamePhase.ACTION, None
                
                # HIGH5-SPECIFIC PHASES: More granular state tracking for High5 games
                if status_text == "WAITING FOR DEALER CARDS":
                    logging.debug("In WAITING_FOR_DEALER_CARDS phase")
                    return GamePhase.WAITING_FOR_DEALER_CARDS, None
                    
                elif status_text == "WAITING FOR PLAYER CARDS":
                    logging.debug("In WAITING_FOR_PLAYER_CARDS phase")
                    return GamePhase.WAITING_FOR_PLAYER_CARDS, None
                    
                elif status_text == "SHOWING WINNERS":
                    logging.debug("In SHOWING_WINNERS phase")
                    return GamePhase.SHOWING_WINNERS, None
                    
            except Exception as e:
                logging.debug(f"Timed out waiting for valid status text: {str(e)}")
                return GamePhase.WAITING, None
                
            # If we somehow get here without a valid status, return WAITING
            logging.debug("No valid status text found after wait - defaulting to WAITING phase")
            return GamePhase.WAITING, None
                
        # --- 360 Variant Check ---
        elif game_type == '360': # Check game_type instead of site list
            # For 360 variants, the betting phase is primarily indicated by the betting timer,
            # and actions are handled by standard locators. Seat selection logic is handled in bot.py.
            try:
                if ensure_iframe_context(driver):
                    try:
                        # REFACTOR: Use WebDriverWait to look for the timer for a short period (e.g., 1 second)
                        # instead of find_element, which fails immediately if the element isn't present.
                        # This makes the check more robust against timing issues where the element might load slightly late.
                        timer_element = WebDriverWait(driver, 1).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-locator="betting-timer"]'))
                        )
                        # If the wait succeeds and finds the element visible, we are in the betting phase.
                        logging.debug("(360) Betting timer found via WebDriverWait. Checking for existing bet...")
                        
                        # --- Add check for existing bet on the player's seat --- 
                        bet_already_placed = False
                        try:
                            # Get the seat number we currently occupy
                            seat_num = session_state.current_seat
                            if seat_num is not None:
                                # Construct the locator for the chip value text within our seat
                                chip_value_locator = f"[data-locator='seat-place-{seat_num}-main'] [data-locator='betPlace-chip-value-main'] [data-locator='chip-value']"
                                
                                # Use find_elements to avoid NoSuchElementException if bet isn't placed yet
                                chip_value_elements = driver.find_elements(By.CSS_SELECTOR, chip_value_locator)
                                
                                if chip_value_elements and chip_value_elements[0].is_displayed():
                                    chip_text = chip_value_elements[0].text.strip()
                                    # Check if the text represents a non-zero number
                                    try:
                                        # Remove currency symbols or other non-numeric chars if necessary (adjust regex if needed)
                                        numeric_text = ''.join(filter(lambda x: x.isdigit() or x == '.', chip_text))
                                        bet_amount = float(numeric_text)
                                        if bet_amount > 0:
                                            bet_already_placed = True
                                            logging.debug(f"(360) Existing bet of {bet_amount} detected on seat {seat_num}. Treating phase as WAITING.")
                                        else:
                                            logging.debug(f"(360) Chip value element found but shows {bet_amount}. Treating as BETTING.")
                                    except ValueError:
                                         logging.debug(f"(360) Could not parse chip value text '{chip_text}'. Assuming no bet placed.")
                                else:
                                    logging.debug("(360) Chip value element not found or not displayed. Treating as BETTING.")
                            else:
                                # This case might occur if we just took the seat and haven't bet
                                logging.debug("(360) current_seat is None in session_state while checking for existing bet. Cannot check.")
                                
                        except Exception as bet_check_err:
                            logging.warning(f"(360) Error checking for existing bet chip: {type(bet_check_err).__name__}. Proceeding cautiously.")
                            # Decide how to handle error: assume no bet placed to avoid getting stuck?
                            bet_already_placed = False 
                            
                        # --- End check for existing bet --- 
                        
                        # Return BETTING only if timer is present AND no bet is already placed
                        if not bet_already_placed:
                            logging.debug("(360) Timer present and no existing bet found. Returning BETTING phase.")
                            return GamePhase.BETTING, None
                        else:
                            # Timer is present, but a bet is already down. We should wait.
                            return GamePhase.WAITING, None
                            
                    except TimeoutException:
                        # If the timer doesn't appear within the timeout, it's not the betting phase (or the element is missing).
                        # Log this and proceed to check for action buttons as the next step.
                        logging.debug("(360) Betting timer not found/visible within timeout. Checking action buttons.")
                    except Exception as e:
                        # Catch other potential errors during the WebDriverWait itself.
                        logging.warning(f"(360) Error checking for betting timer: {type(e).__name__}")
                    # If we reach here, the timer wasn't found or there was an error checking it.
                    # The original code had a logging.debug("(360) Betting timer not visible.") here, 
                    # which is now covered by the TimeoutException logging above.
                else:
                    # Log if we couldn't even get into the iframe context.
                    logging.warning("(360) Could not ensure iframe context for betting-timer check.")
                    # If we can't ensure context, we can't reliably check anything else, return WAITING
                    return GamePhase.WAITING, None

                # ---- 360 Action Button Check ----
                # If timer logic didn't return BETTING or WAITING, proceed to check action buttons.
                # Prioritize direct Selenium check over potentially failing JS.
                action_buttons_present = False
                button_details = [] # Store details of enabled buttons
                try:
                    action_button_locators = [
                        'hit-button',
                        'stand-button',
                        'double-button',
                        'split-button'
                    ]
                    combined_selector = ", ".join([f"button[data-locator='{loc}']" for loc in action_button_locators])
                    
                    # Use find_elements which returns empty list if none found
                    possible_buttons = driver.find_elements(By.CSS_SELECTOR, combined_selector)
                    
                    if possible_buttons:
                        # Check if any of the found buttons are displayed and enabled
                        for btn in possible_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                action_buttons_present = True
                                button_details.append({
                                    'type': btn.get_attribute('data-locator'),
                                    'enabled': True,
                                    'visible': True
                                })
                        
                        if action_buttons_present:
                            logging.debug(f"(360) Action buttons found via Selenium: {[d['type'] for d in button_details]}")
                            return GamePhase.ACTION, button_details # Return ACTION and button states
                        else:
                            logging.debug("(360) Action buttons found in DOM via Selenium, but none are displayed/enabled.")
                    else:
                         logging.debug("(360) No action buttons found in DOM via Selenium check.")
                except Exception as selenium_err:
                     logging.warning(f"(360) Error during Selenium action button check: {type(selenium_err).__name__}.")
                     # If Selenium check errors, we cannot reliably determine the phase
                     action_buttons_present = False # Ensure we don't accidentally proceed
                     # Removed JS Fallback: If Selenium check fails, assume WAITING
                     # The JS check was consistently causing JavascriptException
                     
                # If Selenium check did not find active buttons (or errored), default to WAITING
                if not action_buttons_present:
                    logging.debug("(360) No active action buttons confirmed by Selenium check. Returning WAITING phase.")
                    return GamePhase.WAITING, None
                    
            except Exception as e:
                # Handle potential errors during the overall 360 phase check
                logging.debug(f"(360) Error during phase check: {type(e).__name__}. Defaulting to WAITING.")
                return GamePhase.WAITING, None

       # --- Standard Gravity (fast path) ------------------------------------------
        elif game_type == "gravity":          # ← keep your existing outer branches
            try:
                # 0️⃣ only switch frames if a cheap probe says we're out of context
                #    (once you're inside the <iframe>, window.top !== window should be True)
                if driver.execute_script("return window.top === window;"):
                    if not ensure_iframe_context(driver):          # one‑time recovery
                        return GamePhase.WAITING, None

                # 1️⃣ JS snapshot – pull all the data we need in one go
                result = driver.execute_script(
                    """
                    const resp = {phase: "WAITING", buttons: []};

                    const bet = document.querySelector('[data-locator="main-bet-place"]');
                    if (bet) {
                        const cls = bet.className || "";
                        const noChip  = cls.includes("betPlace_withoutChip");
                        const withChip= cls.includes("betPlace_withChip");
                        const enabled = cls.includes("betPlace_enabled");
                        const open    = !cls.includes("betPlace_roundState_waiting");

                        if (!withChip && enabled && noChip && open) {
                            resp.phase = "BETTING";
                            return resp;
                        }
                    }

                    const ids = ["hit", "stand", "double", "split"];
                    ids.forEach(id => {
                        const btn = document.querySelector(
                            `button[data-locator="${id}-button"]`);
                        if (btn && !btn.disabled && btn.offsetParent !== null) {
                            resp.buttons.push(id);
                        }
                    });

                    if (resp.buttons.length) resp.phase = "ACTION";
                    return resp;
                    """
                )

                # 2️⃣ map JS → Python enum once
                if result["phase"] == "BETTING":
                    return GamePhase.BETTING, None
                if result["phase"] == "ACTION":
                    return GamePhase.ACTION, result["buttons"]
                return GamePhase.WAITING, None

            except Exception as err:
                logging.debug(f"Gravity phase check failed: {err}")
                return GamePhase.WAITING, None

        
    except Exception as e:
        if "no such window" in str(e).lower():
            logging.error("Lost connection to game window")
            raise
        logging.debug(f"Error determining game phase: {str(e)}")
        return GamePhase.WAITING, None

def ensure_iframe_context(driver):
    """Ensure we're in the correct iframe context."""
    try:
        # Get current site configuration
        site = os.getenv('SITE', 'mcluck').lower()
        
        if site == 'high5':
            # For High5, just switch to game frame directly without verification
            # (Assuming High5 doesn't have complex intermediate frames like some others)
            try:
                # Check if already in the frame by looking for a known High5 element
                driver.find_element(By.CSS_SELECTOR, '.dealer-hand') # Example element
                return True # Already in the correct frame
            except:
                # Not in the frame, try switching
                driver.switch_to.default_content()
                try:
                    WebDriverWait(driver, 1).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, "game-iframe"))
                    )
                    logging.debug("Switched to High5 iframe context.")
                    return True
                except Exception as e:
                    logging.debug(f"Error switching to High5 game frame: {str(e)}")
                    return False
        
        # For other sites (Gravity, 360, etc.)
        try:
            # More robust check: Look for EITHER main bet spot OR another stable game element
            # Using balance amount as the alternative stable element.
            stable_element_found = False
            try:
                # Check for main bet spot (Gravity)
                driver.find_element(By.CSS_SELECTOR, '[data-locator="main-bet-place"]')
                stable_element_found = True
                # logging.debug("Context check: Found main-bet-place")
            except NoSuchElementException:
                # If main bet spot not found, check for balance amount (Common)
                try:
                    driver.find_element(By.CSS_SELECTOR, '[data-locator="balance-amount"]')
                    stable_element_found = True
                    # logging.debug("Context check: Found balance-amount")
                except NoSuchElementException:
                    # logging.debug("Context check: Neither main-bet-place nor balance-amount found.")
                    pass # Neither common element found, context might be lost
            
            if stable_element_found:
                # logging.debug("Context check: Stable element found, context assumed correct.")
                return True # Context is likely correct
        except Exception as check_err:
            # Log error during the check, but proceed to recovery attempt
            logging.debug(f"Error during context check: {check_err}")
            pass 

        # --- Context recovery logic (if check above failed or skipped) --- 
        logging.warning("Context check failed or skipped, attempting iframe recovery...")
        driver.switch_to.default_content()
        
        # Get current site configuration
        config = SITE_CONFIGS.get(site)
        if not config:
            logging.error(f"Invalid site configuration: {site}")
            return False
        
        # Follow the frame chain from the site configuration
        for frame_type, frame_selector, *extra in config["frames"]:
            try:
                WebDriverWait(driver, 0.5).until(
                    EC.frame_to_be_available_and_switch_to_it((frame_type, frame_selector))
                )
            except Exception as e:
                logging.debug(f"Error switching to frame {frame_selector}: {str(e)}")
                return False
        
        logging.debug("Successfully restored iframe context")
        return True
        
    except Exception as e:
        logging.debug(f"Error ensuring iframe context: {str(e)}")
        return False