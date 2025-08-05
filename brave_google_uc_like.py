#!/usr/bin/env python3
"""
UC‑like driver that launches Brave, hides Selenium fingerprints,
and navigates to https://www.google.com.

Author:  (your name)
Date:    2025‑08‑05
"""

from __future__ import annotations

# --------------------------------------------------------------
# 0️⃣  Suppress noisy Chrome / TensorFlow logs (optional)
# --------------------------------------------------------------
import os
os.environ["CHROME_LOG_FILE"] = "NUL"          # Windows – discard Chrome logs
# os.environ["CHROME_LOG_FILE"] = "/dev/null" # Linux/macOS
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"      # Show only errors from TF (if TF ever loads)

import random
import time
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# --------------------------------------------------------------
# Logging (optional – makes it easy to see what’s happening)
# --------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# --------------------------------------------------------------
# 1️⃣  Helper: pick a realistic user‑agent
# --------------------------------------------------------------
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36 Brave/129",
]


def _random_ua() -> str:
    return random.choice(_UA_POOL)


# --------------------------------------------------------------
# 2️⃣  Build the driver with UC‑style stealth tweaks
# --------------------------------------------------------------
def configure_brave_driver(
    *,
    headless: bool = False,
    proxy: str | None = None,
    user_data_dir: str | None = None,
    binary_path: str | None = None,
    driver_executable_path: str | None = None,
) -> webdriver.Chrome:
    opts = Options()
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-agent={_random_ua()}")

    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-features=VizDisplayCompositor")

    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")

    if user_data_dir:
        profile_path = Path(user_data_dir).expanduser().resolve()
        profile_path.mkdir(parents=True, exist_ok=True)
        opts.add_argument(f"--user-data-dir={profile_path}")

    if binary_path:
        opts.binary_location = binary_path
    else:
        env_path = os.getenv("BRAVE_BINARY_PATH")
        if env_path:
            opts.binary_location = env_path

    service = Service(executable_path=driver_executable_path) if driver_executable_path else Service()
    driver = webdriver.Chrome(service=service, options=opts)

    # ---- Stealth CDP tweaks -------------------------------------------------
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                });
            """
        },
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'languages', {
                  get: () => ['en-US', 'en']
                });
                Object.defineProperty(navigator, 'plugins', {
                  get: () => [1, 2, 3, 4, 5]
                });
            """
        },
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                (function () {
                    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function (param) {
                        if (param === 0x1F00) {   // UNMASKED_VENDOR_WEBGL
                            return 'Intel Inc.';
                        }
                        if (param === 0x1F01) {   // UNMASKED_RENDERER_WEBGL
                            return 'Intel Iris OpenGL Engine';
                        }
                        return originalGetParameter.apply(this, arguments);
                    };
                })();
            """
        },
    )

    log.debug(
        "Brave driver created – headless=%s, proxy=%s, profile=%s",
        headless,
        proxy,
        user_data_dir,
    )
    return driver


# --------------------------------------------------------------
# 3️⃣  Small helper: a human‑like pause (optional)
# --------------------------------------------------------------
def human_delay(min_sec: float = 0.5, max_sec: float = 1.5) -> None:
    mean = (min_sec + max_sec) / 2.0
    sigma = 0.2 * (max_sec - min_sec)
    pause = max(min_sec, min(max_sec, random.gauss(mean, sigma)))
    time.sleep(pause)


# --------------------------------------------------------------
# 4️⃣  Main – open Google, print title, then wait
# --------------------------------------------------------------
def main() -> None:
    driver = configure_brave_driver(
        headless=False,
        user_data_dir="/tmp/brave_profile",   # optional persistent profile
        # binary_path="C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
        # proxy="http://user:pass@proxy.example:3128",
    )

    try:
        log.info("Navigating to https://www.google.com")
        driver.get("https://www.google.com")
        human_delay(2.0, 3.0)                 # give Google a moment to settle
        log.info("Page title: %s", driver.title)

        # -----------------------------------------------------------------
        #  👉  Choose how long you want the window to stay open:
        # -----------------------------------------------------------------
        # 1️⃣  Fixed time (the original behavior):
        # log.info("Keeping the browser open for   10 seconds …")
        # human_delay(10, 12)

        # 2️⃣  Wait for user input (uncomment to use):
        # input("\nPress ENTER to close the browser … ")

        # 3️⃣  Infinite loop (good for debugging):
        # while True:
        #     time.sleep(1)

        # -----------------------------------------------------------------
        # Quick visual verification that the Selenium flag is hidden:
        #   * Open DevTools → Console → `navigator.webdriver`
        #   * Should print `undefined`.
        #   * Network → any request → Headers should show a full set of
        #     Sec‑* headers and a realistic User‑Agent.
        # -----------------------------------------------------------------
        log.info(
            "Keeping the browser open for   10 seconds – feel free to inspect manually."
        )
        human_delay(10, 12)   # <-- replace this line with one of the three alternatives above

    finally:
        log.info("Quitting driver")
        driver.quit()


if __name__ == "__main__":
    main()
