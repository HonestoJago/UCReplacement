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

### Core Driver API

#### Basic Driver Creation

```python
from my_stealth.driver_factory import get_driver

# Minimal setup
driver = get_driver()

# With common options
driver = get_driver(
    maximise=True,               # Start maximized
    enable_stealth=True,         # Apply anti-detection patches
    apply_viewport=True          # Apply consistent viewport per profile
)
```

### All Configuration Options

```python
driver = get_driver(
    # === Browser Behavior ===
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
    apply_viewport=True,               # Apply consistent viewport per profile
)
```

### Enhanced WebElement Methods

```python
from my_stealth import enhance_driver_elements, find_elements_recursive, EnhancedWebElement

# Auto-enhance all driver elements
driver = uc.Chrome()
enhance_driver_elements(driver)

# Now all elements have enhanced methods
element = driver.find_element(By.ID, "button")
element.click_safe()  # Stealth clicking with human-like timing
element.type_human("text", typing_speed=0.1)  # Human-like typing
element.hover(duration=2.0)  # Natural mouse hover
element.scroll_to()  # Smooth scroll into view

# Enhanced DOM traversal
children = element.children(tag="div", recursive=True)
for child in children:
    print(f"Child element: {child.tag_name}")

# Cross-frame element finding
all_buttons = find_elements_recursive(driver, By.TAG_NAME, "button")
print(f"Found {len(all_buttons)} buttons across all frames")
```

#### Enhanced Element Methods Reference

| Method | Description | Parameters |
|--------|-------------|------------|
| `click_safe()` | Stealth clicking with human timing | `pause_before=None, pause_after=None` |
| `type_human()` | Human-like typing with mistakes | `text, typing_speed=0.1, mistakes=True` |
| `hover()` | Natural mouse hover | `duration=None` |
| `scroll_to()` | Smooth scroll into view | `behavior='smooth'` |
| `children()` | Get child elements | `tag=None, recursive=False` |
| `wait_for_clickable()` | Wait for element to be clickable | `timeout=10` |

### CDP Event Monitoring System

```python
from my_stealth import enable_cdp_events, add_cdp_listener, CDPEventMonitor

# Method 1: Simple UC-style API
driver = uc.Chrome()
monitor = enable_cdp_events(driver)

# Add event listeners
def log_request(params):
    request = params['request']
    print(f"🌐 {request['method']} {request['url']}")

def log_response(params):
    response = params['response']
    print(f"📥 {response['status']} {response['url']}")

add_cdp_listener(driver, 'Network.requestWillBeSent', log_request)
add_cdp_listener(driver, 'Network.responseReceived', log_response)
add_cdp_listener(driver, '*', lambda event: print(f"Event: {event['method']}"))  # All events

# Method 2: Advanced monitoring with analysis
monitor = CDPEventMonitor(driver)
monitor.start_monitoring(capture_events=True)

# Navigate and capture events
driver.get("https://example.com")
time.sleep(3)

# Analyze captured data
requests = monitor.get_network_requests(filter_url="api")
responses = monitor.get_network_responses(filter_url="json")

print(f"API requests: {len(requests)}")
for req in requests:
    print(f"  {req['method']} {req['url']}")

monitor.stop_monitoring()
```

#### CDP Event Methods Reference

| Function | Description | Parameters |
|----------|-------------|------------|
| `enable_cdp_events(driver)` | Enable CDP monitoring | Returns `CDPEventMonitor` |
| `add_cdp_listener(driver, event, callback)` | Add event listener | `event` (str or '*'), `callback` (function) |
| `CDPEventMonitor(driver)` | Create advanced monitor | Manual monitoring control |

#### CDPEventMonitor Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `start_monitoring()` | Begin event capture | `capture_events=True` |
| `stop_monitoring()` | Stop event capture | None |
| `add_listener()` | Add event listener | `event, callback` |
| `remove_listener()` | Remove event listener | `event, callback` |
| `get_network_requests()` | Get captured requests | `filter_url=None` |
| `get_network_responses()` | Get captured responses | `filter_url=None` |
| `clear_events()` | Clear event history | None |

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

