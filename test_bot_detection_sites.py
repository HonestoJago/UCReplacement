#!/usr/bin/env python3
"""Detection-site smoke test for *my_stealth*.

The script launches a **single** stealth-patched Brave session using the same
persistent profile approach as the main interaction tests and visits a handful
of well-known bot-detection demo sites.  For each site we run a tiny heuristic
(JavaScript or text scan) to decide whether the browser was flagged as
"automation".  Results are printed in a compact summary at the end.

Sites tested
------------
1. https://bot.sannysoft.com/          – popular fingerprint-tester
2. https://nowsecure.nl/               – Cloudflare style challenge
3. https://qp9q6.app/                  – CreepJS live demo (mirrors creepjs)

The heuristics are intentionally simple – they are meant to give a *quick* yes
/ no indication, not a detailed analysis.
"""
from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, Tuple

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from my_stealth.driver_factory import get_driver

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bot_tests")

# ---------------------------------------------------------------------------
# Environment-based configuration – reuse real Brave profile for realism
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
BRAVE_USER_DATA_DIR = Path(os.getenv("BRAVE_USER_DATA_DIR", BASE_DIR)).expanduser()
BRAVE_PROFILE_NAME = os.getenv("BRAVE_PROFILE_NAME", "Default")

# Ensure directory exists (esp. when user overrides)
BRAVE_USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

log.info("Using Brave profile: %s in user data dir: %s", BRAVE_PROFILE_NAME, BRAVE_USER_DATA_DIR)

# ---------------------------------------------------------------------------
# Helper functions for individual site heuristics
# ---------------------------------------------------------------------------

def _wait_for_body_text(driver, timeout: int = 15) -> str:
    """Return full innerText of <body> once it exists."""
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return driver.execute_script("return document.body.innerText;")


def check_sannysoft(driver) -> bool:
    """Pass if page reports *not detected* (green banner)."""
    driver.get("https://bot.sannysoft.com/")
    text = _wait_for_body_text(driver)
    return "Everything looks good" in text or "You are not detected" in text


def check_nowsecure(driver) -> bool:
    """Pass Cloudflare turnstile and ensure no automation block."""
    driver.get("https://nowsecure.nl/")

    # Try to solve simple turnstile checkbox if present
    try:
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title^='Widget containing']"))
        )
        driver.switch_to.frame(iframe)
        checkbox = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='checkbox']"))
        )
        checkbox.click()
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

    text = _wait_for_body_text(driver)
    return "detected automation" not in text.lower() and "selenium" not in text.lower()


CREEP_MIRRORS = [
    "https://reports.exanson.org/creepjs/",
    "https://loicmouton.github.io/creepjs/",
]


def check_creepjs(driver) -> bool:
    """Pass if CreepJS summary shows *GOOD* on first reachable mirror."""
    for url in CREEP_MIRRORS:
        try:
            driver.get(url)
            el = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".status-good, .passed"))
            )
            return el is not None
        except Exception:
            continue  # try next mirror
    return False

# Mapping of test name → function
TESTS: Dict[str, callable] = {
    "Sannysoft": check_sannysoft,
    "NowSecure": check_nowsecure,
    "CreepJS": check_creepjs,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:  # pragma: no cover
    driver = get_driver(
        headless=False,
        profile_path=str(BRAVE_USER_DATA_DIR),
        profile_name=BRAVE_PROFILE_NAME,
        maximise=True,
    )

    results: Dict[str, Tuple[bool, float]] = {}

    try:
        for name, func in TESTS.items():
            log.info("🧪 Running %s test", name)
            start = time.perf_counter()
            passed = func(driver)
            duration = time.perf_counter() - start
            results[name] = (passed, duration)
            status = "✅ PASS" if passed else "❌ FAIL"
            log.info("%s finished in %.1fs – %s", name, duration, status)
            time.sleep(2)  # small pause between tests

        # Summary
        log.info("\n" + "=" * 50)
        log.info("BOT DETECTION SUMMARY")
        log.info("=" * 50)
        for name, (passed, dur) in results.items():
            log.info("%-10s: %s (%.1fs)", name, "PASS" if passed else "FAIL", dur)

    finally:
        input("\n>>> Press ENTER to close the browser … ")
        driver.quit()


if __name__ == "__main__":
    main()
