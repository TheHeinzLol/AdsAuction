
"""
Tests for generator.py — verifies output structure, type, and guarantees.
"""

from OWS.generate_user import main
from OWS.user_data import DEVICES, CATEGORIES, COUNTRIES_LANGUAGES


# ===== STRUCTURAL =====

def test_returns_dict():
    """main must return dict."""
    assert isinstance(main(), dict)

def test_has_exactly_expected_fields():
    """Output must contain all of the expected fields and only those."""
    user = main()
    expected = {
            "device",
            "channel",
            "ad_size",
            "region",
            "languages",
            "local_hour",
            "categories"
    }
    assert set(user.keys()) == expected, (
        f"Expected fields {expected}, got {set(user.keys())}"
    )


# ===== TYPE =====

def test_device_is_string():
    assert isinstance(main()["device"], str)

def test_channel_is_string():
    assert isinstance(main()["channel"], str)

def test_ad_size_is_tuple_or_none():
    ad_size = main()["ad_size"]
    assert ad_size is None or isinstance(ad_size, tuple)

def test_region_is_string():
    assert isinstance(main()["region"], str)

def test_languages_is_list():
    assert isinstance(main()["languages"], list)

def test_categories_is_list():
    assert isinstance(main()["categories"], list)

def test_local_hour_is_int():
    assert isinstance(main()["local_hour"], int)


# ===== GUARANTEES =====

def test_languages_not_empty():
    assert len(main()["languages"]) > 0

def test_languages_unique():
    user = main()
    assert len(user["languages"]) == len(set(user["languages"]))

def test_categories_not_empty():
    assert len(main()["categories"]) > 0

def test_categories_unique():
    user = main()
    assert len(user["categories"]) == len(set(user["categories"]))

def test_local_hour_in_range():
    assert 0 <= main()["local_hour"] <= 23


# ===== CONSISTENCY =====

def test_speaker_has_no_ad_size():
    """Generate many users; any speaker should have None ad_size."""
    for _ in range(100):
        user = main()
        if user["device"] == "speaker":
            assert user["ad_size"] is None

def test_ad_size_matches_device():
    for _ in range(100):
        user = main()
        assert user["ad_size"] in DEVICES[user["device"]]["ad_sizes"]

def test_channel_matches_device():
    for _ in range(100):
        user = main()
        assert user["channel"] in DEVICES[user["device"]]["channels"]


# ===== DISTRIBUTION =====

def test_generates_multiple_devices():
    devices = {main()["device"] for _ in range(1000)}
    assert len(devices) > 1  # Should generate variety