# Force maximized window (disables viewport consistency)
driver = get_driver(
    maximise=True,           # Maximize window
    apply_viewport=False     # Don't apply viewport mask
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

### 5. Browser-Side API Requests

```python
# Perfect for game bots or authenticated APIs
driver = get_driver(
    profile_path="./game_profile",
    maximise=True
)

# Navigate to establish proper context
driver.get("https://yourgame.com")
driver.execute_cdp_cmd("Runtime.enable", {})

# Send authentic browser-side requests
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": """
    (async () => {
        const response = await fetch('/api/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: 'play'}),
            credentials: 'include'
        });
        return await response.json();
    })()
    """,
    "awaitPromise": True,
    "returnByValue": True
})

api_data = result["result"]["value"]
print(f"API response: {api_data}")
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

## 🌐 Browser-Side Network Requests (Fetch API)

For sending API requests that appear completely authentic, use the browser's native `fetch` API instead of external HTTP libraries. This ensures requests have perfect browser fingerprints and bypass CORS restrictions.

### Why Use Browser-Side Fetch?

- ✅ **Perfect Headers**: Automatic browser headers (User-Agent, Accept, etc.)
- ✅ **CORS Compliance**: Handles preflight requests naturally  
- ✅ **Cookie Integration**: Automatic session/authentication cookies
- ✅ **No Detection**: Indistinguishable from real user requests
- ✅ **Consistent Fingerprint**: Matches your browser's actual network stack

### Basic Fetch Examples

#### 1. Simple GET Request

```python
import my_stealth as uc
import json

driver = uc.Chrome(profile_path="./my_profile")
driver.get("about:blank")  # Initialize context

# Enable CDP for most reliable execution
driver.execute_cdp_cmd("Runtime.enable", {})

# Execute fetch via CDP (recommended method)
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": """
    (async () => {
        try {
            const response = await fetch('https://httpbin.org/get', {
                method: 'GET',
                mode: 'cors'
            });
            const data = await response.json();
            return { 
                success: true, 
                status: response.status, 
                data: data 
            };
        } catch (error) {
            return { 
                success: false, 
                error: error.message 
            };
        }
    })()
    """,
    "awaitPromise": True,
    "returnByValue": True
})

fetch_result = result["result"]["value"]
if fetch_result["success"]:
    print(f"✅ Request successful: {fetch_result['status']}")
    print(f"User-Agent sent: {fetch_result['data']['headers']['User-Agent']}")
else:
    print(f"❌ Request failed: {fetch_result['error']}")
```

#### 2. POST Request with JSON

```python
driver = uc.Chrome(profile_path="./my_profile")
driver.get("about:blank")
driver.execute_cdp_cmd("Runtime.enable", {})

# Prepare payload
payload = {
    "username": "user123",
    "action": "login",
    "timestamp": "2025-01-11T10:00:00Z"
}

# Execute POST request
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": f"""
    (async () => {{
        try {{
            const response = await fetch('https://httpbin.org/post', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }},
                body: JSON.stringify({json.dumps(payload)}),
                credentials: 'include'  // Include cookies
            }});
            const data = await response.json();
            return {{ 
                success: true, 
                status: response.status, 
                data: data 
            }};
        }} catch (error) {{
            return {{ 
                success: false, 
                error: error.message 
            }};
        }}
    }})()
    """,
    "awaitPromise": True,
    "returnByValue": True
})

post_result = result["result"]["value"]
if post_result["success"]:
    echo_data = post_result["data"]["json"]
    print(f"✅ POST successful: {echo_data}")
else:
    print(f"❌ POST failed: {post_result['error']}")
```

#### 3. Game/API Authentication Example

```python
# Perfect for gaming bots or authenticated APIs
driver = uc.Chrome(profile_path="./game_profile")

# Navigate to your game/app (establishes proper origin)
driver.get("https://yourgame.com/play")

# Wait for page load and switch to game frame if needed
time.sleep(3)
iframes = driver.find_elements("tag name", "iframe")
if iframes:
    driver.switch_to.frame(iframes[0])  # Switch to game context

driver.execute_cdp_cmd("Runtime.enable", {})

# Send authenticated game action
game_action = {
    "action": "place_bet",
    "amount": 100,
    "game_round": "abc123"
}

result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": f"""
    (async () => {{
        try {{
            // This request will include all cookies and proper origin
            const response = await fetch('/api/game/action', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }},
                body: JSON.stringify({json.dumps(game_action)}),
                credentials: 'include'  // Critical for game sessions
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
            }}
            
            const data = await response.json();
            return {{ 
                success: true, 
                status: response.status, 
                data: data 
            }};
        }} catch (error) {{
            return {{ 
                success: false, 
                error: error.message,
                type: error.name
            }};
        }}
    }})()
    """,
    "awaitPromise": True,
    "returnByValue": True,
    "userGesture": True  # Simulate user interaction
})

api_result = result["result"]["value"]
if api_result["success"]:
    print(f"🎮 Game action successful: {api_result['data']}")
else:
    print(f"❌ Game action failed: {api_result['error']}")
```

### Advanced Fetch Patterns

#### 1. Helper Function for Cleaner Code

```python
def browser_fetch(driver, url, options=None):
    """
    Helper function for clean browser-side fetch requests.
    
    Args:
        driver: Selenium WebDriver instance
        url: Target URL
        options: Fetch options dict (method, headers, body, etc.)
    
    Returns:
        dict: {success: bool, status: int, data: any, error: str}
    """
    options = options or {}
    options_json = json.dumps(options)
    
    result = driver.execute_cdp_cmd("Runtime.evaluate", {
        "expression": f"""
        (async () => {{
            try {{
                const response = await fetch('{url}', {options_json});
                
                let data;
                const contentType = response.headers.get('content-type') || '';
                if (contentType.includes('application/json')) {{
                    data = await response.json();
                }} else {{
                    data = await response.text();
                }}
                
                return {{
                    success: true,
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                    data: data,
                    url: response.url
                }};
            }} catch (error) {{
                return {{
                    success: false,
                    error: error.message,
                    type: error.name
                }};
            }}
        }})()
        """,
        "awaitPromise": True,
        "returnByValue": True
    })
    
    return result["result"]["value"]

# Usage
driver = uc.Chrome(profile_path="./my_profile")
driver.get("https://example.com")
driver.execute_cdp_cmd("Runtime.enable", {})

# Clean GET request
get_result = browser_fetch(driver, "https://httpbin.org/get")

# Clean POST request  
post_result = browser_fetch(driver, "https://httpbin.org/post", {
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps({"key": "value"}),
    "credentials": "include"
})
```

#### 2. Alternative: Using execute_async_script

```python
# Less stealthy but more widely supported fallback
driver.set_script_timeout(30)  # Set timeout for async operations

result = driver.execute_async_script("""
    const [url, options, callback] = arguments;
    
    fetch(url, options)
        .then(async response => {
            const data = await response.json();
            callback({
                success: true,
                status: response.status,
                data: data
            });
        })
        .catch(error => {
            callback({
                success: false,
                error: error.message
            });
        });
