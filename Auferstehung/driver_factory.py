# driver_factory.py
import os
import logging
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchWindowException

# Optional auto-downloader (fallback when our own patcher is not used)
from webdriver_manager.chrome import ChromeDriverManager

# 🆕  Stealth patcher – download **and** patch a compatible driver in one go
from Auferstehung.patcher import get_patched_chromedriver

# Load environment variables
load_dotenv()

# ------------------------------------------------------------------
# 1️⃣  Helpers – **absolute** import works for a flat‑folder layout
# ------------------------------------------------------------------
# If you moved the files into a sub‑package (`my_stealth/`) keep the
# relative import (`from .utils …`).  For a single‑folder layout use the
# absolute import as shown here.
from Auferstehung.utils import get_consistent_user_agent, get_consistent_viewport, get_system_timezone, get_system_timezone_offset, get_consistent_hardware

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 0️⃣  Profile helper – prevent Brave from restoring old tabs
# ------------------------------------------------------------------
def _fix_exit_type(user_data_dir: Path, profile_name: str = "Default") -> None:
    """Ensure the profile's *exit_type* is set to *CleanExit*.

    Brave/Chrome write the last shutdown state into the *Preferences* JSON.  If
    the browser did not close gracefully (common with scripted sessions) the
    value becomes "Crashed" and the next launch will auto-restore all tabs –
    exactly what we *do not* want in automated tests.  UC solves this by
    resetting the flag; we replicate that here.
    """
    pref_file = user_data_dir / profile_name / "Preferences"
    try:
        if not pref_file.is_file():
            return  # nothing to do – fresh profile

        prefs = json.loads(pref_file.read_text(encoding="utf-8"))
        if prefs.get("profile", {}).get("exit_type") != "CleanExit":
            prefs.setdefault("profile", {})["exit_type"] = "CleanExit"
            pref_file.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
            log.debug("Reset profile exit_type → CleanExit to avoid session restore")
    except Exception as exc:  # pragma: no cover – safety net
        log.warning("Failed to set exit_type=CleanExit (non-fatal): %s", exc)

# ------------------------------------------------------------------
# 2️⃣  CDP script injector (used by every mask)
# ------------------------------------------------------------------
def _add_script(driver, js_source: str) -> None:
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": js_source},
        )
    except NoSuchWindowException:
        # The initial window got closed (session restore). Open a fresh tab and retry once.
        log.debug("NoSuchWindowException during CDP inject – creating new blank tab and retrying")
        try:
            driver.switch_to.new_window("tab")
        except Exception:
            driver.execute_script("window.open('about:blank','_blank');")
            driver.switch_to.window(driver.window_handles[-1])

        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": js_source},
        )

    log.debug("Injected script (first 80 chars): %s", js_source[:80].replace("\n", " "))

# ------------------------------------------------------------------
# 3️⃣  Stealth‑mask functions (unchanged except for viewport)
# ------------------------------------------------------------------
def mask_webdriver(driver) -> None:
    _add_script(
        driver,
        """
        (function () {
            // Remove navigator.webdriver entirely (prototype and instance)
            try {
                delete Navigator.prototype.webdriver;
            } catch (e) {}
            try {
                delete navigator.webdriver;
            } catch (e) {}
        })();
        """
    )

