"""
Game state tracking for McLuck BGaming titles.

This module defines a small, focused class `GameState` that:
  - Initializes from the parsed JSON of the first "init" API response
  - Updates itself from subsequent API responses
  - Tracks per-session counters we care about (amount wagered, wash progress)
  - Computes RTP and Profit/Loss from tracked values

Golden rule: Simple, surgical, well-documented. No changes to unrelated code.

Usage example (after the init response is captured in `driver._last_init_response`):
    from McLuckTest.game_state import GameState
    gs = GameState.from_init_response(driver._last_init_response['raw'])
    # Record a bonus buy of 7770 GC
    gs.record_bonus_buy(7770)
    # Later, after a spin/freespin response
    gs.update_from_response(parsed_response)
    print(gs.snapshot())
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from McLuckTest.logging import get_or_create_logger, log_state_change


load_dotenv()


def _read_int_env(name: str, default: int = 0) -> int:
    """
    Read integer environment variables safely.
    Accepts plain integers; trims whitespace; empty/invalid → default.
    """
    try:
        raw = os.getenv(name, "").strip()
        if raw == "":
            return default
        return int(float(raw))  # Allow "7770" or "7770.0"
    except Exception:
        return default


@dataclass
class GameState:
    """
    Track and compute top-level game state derived from BGaming API responses.

    Fields that mirror the BGaming responses (kept in sync on update):
      - available_actions: From response.flow.available_actions
      - round_id:          From response.flow.round_id
      - balance_wallet:    From response.balance.wallet  (site balance, e.g., GC)
      - balance_game:      From response.balance.game    (amount returned this session)
      - currency:          From response.options.currency.code (e.g., "GC")

    Session counters we track locally:
      - amount_wagered:    Sum of wagers we place (bonus buys only)
      - remaining_wash:    Starts at env `MCLUCK_WASH_AMOUNT_GC`, reduced by every
                           bonus buy amount regardless of outcome

    Derived metrics:
      - rtp:               amount_won / amount_wagered (None if not applicable)
      - profit_loss:       amount_won - amount_wagered
    """

    # From responses
    available_actions: List[str] = field(default_factory=list)
    round_id: Optional[int] = None
    balance_wallet: int = 0
    balance_game: int = 0
    currency: str = "GC"

    # Local counters
    amount_wagered: int = 0
    remaining_wash: int = 0

    # Internal bookkeeping (optional, for consumers)
    last_raw_response: Optional[Dict[str, Any]] = None
    _last_snapshot: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _logger_name: str = field(default="mcluck.game_state", init=False, repr=False)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_init_response(cls, init_response: Dict[str, Any], *,
                           wash_env_var: str = "MCLUCK_WASH_AMOUNT_GC") -> "GameState":
        """
        Build a `GameState` from the parsed JSON body of the first init response.
        """
        options = init_response.get("options", {}) if isinstance(init_response, dict) else {}
        flow = init_response.get("flow", {}) if isinstance(init_response, dict) else {}
        balance = init_response.get("balance", {}) if isinstance(init_response, dict) else {}

        gs = cls(
            available_actions=list(flow.get("available_actions", []) or []),
            round_id=flow.get("round_id"),
            balance_wallet=int(balance.get("wallet", 0) or 0),
            balance_game=int(balance.get("game", 0) or 0),
            currency=(options.get("currency", {}) or {}).get("code", "GC"),
            remaining_wash=_read_int_env(wash_env_var, default=0),
            last_raw_response=init_response,
        )
        # Log initial state
        gs._log_if_changed(source="init")
        return gs

    # ------------------------------------------------------------------
    # Update logic – feed subsequent API responses to keep fields current
    # ------------------------------------------------------------------
    def update_from_response(self, response: Dict[str, Any]) -> None:
        """
        Update fields from any subsequent BGaming API response (e.g., spin).
        We only write fields that appear in the response to avoid regressions.
        """
        if not isinstance(response, dict):
            return

        self.last_raw_response = response

        flow = response.get("flow")
        if isinstance(flow, dict):
            if "available_actions" in flow:
                try:
                    self.available_actions = list(flow.get("available_actions") or [])
                except Exception:
                    pass
            if "round_id" in flow:
                try:
                    self.round_id = flow.get("round_id")
                except Exception:
                    pass

        balance = response.get("balance")
        if isinstance(balance, dict):
            if "wallet" in balance:
                try:
                    self.balance_wallet = int(balance.get("wallet") or 0)
                except Exception:
                    pass
            if "game" in balance:
                try:
                    self.balance_game = int(balance.get("game") or 0)
                except Exception:
                    pass

        options = response.get("options")
        if isinstance(options, dict):
            cur = options.get("currency")
            if isinstance(cur, dict) and "code" in cur:
                try:
                    self.currency = str(cur.get("code") or self.currency)
                except Exception:
                    pass

        # After applying response changes, log if anything changed
        self._log_if_changed(source="update_response")

    # ------------------------------------------------------------------
    # Session bookkeeping
    # ------------------------------------------------------------------
    def record_bonus_buy(self, amount: int) -> None:
        """
        Record a bonus buy. This increases `amount_wagered` and reduces
        `remaining_wash` by the same amount regardless of win/loss outcome.
        """
        try:
            amt = int(amount)
        except Exception:
            return
        self.amount_wagered += amt
        self.remaining_wash -= amt
        self._log_if_changed(source="bonus_buy")

    def record_manual_win(self, amount: int) -> None:
        """
        Optional helper: manually increment the tracked session win amount.
        Typically not needed because `balance_game` is read from responses.
        """
        try:
            amt = int(amount)
        except Exception:
            return
        self.balance_game += amt
        self._log_if_changed(source="manual_win")

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------
    @property
    def amount_won(self) -> int:
        """Alias to the session return tracked by the API (`balance_game`)."""
        return self.balance_game

    @property
    def profit_loss(self) -> int:
        """Return profit/loss = amount won - amount wagered."""
        return self.amount_won - self.amount_wagered

    @property
    def rtp(self) -> Optional[float]:
        """
        Return-to-Player ratio for the session: amount_won / amount_wagered.
        Returns None when undefined (no wagers yet).
        """
        if self.amount_wagered <= 0:
            return None
        return float(self.amount_won) / float(self.amount_wagered)

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """
        Return a compact dictionary suitable for logging or persistence.
        """
        return {
            "available_actions": list(self.available_actions),
            "round_id": self.round_id,
            "balance_wallet": self.balance_wallet,
            "balance_game": self.balance_game,
            "currency": self.currency,
            "amount_wagered": self.amount_wagered,
            "amount_won": self.amount_won,
            "profit_loss": self.profit_loss,
            "rtp": self.rtp,
            "remaining_wash": self.remaining_wash,
        }

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def _get_logger(self) -> logging.Logger:
        """Use centralized logger config under McLuckTest/logging.py."""
        return get_or_create_logger(self._logger_name, file_basename="game_state.log")

    def _log_if_changed(self, *, source: str) -> None:
        """
        Compare current snapshot to the last logged snapshot. If different,
        log the full state (JSON) to both console and file.
        """
        snap = self.snapshot()
        if self._last_snapshot == snap:
            return

        logger = self._get_logger()
        log_state_change(logger, source=source, snapshot=snap)
        self._last_snapshot = snap


