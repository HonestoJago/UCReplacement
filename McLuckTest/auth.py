"""
McLuck – GC/SC game launcher with robust login and iframe navigation.

This script drives the Brave/Chrome browser using the Auferstehung stealth
driver. It navigates to the desired McLuck game URL (GC or SC mode), deals with
Cloudflare interstitials, performs login (username/password or Google OAuth),
ensures we are on the correct game page, and finally waits for and switches
into the required nested iframes for gameplay automation.

Golden rule followed: This file contains a precise, surgical implementation for
the requested workflow only. We do not modify unrelated logic elsewhere.

Environment variables (optional but recommended):
  - MCLUCK_MODE: "GC" or "SC" (default: GC). Determines which URL to open.
  - BRAVE_USER_DATA_DIR: Absolute path to Brave's real user data directory
    (e.g., C:\\Users\\you\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data).
    When set, we load the real profile so Google password is NOT needed.
  - BRAVE_PROFILE_NAME: The profile directory name within the user data dir
    (e.g., "Default").
  - MCLUCK_EMAIL, MCLUCK_PASSWORD: Credentials for username/password login
    (used only when no real profile is provided or session is not present).
  - GOOGLE_EMAIL, GOOGLE_PASSWORD: Credentials for Google OAuth login
    (used only when no real profile is provided; real profile should skip this).

Usage from terminal (Windows CMD example):
  set MCLUCK_MODE=GC
  set BRAVE_USER_DATA_DIR=C:\\Users\\you\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data
  set BRAVE_PROFILE_NAME=Default
  set MCLUCK_EMAIL=you@example.com
  set MCLUCK_PASSWORD=yourpassword
  python -m McLuckTest.auth --mode GC

Notes:
  - We strongly recommend using your real Brave profile via BRAVE_USER_DATA_DIR
    + BRAVE_PROFILE_NAME for account safety and fewer logins/CF prompts.
  - Cloudflare challenges vary. We implement heuristic waits that handle common
    cases ("Just a moment…", Turnstile frames, transient redirects). This may
    take up to 90 seconds on first visit.
  - If you prefer Google OAuth, set GOOGLE_EMAIL/GOOGLE_PASSWORD. The script
    will try Google first when those values are present; otherwise it falls
    back to username/password if provided.
"""

import os
import time
import logging
from typing import Optional, Tuple
import json
import threading
import json

from dotenv import load_dotenv

# Absolute imports per project rules
from Auferstehung.driver_factory import create_stealth_driver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException


log = logging.getLogger(__name__)
load_dotenv()


# ---------------------------------------------------------------------------
# Logging controls – reduce noisy Selenium/urllib3 output
# ---------------------------------------------------------------------------
def _quiet_external_logs() -> None:
    """
    Reduce verbosity from Selenium, urllib3, and related libraries.
    This keeps console output focused on our own high-signal events.
    """
    try:
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("WDM").setLevel(logging.ERROR)  # webdriver-manager
        logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.ERROR)
        logging.getLogger("Auferstehung").setLevel(logging.WARNING)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 1) URL selection – GC vs. SC
# ---------------------------------------------------------------------------
def _get_target_url(mode: str) -> str:
    """
    Return the requested McLuck game URL based on mode.

    mode: "GC" or "SC" (case-insensitive). Defaults to GC when unknown.
    """
    mode_upper = (mode or "GC").strip().upper()
    if mode_upper == "SC":
        # SC (sweepstakes) mode – provided by user
        return (
            "https://www.mcluck.com/games/slots/aloha-king-elvis/sweepstake/"
            "play?category=&gameIndex=&isOtpRequired=false"
        )
    # Default GC mode – provided by user
    return (
        "https://www.mcluck.com/games/slots/aloha-king-elvis/play?"
        "category=&gameIndex=&isOtpRequired=false"
    )


