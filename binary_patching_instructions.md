# ChromeDriver Binary Patcher Implementation Guide

## OBJECTIVE
Implement UC-style binary patching for ChromeDriver to prevent injection of detectable CDC variables. This addresses the root cause of automation detection by modifying the ChromeDriver executable itself.

## UNDERSTANDING THE PROBLEM

### What ChromeDriver Injects
When ChromeDriver runs, it injects JavaScript code blocks into web pages:
```javascript
{window.cdc_adoQpoasnfa76pfcZLmcfl_Array = Array;}
{window.cdc_adoQpoasnfa76pfcZLmcfl_Object = Object;}
{window.cdc_adoQpoasnfa76pfcZLmcfl_Promise = Promise;}
```

### How Detection Works
Anti-bot systems detect these variables:
```javascript
// Simple detection
if (window.cdc_adoQpoasnfa76pfcZLmcfl_Array) {
    console.log("ChromeDriver detected!");
    // Block user
}

// Advanced detection
const cdcVars = Object.keys(window).filter(key => key.startsWith('cdc_'));
if (cdcVars.length > 0) {
    // Immediate blocking
}
```

## UC'S PROVEN SOLUTION

### Current UC Approach (v3.5+)
UC **prevents injection entirely** by replacing the injection code blocks in the binary:

```python
# UC's current patching method
def patch_exe(self):
    with io.open(self.executable_path, "r+b") as fh:
        content = fh.read()
        
        # Find injection code blocks
        match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
        
        if match_injected_codeblock:
            target_bytes = match_injected_codeblock[0]
            
            # Replace with harmless code
            new_target_bytes = (
                b'{console.log("undetected chromedriver 1337!")}'.ljust(
                    len(target_bytes), b" "
                )
            )
            
            new_content = content.replace(target_bytes, new_target_bytes)
            fh.seek(0)
            fh.write(new_content)
```

**Key Insight**: Instead of changing variable names, UC **prevents the variables from being created at all**.

## IMPLEMENTATION PLAN

### File Structure
```
my_stealth/
├── __init__.py
├── cookies.py
├── driver_factory.py
├── utils.py
└── patcher.py          # 🆕 NEW FILE - Binary patching logic
```

### 1. Create `my_stealth/patcher.py`

