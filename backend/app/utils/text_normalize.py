"""Text normalization helpers."""

from __future__ import annotations

import re

_NAME_KEEP_PATTERN = re.compile(r"[^0-9a-zA-Z가-힣\s]")
_MULTI_SPACE_PATTERN = re.compile(r"\s+")


def normalize_place_name(name: str) -> str:
    """Normalize place name for duplicate/search matching.

    Args:
        name: Raw place name.

    Returns:
        Lower-cased normalized name with special characters removed.
    """
    lowered = name.lower()
    stripped = _NAME_KEEP_PATTERN.sub(" ", lowered)
    collapsed = _MULTI_SPACE_PATTERN.sub(" ", stripped)
    return collapsed.strip().replace(" ", "")


def normalize_phone(phone: str) -> str:
    """Normalize phone number to digits-only Korean local form.

    Args:
        phone: Raw phone string.

    Returns:
        Digits-only phone number.
    """
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("82"):
        digits = f"0{digits[2:]}"
    return digits
