# profile.py
import json
import os
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver

def save_cookies(driver: WebDriver, file_path: str) -> None:
    """Write driver cookies to a JSON file."""
    Path(file_path).write_text(json.dumps(driver.get_cookies()))
    

def load_cookies(driver: WebDriver, file_path: str) -> None:
    """Read cookies from a JSON file and add them to the driver."""
    if not os.path.exists(file_path):
        return
    for cookie in json.loads(Path(file_path).read_text()):
        # Selenium 4.x requires the “sameSite” field to be present on recent Chrome.
        if "sameSite" not in cookie:
            cookie["sameSite"] = "Lax"
        driver.add_cookie(cookie)


def clear_profile(profile_path: str) -> None:
    """
    Delete everything inside a Chrome/Brave user‑data‑dir.
    Useful when you want a *clean* start but still want the profile folder to exist.
    """
    p = Path(profile_path)
    if p.is_dir():
        for child in p.iterdir():
            if child.is_file():
                child.unlink()
            else:
                # recursive delete
                for sub in child.rglob("*"):
                    sub.unlink()
                child.rmdir()