```python
#!/usr/bin/env python3
"""
ChromeDriver binary patcher for my_stealth.
Based on undetected-chromedriver's proven approach.
"""

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
from packaging.version import Version as LooseVersion

logger = logging.getLogger(__name__)

IS_POSIX = sys.platform.startswith(("darwin", "cygwin", "linux", "linux2"))

class ChromeDriverPatcher:
    """
    Downloads, patches, and manages ChromeDriver binaries for stealth operation.
    Based on UC's proven binary patching approach.
    """
    
    def __init__(self, version_main: Optional[int] = None, force: bool = False):
        """
        Initialize the patcher.
        
        Args:
            version_main: Specific Chrome major version (e.g., 131), None = auto-detect
            force: Force re-download and re-patch even if exists
        """
        self.version_main = version_main
        self.force = force
        self.version_full = None
        
        # Set platform-specific paths and names
        self._setup_platform()
        self._setup_paths()
        
        # Determine if this is old or new ChromeDriver API
        self.is_old_chromedriver = version_main and version_main <= 114
        
        # Set correct repository URLs
        if self.is_old_chromedriver:
            self.url_repo = "https://chromedriver.storage.googleapis.com"
        else:
            self.url_repo = "https://googlechromelabs.github.io/chrome-for-testing"
    
    def _setup_platform(self):
        """Set platform-specific executable names and platform identifiers."""
        if sys.platform.endswith("win32"):
            self.platform_name = "win32"
            self.exe_name = "chromedriver.exe"
        elif sys.platform.endswith(("linux", "linux2")):
            self.platform_name = "linux64"
            self.exe_name = "chromedriver"
        elif sys.platform.endswith("darwin"):
            if self.is_old_chromedriver:
                self.platform_name = "mac64"
            else:
                self.platform_name = "mac-x64"
            self.exe_name = "chromedriver"
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")
    
    def _setup_paths(self):
        """Setup data directory and executable paths."""
        # Data directory (cross-platform)
        if sys.platform.endswith("win32"):
            data_dir = "~/AppData/Roaming/my_stealth"
        elif "LAMBDA_TASK_ROOT" in os.environ:
            data_dir = "/tmp/my_stealth"
        elif sys.platform.startswith(("linux", "linux2")):
            data_dir = "~/.local/share/my_stealth"
        elif sys.platform.endswith("darwin"):
            data_dir = "~/Library/Application Support/my_stealth"
        else:
            data_dir = "~/.my_stealth"
        
        self.data_path = os.path.abspath(os.path.expanduser(data_dir))
        os.makedirs(self.data_path, exist_ok=True)
        
        # Executable path
        self.executable_path = os.path.join(self.data_path, f"stealth_{self.exe_name}")
        self.zip_path = os.path.join(self.data_path, "temp_download")
    
    def get_patched_driver(self) -> str:
        """
        Get a patched ChromeDriver, downloading and patching if necessary.
        
        Returns:
            str: Path to patched ChromeDriver executable
        """
        # Check if already patched and not forcing update
        if not self.force and self.is_binary_patched():
            logger.info(f"Using existing patched driver: {self.executable_path}")
            return self.executable_path
        
        # Remove existing if forcing update
        if self.force:
            try:
                os.unlink(self.executable_path)
            except FileNotFoundError:
                pass
            except PermissionError:
                self._force_kill_chromedriver()
                try:
                    os.unlink(self.executable_path)
                except FileNotFoundError:
                    pass
        
        # Download and patch
        logger.info("Downloading and patching ChromeDriver...")
        
        # Get version info
        release = self._fetch_release_number()
        self.version_main = release.major
        self.version_full = release
        
        # Download and extract
        zip_path = self._download_chromedriver()
        self._extract_chromedriver(zip_path)
        
        # Apply patch
        if self._patch_binary():
            logger.info(f"Successfully patched ChromeDriver: {self.executable_path}")
            return self.executable_path
        else:
            raise RuntimeError("Failed to patch ChromeDriver binary")
    
    def _fetch_release_number(self) -> LooseVersion:
        """Fetch the appropriate ChromeDriver version."""
        if self.is_old_chromedriver:
            # Old API (≤114)
            path = f"/LATEST_RELEASE_{self.version_main}"
            url = self.url_repo + path
            logger.debug(f"Fetching version from: {url}")
            
            with urlopen(url) as response:
                version_str = response.read().decode().strip()
            return LooseVersion(version_str)
        
        else:
            # New API (115+)
            if not self.version_main:
                # Get latest stable
                path = "/last-known-good-versions-with-downloads.json"
                url = self.url_repo + path
                
                with urlopen(url) as response:
                    data = json.loads(response.read().decode())
                return LooseVersion(data["channels"]["Stable"]["version"])
            
            else:
                # Get specific major version
                path = "/latest-versions-per-milestone-with-downloads.json"
                url = self.url_repo + path
                
                with urlopen(url) as response:
                    data = json.loads(response.read().decode())
                
                if str(self.version_main) not in data["milestones"]:
                    raise ValueError(f"ChromeDriver version {self.version_main} not available")
                
                return LooseVersion(data["milestones"][str(self.version_main)]["version"])
    
    def _download_chromedriver(self) -> str:
        """Download ChromeDriver zip file."""
        zip_name = f"chromedriver_{self.platform_name}.zip"
        
        if self.is_old_chromedriver:
            download_url = f"{self.url_repo}/{self.version_full}/{zip_name}"
        else:
            zip_name = zip_name.replace("_", "-", 1)  # chromedriver-platform.zip
            download_url = (
                f"https://storage.googleapis.com/chrome-for-testing-public/"
                f"{self.version_full}/{self.platform_name}/{zip_name}"
            )
        
        logger.debug(f"Downloading from: {download_url}")
        zip_path, _ = urlretrieve(download_url)
        return zip_path
    
    def _extract_chromedriver(self, zip_path: str):
        """Extract ChromeDriver from zip file."""
        # Clean up temp directory
        if os.path.exists(self.zip_path):
            shutil.rmtree(self.zip_path)
        os.makedirs(self.zip_path, exist_ok=True)
        
        # Extract
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(self.zip_path)
        
        # Find the chromedriver executable
        if self.is_old_chromedriver:
            source_path = os.path.join(self.zip_path, self.exe_name)
        else:
            # New format has subfolder
            subfolder = f"chromedriver-{self.platform_name}"
            source_path = os.path.join(self.zip_path, subfolder, self.exe_name)
        
        # Move to final location
        shutil.move(source_path, self.executable_path)
        
        # Set executable permissions
        os.chmod(self.executable_path, 0o755)
        
        # Cleanup
        os.unlink(zip_path)
        shutil.rmtree(self.zip_path)
        
        logger.debug(f"Extracted ChromeDriver to: {self.executable_path}")
    
    def _patch_binary(self) -> bool:
        """
        Apply UC-style binary patching to prevent CDC injection.
        
        Returns:
            bool: True if patching successful
        """
        start_time = time.perf_counter()
        logger.info(f"Patching ChromeDriver binary: {self.executable_path}")
        
        try:
            with io.open(self.executable_path, "r+b") as fh:
                content = fh.read()
                
                # UC's current approach: find and replace injection code blocks
                # Pattern matches: {window.cdc_...;}
                pattern = rb"\{window\.cdc.*?;\}"
                matches = list(re.finditer(pattern, content))
                
                if not matches:
                    logger.warning("No CDC injection code blocks found - binary might already be patched or incompatible")
                    return False
                
                logger.debug(f"Found {len(matches)} CDC injection code blocks")
                
                # Replace each injection block
                new_content = content
                patches_applied = 0
                
                for match in reversed(matches):  # Reverse to maintain offsets
                    target_bytes = match.group(0)
                    
                    # Create replacement (same length, padded with spaces)
                    replacement_code = b'{console.log("my_stealth patched!");}'
                    new_target_bytes = replacement_code.ljust(len(target_bytes), b" ")
                    
                    # Apply replacement
                    start_pos = match.start()
                    end_pos = match.end()
                    new_content = (
                        new_content[:start_pos] + 
                        new_target_bytes + 
                        new_content[end_pos:]
                    )
                    patches_applied += 1
                    
                    logger.debug(
                        f"Replaced CDC block {patches_applied}: "
                        f"{target_bytes[:50]}... -> "
                        f"{new_target_bytes[:50]}..."
                    )
                
                # Write patched content
                fh.seek(0)
                fh.write(new_content)
                fh.truncate()
                
                # Add patch marker for future detection
                marker = b"my_stealth_patched_binary"
                if marker not in new_content:
                    fh.write(marker)
                
                patch_time = time.perf_counter() - start_time
                logger.info(
                    f"Successfully patched {patches_applied} CDC injection blocks "
                    f"in {patch_time:.2f} seconds"
                )
                
                return patches_applied > 0
                
        except Exception as e:
            logger.error(f"Failed to patch binary: {e}")
            return False
    
    def is_binary_patched(self, executable_path: Optional[str] = None) -> bool:
        """
        Check if ChromeDriver binary is already patched.
        
        Args:
            executable_path: Path to check, defaults to self.executable_path
            
        Returns:
            bool: True if binary is patched
        """
        path = executable_path or self.executable_path
        
        try:
            with io.open(path, "rb") as fh:
                content = fh.read()
                # Check for our patch marker
                return b"my_stealth_patched_binary" in content
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _force_kill_chromedriver(self):
        """Force kill any running ChromeDriver processes."""
        try:
            if IS_POSIX:
                # Unix-like systems
                result = subprocess.run(
                    ["pkill", "-f", "chromedriver"], 
                    capture_output=True, 
                    timeout=10
                )
                logger.debug(f"Killed ChromeDriver processes (exit code: {result.returncode})")
            else:
                # Windows
                result = subprocess.run(
                    ["taskkill", "/f", "/im", "chromedriver.exe"], 
                    capture_output=True, 
                    timeout=10
                )
                logger.debug(f"Killed ChromeDriver processes (exit code: {result.returncode})")
        except Exception as e:
            logger.warning(f"Failed to kill ChromeDriver processes: {e}")
    
    def cleanup_old_drivers(self):
        """Remove old/unused ChromeDriver files."""
        try:
            data_path = pathlib.Path(self.data_path)
            for item in data_path.glob("*chromedriver*"):
                if item != pathlib.Path(self.executable_path):
                    item.unlink()
                    logger.debug(f"Cleaned up old driver: {item}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old drivers: {e}")


# Convenience function for easy usage
def get_patched_chromedriver(version_main: Optional[int] = None, force: bool = False) -> str:
    """
    Get a patched ChromeDriver executable path.
    
    Args:
        version_main: Specific Chrome major version, None = latest
        force: Force re-download and re-patch
        
    Returns:
        str: Path to patched ChromeDriver executable
    """
    patcher = ChromeDriverPatcher(version_main=version_main, force=force)
    return patcher.get_patched_driver()
```

