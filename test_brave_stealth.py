# test_brave_stealth.py
import logging
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------------------------------------------
# 1️⃣  Logging configuration (same as before)
# -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# -----------------------------------------------------------------
# 2️⃣  Import from the new package
# -----------------------------------------------------------------
from my_stealth.driver_factory import get_driver
from my_stealth.cookies import load_cookies, save_cookies

# -----------------------------------------------------------------
# 3️⃣  Paths for the persistent profile & cookies file (using environment variables)
# -----------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Get Brave user data directory from environment variable, fallback to BASE_DIR if not set
BRAVE_USER_DATA_DIR = os.getenv("BRAVE_USER_DATA_DIR", BASE_DIR)
if not os.path.isabs(BRAVE_USER_DATA_DIR):
    # If BRAVE_USER_DATA_DIR is relative, make it relative to BASE_DIR
    BRAVE_USER_DATA_DIR = os.path.join(BASE_DIR, BRAVE_USER_DATA_DIR)

# Get Brave profile name from environment variable, fallback to "Default" if not set  
BRAVE_PROFILE_NAME = os.getenv("BRAVE_PROFILE_NAME", "Default")
PROFILE_DIR = os.path.join(BRAVE_USER_DATA_DIR, BRAVE_PROFILE_NAME)

# Create the profile directory if it doesn't exist
os.makedirs(PROFILE_DIR, exist_ok=True)

COOKIES_JSON = os.path.join(PROFILE_DIR, "cookies.json")

# Optional: Get Brave version from environment (for future use)
BRAVE_VERSION = os.getenv("BRAVE_VERSION", "139")

log.info(f"Using Brave user data directory: {BRAVE_USER_DATA_DIR}")
log.info(f"Using Brave profile name: {BRAVE_PROFILE_NAME}")
log.info(f"Full profile path: {PROFILE_DIR}")
log.info(f"Brave version (for reference): {BRAVE_VERSION}")

# -----------------------------------------------------------------
# 4️⃣  Main test routine (unchanged, just the imports above moved)
# -----------------------------------------------------------------
def main() -> None:
    driver = get_driver(
        headless=False,                    # you want a visible window
        profile_path=BRAVE_USER_DATA_DIR,  # Brave user data directory
        profile_name=BRAVE_PROFILE_NAME,   # Specific Brave profile to use  
        maximise=True,                     # <‑‑ NEW – forces maximised window
        # proxy="http://user:pass@myproxy:3128",   # optional
    )

    # Restore cookies from a previous run (if they exist)
    load_cookies(driver, COOKIES_JSON)

    # Verify that Selenium is hidden
    driver.get("about:blank")
    is_stealth = driver.execute_script(
        "return navigator.webdriver === undefined;"
    )
    log.info("navigator.webdriver hidden? %s", is_stealth)

    # Go to Google (or any site you want to test)
    driver.get("https://www.google.com")
    time.sleep(2)                     # give the page a moment to settle
    log.info("Page title: %s", driver.title)

    # (optional) persist cookies after a successful login
    # save_cookies(driver, COOKIES_JSON)

    input("\n>>> Press ENTER to close the browser … ")
    driver.quit()
    log.info("Driver quit – script finished.")


if __name__ == "__main__":
    main()
