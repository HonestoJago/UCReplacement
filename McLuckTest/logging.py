"""
Centralized logging helpers for McLuck test utilities.

Provides:
  - get_or_create_logger(name, file_basename): idempotent console+file logger
  - log_state_change(logger, source, snapshot): standardized JSON state logging

All logs are written to `McLuckTest/logs/` relative to this module, and to the
console. File handler uses UTF-8 and INFO level by default.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any


def get_or_create_logger(name: str, file_basename: str = "app.log") -> logging.Logger:
    """
    Create or return a configured logger that logs to console and to
    `McLuckTest/logs/<file_basename>`.

    Idempotent: repeated calls won't duplicate handlers.
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_configured", False):  # type: ignore[attr-defined]
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(sh)

    # File handler
    logs_dir = Path(__file__).resolve().parent / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh_path = logs_dir / file_basename
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            fh = logging.FileHandler(fh_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(fh)
    except Exception:
        # If file cannot be created, proceed with console-only logging
        pass

    setattr(logger, "_configured", True)  # type: ignore[attr-defined]
    return logger


def log_state_change(logger: logging.Logger, *, source: str, snapshot: Dict[str, Any]) -> None:
    """
    Log a standardized JSON line representing the new state.
    """
    try:
        payload = json.dumps(snapshot, ensure_ascii=False)
    except Exception:
        payload = str(snapshot)
    logger.info("state_change source=%s state=%s", source, payload)


