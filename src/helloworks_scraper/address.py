# src/helloworks_scraper/address.py
"""住所文字列を正規化して pref / city / full address を取り出す。"""

from normalize_japanese_addresses import normalize


def _normalize_via_lib(text: str) -> dict | None:
    """Thin wrapper around the library for mocking in tests."""
    try:
        result = normalize(text)
    except Exception:
        return None
    if not result or not result.get("pref"):
        return None
    return result


def normalize_address(text: str | None) -> dict | None:
    """Return {'address', 'pref', 'city'} or None.

    pref と city が取れない住所は None。それ以外の場合 address は原文を保持。
    """
    if not text:
        return None

    text = text.strip()
    if not text:
        return None

    result = _normalize_via_lib(text)
    if not result:
        return None

    return {
        "address": text,
        "pref": result.get("pref") or "",
        "city": result.get("city") or "",
    }