""", "https://httpbin.org/get", {"method": "GET"})

print(f"Async script result: {result}")
```

### Best Practices for Browser Fetch

#### 1. Proper Context Setup

```python
# ✅ CORRECT: Establish proper context first
driver = uc.Chrome(profile_path="./consistent_profile")
driver.get("https://your-target-site.com")  # Navigate to establish origin
time.sleep(2)  # Let page load completely

# Switch to correct frame if needed (games, SPAs)
iframes = driver.find_elements("tag name", "iframe")
if iframes:
    driver.switch_to.frame(iframes[0])

# Enable CDP
driver.execute_cdp_cmd("Runtime.enable", {})

# Now fetch requests will have proper origin/cookies
result = browser_fetch(driver, "/api/endpoint", {"credentials": "include"})
```

#### 2. Handle CORS Properly

```python
# Cross-origin requests need proper mode
options = {
    "method": "POST",
    "mode": "cors",  # Handle CORS properly
    "credentials": "omit",  # Don't send cookies for cross-origin
    "headers": {
        "Content-Type": "application/json"
        # Don't add custom headers that trigger preflight unless server supports them
    },
    "body": json.dumps(data)
}

# Same-origin requests can include credentials
same_origin_options = {
    "method": "POST", 
    "credentials": "include",  # Include cookies for same-origin
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps(data)
}
```

#### 3. Error Handling and Debugging

```python
def robust_fetch(driver, url, options=None, max_retries=3):
    """Robust fetch with error handling and retries."""
    
    for attempt in range(max_retries):
        try:
            result = browser_fetch(driver, url, options)
            
            if result["success"]:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result['error']}")
                if "Failed to fetch" in result.get("error", ""):
                    print("Possible CORS issue - check server headers")
                elif "TypeError" in result.get("type", ""):
                    print("Possible syntax error in fetch options")
                    
        except Exception as e:
            print(f"CDP execution failed on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return {"success": False, "error": "Max retries exceeded"}

# Usage
result = robust_fetch(driver, "https://api.example.com/data", {
    "method": "GET",
    "credentials": "include"
})
```

### Testing Your Fetch Implementation

Use the included test script to verify everything works:

```bash
# Run comprehensive fetch tests
python test_browser_fetch.py
```

This tests:
- ✅ Basic GET/POST requests
- ✅ CORS preflight handling  
- ✅ Cookie management
- ✅ Error scenarios
- ✅ User-Agent consistency

### Troubleshooting Fetch Issues

#### "Failed to fetch" Errors

```python
# Check if it's a CORS issue
driver.get("about:blank")
context = driver.execute_script("""
    return {
        origin: location.origin,
        href: location.href,
        userAgent: navigator.userAgent.substring(0, 50)
    };
