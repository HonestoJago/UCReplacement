#!/usr/bin/env python3
"""
ChromeDriver binary patcher for my_stealth.

This module is responsible for downloading, patching and managing ChromeDriver
binaries so that the infamous `cdc_*` JavaScript variables are **never**
inserted into the rendered pages.  The logic is heavily inspired by the proven
approach used in the undetected-chromedriver (UC) project but has been
rewritten from scratch to be:

1. **Easier to maintain** – clean, well-documented Python 3.8+ code with type
   hints and logging.
2. **Safer** – extra sanity checks, clear error handling and platform support.
3. **Focused on Brave** – defaults work out-of-the-box with the Brave browser
   while still remaining compatible with vanilla Chrome/Chromium if desired.

Typical usage
-------------
>>> from my_stealth.patcher import get_patched_chromedriver
>>> chromedriver_path = get_patched_chromedriver()  # auto-detect & patch

You can then pass *chromedriver_path* to Selenium’s `Service(...)` **or** let
`my_stealth.driver_factory` do that automatically (recommended).
"""
# ---------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------
import io
import json
import logging
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from typing import Optional
from urllib.request import urlopen, urlretrieve

# Third-party
from packaging.version import Version as LooseVersion  # type: ignore


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform helpers – keep everything in one place for readability
# ---------------------------------------------------------------------------
IS_POSIX = sys.platform.startswith(("darwin", "linux", "linux2", "cygwin"))


