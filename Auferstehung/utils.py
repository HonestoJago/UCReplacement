# utils.py
"""
Utility helpers used by the stealth driver.
Follows UC's consistency-based approach: hide automation signatures,
maintain consistent fingerprints to act like a real persistent user.
"""

import os
import time
import platform
from typing import Tuple

# ----------------------------------------------------------------------
# 1️⃣  Consistent User Agent (matches actual browser)
# ----------------------------------------------------------------------
def get_consistent_user_agent() -> str:
    """
    Return a realistic user agent that matches the system and browser.
    Always returns the same UA for this system to maintain consistency.
    
    UC's approach: Use the actual browser's real user agent to maintain
    consistency across sessions. Changing user agents is suspicious.
    """
    # Detect actual system info for consistent UA
    system = platform.system()
    architecture = platform.architecture()[0]
    
    if system == "Windows":
        if "64" in architecture:
            # Most common Windows Chrome UA (matches real browser)
            return ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/139.0.0.0 Safari/537.36")
        else:
            return ("Mozilla/5.0 (Windows NT 10.0; WOW64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/139.0.0.0 Safari/537.36")
    elif system == "Darwin":  # macOS
        return ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/139.0.0.0 Safari/537.36")
    else:  # Linux
        return ("Mozilla/5.0 (X11; Linux x86_64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/139.0.0.0 Safari/537.36")


# ----------------------------------------------------------------------
# 2️⃣  Consistent viewport (real screen size or sensible preset)
# ----------------------------------------------------------------------
def get_consistent_viewport() -> Tuple[int, int, float]:
    """
    Return consistent viewport dimensions for this profile.
    
    UC's approach: Same profile = same viewport = same "device" fingerprint.
    Maintains account safety by being the exact same "device" every session.
    
    Returns (width, height, device_pixel_ratio)
    """
    # Most common resolutions that match real devices
    # These create believable, consistent fingerprints
    common_resolutions = [
        (1920, 1080, 1.0),  # Full HD (most common)
        (1366, 768, 1.0),   # HD (common laptop)
        (1440, 900, 1.0),   # MacBook Air equivalent
        (1280, 720, 1.0),   # HD (older devices)
    ]
    
    # Use profile path to ensure same resolution for same profile
    # This creates a stable "device" fingerprint per profile
    profile_path = os.getenv("BRAVE_USER_DATA_DIR", "default")
    profile_hash = hash(profile_path)
    resolution_index = abs(profile_hash) % len(common_resolutions)
    
    return common_resolutions[resolution_index]


# ----------------------------------------------------------------------
# 3️⃣  System timezone (real user's timezone)
# ----------------------------------------------------------------------
def get_system_timezone() -> str:
    """
    Get the actual system timezone using the most reliable method.
    
    UC's approach: Use the real system timezone to maintain consistency.
    Timezone changes are extremely suspicious for account security.
    """
    try:
        # Enhanced timezone detection (inspired by Claude's approach)
        if platform.system() == "Windows":
            # Windows: Use tzutil command for accurate timezone
            import subprocess
            result = subprocess.run(
                ["tzutil", "/g"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
                
        else:
            # Unix-like systems: Check timezone file
            if os.path.exists('/etc/timezone'):
                with open('/etc/timezone', 'r') as f:
                    return f.read().strip()
        
        # Fallback: Use time module
        if hasattr(time, 'tzname') and time.tzname[0]:
            return time.tzname[time.daylight] if time.daylight else time.tzname[0]
        else:
            # Final fallback to UTC offset
            offset = time.timezone
            hours = abs(offset) // 3600
            return f"UTC{'-' if offset > 0 else '+'}{hours:02d}:00"
            
    except Exception as e:
        # Safe fallback
        return "UTC"


def get_system_timezone_offset() -> int:
    """
    Get actual system timezone offset in minutes.
    Handles daylight saving time properly.
    """
    try:
        # Get local timezone offset in seconds, convert to minutes
        # Use altzone if daylight saving is active
        offset_seconds = time.timezone if time.daylight == 0 else time.altzone
        return -offset_seconds // 60  # Convert to minutes, negate for correct sign
    except Exception:
        return 0  # UTC fallback


# ----------------------------------------------------------------------
# 4️⃣  Consistent hardware specs (match system or realistic preset)
# ----------------------------------------------------------------------
def get_consistent_hardware() -> Tuple[int, int]:
    """
    Return consistent hardware specs (CPU cores, RAM GB).
    
    UC's approach: Use actual system specs to create believable,
    consistent fingerprints that match the real system.
    
    Returns (cpu_cores, memory_gb)
    """
    try:
        # Try to get actual system specs for maximum consistency
        cpu_cores = os.cpu_count() or 4
        # Cap at reasonable maximum (16 cores max for realism)
        cpu_cores = min(cpu_cores, 16)
        
        # Memory allocation based on CPU cores (more realistic)
        # This creates consistent, believable hardware combinations
        if cpu_cores <= 4:
            memory_gb = 8
        elif cpu_cores <= 8:
            memory_gb = 16
        else:
            memory_gb = 32
        
        return cpu_cores, memory_gb
        
    except:
        # Safe fallback for common system
        return 4, 8


# ----------------------------------------------------------------------
# 5️⃣  Profile-based fingerprint management
# ----------------------------------------------------------------------
def get_profile_fingerprint(profile_id: str = None) -> dict:
    """
    Generate a comprehensive, consistent fingerprint for a profile.
    Same profile = same fingerprint across sessions.
    
    This centralizes all fingerprint components for consistency.
    """
    if not profile_id:
        profile_id = os.getenv("BRAVE_USER_DATA_DIR", "default")
    
    width, height, dpr = get_consistent_viewport()
    cores, memory = get_consistent_hardware()
    timezone = get_system_timezone()
    timezone_offset = get_system_timezone_offset()
    
    return {
        'viewport': {'width': width, 'height': height, 'dpr': dpr},
        'hardware': {'cores': cores, 'memory': memory},
        'timezone': {'name': timezone, 'offset': timezone_offset},
        'user_agent': get_consistent_user_agent(),
        'profile_id': profile_id
    }


# ----------------------------------------------------------------------
# 6️⃣  UC's Canvas Approach: Do Nothing
# ----------------------------------------------------------------------
# UC Philosophy: Let canvas render naturally using real system hardware.
# Consistent fingerprint = consistent "device" = account safety.
# Same profile always shows the same canvas fingerprint (same "device").
# 
# Canvas fingerprint protection follows UC's philosophy:
# 1. UC doesn't add canvas noise - it maintains fingerprint consistency
# 2. Consistent fingerprints appear as the same "device" every session
# 3. Account safety requires being the same "device", not a different one


# ----------------------------------------------------------------------
# 7️⃣  Backward compatibility aliases (for existing code)
# ----------------------------------------------------------------------
def random_user_agent() -> str:
    """Deprecated: Use get_consistent_user_agent() for UC-style consistency.
    
    Note: This function never returned random values - it maintains consistency
    like UC. The name is misleading and kept only for backward compatibility.
    """
    return get_consistent_user_agent()

def random_viewport() -> Tuple[int, int, float]:
    """Deprecated: Use get_consistent_viewport() for UC-style consistency.
    
    Note: This function never returned random values - it maintains consistency
    per profile like UC. The name is misleading and kept only for compatibility.
    """
    return get_consistent_viewport()