""")
print(f"Context: {context}")

# Test with simple same-origin request first
driver.get("https://httpbin.org")
simple_test = browser_fetch(driver, "/get")  # Same-origin
print(f"Simple test: {simple_test['success']}")
```

#### Cookie/Session Issues

```python
# Verify cookies are being sent
result = browser_fetch(driver, "https://httpbin.org/cookies", {
    "credentials": "include"
})
print(f"Cookies sent: {result['data']['cookies']}")

# Set a test cookie first
driver.get("https://httpbin.org")
driver.add_cookie({"name": "test", "value": "my_stealth"})
result = browser_fetch(driver, "/cookies", {"credentials": "include"})
print(f"Test cookie: {result['data']['cookies']}")
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
    apply_viewport=False        # Don't apply viewport mask
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

## 🧪 Testing Suite

Comprehensive test scripts are provided to validate all functionality:

### Quick Test - All Features
```bash
# Run comprehensive test of all major features
python test_comprehensive_features.py
```

### Individual Feature Tests
```bash
# Test CDP event monitoring
python test_cdp_events.py

# Test enhanced WebElement methods  
python test_enhanced_elements.py

# Test browser-side fetch requests
python test_browser_fetch.py

# Test human-like interactions
python test_human_interactions.py

# Test bot detection evasion
python test_bot_detection_sites.py
```

### Manual Detection Testing

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

## 📚 Complete API Reference

### Core Functions

| Function | Module | Description |
|----------|--------|--------------|
| `uc.Chrome()` | `__init__` | Main driver constructor (UC-compatible) |
| `create_driver()` | `driver_factory` | Advanced driver creation with all options |
| `get_driver()` | `driver_factory` | Alias for create_driver() |
| `get_patched_chromedriver()` | `patcher` | Download and patch ChromeDriver binary |
| `find_chrome_executable()` | `__init__` | Auto-detect browser executable paths |

### CDP Event Monitoring

| Function | Description | Returns |
|----------|-------------|----------|
| `enable_cdp_events(driver)` | Enable basic CDP monitoring | `CDPEventMonitor` |
| `add_cdp_listener(driver, event, callback)` | Add event listener (UC-style) | `None` |
| `CDPEventMonitor(driver)` | Create advanced monitor | Monitor instance |

### CDPEventMonitor Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `start_monitoring()` | `capture_events=True` | Begin event capture |
| `stop_monitoring()` | None | Stop event capture |
| `add_listener()` | `event, callback` | Add event listener |
| `remove_listener()` | `event, callback` | Remove specific listener |
| `get_network_requests()` | `filter_url=None` | Get captured HTTP requests |
| `get_network_responses()` | `filter_url=None` | Get captured HTTP responses |
| `clear_events()` | None | Clear event history |

### Enhanced WebElements

| Function | Description | Returns |
|----------|-------------|----------|
| `enhance_driver_elements(driver)` | Auto-enhance all driver elements | `None` |
| `find_elements_recursive(driver, by, value)` | Cross-frame element search | `List[EnhancedWebElement]` |
| `EnhancedWebElement(element, driver)` | Wrap standard element | Enhanced element |

### EnhancedWebElement Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `click_safe()` | `pause_before=None, pause_after=None` | Human-like clicking |
| `type_human()` | `text, typing_speed=0.1, mistakes=True` | Realistic typing |
| `hover()` | `duration=None` | Natural mouse hover |
| `scroll_to()` | `behavior='smooth'` | Smooth scroll to element |
| `children()` | `tag=None, recursive=False` | Get child elements |
| `wait_for_clickable()` | `timeout=10` | Wait for element to be clickable |

### Stealth Utilities

| Function | Module | Description |
|----------|--------|--------------|
| `get_consistent_user_agent()` | `utils` | Get consistent UA for system |
| `get_consistent_viewport()` | `utils` | Get consistent viewport per profile |
| `get_system_timezone()` | `utils` | Get actual system timezone |
| `get_consistent_hardware()` | `utils` | Get consistent CPU/RAM specs |
| `get_profile_fingerprint()` | `utils` | Complete fingerprint for profile |

### Cookie Management

| Function | Module | Parameters | Description |
|----------|--------|------------|-------------|
| `save_cookies()` | `cookies` | `driver, file_path` | Save cookies to JSON |
| `load_cookies()` | `cookies` | `driver, file_path` | Load cookies from JSON |

### Configuration Options

All options for `create_driver()` / `uc.Chrome()`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxy` | `str` | `None` | Proxy URL |
| `profile_path` | `str` | `None` | Browser profile directory |
| `profile_name` | `str` | `None` | Specific profile name |
| `binary_path` | `str` | `None` | Custom browser executable |
| `driver_path` | `str` | `None` | Custom ChromeDriver path |
| `enable_stealth` | `bool` | `True` | Apply stealth patches |
| `maximise` | `bool` | `True` | Maximize window on startup |
| `apply_viewport` | `bool` | `True` | Apply consistent viewport |

### Environment Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `BRAVE_BINARY_PATH` | Path to Brave executable | `/path/to/brave` |
| `BRAVE_USER_DATA_DIR` | User data directory | `/path/to/profile` |
| `BRAVE_PROFILE_NAME` | Profile name within user data | `Default` |
| `BRAVE_VERSION` | Browser version reference | `139` |

### Event Types (CDP)

Common CDP event types for `add_cdp_listener()`:

| Event | Description |
|-------|-------------|
| `'Network.requestWillBeSent'` | HTTP request initiated |
| `'Network.responseReceived'` | HTTP response received |
| `'Network.dataReceived'` | Response data chunk |
| `'Runtime.consoleAPICalled'` | Console.log/error/warn |
| `'Security.certificateError'` | SSL/TLS certificate issues |
| `'*'` | All events (wildcard) |

## 📊 Performance Tips

- **Profile reuse**: Use persistent profiles to avoid setup time and maintain sessions
- **Resource cleanup**: Always call `driver.quit()` to free memory and ports
- **Proxy rotation**: Change proxies between sessions if needed
- **Minimize stealth overhead**: Disable stealth features you don't need
- **Connection pooling**: Reuse the same profile for multiple automation sessions

## 🔧 Advanced Usage Examples

### CDP Event Monitoring Example
```python
import my_stealth as uc
from my_stealth import enable_cdp_events, add_cdp_listener

# Create driver with CDP monitoring
driver = uc.Chrome(profile_path="./my_profile")
monitor = enable_cdp_events(driver)

# Monitor all network traffic
def log_request(params):
    request = params['request']
    print(f"🌐 {request['method']} {request['url']}")

def log_response(params):
    response = params['response']
    print(f"📥 {response['status']} {response['url']}")

add_cdp_listener(driver, 'Network.requestWillBeSent', log_request)
add_cdp_listener(driver, 'Network.responseReceived', log_response)

# Browse and monitor
driver.get("https://example.com")
time.sleep(5)

# Analyze captured data
requests = monitor.get_network_requests()
print(f"Captured {len(requests)} requests")
```

### Enhanced Elements Example
```python
import my_stealth as uc
from my_stealth import enhance_driver_elements, find_elements_recursive
from selenium.webdriver.common.by import By

# Create driver with enhanced elements
driver = uc.Chrome()
enhance_driver_elements(driver)

# All elements now have enhanced methods
driver.get("https://www.google.com")
search_box = driver.find_element(By.NAME, "q")

# Use enhanced methods
search_box.click_safe(pause_before=0.3, pause_after=0.2)
search_box.type_human("my search query", typing_speed=0.12, mistakes=True)
search_box.hover(duration=1.5)

# Cross-frame element finding
all_buttons = find_elements_recursive(driver, By.TAG_NAME, "button")
print(f"Found {len(all_buttons)} buttons across all frames")

# Natural interactions
for button in all_buttons[:3]:
    button.hover(duration=0.8)
    time.sleep(0.5)
```

### Game Bot API Example
```python
import my_stealth as uc
import json
import time

# Create driver for game automation
driver = uc.Chrome(
    profile_path="./game_profile",
    maximise=True
)

# Navigate to game
driver.get("https://yourgame.com/play")
time.sleep(5)

# Switch to game frame if needed
iframes = driver.find_elements("tag name", "iframe")
if iframes:
    driver.switch_to.frame(iframes[0])

# Enable CDP for API calls
driver.execute_cdp_cmd("Runtime.enable", {})

# Send authentic game API request
api_payload = {
    "action": "place_bet",
    "amount": 100,
    "game_id": "slot_001"
}

result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": f"""
    (async () => {{
        try {{
            const response = await fetch('/api/game/action', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }},
                body: JSON.stringify({json.dumps(api_payload)}),
                credentials: 'include'
            }});
            const data = await response.json();
            return {{ success: true, data: data }};
        }} catch (error) {{
            return {{ success: false, error: error.message }};
        }}
    }})()
    """,
    "awaitPromise": True,
    "returnByValue": True
})

api_result = result["result"]["value"]
if api_result["success"]:
    print(f"🎮 Game action successful: {api_result['data']}")
else:
    print(f"❌ Game action failed: {api_result['error']}")
```

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

### New Test Scripts Issues

#### ModuleNotFoundError: No module named 'my_stealth'
```bash
# Make sure you're in the project root directory
cd /path/to/UCReplacement

# Run tests from the root where my_stealth/ folder is located
python test_comprehensive_features.py
```

#### Import Errors in Module Files
The module files (`my_stealth/*.py`) no longer contain test code that causes import loops. All test code has been moved to dedicated test scripts in the root directory.

#### Test Profile Permissions
```bash
# If profile creation fails, ensure write permissions
chmod 755 ./test_profiles/

# Or use a different test profile path
export TEST_PROFILE_PATH="/tmp/my_stealth_test"
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
- ✅ CDP event monitoring (`enable_cdp_events`, `add_cdp_listener`)
- ✅ Enhanced WebElement methods (`click_safe`, `children`, etc.)
- ✅ Cross-frame element finding (`find_elements_recursive`)
- ✅ Binary patching with CDC replacement

### Improvements Over UC
- ✅ **Better maintained** - Active development vs abandoned UC
- ✅ **Brave support** - Privacy-focused browser with auto-detection
- ✅ **Environment config** - Easy `.env` setup
- ✅ **Type hints** - Full type safety for better IDE support
- ✅ **Modular design** - Clean architecture, easier to extend
- ✅ **Enhanced CDP system** - Thread-safe, more features than UC
- ✅ **Advanced element methods** - More human-like interactions
- ✅ **Comprehensive testing** - Full test suite included
- ✅ **No headless mode** - Eliminates major detection vector
- ✅ **Consistent fingerprinting** - Safer for persistent accounts
- ✅ **Better error handling** - Robust recovery mechanisms
- ✅ **Performance monitoring** - Built-in performance tracking

## 📄 License

This project is for educational and research purposes. Ensure compliance with website terms of service and applicable laws when using for automation.

---

**Ready to build undetectable automation? Get started with `my_stealth` today!** 🚀
