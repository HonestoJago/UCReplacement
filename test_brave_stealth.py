# test_brave_stealth.py
import logging
import os
import time

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
# 3️⃣  Paths for the persistent profile & cookies file
# -----------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "brave_profile")
COOKIES_JSON = os.path.join(PROFILE_DIR, "cookies.json")

# -----------------------------------------------------------------
# 4️⃣  Main test routine (unchanged, just the imports above moved)
# -----------------------------------------------------------------
def main() -> None:
    driver = get_driver(
        headless=False,                 # you want a visible window
        profile_path=PROFILE_DIR,       # persistent profile
        maximise=True,                  # <‑‑ NEW – forces maximised window
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
