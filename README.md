# My Stealth - Undetected ChromeDriver Replacement

A modern, maintainable replacement for undetected-chromedriver that uses **Brave browser** with advanced anti-detection techniques for web automation and scraping.

## 🎯 Features

- **Drop-in UC replacement** - Compatible with `undetected_chromedriver` API
- **Brave browser support** - Privacy-focused, Chromium-based browser
- **Advanced stealth** - Comprehensive fingerprint spoofing and detection evasion
- **Environment configuration** - Easy setup via `.env` files
- **Automatic driver management** - Auto-downloads compatible ChromeDriver versions
- **Profile persistence** - Use your real browser profile or create isolated profiles
- **Human-like interactions** - Built-in utilities for realistic automation

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install selenium python-dotenv webdriver-manager

# Clone or copy the my_stealth package to your project
```

### Basic Usage

```python
# Drop-in replacement for undetected_chromedriver
import my_stealth as uc

# Create stealth driver (automatically detects Brave)
driver = uc.Chrome()
driver.get('https://www.google.com')
driver.quit()
```

### Environment Configuration

Create a `.env` file in your project root:

```env
# Brave browser paths (auto-detected if not specified)
BRAVE_BINARY_PATH=C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe

# Profile configuration
BRAVE_USER_DATA_DIR=C:\Users\YourUser\AppData\Local\BraveSoftware\Brave-Browser\User Data
BRAVE_PROFILE_NAME=Default

# Version reference (for logging)
BRAVE_VERSION=139
```

## 📖 Complete API Reference

### Basic Driver Creation

```python
from my_stealth.driver_factory import get_driver

# Minimal setup
driver = get_driver()

# With common options
driver = get_driver(
    headless=False,              # Visible browser window
    maximise=True,               # Start maximized
    enable_stealth=True,         # Apply anti-detection patches
    randomise_viewport=True      # Randomize window size
)
```

### All Configuration Options

```python
driver = get_driver(
    # === Browser Behavior ===
    headless=False,                    # Run in headless mode
    maximise=True,                     # Maximize window on startup
    
    # === Profile & Data ===
    profile_path="/path/to/user-data", # Browser user data directory
    profile_name="Default",            # Specific profile within user data dir
    
    # === Browser Binary ===
    binary_path="/path/to/brave.exe",  # Custom browser executable
    
    # === Driver ===
    driver_path="/path/to/chromedriver", # Custom ChromeDriver path
    
    # === Network ===
    proxy="http://user:pass@proxy:port", # Proxy configuration
    
    # === Stealth Configuration ===
    enable_stealth=True,               # Enable/disable stealth patches
    randomise_viewport=True,           # Randomize window size (vs fixed/maximized)
)
```

## 🛡️ Stealth Features

### What Gets Hidden/Spoofed

- ✅ **`navigator.webdriver`** - Hidden (returns `undefined`)
- ✅ **WebGL fingerprinting** - Consistent vendor/renderer info
- ✅ **Audio fingerprinting** - Neutralized AudioContext
- ✅ **Hardware detection** - Consistent CPU cores, memory (matches real system)
- ✅ **Timezone/locale** - Uses actual system timezone (consistent)
- ✅ **Viewport size** - Consistent screen dimensions per profile
- ✅ **User agent** - Realistic Chrome/Brave user agents (matches system)
- ✅ **Platform detection** - Consistent platform information
- ✅ **Permissions API** - Consistent privacy-focused responses
- ✅ **Automation flags** - Disabled Chrome automation indicators

### UC Philosophy: Consistency Over Randomization

Unlike other stealth solutions, `my_stealth` follows UC's proven approach:
- **Same profile = same "device"** across sessions
- **Consistent fingerprints** prevent account security flags
- **Real system specs** instead of fake random values
- **Account safety** for persistent login scenarios

### Browser Arguments Applied

```python
# Automatically applied Chrome arguments:
[
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions", 
    "--disable-popup-blocking",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--start-maximized",
    # Custom user agent
    # Profile/proxy settings as specified
]
```

## 💼 Common Use Cases

### 1. Basic Stealth Browsing

```python
import my_stealth as uc

# Create driver with your real Brave profile
driver = uc.Chrome()
driver.get('https://httpbin.org/headers')
print(driver.page_source)  # Check headers sent
driver.quit()
```

### 2. Maximized Window Automation

```python
from my_stealth import get_driver

# Force maximized window (disables viewport randomization)
driver = get_driver(
    maximise=True,           # Maximize window
    randomise_viewport=False # Don't randomize size
)

