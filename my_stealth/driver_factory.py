# driver_factory.py
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from selenium import webdriver
# Selenium helpers
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Optional auto-downloader (fallback when our own patcher is not used)
from webdriver_manager.chrome import ChromeDriverManager

# 🆕  Stealth patcher – download **and** patch a compatible driver in one go
from my_stealth.patcher import get_patched_chromedriver

# Load environment variables
load_dotenv()

# ------------------------------------------------------------------
# 1️⃣  Helpers – **absolute** import works for a flat‑folder layout
# ------------------------------------------------------------------
# If you moved the files into a sub‑package (`my_stealth/`) keep the
# relative import (`from .utils …`).  For a single‑folder layout use the
# absolute import as shown here.
from my_stealth.utils import get_consistent_user_agent, get_consistent_viewport, get_system_timezone, get_system_timezone_offset, get_consistent_hardware

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 2️⃣  CDP script injector (used by every mask)
# ------------------------------------------------------------------
def _add_script(driver, js_source: str) -> None:
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": js_source},
    )
    log.debug(
        "Injected script (first 80 chars): %s",
        js_source[:80].replace("\n", " ")
    )

# ------------------------------------------------------------------
# 3️⃣  Stealth‑mask functions (unchanged except for viewport)
# ------------------------------------------------------------------
def mask_webdriver(driver) -> None:
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        });
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
        
        // Mock realistic plugins array (inspired by Claude's approach)
        Object.defineProperty(navigator, 'plugins', {
          get: () => {
            const plugins = [
              {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
              {name: 'Chromium PDF Plugin', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
              {name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer'},
              {name: 'Native Client', filename: 'internal-nacl-plugin'}
            ];
            plugins.length = 4;  // Set length property for realism
            return plugins;
          }
        });
        """
    )

def mask_viewport(driver, *, randomise: bool = True) -> None:
    """
    Set consistent viewport size when randomise is True.
    UC approach: Use consistent viewport per profile, not random each session.
    When you want the window to stay maximised, call with randomise=False.
    """
    if not randomise:
        log.debug("Viewport mask disabled – keeping Chrome's original size.")
        return

    w, h, dpr = get_consistent_viewport()
    driver.set_window_size(w, h)
    _add_script(
        driver,
        f"""
        Object.defineProperty(window, 'devicePixelRatio', {{
          get: () => {dpr}
        }});
        
        // Ensure screen properties are consistent (inspired by Claude)
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
                0x1F02: '4.1 Intel Iris OpenGL Engine',  // VERSION
                0x8B8C: 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)'  // SHADING_LANGUAGE_VERSION
            };
            
            function getParameterProxy(original) {
                return function(param) {
                    if (overrides.hasOwnProperty(param)) {
                        return overrides[param];
                    }
                    return original.apply(this, arguments);
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
            const deniedPermissions = ['notifications', 'geolocation', 'camera', 'microphone'];
            if (deniedPermissions.includes(parameters.name)) {
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

def apply_stealth(driver, *, randomise_viewport: bool = True) -> None:
    """
    Run *all* masks.  The only mask you might want to skip is the viewport
    one – pass `randomise_viewport=False` to keep the window size you set
    (maximised or a fixed size you supplied via Chrome options).
    """
    mask_webdriver(driver)
    mask_languages_and_plugins(driver)
    mask_viewport(driver, randomise=randomise_viewport)   # <-- respects the flag
    mask_webgl(driver)
    # mask_canvas(driver) - REMOVED: UC approach is to let canvas render naturally
    mask_audio_context(driver)
    mask_hardware_and_timezone(driver)
    mask_misc(driver)
    log.info("All stealth patches applied.")

# ------------------------------------------------------------------
# 4️⃣  Public factory – the only thing you import from this module
# ------------------------------------------------------------------
def create_stealth_driver(*,
                         headless: bool = False,
                         proxy: Optional[str] = None,
                         profile_path: Optional[str] = None,
                         profile_name: Optional[str] = None,
                         binary_path: Optional[str] = None,
                         driver_path: Optional[str] = None,
                         enable_stealth: bool = True,
                         maximise: bool = True,
                         randomise_viewport: bool = True) -> webdriver.Chrome:
    """
    Build a Brave/Chrome driver with the classic UC stealth masks **and**
    an optional persistent profile.

    Parameters
    ----------
    headless          – run Chrome headless.
    proxy             – optional proxy URL.
    profile_path      – folder that will be used as `--user-data-dir`.
    binary_path       – explicit path to Brave/Chrome binary (optional).
    driver_path       – explicit path to chromedriver (optional).
    enable_stealth    – set False to get a plain driver (useful for debugging).
    maximise          – ask Chrome to start maximised **and** call
                         `driver.maximize_window()` after creation.
    randomise_viewport – if True (default) the classic UC random‑viewport mask
                         is applied; set to False when you want a deterministic
                         size (e.g. maximised).
    """
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
    opts.add_argument("--start-maximized")          # ask Chrome to start maximised
    opts.add_argument(f"user-agent={get_consistent_user_agent()}")

    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-features=VizDisplayCompositor")

    if proxy:
        opts.add_argument(f"--proxy-server={proxy}")

    if profile_path:
        p = Path(profile_path).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
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

    # --------------------------------------------------------------
    # 5️⃣  **Maximise** – only when we have a UI (headless == False)
    # --------------------------------------------------------------
    if maximise and not headless:
        try:
            driver.maximize_window()
            log.info("Browser window maximised via driver.maximize_window()")
        except Exception as exc:   # pragma: no cover – safety net
            log.warning("Failed to maximise window: %s", exc)

    # --------------------------------------------------------------
    # 6️⃣  Apply stealth masks – pass the flag that controls viewport randomisation
    # --------------------------------------------------------------
    if enable_stealth:
        apply_stealth(driver, randomise_viewport=randomise_viewport)

    log.info(
        "Stealth driver created – headless=%s, proxy=%s, profile=%s, maximise=%s, randomise_viewport=%s",
        headless, proxy, profile_path, maximise, randomise_viewport,
    )
    return driver


def get_driver(**kwargs) -> webdriver.Chrome:
    """
    Thin wrapper that mimics the old `undetected_chromedriver.Chrome`
    constructor signature.  All kwargs are passed straight through.
    """
    return create_stealth_driver(**kwargs)
