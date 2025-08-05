# cookies.py
"""
Very light‑weight cookie persistence.
The functions write/read a JSON file that contains the list returned by
driver.get_cookies() – that format works with every recent Chrome/Brave version.
"""

import json
from pathlib import Path
from typing import List, Dict
from selenium.webdriver.remote.webdriver import WebDriver


def save_cookies(driver: WebDriver, file_path: str) -> None:
    """
    Dump the current driver cookies to a JSON file.
    The file is created if it does not exist.
    """
    Path(file_path).write_text(json.dumps(driver.get_cookies(), indent=2))


def load_cookies(driver: WebDriver, file_path: str) -> None:
    """
    Load cookies from a JSON file (if it exists) and add them to the driver.
    The function silently does nothing when the file is missing.
    """
    p = Path(file_path)
    if not p.is_file():
        return

    for cookie in json.loads(p.read_text()):
        # Chrome ≥ 96 requires the `sameSite` attribute; add a safe default.
        if "sameSite" not in cookie:
            cookie["sameSite"] = "Lax"
        driver.add_cookie(cookie)
