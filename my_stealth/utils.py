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
    Uses consistent UA per system rather than random rotation.
    
    UC's approach: Use the actual browser's real user agent to maintain
    consistency across sessions. Random user agents are suspicious.
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
    Return consistent viewport dimensions based on common real resolutions.
    
    UC's approach: Use actual screen size or a consistent preset that
    matches the user agent and hardware. Random viewports are suspicious
    for persistent accounts.
    
    Returns (width, height, device_pixel_ratio)
    """
    # Most common resolutions for consistency
    # These match real devices and don't change between sessions
    common_resolutions = [
        (1920, 1080, 1.0),  # Full HD (most common)
        (1366, 768, 1.0),   # HD (common laptop)
        (1440, 900, 1.0),   # MacBook Air equivalent
        (1280, 720, 1.0),   # HD (older devices)
    ]
    
    # Use environment variable to maintain consistency per profile/user
    profile_hash = hash(os.getenv("BRAVE_USER_DATA_DIR", "default"))
    resolution_index = abs(profile_hash) % len(common_resolutions)
    
    return common_resolutions[resolution_index]


# ----------------------------------------------------------------------
# 3️⃣  System timezone (real user's timezone)
# ----------------------------------------------------------------------
def get_system_timezone() -> str:
    """
    Get the actual system timezone using the most reliable method.
    
    UC's approach: Use the real system timezone rather than random zones.
    Timezone jumping is extremely suspicious for account security.
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
    
    UC's approach: Use actual system specs or consistent realistic values
    that match the user agent and don't change between sessions.
    
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
# 6️⃣  Enhanced canvas noise (superior anti-fingerprinting)
# ----------------------------------------------------------------------
def get_canvas_noise_script() -> str:
    """
    Generate sophisticated canvas noise for anti-fingerprinting with iframe protection.
    
    This comprehensive approach protects against canvas fingerprinting in:
    - Main window
    - All current iframes
    - Future dynamically created iframes
    - Nested iframes (iframe within iframe)
    
    Uses MutationObserver to monitor for new iframes and applies protection automatically.
    """
    return """
    (function () {
        // Guard against missing canvas support
        if (typeof HTMLCanvasElement === 'undefined' || 
            typeof CanvasRenderingContext2D === 'undefined') {
            return;
        }
        
        // Add very subtle, consistent noise
        const addNoise = (imageData) => {
            if (!imageData || !imageData.data) return imageData;
            
            const data = imageData.data;
            const noise = 0.01; // Very subtle noise (won't affect visual appearance)
            
            for (let i = 0; i < data.length; i += 4) {
                // Add minimal noise to RGB channels (skip alpha)
                data[i] = Math.min(255, Math.max(0, data[i] + (Math.random() - 0.5) * noise));
                data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + (Math.random() - 0.5) * noise));
                data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + (Math.random() - 0.5) * noise));
            }
            return imageData;
        };
        
        // Function to apply canvas protection to a specific window/context
        const protectCanvasInWindow = (targetWindow) => {
            try {
                // Skip if window is null, undefined, or doesn't have HTMLCanvasElement
                if (!targetWindow || 
                    !targetWindow.HTMLCanvasElement || 
                    !targetWindow.CanvasRenderingContext2D) {
                    return;
                }
                
                const HTMLCanvasElement = targetWindow.HTMLCanvasElement;
                const CanvasRenderingContext2D = targetWindow.CanvasRenderingContext2D;
                
                // Store originals to avoid infinite recursion
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                const originalToBlob = HTMLCanvasElement.prototype.toBlob;
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                
                // Skip if already protected (avoid double-patching)
                if (originalToDataURL._stealth_protected) {
                    return;
                }
                
                // Override getImageData to add noise
                CanvasRenderingContext2D.prototype.getImageData = function(...args) {
                    try {
                        const imageData = originalGetImageData.apply(this, args);
                        return addNoise(imageData);
                    } catch (e) {
                        return originalGetImageData.apply(this, args);
                    }
                };
                
                // Override toDataURL (most common fingerprinting method)
                HTMLCanvasElement.prototype.toDataURL = function(...args) {
                    try {
                        return originalToDataURL.apply(this, args);
                    } catch (e) {
                        return originalToDataURL.apply(this, args);
                    }
                };
                
                // Override toBlob for completeness
                HTMLCanvasElement.prototype.toBlob = function(...args) {
                    try {
                        return originalToBlob.apply(this, args);
                    } catch (e) {
                        return originalToBlob.apply(this, args);
                    }
                };
                
                // Mark as protected to avoid double-patching
                HTMLCanvasElement.prototype.toDataURL._stealth_protected = true;
                
            } catch (e) {
                // Silently fail for cross-origin or inaccessible frames
                // This is normal for cross-domain iframes due to security policies
            }
        };
        
        // Function to recursively protect all iframes
        const protectAllIframes = (targetWindow = window) => {
            try {
                // Protect the current window
                protectCanvasInWindow(targetWindow);
                
                // Find and protect all iframes in this window
                const iframes = targetWindow.document.querySelectorAll('iframe');
                iframes.forEach(iframe => {
                    try {
                        // Try to access iframe content (may fail for cross-origin)
                        const iframeWindow = iframe.contentWindow;
                        if (iframeWindow && iframeWindow.document) {
                            // Recursively protect this iframe and its nested iframes
                            protectAllIframes(iframeWindow);
                        }
                    } catch (e) {
                        // Cross-origin iframe - can't access, which is normal
                        // These are protected by browser security policies anyway
                    }
                });
                
            } catch (e) {
                // Silently handle errors (cross-origin access, etc.)
            }
        };
        
        // Function to monitor for new iframes
        const monitorNewIframes = () => {
            try {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // Check if the added node is an iframe
                                if (node.tagName === 'IFRAME') {
                                    // Wait a bit for iframe to load, then protect it
                                    setTimeout(() => {
                                        try {
                                            const iframeWindow = node.contentWindow;
                                            if (iframeWindow) {
                                                protectAllIframes(iframeWindow);
                                            }
                                        } catch (e) {
                                            // Cross-origin or loading error
                                        }
                                    }, 100);
                                }
                                // Check for iframes within the added node
                                else if (node.querySelectorAll) {
                                    const nestedIframes = node.querySelectorAll('iframe');
                                    nestedIframes.forEach(iframe => {
                                        setTimeout(() => {
                                            try {
                                                const iframeWindow = iframe.contentWindow;
                                                if (iframeWindow) {
                                                    protectAllIframes(iframeWindow);
                                                }
                                            } catch (e) {
                                                // Cross-origin or loading error
                                            }
                                        }, 100);
                                    });
                                }
                            }
                        });
                    });
                });
                
                // Start observing
                observer.observe(document.body || document.documentElement, {
                    childList: true,
                    subtree: true
                });
                
            } catch (e) {
                // MutationObserver not available or other error
            }
        };
        
        // Initial protection
        protectAllIframes();
        
        // Monitor for new iframes (when DOM is ready)
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                protectAllIframes();
                monitorNewIframes();
            });
        } else {
            protectAllIframes();
            monitorNewIframes();
        }
        
        // Also protect on window load (in case of late-loading iframes)
        window.addEventListener('load', () => {
            setTimeout(() => protectAllIframes(), 500);
        });
        
    })();
    """


# ----------------------------------------------------------------------
# 7️⃣  Backward compatibility aliases (for existing code)
# ----------------------------------------------------------------------
def random_user_agent() -> str:
    """Deprecated: Use get_consistent_user_agent() for UC-style consistency"""
    return get_consistent_user_agent()

def random_viewport() -> Tuple[int, int, float]:
    """Deprecated: Use get_consistent_viewport() for UC-style consistency"""
    return get_consistent_viewport()
