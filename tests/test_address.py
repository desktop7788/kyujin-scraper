# tests/test_address.py
from helloworks_scraper.address import normalize_address


def test_basic_address(mocker):
    mock_normalize = mocker.patch("helloworks_scraper.address._normalize_via_lib")
    mock_normalize.return_value = {"pref": "東京都", "city": "千代田区", "town": "永田町", "addr": "1-1-1"}
    result = normalize_address("東京都千代田区永田町1-1-1")
    assert result == {
        "address": "東京都千代田区永田町1-1-1",
        "pref": "東京都",
        "city": "千代田区",
    }


def test_address_with_prefecture_omitted(mocker):
    mock_normalize = mocker.patch("helloworks_scraper.address._normalize_via_lib")
    mock_normalize.return_value = {"pref": "東京都", "city": "千代田区", "town": "永田町", "addr": ""}
    result = normalize_address("千代田区永田町")
    assert result["pref"] == "東京都"
    assert result["city"] == "千代田区"


def test_unparseable_returns_none(mocker):
    mocker.patch("helloworks_scraper.address._normalize_via_lib", return_value=None)
    assert normalize_address("foobar") is None


def test_none_input():
    assert normalize_address(None) is None


def test_empty_input():
    assert normalize_address("") is None
