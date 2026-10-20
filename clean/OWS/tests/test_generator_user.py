"""
Tests for generator.py — verifies output structure, type, and guarantees.
"""

from OWS.src.generator_user import UserProfile, generate_user
from OWS.src.user_data import DEVICES

# ===== STRUCTURAL =====


def test_returns_dict():
    """Generator must return UserProfile."""
    assert isinstance(generate_user(), UserProfile)


# ===== GUARANTEES =====


def test_languages_unique():
    user = generate_user().model_dump()
    assert len(user["languages"]) == len(set(user["languages"]))


def test_local_hour_in_range():
    assert 0 <= generate_user().model_dump()["local_hour"] <= 23


# ===== CONSISTENCY =====
# These seem flaky


def test_speaker_has_no_ad_size():
    """Generate many users; any speaker should have None ad_size."""
    for _ in range(100):
        user = generate_user().model_dump()
        if user["device"] == "speaker":
            assert user["ad_size"] is None


def test_ad_size_matches_device():
    for _ in range(100):
        user = generate_user().model_dump()
        assert user["ad_size"] in DEVICES[user["device"]]["ad_sizes"]


def test_channel_matches_device():
    for _ in range(100):
        user = generate_user().model_dump()
        assert user["channel"] in DEVICES[user["device"]]["channels"]


# ===== DISTRIBUTION =====


def test_generates_multiple_devices():
    devices = {generate_user().model_dump()["device"] for _ in range(1000)}
    assert len(devices) > 1  # Should generate variety
