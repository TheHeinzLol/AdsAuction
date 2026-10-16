"""
Tests for publisher data. Verifies data correctness.
"""
from OWS.src.publisher_data import PUBLISHERS
def test_publisher_data_all_keys_present():
    for publisher in PUBLISHERS:
        assert "publisher_id" in publisher.keys()
        assert "category" in publisher.keys()
        assert "floor_price" in publisher.keys()

def test_publisher_data_positive_floor_price():
    for publisher in PUBLISHERS:
        assert publisher["floor_price"] > 0
