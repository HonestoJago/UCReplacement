# driver_factory.py
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# ------------------------------------------------------------------
# 1️⃣  Helpers – **absolute** import works for a flat‑folder layout
# ------------------------------------------------------------------
# If you moved the files into a sub‑package (`my_stealth/`) keep the
# relative import (`from .utils …`).  For a single‑folder layout use the
# absolute import as shown here.
from my_stealth.utils import random_user_agent, random_viewport

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
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'languages', {
          get: () => ['en-US', 'en']
        });
        Object.defineProperty(navigator, 'plugins', {
          get: () => [1, 2, 3, 4, 5]
        });
        """
    )

def mask_viewport(driver, *, randomise: bool = True) -> None:
    """
    Randomise the viewport **only** when `randomise` is True.
    When you want the window to stay maximised (or you will set a fixed size later),
    call this function with `randomise=False`.
    """
    if not randomise:
        log.debug("Viewport mask disabled – keeping Chrome's original size.")
        return

    w, h, dpr = random_viewport()
    driver.set_window_size(w, h)
    _add_script(
        driver,
        f"""
        Object.defineProperty(window, 'devicePixelRatio', {{
          get: () => {dpr}
        }});
        """
    )
    log.debug("Random viewport set to %dx%d, DPR %.1f", w, h, dpr)

def mask_webgl(driver) -> None:
    _add_script(
        driver,
        """
        (function () {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function (param) {
                if (param === 0x1F00) {return 'Intel Inc.';}
                if (param === 0x1F01) {return 'Intel Iris OpenGL Engine';}
                return getParameter.apply(this, arguments);
            };
        })();
        """
    )

def mask_canvas(driver) -> None:
    _add_script(
        driver,
        """
        (function () {
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function () {
                const ctx = this.getContext('2d');
                if (ctx) {
                    const img = ctx.getImageData(0, 0, this.width, this.height);
                    const i = Math.floor(Math.random() * img.data.length);
                    img.data[i] = (img.data[i] + Math.floor(Math.random() * 256)) % 256;
                    ctx.putImageData(img, 0, 0);
                }
                return toDataURL.apply(this, arguments);
            };
        })();
        """
    )

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
    import random
    tz = random.choice([
        "America/New_York", "America/Los_Angeles",
        "Europe/London", "Europe/Berlin",
        "Asia/Tokyo", "Asia/Singapore"
    ])
    offset = random.choice([-60, 0, 60, 120, 180, 240, 300, 360])
    # cores / RAM
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'hardwareConcurrency', {get:()=>8});
        Object.defineProperty(navigator, 'deviceMemory', {get:()=>8});
        """
    )
    # timezone
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
    log.debug("Hardware & timezone spoofed (tz=%s, offset=%d)", tz, offset)

def mask_misc(driver) -> None:
    _add_script(
        driver,
        """
        const origQuery = navigator.permissions.query;
        navigator.permissions.__proto__.query = function(p) {
            if (['notifications','geolocation'].includes(p.name)) {
                return Promise.resolve({state:'denied'});
            }
            return origQuery.apply(this, arguments);
        };
        Object.defineProperty(navigator, 'maxTouchPoints', {get:()=>0});
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
    mask_canvas(driver)
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
    opts.add_argument(f"user-agent={random_user_agent()}")

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
        service = Service(executable_path=driver_path)
    else:
        # Auto‑download the correct ChromeDriver version:
        # Note: BRAVE_VERSION from .env is used for reference/logging but webdriver-manager
        # will auto-detect the actual browser version and download the matching driver
        chrome_version = os.getenv("BRAVE_VERSION")
        if chrome_version:
            log.info(f"BRAVE_VERSION environment variable is set to: {chrome_version}")
            log.info("WebDriver Manager will auto-detect actual browser version and download matching ChromeDriver")
        else:
            log.info("No BRAVE_VERSION set, auto-detecting Chrome version and using compatible ChromeDriver")
        
        service = Service(ChromeDriverManager().install())
        log.info("Using webdriver-manager to auto-download compatible ChromeDriver")

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