# ---------------------------------------------------------------------------
# 2) Cloudflare heuristics – wait until main app is ready
# ---------------------------------------------------------------------------
def _wait_for_cloudflare_and_app(driver: WebDriver, timeout: int = 90) -> None:
    """
    Heuristically wait out Cloudflare interstitials and the app bootstrap.

    Strategy:
      - Poll for typical Cloudflare signals (title "Just a moment", cf iframes)
      - Consider page ready when the app root (#main-layout) appears and the
        main content area is present.
      - Cap the wait to the provided timeout.
    """
    end_ts = time.time() + timeout

    # Quick helper: detect common CF challenge markers
    def cf_in_progress() -> bool:
        try:
            title = (driver.title or "").lower()
        except Exception:
            title = ""
        if any(kw in title for kw in ["just a moment", "checking your browser"]):
            return True
        try:
            # Turnstile/challenge frames often include these substrings
            cf_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='challenges']")
            if not cf_frames:
                cf_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='turnstile']")
            return len(cf_frames) > 0
        except Exception:
            return False

    # Loop until either app root is present or timeout
    while time.time() < end_ts:
        try:
            if not cf_in_progress():
                # App root for McLuck UI
                root = driver.find_elements(By.CSS_SELECTOR, "#main-layout")
                if root:
                    # Also ensure the page has some interactive content mounted
                    content = driver.find_elements(By.CSS_SELECTOR, "main, nav, header, footer, [role='main']")
                    if content:
                        return
            # Small backoff to avoid busy-waiting
            time.sleep(0.6)
        except Exception:
            time.sleep(0.8)

    # If we reach here, we didn't detect readiness; we do not raise hard errors
    # because the app may still be functional. Log a warning so the caller can
    # choose to proceed.
    log.warning("Cloudflare/app readiness wait timed out after %ss", timeout)


# ---------------------------------------------------------------------------
# 3) Login flows – Google or Username/Password
# ---------------------------------------------------------------------------
def _is_logged_in(driver: WebDriver) -> bool:
    """
    Best-effort detection: determine if the user appears logged in.

    We check for common signs of an authenticated state (e.g., presence of
    avatar/user menu, absence of Sign In buttons). Selectors may change – this
    remains heuristic by design.
    """
    try:
        # Signs of being logged in: avatar button/menu typically present on
        # the right; lack of a visible login button.
        avatar = driver.find_elements(By.CSS_SELECTOR, "[data-test*='avatar'], [class*='avatar'], [class*='profile']")
        login_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'SIGNIN', 'signin'), 'sign in') or contains(translate(., 'LOGIN', 'login'), 'log in')]")
        if avatar and not login_buttons:
            return True
        # Also consider presence of the game canvas as a strong signal
        game_canvas = driver.find_elements(By.CSS_SELECTOR, ".GameCanvas_root__s_B_r, .GameCanvas_gameCanvas__DzY4w")
        if game_canvas:
            return True
    except Exception:
        pass
    return False


def _try_google_login(driver: WebDriver, email: str, password: str, max_wait: int = 30) -> bool:
    """
    Attempt Google OAuth login when a "Continue with Google" button is present.

    We:
      1) Click the Google button
      2) Switch to the Google popup window
      3) Enter email and password
      4) Return to the original window
    Returns True on apparent success; False otherwise.
    """
    try:
        # Locate a Google continue button by common attributes/text.
        candidates = [
            (By.CSS_SELECTOR, "button[aria-label*='Google']"),
            (By.XPATH, "//button[contains(., 'Google') or contains(@aria-label, 'Google')]")
        ]
        google_btn = None
        for by, sel in candidates:
            elems = driver.find_elements(by, sel)
            if elems:
                google_btn = elems[0]
                break
        if not google_btn:
            return False

        parent_handle = driver.current_window_handle
        google_btn.click()

        # Wait for new window to appear and switch
        WebDriverWait(driver, max_wait).until(lambda d: len(d.window_handles) > 1)
        new_handles = [h for h in driver.window_handles if h != parent_handle]
        driver.switch_to.window(new_handles[-1])

        # Google auth flow – identifiers and buttons are relatively stable
        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.ID, "identifierId")))
        driver.find_element(By.ID, "identifierId").send_keys(email)
        driver.find_element(By.ID, "identifierNext").click()

        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.NAME, "Passwd")))
        driver.find_element(By.NAME, "Passwd").send_keys(password)
        driver.find_element(By.ID, "passwordNext").click()

        # Give Google a moment to finish and close/switch back
        WebDriverWait(driver, max_wait).until(lambda d: len(d.window_handles) >= 1)
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(parent_handle)
        else:
            driver.switch_to.window(parent_handle)

        # Allow redirect/handshake to complete
        _wait_for_cloudflare_and_app(driver, timeout=60)
        return _is_logged_in(driver)
    except Exception as exc:
        log.warning("Google login flow failed: %s", exc)
        # Best-effort: return to original window if possible
        try:
            for h in driver.window_handles:
                driver.switch_to.window(h)
        except Exception:
            pass
        return False