### 2. Update `my_stealth/driver_factory.py`

Add patcher integration to your existing driver factory:

```python
# Add this import at the top
from .patcher import get_patched_chromedriver

# Update the driver service creation section
def create_stealth_driver(...):
    # ... existing code ...
    
    # Driver service - use patched ChromeDriver
    if driver_path:
        service = Service(executable_path=driver_path)
    else:
        # Get patched ChromeDriver instead of regular one
        patched_driver_path = get_patched_chromedriver(
            version_main=None,  # Auto-detect
            force=False  # Use cached if available
        )
        service = Service(patched_driver_path)
        log.info(f"Using patched ChromeDriver: {patched_driver_path}")
    
    # ... rest of existing code ...
```

### 3. Update `my_stealth/__init__.py`

Add patcher exports:

```python
# Add these imports
from .patcher import get_patched_chromedriver, ChromeDriverPatcher

# Add to __all__
__all__ = [
    'Chrome', 
    'ChromeOptions', 
    'TARGET_VERSION', 
    'create_driver',
    'get_patched_chromedriver',  # 🆕 NEW
    'ChromeDriverPatcher',       # 🆕 NEW
    '__version__'
]

# UC compatibility function
def install(executable_path: Optional[str] = None):
    """
    UC-compatible install function.
    Downloads and patches ChromeDriver.
    """
    if executable_path:
        # Patch existing driver
        patcher = ChromeDriverPatcher()
        if not patcher.is_binary_patched(executable_path):
            logger.info(f"Patching existing ChromeDriver: {executable_path}")
            # Would need to implement in-place patching
        return executable_path
    else:
        # Download and patch new driver
        return get_patched_chromedriver()
```

