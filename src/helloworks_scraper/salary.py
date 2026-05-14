# src/helloworks_scraper/salary.py
"""給与文字列を salary_type と wage_numbers に分解する。"""

import re


def parse_salary(text: str | None) -> dict | None:
    """例: '時給1,200円〜1,500円' → {'salary_type': '時給', 'wage_numbers': 1200}.

    Returns None if the text cannot be parsed.
    """
    if not text:
        return None

    match = re.match(r"([^\d]+?)([\d,]+)(万)?円", text)
    if not match:
        return None

    salary_type = match.group(1).strip()
    digits = match.group(2).replace(",", "")
    is_man = match.group(3) is not None

    try:
        n = int(digits)
    except ValueError:
        return None

    if is_man:
        n *= 10000

    return {"salary_type": salary_type, "wage_numbers": n}