def _try_password_login(driver: WebDriver, email: str, password: str, max_wait: int = 30) -> bool:
    """
    Attempt username/password login by locating common input fields and submit.
    Returns True on apparent success; False otherwise.
    """
    try:
        # Navigate to a login form if a login button is present
        possible_login_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'SIGNIN', 'signin'), 'sign in') or contains(translate(., 'LOGIN', 'login'), 'log in')]")
        if possible_login_buttons:
            try:
                possible_login_buttons[0].click()
                time.sleep(1)
            except Exception:
                pass

        # Locate email/username field
        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.CSS_SELECTOR, "input[name='username']"),
        ]
        email_el = None
        for by, sel in email_selectors:
            elems = driver.find_elements(by, sel)
            if elems:
                email_el = elems[0]
                break
        if not email_el:
            return False
        email_el.clear()
        email_el.send_keys(email)

        # Locate password field
        pwd_selectors = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
        ]
        pwd_el = None
        for by, sel in pwd_selectors:
            elems = driver.find_elements(by, sel)
            if elems:
                pwd_el = elems[0]
                break
        if not pwd_el:
            return False
        pwd_el.clear()
        pwd_el.send_keys(password)

        # Submit – prefer explicit submit button, else press Enter via JS
        submit_btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button[data-test*='submit']")
        if submit_btns:
            submit_btns[0].click()
        else:
            try:
                driver.execute_script("arguments[0].form && arguments[0].form.submit();", pwd_el)
            except Exception:
                pass

        _wait_for_cloudflare_and_app(driver, timeout=60)
        return _is_logged_in(driver)
    except Exception as exc:
        log.warning("Password login flow failed: %s", exc)
        return False


def _try_google_handshake_without_credentials(driver: WebDriver, max_wait: int = 30) -> bool:
    """
    When a real Brave profile is loaded, McLuck's "Continue with Google"
    often only needs a click to complete an OAuth handshake (no typing).

    This method clicks the Google button, handles potential popup/same-tab
    navigation, waits for completion and Cloudflare, and returns True if the
    session appears logged in afterwards.
    """
    try:
        # Find a Google continue button
        candidates = [
            (By.CSS_SELECTOR, "button[aria-label*='Google']"),
            (By.XPATH, "//button[contains(., 'Google') or contains(@aria-label, 'Google')]")
        ]
        google_btn = None
        for by, sel in candidates:
            elems = driver.find_elements(by, sel)
            if elems:
                google_btn = elems[0]
                break
        if not google_btn:
            return False

        parent = driver.current_window_handle
        prev_handles = set(driver.window_handles)
        google_btn.click()

        # Wait briefly for either a new window or same-tab redirect
        t_end = time.time() + max_wait
        switched = False
        while time.time() < t_end:
            cur_handles = set(driver.window_handles)
            new_handles = list(cur_handles - prev_handles)
            if new_handles:
                driver.switch_to.window(new_handles[-1])
                switched = True
                break
            # Same-tab flow: detect Google accounts or auth redirect
            try:
                url = driver.current_url
                if "accounts.google" in url or "/signin/oauth" in url:
                    # Let it settle; with a real profile it should bounce back quickly
                    time.sleep(1.0)
                    break
            except Exception:
                pass
            time.sleep(0.3)

        # Give the OAuth a moment to complete
        time.sleep(2.0)

        # If we opened a popup, try to close it once it finishes
        try:
            if switched:
                # If popup closed itself, switch back; else close it
                if len(driver.window_handles) > 1:
                    try:
                        driver.close()
                    except Exception:
                        pass
                # Switch to parent regardless
                driver.switch_to.window(parent)
        except Exception:
            # Ensure we are on some valid window
            try:
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                pass

        _wait_for_cloudflare_and_app(driver, timeout=60)
        return _is_logged_in(driver)
    except Exception as exc:
        log.info("Google handshake without credentials did not complete: %s", exc)
        return False


