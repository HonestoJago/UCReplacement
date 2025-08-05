# stealth.py
import random
import logging
from typing import Any, Dict

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper to run a CDP script that executes *before* any page JS runs.
# ----------------------------------------------------------------------
def _add_script(driver, js_source: str) -> None:
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": js_source},
    )
    log.debug("Injected stealth script: %s", js_source[:80].replace("\n", " "))


# ----------------------------------------------------------------------
# 1️⃣  Hide the Selenium flag
# ----------------------------------------------------------------------
def mask_webdriver(driver) -> None:
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        });
        """,
    )


# ----------------------------------------------------------------------
# 2️⃣  Spoof languages & plugins (classic fingerprint vectors)
# ----------------------------------------------------------------------
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
        """,
    )


# ----------------------------------------------------------------------
# 3️⃣  Randomise screen size / device pixel ratio
# ----------------------------------------------------------------------
def mask_viewport(driver, min_width=1024, max_width=1920, min_height=720, max_height=1080) -> None:
    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)
    # Chrome actually respects the *window* size; the CSS pixel ratio we fake later.
    driver.set_window_size(width, height)

    # Spoof `window.devicePixelRatio` (many sites read it)
    _add_script(
        driver,
        f"""
        Object.defineProperty(window, 'devicePixelRatio', {{
          get: () => {random.choice([1, 1.5, 2])}
        }});
        """,
    )


# ----------------------------------------------------------------------
# 4️⃣  Spoof WebGL vendor / renderer (canvas fingerprint)
# ----------------------------------------------------------------------
def mask_webgl(driver) -> None:
    _add_script(
        driver,
        """
        (function () {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function (param) {
                // 0x1F00 = UNMASKED_VENDOR_WEBGL
                // 0x1F01 = UNMASKED_RENDERER_WEBGL
                if (param === 0x1F00) {
                    return 'Intel Inc.';
                }
                if (param === 0x1F01) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        })();
        """,
    )


# ----------------------------------------------------------------------
# 5️⃣  Canvas fingerprint randomisation (noise injection)
# ----------------------------------------------------------------------
def mask_canvas(driver) -> None:
    """
    Add a tiny amount of noise to the canvas pixel data.
    This mirrors what the original undetected‑chromedriver does
    (it draws a 1×1 pixel hidden canvas and overwrites its getImageData).
    """
    _add_script(
        driver,
        """
        (function () {
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function () {
                // Slightly perturb the image data before it’s read.
                const ctx = this.getContext('2d');
                if (ctx) {
                    const imgData = ctx.getImageData(0, 0, this.width, this.height);
                    // Flip a single pixel randomly – invisible to the user.
                    const i = Math.floor(Math.random() * imgData.data.length);
                    imgData.data[i] = (imgData.data[i] + Math.floor(Math.random() * 256)) % 256;
                    ctx.putImageData(imgData, 0, 0);
                }
                return toDataURL.apply(this, arguments);
            };
        })();
        """,
    )


# ----------------------------------------------------------------------
# 6️⃣  AudioContext fingerprint randomisation
# ----------------------------------------------------------------------
def mask_audio_context(driver) -> None:
    """
    AudioContext fingerprinting is used by some anti‑bot services.
    We simply change the `sampleRate` property to a common value.
    """
    _add_script(
        driver,
        """
        (function () {
            const getChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function () {
                // Return a Float32Array filled with zeros – deterministic.
                const length = this.length;
                const arr = new Float32Array(length);
                return arr;
            };
        })();
        """,
    )


# ----------------------------------------------------------------------
# 7️⃣  Hardware / device properties (concurrency, memory, timezone)
# ----------------------------------------------------------------------
def mask_hardware_and_timezone(driver) -> None:
    """
    * `navigator.hardwareConcurrency` – how many logical CPU cores.
    * `navigator.deviceMemory` – GB of RAM reported to the page.
    * `Intl.DateTimeFormat().resolvedOptions().timeZone` – the timezone string.
    * `Date` prototype – offset / DST tricks.
    """
    # 1️⃣  Hardware concurrency & device memory
    _add_script(
        driver,
        """
        Object.defineProperty(navigator, 'hardwareConcurrency', {
          get: () => 8
        });
        Object.defineProperty(navigator, 'deviceMemory', {
          get: () => 8
        });
        """,
    )

    # 2️⃣  Timezone spoof (pick a random, plausible zone)
    tz = random.choice(
        [
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Singapore",
        ]
    )
    _add_script(
        driver,
        f"""
        // Spoof the Intl time‑zone API
        Intl.DateTimeFormat.prototype.resolvedOptions = function () {{
            return {{timeZone: '{tz}'}};
        }};
        // Spoof the global Date object’s offset
        const RealDate = Date;
        class MockDate extends RealDate {{
            constructor(...args) {{
                super(...args);
                // force the same offset for all dates
                Object.defineProperty(this, 'getTimezoneOffset', {{
                    value: () => {random.choice([-60, 0, 60, 120, 180, 240, 300, 360])}
                }});
            }}
        }}
        window.Date = MockDate;
        """,
    )


# ----------------------------------------------------------------------
# 8️⃣  Miscellaneous tiny patches (permissions, webdriver, etc.)
# ----------------------------------------------------------------------
def mask_misc(driver) -> None:
    """
    * `navigator.permissions.query` – some sites check the “notifications” permission.
    * `navigator.maxTouchPoints` – for “mobile‑like” fingerprinting.
    """
    _add_script(
        driver,
        """
        // Permissions – always return “denied” for notifications/geolocation
        const originalQuery = navigator.permissions.query;
        navigator.permissions.__proto__.query = function (params) {
            if (params.name === 'notifications' || params.name === 'geolocation') {
                return Promise.resolve({state: 'denied'});
            }
            return originalQuery.apply(this, arguments);
        };
        // Touch points – pretend we have a mouse‑only device.
        Object.defineProperty(navigator, 'maxTouchPoints', {
          get: () => 0
        });
        """
    )


# ----------------------------------------------------------------------
# 🎯  One‑liner that applies *all* of the above patches
# ----------------------------------------------------------------------
def apply_stealth(driver) -> None:
    """
    Call this once, right after the driver has been created.
    It runs every mask defined in this module – you can comment out any
    you don’t need.
    """
    mask_webdriver(driver)
    mask_languages_and_plugins(driver)
    mask_viewport(driver)                # random screen size + devicePixelRatio
    mask_webgl(driver)
    mask_canvas(driver)
    mask_audio_context(driver)
    mask_hardware_and_timezone(driver)
    mask_misc(driver)

    # You can add more masks here later (e.g. `mask_navigator_properties`)
    log.info("All stealth patches applied.")