def mask_languages_and_plugins(driver) -> None:
    """Set realistic, consistent language and plugin values"""
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'languages', {
          get: () => ['en-US', 'en']
        });
        
        // Only spoof plugins if the real profile has none (e.g. temp profile)
        if (navigator.plugins.length === 0) {
          const createPlugin = (name, filename, description = '') => {
            const p = Object.create(Plugin.prototype);
            Object.assign(p, { name, filename, description, 0: {} });
            return p;
          };
          const fakePlugins = Object.assign(Object.create(PluginArray.prototype), {
            0: createPlugin('Chrome PDF Plugin', 'internal-pdf-viewer'),
            1: createPlugin('Chromium PDF Plugin', 'mhjfbmdgcfjbbpaeojofohoefgiehjai'),
            2: createPlugin('Chrome PDF Viewer', 'internal-pdf-viewer'),
            3: createPlugin('Native Client', 'internal-nacl-plugin'),
            length: 4,
            item: function (i) { return this[i]; },
            namedItem: function (name) { return Array.from(this).find(p => p.name === name); },
            refresh: () => {}
          });
          Object.defineProperty(navigator, 'plugins', { get: () => fakePlugins });
        }
        """
    )

def mask_viewport(driver, *, apply_viewport: bool = True) -> None:
    """
    Set consistent viewport size based on profile.
    UC approach: Use consistent viewport per profile, same "device" every session.
    When you want the window to stay maximized, call with apply_viewport=False.
    """
    if not apply_viewport:
        log.debug("Viewport mask disabled – keeping browser's original size.")
        return

    w, h, dpr = get_consistent_viewport()
    driver.set_window_size(w, h)
    _add_script(
        driver,
        f"""
        Object.defineProperty(window, 'devicePixelRatio', {{
          get: () => {dpr}
        }});
        
        // Ensure screen properties are consistent - same "device" every session
        Object.defineProperty(screen, 'width', {{
          get: () => {w}
        }});
        Object.defineProperty(screen, 'height', {{
          get: () => {h}
        }});
        Object.defineProperty(screen, 'availWidth', {{
          get: () => {w}
        }});
        Object.defineProperty(screen, 'availHeight', {{
          get: () => {h - 40}  // Account for taskbar
        }});
        """
    )
    log.debug("Consistent viewport set to %dx%d, DPR %.1f", w, h, dpr)

def mask_webgl(driver) -> None:
    """Enhanced WebGL spoofing with WebGL2 support (inspired by Claude)"""
    _add_script(
        driver,
        """
        (function () {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            
            // Enhanced parameter overrides
            const overrides = {
                0x1F00: 'Intel Inc.',  // VENDOR
                0x1F01: 'Intel Iris OpenGL Engine',  // RENDERER
                0x9246: 'Intel Iris OpenGL Engine'   // UNMASKED_RENDERER_WEBGL
            };
            
            function getParameterProxy(original) {
                return function(param) {
                    const value = original.apply(this, arguments);
                    // If SwiftShader detected, override with realistic values
                    const rendererStr = typeof value === 'string' ? value : '';
                    if (/SwiftShader/i.test(rendererStr) && overrides[param]) {
                        return overrides[param];
                    }
                    if (overrides.hasOwnProperty(param)) {
                        return overrides[param];
                    }
                    return value;
                };
            }
            
            // Apply to both WebGL 1 and WebGL 2
            WebGLRenderingContext.prototype.getParameter = getParameterProxy(WebGLRenderingContext.prototype.getParameter);
            if (window.WebGL2RenderingContext) {
                WebGL2RenderingContext.prototype.getParameter = getParameterProxy(WebGL2RenderingContext.prototype.getParameter);
            }
        })();
        """
    )

# Canvas protection removed - UC approach: let canvas render naturally
# Consistent fingerprints = same "device" = safer for account security

def mask_audio_context(driver) -> None:
    _add_script(
        driver,
        """
        (function () {
            const getChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function () {
                return new Float32Array(this.length);   // deterministic zeros
            };
        })();
        """
    )

def mask_hardware_and_timezone(driver) -> None:
    """
    Use consistent system-based hardware and timezone info.
    UC approach: Match actual system specs rather than random values.
    """
    # Get consistent hardware specs (same per profile)
    cpu_cores, memory_gb = get_consistent_hardware()
    
    # Get actual system timezone (most realistic)
    tz = get_system_timezone()
    
    # Calculate timezone offset using improved method (handles DST)
    offset = get_system_timezone_offset()
    
    # Set consistent hardware specs
    _add_script(
        driver,
        f"""
        Object.defineProperty(navigator, 'hardwareConcurrency', {{get:()=>{cpu_cores}}});
        Object.defineProperty(navigator, 'deviceMemory', {{get:()=>{memory_gb}}});
        """
    )
    
    # Set system timezone (not random)
    _add_script(
        driver,
        f"""
        Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
            return {{timeZone: '{tz}'}};
        }};
        const RealDate = Date;
        class MockDate extends RealDate {{
            constructor(...args) {{ super(...args);
                Object.defineProperty(this,'getTimezoneOffset',{{value:()=>{offset}}});
            }}
        }}
        window.Date = MockDate;
        """
    )
    log.debug("Consistent hardware & timezone set (tz=%s, offset=%d, cores=%d, RAM=%dGB)", 
              tz, offset, cpu_cores, memory_gb)

def mask_misc(driver) -> None:
    """Enhanced misc property spoofing (inspired by Claude's approach)"""
    _add_script(
        driver,
        """
        // Permissions - consistent denials for privacy-sensitive permissions
        const originalQuery = navigator.permissions.query;
        navigator.permissions.__proto__.query = function(parameters) {
            if (parameters.name === 'notifications') {
                // Realistic: default (not yet granted) state
                return Promise.resolve({state: 'default'});
            }
            if (['geolocation','camera','microphone'].includes(parameters.name)) {
                return Promise.resolve({state: 'denied'});
            }
            return originalQuery.apply(this, arguments);
        };
        
        // Touch - consistent with desktop environment
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0
        });
        
        // Platform - should match user agent (Windows)
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'  // Consistent with Windows UA
        });
        """
    )

def apply_stealth(driver, *, apply_viewport: bool = True) -> None:
    """
    Run *all* stealth masks for consistent "device" fingerprint.
    The only mask you might want to skip is the viewport one – pass 
    `apply_viewport=False` to keep the window size you set (maximized).
    
    UC Philosophy: Same profile = same "device" = consistent fingerprint.
    """
    mask_webdriver(driver)
    mask_languages_and_plugins(driver)
    mask_viewport(driver, apply_viewport=apply_viewport)   # <-- respects the flag
    mask_webgl(driver)
    # mask_canvas(driver) - REMOVED: UC approach is to let canvas render naturally
    mask_audio_context(driver)
    mask_hardware_and_timezone(driver)
    mask_misc(driver)
    log.info("All stealth patches applied - consistent fingerprint established.")

# ------------------------------------------------------------------
# 4️⃣  Public factory – the only thing you import from this module
# ------------------------------------------------------------------
def create_stealth_driver(*,
                         proxy: Optional[str] = None,
                         profile_path: Optional[str] = None,
                         profile_name: Optional[str] = None,
                         binary_path: Optional[str] = None,
                         driver_path: Optional[str] = None,
                         enable_stealth: bool = True,
                         maximise: bool = True,
                         apply_viewport: bool = True) -> webdriver.Chrome:
    """
    Build a Brave/Chrome driver with the classic UC stealth masks **and**
    an optional persistent profile.
    
    UC Philosophy: Always run with visible UI - headless is a major bot detection flag.
    Real users don't browse headlessly, so neither should stealth automation.

    Parameters
    ----------
    proxy             – optional proxy URL.
    profile_path      – folder that will be used as `--user-data-dir`.
    profile_name      – specific profile directory name within user_data_dir.
    binary_path       – explicit path to Brave/Chrome binary (optional).
    driver_path       – explicit path to chromedriver (optional).
    enable_stealth    – set False to get a plain driver (useful for debugging).
    maximise          – ask Chrome to start maximised **and** call
                         `driver.maximize_window()` after creation.
    apply_viewport    – if True (default) applies consistent viewport mask
                         for this profile; set to False when you want to keep
                         the browser's natural size (e.g. maximized).
    """
    opts = Options()
    # Reduce Chromium console spam and keep automation switches disabled
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # silence "DevTools listening..."
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    # Do NOT disable GPU – keeping hardware acceleration avoids noisy WebGL/SwiftShader logs
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")          # ask Chrome to start maximised
    # Lower Chromium's own logging verbosity
    opts.add_argument("--log-level=3")              # 0=INFO,1=WARNING,2=LOG_ERROR,3=LOG_FATAL
    opts.add_argument("--disable-logging")
    opts.add_argument(f"user-agent={get_consistent_user_agent()}")
    
    # Enable performance logging for CDP event monitoring
    # This allows my_stealth.cdp_events to capture network and other browser events
    opts.add_experimental_option("perfLoggingPrefs", {
        "enableNetwork": True,
        "enablePage": True
    })
    opts.set_capability("goog:loggingPrefs", {
        "performance": "ALL",
        "browser": "ALL"
    })
    
    # UC Philosophy: NEVER run headless - it's a major detection flag
    # Real users always have visible browsers, so we do too

    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")

    if profile_path:
        p = Path(profile_path).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)

        # 🆕  Make sure Brave does **not** restore previous session tabs
        _fix_exit_type(Path(profile_path).expanduser().resolve(), profile_name or "Default")
        opts.add_argument(f"--user-data-dir={p}")
        
        # If a specific profile name is provided, use it
        if profile_name:
            opts.add_argument(f"--profile-directory={profile_name}")
            log.info(f"Using Brave profile: {profile_name} in user data dir: {p}")

    if binary_path:
        opts.binary_location = binary_path
    else:
        env_path = os.getenv("BRAVE_BINARY_PATH")
        if env_path:
            opts.binary_location = env_path
        else:
            # Auto-detect Brave browser on Windows
            brave_paths = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
            ]
            
            for brave_path in brave_paths:
                if os.path.exists(brave_path):
                    opts.binary_location = brave_path
                    log.info(f"Found Brave browser at: {brave_path}")
                    break
            else:
                log.warning("Brave browser not found in standard locations. Will use default Chrome browser.")
                log.info("To use Brave, set BRAVE_BINARY_PATH environment variable to your Brave executable path.")

    # Driver service – you can enable webdriver‑manager here if you wish
    if driver_path:
        # User supplied an explicit chromedriver – honour it *without* interference.
        service = Service(executable_path=driver_path)
    else:
        # Default & *recommended* path: download a **patched** driver that no longer
        # injects the easily detectable `cdc_*` variables.  Fallback to
        # webdriver-manager only when our patcher fails (rare network issues).

        try:
            patched_path = get_patched_chromedriver()
            service = Service(patched_path)
            log.info("Using patched ChromeDriver: %s", patched_path)
        except Exception as exc:
            log.warning("get_patched_chromedriver failed (%s) – falling back to webdriver-manager", exc)

            chrome_version = os.getenv("BRAVE_VERSION")
            if chrome_version:
                log.info("BRAVE_VERSION=%s – webdriver-manager will attempt to match it", chrome_version)
            else:
                log.info("No BRAVE_VERSION set – webdriver-manager will auto-detect the browser version")

            service = Service(ChromeDriverManager().install())
            log.info("Using *unpatched* driver from webdriver-manager – stealth might be reduced")

    driver = webdriver.Chrome(service=service, options=opts)

    # Ensure a stable window before we start injecting CDP scripts.
    try:
        driver.get("about:blank")
    except Exception as exc:   # pragma: no cover
        log.warning("Initial about:blank navigation failed (non-fatal): %s", exc)

    # --------------------------------------------------------------
    # 5️⃣  **Maximise** – we always have a visible UI for stealth
    # --------------------------------------------------------------
    if maximise:
        try:
            driver.maximize_window()
            log.info("Browser window maximised via driver.maximize_window()")
            
            # Verify window size is valid after maximizing
            window_size = driver.get_window_size()
            if window_size['width'] <= 0 or window_size['height'] <= 0:
                log.warning("Invalid window size after maximize, setting fallback size")
                driver.set_window_size(1280, 720)
                
        except Exception as exc:   # pragma: no cover – safety net
            log.warning("Failed to maximise window: %s", exc)
            # Fallback to reasonable size
            try:
                driver.set_window_size(1280, 720)
                log.info("Set fallback window size: 1280x720")
            except Exception:
                pass

    # --------------------------------------------------------------
    # 6️⃣  Apply stealth masks – consistent fingerprint per profile
    # --------------------------------------------------------------
    if enable_stealth:
        apply_stealth(driver, apply_viewport=apply_viewport)

    log.info(
        "Stealth driver created – proxy=%s, profile=%s, maximise=%s, apply_viewport=%s",
        proxy, profile_path, maximise, apply_viewport,
    )
    return driver


def get_driver(**kwargs) -> webdriver.Chrome:
    """
    Thin wrapper that mimics the old `undetected_chromedriver.Chrome`
    constructor signature.  All kwargs are passed straight through.
    """
    return create_stealth_driver(**kwargs)
