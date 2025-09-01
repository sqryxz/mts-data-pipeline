"""
Cross-process alert deduplication utility.

This module provides a simple file-backed deduper so that multiple
processes (e.g., enhanced scheduler and correlation analysis) can
coordinate and prevent duplicate Discord alerts from being posted.

Design goals:
- Minimal dependencies, works without Redis
- Atomic updates using rename for crash safety
- TTL-based eviction to avoid unbounded file growth

Usage:
    deduper = AlertDeduper("data/alert_dedupe_state.json", ttl_seconds=3600)
    if deduper.should_send(unique_key):
        # send alert
        deduper.mark_sent(unique_key)
"""

from __future__ import annotations

import json
import os
import time
import tempfile
from pathlib import Path
from typing import Dict


class AlertDeduper:
    def __init__(self, state_file: str = "data/alert_dedupe_state.json", ttl_seconds: int = 3600) -> None:
        self.state_path = Path(state_file)
        self.ttl_seconds = ttl_seconds
        self._state: Dict[str, float] = {}
        self._ensure_parent_dir()
        self._load_state()

    def _ensure_parent_dir(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> None:
        try:
            if self.state_path.exists():
                with self.state_path.open("r", encoding="utf-8") as f:
                    self._state = json.load(f)
            else:
                self._state = {}
        except Exception:
            # Corrupt state; reset
            self._state = {}

    def _persist_state(self) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="dedupe_", dir=str(self.state_path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                json.dump(self._state, tmp_file)
            os.replace(tmp_path, self.state_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _sweep_expired(self) -> None:
        now_ts = time.time()
        expired_keys = [k for k, ts in self._state.items() if now_ts - ts > self.ttl_seconds]
        if expired_keys:
            for key in expired_keys:
                self._state.pop(key, None)
            self._persist_state()

    def make_key(self, *, source: str, strategy: str | None, symbol: str, signal_type: str | None, price: float | None) -> str:
        parts = [
            f"src={source}",
            f"strategy={strategy or '-'}",
            f"symbol={symbol.lower()}",
            f"type={signal_type or '-'}",
            f"price={price:.2f}" if price is not None else "price=-",
        ]
        return "|".join(parts)

    def should_send(self, unique_key: str) -> bool:
        self._sweep_expired()
        ts = self._state.get(unique_key)
        if ts is None:
            return True
        # If within TTL, do not resend
        age_seconds = time.time() - ts
        if age_seconds < self.ttl_seconds:
            return False
        # If expired, allow resending
        return True

    def mark_sent(self, unique_key: str) -> None:
        self._state[unique_key] = time.time()
        self._persist_state()