class ChromeDriverPatcher:
    """Download, patch and cache *ChromeDriver* so it becomes stealthy.

    The public API consists of a **single** method – :py:meth:`get_patched_driver`.
    Everything else is considered an implementation detail.
    """

    # Marker that is appended to every patched binary so we can quickly detect
    # whether a driver has already been processed.
    _PATCH_MARKER = b"my_stealth_patched_binary"

    def __init__(self, *, version_main: Optional[int] = None, force: bool = False) -> None:
        """Create a new patcher instance.

        Parameters
        ----------
        version_main
            Major *Chrome* version you want a driver for e.g. ``114``.  *None*
            (default) means *auto-detect the latest stable*.
        force
            Re-download & re-patch even when a patched binary already exists in
            the cache directory.
        """
        self.version_main = version_main
        self.force = force
        self.version_full: Optional[LooseVersion] = None

        # Attributes that are initialised a little later in helper methods
        self.platform_name: str
        self.exe_name: str
        self.data_path: str
        self.executable_path: str
        self.zip_extract_path: str
        self.url_repo: str
        self.is_old_chromedriver: bool

        # Compute platform-specific settings first
        self._setup_platform()
        self._setup_paths()

        # API split (old ≤114 vs. new ≥115)
        self.is_old_chromedriver = bool(self.version_main and self.version_main <= 114)
        self.url_repo = (
            "https://chromedriver.storage.googleapis.com"
            if self.is_old_chromedriver
            else "https://googlechromelabs.github.io/chrome-for-testing"
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _setup_platform(self) -> None:
        """Figure out file names & platform identifiers for downloads."""
        if sys.platform.endswith("win32"):
            self.platform_name = "win32"
            self.exe_name = "chromedriver.exe"
        elif sys.platform.startswith(("linux", "linux2")):
            self.platform_name = "linux64"
            self.exe_name = "chromedriver"
        elif sys.platform == "darwin":
            # New chromedriver API (≥115) distinguishes between arm/x64 but we
            # keep things simple – the universal build works fine for both.
            self.platform_name = "mac-x64" if (self.version_main or 999) >= 115 else "mac64"
            self.exe_name = "chromedriver"
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def _setup_paths(self) -> None:
        """Create (if needed) and remember our data/cache directory."""
        if sys.platform.endswith("win32"):
            base = os.path.expanduser("~/AppData/Roaming/my_stealth")
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support/my_stealth")
        elif "LAMBDA_TASK_ROOT" in os.environ:
            # AWS Lambda – writable area
            base = "/tmp/my_stealth"
        else:
            base = os.path.expanduser("~/.local/share/my_stealth")

        pathlib.Path(base).mkdir(parents=True, exist_ok=True)

        self.data_path = base
        self.executable_path = os.path.join(base, f"stealth_{self.exe_name}")
        self.zip_extract_path = os.path.join(base, "tmp_extract")

    # ------------------------------------------------------------------
    # Public facade – that’s what the rest of the codebase should call
    # ------------------------------------------------------------------
    def get_patched_driver(self) -> str:
        """Return a *patched* Chromedriver executable – download/patch if needed."""
        if not self.force and self.is_binary_patched():
            logger.info("Using cached patched chromedriver: %s", self.executable_path)
            return self.executable_path

        # Optionally remove old binary first (helps on Windows where the file
        # might be locked when still in use).
        if self.force:
            try:
                os.unlink(self.executable_path)
            except PermissionError:
                self._force_kill_chromedriver()
                try:
                    os.unlink(self.executable_path)
                except FileNotFoundError:
                    pass
            except FileNotFoundError:
                pass

        logger.info("Fetching & patching ChromeDriver – this can take a moment…")

        self.version_full = self._determine_version()
        zip_path = self._download_zip()
        self._extract_zip(zip_path)

        if not self._patch_binary():
            raise RuntimeError("Failed to patch ChromeDriver binary – see logs for details")

        logger.info("Patched chromedriver stored at: %s", self.executable_path)
        return self.executable_path

    # ------------------------------------------------------------------
    # Step-by-step helpers utilised by *get_patched_driver*
    # ------------------------------------------------------------------
    def _determine_version(self) -> LooseVersion:
        """Figure out the *full* version string we are about to download."""
        if self.is_old_chromedriver:
            # Simple text file containing just the version number
            path = f"/LATEST_RELEASE_{self.version_main or ''}".rstrip("_")
            url = f"{self.url_repo}{path}"
            logger.debug("Querying old chromedriver API: %s", url)
            with urlopen(url) as resp:
                version_str = resp.read().decode().strip()
            return LooseVersion(version_str)

        # New *Chrome-for-testing* JSON API
        if self.version_main is None:
            url = f"{self.url_repo}/last-known-good-versions-with-downloads.json"
            logger.debug("Querying new chromedriver API (stable): %s", url)
            with urlopen(url) as resp:
                data = json.loads(resp.read().decode())
            return LooseVersion(data["channels"]["Stable"]["version"])

        # Specific milestone requested
        url = f"{self.url_repo}/latest-versions-per-milestone-with-downloads.json"
        logger.debug("Querying new chromedriver API (per milestone): %s", url)
        with urlopen(url) as resp:
            data = json.loads(resp.read().decode())
        if str(self.version_main) not in data["milestones"]:
            raise ValueError(f"ChromeDriver version {self.version_main} not available from Google")
        return LooseVersion(data["milestones"][str(self.version_main)]["version"])

    def _download_zip(self) -> str:
        """Download the chromedriver *zip* archive and return its local path."""
        zip_name = f"chromedriver_{self.platform_name}.zip"
        if not self.is_old_chromedriver:
            # Slightly different naming convention in new API – hyphen instead
            zip_name = zip_name.replace("_", "-", 1)

        # Assemble download URL
        if self.is_old_chromedriver:
            download_url = f"{self.url_repo}/{self.version_full}/{zip_name}"
        else:
            download_url = (
                "https://storage.googleapis.com/chrome-for-testing-public/"
                f"{self.version_full}/{self.platform_name}/{zip_name}"
            )

        logger.debug("Downloading chromedriver from: %s", download_url)
        zip_path, _ = urlretrieve(download_url)
        return zip_path

    def _extract_zip(self, zip_path: str) -> None:
        """Unpack the downloaded archive into our cache directory."""
        # Clean previous extraction remnants first
        shutil.rmtree(self.zip_extract_path, ignore_errors=True)
        pathlib.Path(self.zip_extract_path).mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(self.zip_extract_path)

        # Locate the actual executable – depends on API version
        if self.is_old_chromedriver:
            src = os.path.join(self.zip_extract_path, self.exe_name)
        else:
            subfolder = f"chromedriver-{self.platform_name}"
            src = os.path.join(self.zip_extract_path, subfolder, self.exe_name)

        shutil.move(src, self.executable_path)
        os.chmod(self.executable_path, 0o755)

        # Clean up
        os.unlink(zip_path)
        shutil.rmtree(self.zip_extract_path, ignore_errors=True)

        logger.debug("Extracted chromedriver to cache: %s", self.executable_path)

    # ------------------------------------------------------------------
    # Actual *patching* logic – UC principle: prevent variable injection
    # ------------------------------------------------------------------
    def _patch_binary(self) -> bool:
        """Patch `cdc_*` injection code blocks inside the executable."""
        start = time.perf_counter()
        try:
            with io.open(self.executable_path, "r+b") as fh:
                content = fh.read()

                # Already patched?
                if self._PATCH_MARKER in content:
                    logger.info("Chromedriver already patched – skipping binary modification")
                    return True

                # Regex hits all occurrences of `{window.cdc_…;}` – non-greedy
                pattern = rb"\{window\.cdc.*?;\}"
                matches = list(re.finditer(pattern, content))
                if not matches:
                    logger.warning("No CDC injection blocks found – driver might have changed its behaviour")
                    return False

                logger.debug("Found %d CDC blocks – applying replacements", len(matches))
                new_content = bytearray(content)  # mutable copy

                replacement = b'{console.log("my_stealth patched!");}'
                for match in matches[::-1]:  # reverse to keep offsets stable
                    start_i, end_i = match.span()
                    padded = replacement.ljust(end_i - start_i, b" ")
                    new_content[start_i:end_i] = padded

                # Append patch marker (helps with future checks)
                new_content += self._PATCH_MARKER

                # Write back & truncate in case new content is shorter
                fh.seek(0)
                fh.write(new_content)
                fh.truncate()

            elapsed = time.perf_counter() - start
            logger.info("Patched %d CDC blocks in %.2f s", len(matches), elapsed)
            return True
        except Exception as exc:
            logger.error("Binary patching failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------
    def is_binary_patched(self, path: Optional[str] = None) -> bool:
        """Check whether *path* (or cached driver) already contains our marker."""
        target = path or self.executable_path
        try:
            with io.open(target, "rb") as fh:
                return self._PATCH_MARKER in fh.read()
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _force_kill_chromedriver(self) -> None:
        """Kill running chromedriver processes so the file can be overwritten."""
        try:
            if IS_POSIX:
                subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True, timeout=10)
            else:
                subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], capture_output=True, timeout=10)
            logger.debug("Terminated running chromedriver instances")
        except Exception as exc:
            logger.warning("Unable to terminate chromedriver processes: %s", exc)


# ---------------------------------------------------------------------------
# Convenience wrapper – one-liner for the rest of the codebase
# ---------------------------------------------------------------------------

def get_patched_chromedriver(*, version_main: Optional[int] = None, force: bool = False) -> str:
    """Return a **ready-to-use** patched chromedriver path.

    Parameters
    ----------
    version_main
        Major Chrome version you want. *None* = latest stable.
    force
        Force re-download and re-patch even when cached version is present.
    """
    patcher = ChromeDriverPatcher(version_main=version_main, force=force)
    return patcher.get_patched_driver()