def _ensure_logged_in(driver: WebDriver) -> None:
    """
    Ensure we are logged in by attempting Google OAuth first (when
    GOOGLE_EMAIL/GOOGLE_PASSWORD are set), then username/password (when
    MCLUCK_EMAIL/MCLUCK_PASSWORD are set). If BRAVE_USER_DATA_DIR is provided,
    first attempt a credential-less Google handshake (just clicking the button),
    as real profile cookies are typically sufficient. If already logged in,
    this is a no-op.
    """
    if _is_logged_in(driver):
        return

    # If a real Brave profile is loaded, try a credential-less Google handshake
    if os.getenv("BRAVE_USER_DATA_DIR"):
        if _try_google_handshake_without_credentials(driver):
            return

    user_email = os.getenv("MCLUCK_EMAIL", "").strip()
    user_pass = os.getenv("MCLUCK_PASSWORD", "").strip()
    if user_email and user_pass:
        if _try_password_login(driver, user_email, user_pass):
            return

    # If we still are not logged in, consider full Google login (typing) only
    # when credentials are explicitly provided and no real profile is used.
    if not os.getenv("BRAVE_USER_DATA_DIR"):
        google_email = os.getenv("GOOGLE_EMAIL", "").strip()
        google_pass = os.getenv("GOOGLE_PASSWORD", "").strip()
        if google_email and google_pass:
            if _try_google_login(driver, google_email, google_pass):
                return

    # If we reach here, see if we are already authenticated (e.g., via real
    # Brave profile session cookies). Only log if still not logged in.
    if not _is_logged_in(driver):
        log.info("Automated login not completed – manual login may be required.")


# ---------------------------------------------------------------------------
# 4) Ensure correct page and navigate to nested iframes
# ---------------------------------------------------------------------------
def _ensure_on_target_page(driver: WebDriver, target_url: str) -> None:
    """
    If we're not on the desired game URL, navigate there. This handles cases
    where the site redirects to a lobby/dashboard after login.
    """
    try:
        if not driver.current_url.startswith(target_url.split("?", 1)[0]):
            driver.get(target_url)
            _wait_for_cloudflare_and_app(driver, timeout=60)
    except Exception:
        driver.get(target_url)
        _wait_for_cloudflare_and_app(driver, timeout=60)


