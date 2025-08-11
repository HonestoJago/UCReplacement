# my_stealth/__init__.py
"""
Undetected ChromeDriver Replacement

A modern, maintainable drop-in replacement for undetected-chromedriver 
using Brave browser with advanced anti-detection techniques.

Key differences from original UC:
- Uses consistency-based fingerprinting instead of randomization
- Supports Brave browser out of the box with auto-detection
- Modern Selenium 4.x compatibility with automatic driver management
- Maintains same fingerprint across sessions for account safety
- Profile-aware consistency (same profile = same "device")

Usage:
    import my_stealth as uc
    
    # Drop-in UC replacement - basic usage
    driver = uc.Chrome()
    driver.get('https://example.com')
    
    # With options (UC-compatible)
    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    driver = uc.Chrome(options=options)
    
    # With profile (recommended for account safety)
    driver = uc.Chrome(
        profile_path="./profiles/my_profile",
        headless=False,
        maximise=True
    )
    
    # Advanced usage with environment variables
    # Set BRAVE_USER_DATA_DIR and BRAVE_PROFILE_NAME in .env
    driver = uc.Chrome()  # Uses your real Brave profile
"""

import os
import platform
from .driver_factory import create_stealth_driver, get_driver
from selenium.webdriver.chrome.options import Options as ChromeOptions

# UC-compatible API exports
Chrome = get_driver
TARGET_VERSION = "139.0.0.0"  # Current Chrome/Brave version

# Enhanced API for advanced usage
create_driver = create_stealth_driver

# Package metadata
__version__ = "1.0.0"
__description__ = "UC Replacement - Consistency-based Anti-Detection for Brave Browser"

def find_chrome_executable():
    """
    Find Chrome/Brave executable path across platforms.
    
    Prioritizes Brave over Chrome for better privacy and stealth.
    Returns the first found executable path, or None if not found.
    """
    system = platform.system()
    
    if system == "Windows":
        # Prioritize Brave, then fallback to Chrome
        paths = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif system == "Darwin":  # macOS
        paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    else:  # Linux
        paths = [
            "/usr/bin/brave-browser",
            "/usr/bin/brave",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None

# Public API - clean and focused
__all__ = [
    'Chrome', 
    'ChromeOptions', 
    'TARGET_VERSION', 
    'create_driver',
    'find_chrome_executable',
    '__version__'
]
