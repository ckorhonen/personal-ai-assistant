"""Utility functions for classifying email importance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

VIP_PATH = Path("data/vip_addresses.json")


def _load_vip_addresses() -> set[str]:
    """Load VIP email addresses from :data:`VIP_PATH`."""
    if VIP_PATH.exists():
        with open(VIP_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


VIP_ADDRESSES = _load_vip_addresses()


def classify_importance(msg: Dict[str, Any]) -> str:
    """Classify a Gmail message by importance level.

    Parameters
    ----------
    msg : dict
        Gmail API message resource containing ``labelIds`` and ``payload``.

    Returns
    -------
    str
        One of ``"vip"``, ``"promo"``, ``"newsletter"`` or ``"other"``.
    """

    headers = {
        h.get("name"): h.get("value")
        for h in msg.get("payload", {}).get("headers", [])
        if isinstance(h, dict)
    }
    from_addr = headers.get("From", "")
    labels = set(msg.get("labelIds", []))

    if from_addr in VIP_ADDRESSES or "\\Starred" in labels:
        return "vip"
    if "CATEGORY_PROMOTIONS" in labels:
        return "promo"
    if "List-Id" in headers:
        return "newsletter"
    return "other"
