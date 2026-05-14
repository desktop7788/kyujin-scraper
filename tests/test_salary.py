# tests/test_salary.py
from helloworks_scraper.salary import parse_salary


def test_hourly_simple():
    assert parse_salary("時給1200円") == {"salary_type": "時給", "wage_numbers": 1200}


def test_hourly_range_takes_lower_bound():
    assert parse_salary("時給1,200円〜1,500円") == {"salary_type": "時給", "wage_numbers": 1200}


def test_hourly_with_tilde_fullwidth():
    assert parse_salary("時給1,200円～1,500円") == {"salary_type": "時給", "wage_numbers": 1200}


def test_monthly_man():
    assert parse_salary("月給25万円") == {"salary_type": "月給", "wage_numbers": 250000}


def test_daily():
    assert parse_salary("日給10,000円") == {"salary_type": "日給", "wage_numbers": 10000}


def test_none_input():
    assert parse_salary(None) is None


def test_empty_string():
    assert parse_salary("") is None


def test_no_yen_symbol():
    assert parse_salary("時給1200") is None
