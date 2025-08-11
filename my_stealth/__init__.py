# my_stealth/__init__.py
"""
Undetected ChromeDriver Replacement

A drop-in replacement for undetected-chromedriver using Brave browser
with advanced anti-detection techniques.

Usage:
    import my_stealth as uc
    
    # Drop-in UC replacement
    driver = uc.Chrome()
    driver.get('https://example.com')
    
    # Or with options
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
"""

from .driver_factory import create_stealth_driver, get_driver
from selenium.webdriver.chrome.options import Options as ChromeOptions

# UC-compatible API exports
Chrome = get_driver
TARGET_VERSION = "4.0.0"  # UC compatibility version

# Additional exports for advanced usage
create_driver = create_stealth_driver

__version__ = "1.0.0"
__all__ = ['Chrome', 'ChromeOptions', 'TARGET_VERSION', 'create_driver']