driver.get('https://example.com')
# Window will be maximized and stay that way
driver.quit()
```

### 3. Using Your Real Brave Profile

```python
# .env file:
# BRAVE_USER_DATA_DIR=C:\Users\YourUser\AppData\Local\BraveSoftware\Brave-Browser\User Data
# BRAVE_PROFILE_NAME=Default

from my_stealth import get_driver

driver = get_driver(
    profile_path=os.getenv("BRAVE_USER_DATA_DIR"),
    profile_name=os.getenv("BRAVE_PROFILE_NAME")
)

# Now you have access to:
# - Your bookmarks and extensions
# - Saved passwords and login sessions  
# - Browser history and preferences
# - Existing cookies and site data
```

### 4. Isolated Test Profile

```python
driver = get_driver(
    profile_path="./test_profile",  # Local test profile
    profile_name="testing"          # Custom profile name
)

# Clean slate for testing, isolated from your real browsing
```

### 5. Headless Mode

```python
driver = get_driver(
    headless=True,                  # No visible window
    randomise_viewport=True         # Still randomize fingerprint
)

# Perfect for server environments or background processing
```

### 6. Proxy Usage

```python
driver = get_driver(
    proxy="http://username:password@proxy.example.com:8080"
)

# All traffic routed through proxy
```

### 7. Custom Brave Installation

```python
driver = get_driver(
    binary_path="C:\\Custom\\Path\\To\\brave.exe"
)

