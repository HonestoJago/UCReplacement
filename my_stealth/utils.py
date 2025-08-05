# utils.py
"""
Utility helpers used by the stealth driver.
All functions are deliberately tiny – you can extend them as you wish.
"""

import random
from typing import Tuple

# ----------------------------------------------------------------------
# 1️⃣  Randomised User‑Agent pool
# ----------------------------------------------------------------------
_UA_POOL = [
    # Chrome 129 on Windows 10/11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36",

    # Brave (same Chrome version)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36 Brave/129",
]


def random_user_agent() -> str:
    """
    Return a random UA string from the small pool above.
    Feel free to expand the list with more recent UAs.
    """
    return random.choice(_UA_POOL)


# ----------------------------------------------------------------------
# 2️⃣  Random viewport size + device‑pixel‑ratio
# ----------------------------------------------------------------------
def random_viewport(min_w: int = 1024,
                    max_w: int = 1920,
                    min_h: int = 720,
                    max_h: int = 1080) -> Tuple[int, int, float]:
    """
    Pick a random width / height and a plausible DPR (1, 1.5 or 2).
    Returns (width, height, dpr).
    """
    width = random.randint(min_w, max_w)
    height = random.randint(min_h, max_h)
    dpr = random.choice([1, 1.5, 2])
    return width, height, dpr
