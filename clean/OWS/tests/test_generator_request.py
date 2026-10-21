
from unittest.mock import MagicMock, patch

import aiohttp
from aioresponses import aioresponses
from OWS.src.generator_request import make_ad_request
from OWS.src.user_pool import populate_user_pool

mock_url = "http://localhost:8000"

ad_response = {
    "auction_id_ssp": "852cda8",
    "ad_url": "mock ad url",
    "ttl": 5,
}

# ===== make_ad_request =====


async def test_make_ad_request_returns_parsed_json_on_200():
    """On 200, returns parsed JSON body."""
    populate_user_pool(1)
    with (
            aioresponses() as mocked,
            patch("OWS.src.generator_request.schedule", return_value=MagicMock()),
    ):
        mocked.post(mock_url, status=200, payload=ad_response)
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)
    assert result["ad_url"] == "mock ad url", f"Result: {result}"
    assert result["auction_id_ssp"] == "852cda8"
    assert isinstance(result["ttl"], int)


async def test_make_ad_request_returns_text_on_non_200():
    """On non-200, still returns parsed JSON body."""
    with aioresponses() as mocked:
        mocked.post(mock_url, status=500, payload={"error": "internal server error"})
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)

    assert isinstance(result, str)


async def test_make_ad_request_returns_dict_on_exception():
    """On exception, returns a dict with error text instead of rising."""
    with aioresponses() as mocked:
        mocked.post(
            mock_url,
            exception=TimeoutError(),
        )
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)

    assert "error" in result
    assert result["error_type"] == "TimeoutError"
