
"""
Tests for user_data.py — verifies data integrity.
"""

from OWS.src.user_data import (
        CATEGORIES,
        COUNTRIES_LANGUAGES,
        DEVICES,
        DEVICE_WEIGHTS
)

# Validate foundational data instances lengths
def test_categories_not_empty():
    """CATEGORIES must contain at least one item."""
    assert len(CATEGORIES) > 0, "CATEGORIES is empty"

def test_countries_languages_not_empty():
    """COUNTRIES_LANGUAGES must contain at least one item."""
    assert len(COUNTRIES_LANGUAGES) > 0, "COUNTRIES_LANGUAGES is empty"

def test_devices_not_empty():
    """DEVICES must contain at least one item."""
    assert len(DEVICES) > 0, "DEVICES is empty"

def test_device_weights_length_match():
    """DEVICES and DEVICES_WEIGHTS must have same lengths."""
    assert len(DEVICE_WEIGHTS) == len(DEVICES), (
        "DEVICES and DEVICE_WEIGHTS length mismatch: "
        f"{len(DEVICE_WEIGHTS)} weights for {len(DEVICES)} devices"
    ) 

# Validate languages per country
def test_country_languages_not_empty():
    """Country must have at least one language."""
    for country, langs in COUNTRIES_LANGUAGES.items():
        assert len(langs) > 0, f"{country} has no languages"

def test_country_languages_duplicates():
    """Country must have unique languages."""
    for country, langs in COUNTRIES_LANGUAGES.items():
        assert len(langs) == len(set(langs)), f"{country} has duplicate languages"

# Validate devices
def test_device_channel_not_empty():
    """Device must have channels."""
    for device, data in DEVICES.items():
        channels = data["channels"]
        assert len(channels) > 0, f"{device} has no channels"

def test_device_channel_duplicates():
    """Device must have unique channels."""
    for device, data in DEVICES.items():
        channels = data["channels"]
        assert len(channels) == len(set(channels)), f"{device} has duplicate channels"

def test_device_ad_sizes_not_empty():
    """Device must provide ad sizes. Speaker device is allowed to have None size."""
    for device, data in DEVICES.items():
        sizes = data["ad_sizes"]
        assert len(sizes) > 0, f"{device} has no ad_sizes"

def test_device_ad_sizes_duplicates():
    """Device must have unique sizes."""
    for device, data in DEVICES.items():
        sizes = [tuple(s) for s in data["ad_sizes"] if s is not None]
        assert len(sizes) == len(set(sizes)), f"{device} has duplicate ad sizes"

def test_speaker_has_only_none_ad_size():
    """Speaker must only have 'None' size. 
    Speaker only plays audio ads, so it has no visual ad size."""
    assert DEVICES["speaker"]["ad_sizes"] == [None], (
        f"Speaker should only have None as ad size, "
        f"got {DEVICES['speaker']['ad_sizes']}"
    )
