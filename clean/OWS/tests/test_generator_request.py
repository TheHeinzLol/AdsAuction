from unittest.mock import MagicMock, patch

import aiohttp
from aioresponses import aioresponses

from OWS.src.generator_request import generate_request_data, make_ad_request
from OWS.src.user_pool import User, populate_user_pool
from shared.pydantic_models import AdRequestOWS, AdResponseSSP

mock_url = "http://localhost:8000"


# ===== generate_request_data =====


def test_generate_request_data_return_on_debug_false():
    user, request_data = generate_request_data()
    assert isinstance(user, User)
    assert isinstance(request_data, AdRequestOWS)


def test_generate_request_data_return_on_debug_true():
    request_data = generate_request_data(debug_mode=True)
    assert isinstance(request_data, AdRequestOWS)


# ===== make_ad_request =====


async def test_make_ad_request_returns_parsed_json_on_200(ad_response_ssp):
    """On 200, returns parsed JSON body."""
    populate_user_pool(1)
    with (
        aioresponses() as mocked,
        patch("OWS.src.generator_request.schedule", return_value=MagicMock()),
    ):
        mocked.post(mock_url, status=200, payload=ad_response_ssp.model_dump())
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)
    AdResponseSSP.model_validate(result)
    assert isinstance(result, dict)


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