# Use Brave from non-standard location
```

## 🤖 Human-Like Interactions

For realistic automation that mimics human behavior, you can implement these patterns:

```python
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Human-like delays
def human_delay(min_sec=0.5, max_sec=2.0):
    """Add realistic pauses between actions"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

# Human-like typing
def human_type(element, text, typing_speed=0.1):
    """Type character by character with realistic timing"""
    for char in text:
        element.send_keys(char)
        delay = random.uniform(typing_speed * 0.5, typing_speed * 2.0)
        time.sleep(delay)

# Natural mouse movements
def human_click(driver, element):
    """Click with mouse movement simulation"""
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.pause(random.uniform(0.1, 0.3))
    actions.click()
    actions.perform()

# Example usage
driver = get_driver()
driver.get('https://www.google.com')

search_box = driver.find_element(By.NAME, "q")
human_type(search_box, "my search query", typing_speed=0.1)
human_delay(1.0, 2.0)
search_box.send_keys(Keys.RETURN)
```

## 🍪 Cookie Management

```python
from my_stealth.cookies import load_cookies, save_cookies

driver = get_driver()

# Load cookies from previous session
load_cookies(driver, "cookies.json")

driver.get('https://example.com')
# ... do your automation ...

# Save cookies for next session
save_cookies(driver, "cookies.json")
```

### ⚠️ Important: Cookie Loading Timing

**Common Issue**: `InvalidCookieDomainException: Message: invalid cookie domain`

This happens when you try to load cookies before navigating to a valid domain:

```python
# ❌ WRONG - This will fail
driver = get_driver()
load_cookies(driver, "cookies.json")  # Error! No domain loaded yet

# ✅ CORRECT - Load cookies after navigating
driver = get_driver()
driver.get('https://example.com')     # Navigate to domain first
load_cookies(driver, "cookies.json")  # Now cookies can be loaded
```

**Best Practices:**

1. **Use persistent profiles instead** - Cookies persist automatically:
```python
# Recommended: Use your real Brave profile
driver = get_driver(
    profile_path=os.getenv("BRAVE_USER_DATA_DIR"),
    profile_name=os.getenv("BRAVE_PROFILE_NAME")
)
# Cookies are already available from your profile!
```

2. **Load cookies after navigation**:
```python
driver = get_driver()
driver.get('https://your-target-site.com')  # Navigate first
load_cookies(driver, "cookies.json")        # Then load cookies
```

3. **Save cookies safely**:
```python
# Ensure you're on a valid domain before saving
try:
    driver.get('https://example.com')  # Navigate to valid domain
    save_cookies(driver, "cookies.json")
    print("Cookies saved successfully")
except Exception as e:
    print(f"Could not save cookies: {e}")
```

## 🔧 Advanced Configuration

### Custom ChromeOptions

```python
from selenium.webdriver.chrome.options import Options
from my_stealth import create_driver

# Create custom options
options = Options()
options.add_argument("--window-size=1280,720")
options.add_argument("--lang=en-US")

# Pass to driver factory
driver = create_driver(
    # ... other params ...
)
```

### Disable Specific Stealth Features

```python
# For debugging - create unpatched driver
driver = get_driver(
    enable_stealth=False    # Plain ChromeDriver behavior
)

# Keep stealth but use fixed window size
driver = get_driver(
    enable_stealth=True,
    maximise=True,              # Start maximized
    randomise_viewport=False    # Don't randomize after maximizing
)
```

## 🚨 Error Handling

```python
try:
    driver = get_driver()
    driver.get('https://example.com')
except Exception as e:
    print(f"Driver creation failed: {e}")
    # Check:
    # - Brave browser installation
    # - Network connectivity  
    # - Profile permissions
finally:
    if 'driver' in locals():
        driver.quit()
```

## 📁 Project Structure

```
your_project/
├── .env                    # Environment configuration
├── my_stealth/            # Stealth package
│   ├── __init__.py        # UC-compatible API
│   ├── driver_factory.py  # Core driver creation
│   ├── utils.py          # Helper functions
│   └── cookies.py        # Cookie management
└── your_automation.py     # Your automation scripts
```

## 🔍 Detection Testing

Test your stealth setup against common detection methods:

```python
import my_stealth as uc

driver = uc.Chrome()

# 1. Check if webdriver property is hidden
driver.get("about:blank")
is_hidden = driver.execute_script("return navigator.webdriver === undefined;")
print(f"Webdriver hidden: {is_hidden}")  # Should be True

# 2. Test user agent
user_agent = driver.execute_script("return navigator.userAgent;")
print(f"User agent: {user_agent}")

# 3. Test common bot detection sites
test_sites = [
    "https://bot.sannysoft.com/",
    "https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html",
    "https://arh.antoinevastel.com/bots/areyouheadless"
]

for site in test_sites:
    driver.get(site)
    input(f"Check {site} for detection indicators, then press Enter...")

driver.quit()
```

## 📊 Performance Tips

- **Profile reuse**: Use persistent profiles to avoid setup time and maintain sessions
- **Resource cleanup**: Always call `driver.quit()` to free memory and ports
- **Proxy rotation**: Change proxies between sessions if needed
- **Minimize stealth overhead**: Disable stealth features you don't need
- **Connection pooling**: Reuse the same profile for multiple automation sessions

## 🐛 Troubleshooting

### Brave Not Found
```
WARNING: Brave browser not found in standard locations
```
**Solution**: Set `BRAVE_BINARY_PATH` in your `.env` file

### ChromeDriver Version Mismatch
```
SessionNotCreatedException: This version of ChromeDriver only supports Chrome version X
```
**Solution**: WebDriver Manager should handle this automatically. Check internet connection.

### Profile Permission Errors
```
Invalid argument: user data directory is already in use
```
**Solution**: Close all Brave instances or use a different profile path

### Cookie Loading Errors
```
InvalidCookieDomainException: Message: invalid cookie domain
```
**Solution**: Navigate to a valid domain before loading cookies:
```python
driver.get('https://example.com')  # Navigate first
load_cookies(driver, "cookies.json")  # Then load cookies
```
Or better yet, use persistent profiles which handle cookies automatically.

### Detection Issues
**Solution**: Test with different sites, verify stealth patches are working:
```python
# Check stealth status
driver.get("about:blank")
webdriver_hidden = driver.execute_script("return navigator.webdriver === undefined;")
user_agent = driver.execute_script("return navigator.userAgent;")
print(f"Webdriver hidden: {webdriver_hidden}")
print(f"User agent: {user_agent}")
```

## 🆚 UC Compatibility

This package is designed as a drop-in replacement for `undetected_chromedriver`:

```python
# Old UC code:
import undetected_chromedriver as uc
driver = uc.Chrome()

# New stealth code (same interface):
import my_stealth as uc  
driver = uc.Chrome()
```

### UC Features Supported
- ✅ Basic `Chrome()` constructor
- ✅ `ChromeOptions` compatibility
- ✅ Profile management
- ✅ Stealth detection evasion
- ✅ Automatic driver management

### Improvements Over UC
- ✅ **Better maintained** - Active development vs abandoned UC
- ✅ **Brave support** - Privacy-focused browser
- ✅ **Environment config** - Easy `.env` setup
- ✅ **Type hints** - Better IDE support
- ✅ **Modular design** - Easier to extend and debug
- ✅ **Configurable stealth** - Enable/disable features as needed

## 📄 License

This project is for educational and research purposes. Ensure compliance with website terms of service and applicable laws when using for automation.

---

**Ready to build undetectable automation? Get started with `my_stealth` today!** 🚀