## TESTING THE IMPLEMENTATION

### 1. Test Basic Patching
```python
from my_stealth.patcher import get_patched_chromedriver

# Test patching
driver_path = get_patched_chromedriver()
print(f"Patched driver at: {driver_path}")
```

### 2. Test CDC Variable Absence
```python
import my_stealth as uc

driver = uc.Chrome()
driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")

# Check for CDC variables
cdc_vars = driver.execute_script("""
    return Object.keys(window).filter(key => key.startsWith('cdc_'));
""")

print(f"CDC variables found: {cdc_vars}")  # Should be empty: []

# Check document properties  
doc_cdc = driver.execute_script("""
    return Object.keys(document).filter(key => key.startsWith('$cdc_'));
""")

print(f"Document CDC properties: {doc_cdc}")  # Should be empty: []

driver.quit()
```

### 3. Test Against Detection Sites
```python
import my_stealth as uc

driver = uc.Chrome()
driver.get("https://bot.sannysoft.com/")
# Check if CDC detection test passes

driver.get("https://nowsecure.nl/")
# Check if Cloudflare bypass works

driver.quit()
```

## ERROR HANDLING & EDGE CASES

### Common Issues:
1. **Permission Errors**: Handle file locks from running ChromeDriver
2. **Version Mismatches**: Graceful fallback to compatible versions  
3. **Network Issues**: Retry downloads with backoff
4. **Antivirus Interference**: Log warnings about false positives
5. **Platform Differences**: Handle path separators and permissions

### Logging Strategy:
- **DEBUG**: Detailed patching operations
- **INFO**: High-level operations and success
- **WARNING**: Non-fatal issues
- **ERROR**: Patch failures requiring attention

## SECURITY CONSIDERATIONS

1. **File Integrity**: Verify downloads with checksums if available
2. **Temp File Cleanup**: Always clean up downloaded files
3. **Permissions**: Set appropriate executable permissions
4. **Path Validation**: Validate all file paths to prevent traversal

## SUCCESS CRITERIA

✅ **ChromeDriver starts normally** with patched binary  
✅ **No CDC variables** in window or document  
✅ **Bot detection sites** don't detect automation  
✅ **Cross-platform compatibility** (Windows/Linux/macOS)  
✅ **Version management** works for old and new ChromeDriver APIs  
✅ **Error handling** gracefully handles common issues  

## MAINTENANCE

- **Monitor UC updates** for new patching techniques
- **Test against detection sites** regularly
- **Update for new ChromeDriver versions** as needed
- **Handle API changes** in ChromeDriver download URLs

---

**Note**: This implementation follows UC's proven approach while being tailored for the my_stealth architecture. The binary patching prevents CDC injection at the source, making it much harder to detect than JavaScript-only solutions.