def _wait_game_canvas_ready(driver: WebDriver, timeout: int = 45) -> bool:
    """
    Wait for the game canvas area to mount before attempting iframe switching.
    Returns True if a plausible game canvas or outer iframe appears.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".GameCanvas_root__s_B_r, .GameCanvas_gameCanvas__DzY4w")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.GameCanvas_iframe__h40la")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "#main-layout iframe")),
            )
        )
        return True
    except TimeoutException:
        return False


def _switch_to_required_iframes(driver: WebDriver, outer_wait: int = 40, inner_wait: int = 40) -> Tuple[bool, bool]:
    """
    Wait for and switch into the two required iframes in sequence.

    Outer iframe selector (provided by user):
      #main-layout > main > div > div > div > div > div > div.GameCanvas_root__s_B_r.GameCanvas_gameCanvas__DzY4w > div > div > iframe

    Inner iframe example (provided by user):
      iframe.styles_root__frK1Y with src starting at gamma.interlayer.work

    Returns (outer_ok, inner_ok) indicating whether each switch succeeded.
    """
    outer_selector = (
        "#main-layout > main > div > div > div > div > div > div."
        "GameCanvas_root__s_B_r.GameCanvas_gameCanvas__DzY4w > div > div > iframe"
    )

    try:
        outer_iframe = WebDriverWait(driver, outer_wait).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, outer_selector))
        )
        outer_ok = True
    except TimeoutException:
        # Fallback: locate by class more loosely
        try:
            outer = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".GameCanvas_iframe__h40la, .GameCanvas_root__s_B_r iframe"))
            )
            driver.switch_to.frame(outer)
            outer_ok = True
        except Exception:
            log.error("Failed to locate/switch to outer game iframe.")
            return False, False

    # Inner iframe – prefer class, fallback to src contains gamma.interlayer.work
    try:
        WebDriverWait(driver, inner_wait).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe.styles_root__frK1Y"))
        )
        inner_ok = True
    except TimeoutException:
        try:
            WebDriverWait(driver, 15).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[src*='gamma.interlayer.work/games/AlohaKingElvis']"))
            )
            inner_ok = True
        except Exception:
            log.error("Failed to locate/switch to inner game iframe.")
            # Important: return to default content so callers are not stuck inside a partial frame
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            return True, False

    return True, True


# ---------------------------------------------------------------------------
# 5) CDP network capture – reconstruct curl for gamma API calls
# ---------------------------------------------------------------------------
def _build_curl_command(url: str, method: str, headers: dict, body: Optional[str]) -> str:
    """
    Build a curl command string using key headers in stable order.
    Only includes headers that are present in the captured request.
    """
    wanted = [
        'accept', 'accept-language', 'content-type', 'origin', 'priority', 'referer',
        'sec-ch-ua', 'sec-ch-ua-mobile', 'sec-ch-ua-platform', 'sec-fetch-dest',
        'sec-fetch-mode', 'sec-fetch-site', 'sec-fetch-storage-access', 'sec-gpc',
        'user-agent', 'x-csrf-token'
    ]
    parts = ["curl", f"'{url}'"]
    if method and method.upper() != 'GET':
        parts.insert(1, "-X")
        parts.insert(2, method.upper())
    lower_headers = {k.lower(): v for k, v in (headers or {}).items()}
    for key in wanted:
        if key in lower_headers:
            parts.append(f"-H '{key}: {lower_headers[key]}'")
    if body:
        try:
            body_min = json.dumps(json.loads(body), separators=(',', ':'))
        except Exception:
            body_min = body
        parts.append(f"--data-raw '{body_min}'")
    return " \\\n+  ".join(parts)


def enable_iframe_request_capture(driver: WebDriver) -> None:
    """
    Install JavaScript hooks inside the CURRENT FRAME (inner iframe) to record
    fetch/XMLHttpRequest calls to bgaming-network.com and expose them via
    window.__reqCapGet(). This avoids the performance-log approach.
    """
    js = """
    (function(){
      if (window.__reqCapInstalled) return;
      window.__reqCapInstalled = true;
      const queue = [];
      function normHeaders(h){
        const out = {};
        if (!h) return out;
        try { if (typeof h.forEach === 'function') { h.forEach((v,k)=>out[String(k).toLowerCase()]=String(v)); return out; } } catch(e){}
        try { for (const k in h) { out[String(k).toLowerCase()] = String(h[k]); } } catch(e){}
        return out;
      }
      function push(rec){ try{ queue.push(rec); if (queue.length>200) queue.shift(); }catch(e){} }
      const ORIG_FETCH = window.fetch;
      window.fetch = async function(input, init){
        try {
          const url = (input && input.url) ? input.url : (typeof input==='string'? input : '');
          const method = (init && init.method) || (input && input.method) || 'GET';
          const headers = normHeaders((init && init.headers) || (input && input.headers) || {});
          const body = (init && typeof init.body==='string') ? init.body : '';
          if (url && url.indexOf('bgaming-network.com') !== -1) {
            push({type:'fetch', url, method, headers, body, ts: Date.now()});
          }
        } catch(e) {}
        return ORIG_FETCH.apply(this, arguments);
      };
      const XHR = window.XMLHttpRequest;
      const OPEN = XHR.prototype.open;
      const SEND = XHR.prototype.send;
      const SET = XHR.prototype.setRequestHeader;
      XHR.prototype.open = function(m,u){ this.__m=m; this.__u=u; this.__h={}; return OPEN.apply(this, arguments); };
      XHR.prototype.setRequestHeader = function(k,v){ try{ this.__h[String(k).toLowerCase()] = String(v); }catch(e){} return SET.apply(this, arguments); };
      XHR.prototype.send = function(b){ try { const url=this.__u||''; const m=this.__m||'GET'; if (url.indexOf('bgaming-network.com')!==-1){ push({type:'xhr', url, method:m, headers:(this.__h||{}), body:(typeof b==='string'? b : ''), ts: Date.now()}); } } catch(e){} return SEND.apply(this, arguments); };
      window.__reqCapGet = function(){ return queue.slice(); };
      window.__reqCapClear = function(){ queue.length = 0; };
    })();
    """
    try:
        driver.execute_script(js)
        driver._reqcap_enabled = True
    except Exception as e:
        log.warning("Failed to install iframe request capture: %s", e)


def _start_background_capture_printer(driver: WebDriver, poll_interval: float = 0.5) -> None:
    """
    Start a lightweight background thread that polls window.__reqCapGet() inside
    the inner iframe and prints a reconstructed curl for new requests.
    """
    def loop():
        last_count = 0
        while getattr(driver, "_reqcap_poll", True):
            try:
                items = driver.execute_script("return window.__reqCapGet && window.__reqCapGet();") or []
                if len(items) > last_count:
                    new_items = items[last_count:]
                    for rec in new_items:
                        url = rec.get('url','')
                        if 'bgaming-network.com' not in url:
                            continue
                        method = rec.get('method','GET')
                        headers = rec.get('headers', {}) or {}
                        body = rec.get('body', '')
                        curl_cmd = _build_curl_command(url, method, headers, body if body else None)
                        driver._last_gamma_request = {
                            'url': url,
                            'method': method,
                            'headers': headers,
                            'body': body,
                            'curl': curl_cmd,
                        }
                        print(curl_cmd)
                    last_count = len(items)
            except Exception:
                pass
            time.sleep(poll_interval)

    try:
        driver._reqcap_poll = True
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        driver._reqcap_thread = t
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 6) Orchestration – main entry points
# ---------------------------------------------------------------------------
def launch_and_authenticate(mode: Optional[str] = None) -> WebDriver:
    """
    Launch the stealth driver, open the correct McLuck game URL, clear CF,
    ensure login, navigate (if needed) to the target page, and switch into the
    required nested iframes. Returns the WebDriver focused on the INNER iframe.

    IMPORTANT: After this returns, the driver's current frame context is the
    inner game iframe. If you need to interact with the top page again, call
    driver.switch_to.default_content().
    """
    # Resolve mode and URL
    resolved_mode = (mode or os.getenv("MCLUCK_MODE", "GC")).strip().upper()
    target_url = _get_target_url(resolved_mode)

    # Build driver with a persistent profile when provided
    # Prefer the real Brave user data dir; fall back to legacy MCLUCK_PROFILE_DIR
    profile_dir = os.getenv("BRAVE_USER_DATA_DIR") or os.getenv("MCLUCK_PROFILE_DIR")
    profile_name = os.getenv("BRAVE_PROFILE_NAME") or None

    # Silence verbose logs unless explicitly overridden
    _quiet_external_logs()

    driver = create_stealth_driver(
        profile_path=profile_dir,
        profile_name=profile_name,
        maximise=True,
        apply_viewport=False,  # keep maximized window size consistent
        enable_stealth=True,
    )

    # Navigate to target and pass CF
    driver.get(target_url)
    _wait_for_cloudflare_and_app(driver, timeout=90)

    # Ensure we are authenticated. With a real Brave profile we attempt a
    # credential-less Google handshake; otherwise we try provided credentials.
    _ensure_logged_in(driver)

    # Make sure we are on the intended game URL
    _ensure_on_target_page(driver, target_url)

    # Ensure the game canvas is ready before switching into iframes
    _wait_game_canvas_ready(driver, timeout=60)

    # Wait for nested iframes and switch into them, with a single retry path
    outer_ok, inner_ok = _switch_to_required_iframes(driver)
    # Start JS-based capture in the inner iframe
    if inner_ok:
        try:
            enable_iframe_request_capture(driver)
            _start_background_capture_printer(driver)
        except Exception:
            pass
    if not (outer_ok and inner_ok):
        # Retry once after a brief wait and a sanity re-check of the page
        time.sleep(2.0)
        _ensure_on_target_page(driver, target_url)
        _wait_game_canvas_ready(driver, timeout=30)
        # Reset to default content before retry
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        outer_ok, inner_ok = _switch_to_required_iframes(driver)
        if inner_ok:
            try:
                enable_iframe_request_capture(driver)
                _start_background_capture_printer(driver)
            except Exception:
                pass
        if not (outer_ok and inner_ok):
            log.warning("Iframe switching incomplete after retry (outer_ok=%s, inner_ok=%s)", outer_ok, inner_ok)

    return driver


def main() -> None:
    """
    Minimal CLI wrapper:
      - --mode GC|SC selects the target URL
    Keeps the browser open for manual inspection if desired. Close the browser
    window to end the session.
    """
    import argparse

    parser = argparse.ArgumentParser(description="McLuck authentication and iframe navigation")
    parser.add_argument("--mode", choices=["GC", "SC"], default=os.getenv("MCLUCK_MODE", "GC"), help="Target mode: GC or SC")
    args = parser.parse_args()

    # Basic logging to stdout for visibility
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    driver = launch_and_authenticate(args.mode)
    log.info("Ready – driver is now focused on the inner game iframe. Interact as needed.")

    # Keep process alive until user closes the browser window
    try:
        while True:
            time.sleep(1)
            # Break if window is closed
            if len(driver.window_handles) == 0:
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()


