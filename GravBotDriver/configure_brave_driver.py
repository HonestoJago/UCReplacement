#!/usr/bin/env python3
"""
Plug-and-play Brave driver configuration using my_stealth package.

Drop-in replacement for undetected-chromedriver (UC) that provides:
- Automatic Brave browser detection across platforms
- Persistent profile support with environment variable configuration
- Enhanced stealth capabilities with binary patching
- Simplified API - no version management complexity

Usage:
    from configure_brave_driver import create_brave_driver
    
    # Basic usage (uses default profile)
    driver = create_brave_driver()
    
    # With custom profile
    driver = create_brave_driver(
        profile_path="./profiles/my_bot_profile",
        profile_name="BotProfile"
    )
    
    # Headless mode
    driver = create_brave_driver(headless=True)

Environment Variables (optional):
    BRAVE_USER_DATA_DIR - Path to Brave user data directory
    BRAVE_PROFILE_NAME - Profile name to use (default: "Default")
    BRAVE_BINARY_PATH - Explicit path to Brave executable
"""

import os
import logging
import platform
from pathlib import Path
from typing import Optional
from selenium.webdriver.chrome.webdriver import WebDriver

# Import our stealth package
import Auferstehung as uc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


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
