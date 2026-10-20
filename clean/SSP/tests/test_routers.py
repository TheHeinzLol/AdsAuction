from uuid import uuid4

import aiohttp
from aioresponses import aioresponses

from SSP.src.main import (
    AdResponseADX,
    AdResponseSSP,
    send_ad_request,
)

mock_url_ad_request = "http://localhost:8001/ad_request"
mock_url_confirm_render = "http://localhost:8001/confirm_render"
user_info = {
    "user_id": str(uuid4())[:8],
    "publisher_id": str(uuid4())[:8],
    "category": "sport",
    "floor_price": 0.69,
    "device": "pc",
    "channel": "streaming",
    "ad_size": [800, 600],
    "region": "US",
    "languages": ["ENG"],
    "local_hour": 12,
}
mock_ad_request_response = {
    "adx_id": "adx url",
    "auction_id_adx": str(uuid4())[:8],
    "auction_id_ssp": str(uuid4())[:8],
    "bid_amount": 6.7,
    "ad_url": "mock ad url",
    "categories": ["cars", "pets"],
    "ttl": 5,
}


# ===== send_ad_request =====
async def test_send_ad_request_returns_dict_on_200(
    response: dict = mock_ad_request_response, user_info: dict = user_info
):
    with aioresponses() as mocked:
        mocked.post(
            url=mock_url_ad_request,
            status=200,
            payload=mock_ad_request_response,
        )
        async with aiohttp.ClientSession() as session:
            ad_response = await send_ad_request(
                session=session, url=mock_url_ad_request, json=user_info
            )
    expected_keys = set(AdResponseADX.model_fields)
    got_keys = set(ad_response.keys())
    assert got_keys == expected_keys, f"Expected fields {expected_keys}, got {got_keys}"


# ===== /ad_request =====
import os

from fastapi.testclient import TestClient

from SSP.src.main import app


def test_endpoint_add_request():
    url = os.getenv("ADX_URL", "http://localhost:8001")
    with (
        aioresponses() as mocked,
        TestClient(app) as client,
    ):
        for idx in range(3):
            mocked.post(
                url=url + f"/adx_{idx}_ad_request",
                status=200,
                payload=mock_ad_request_response,
            )
        response = client.post("/ad_request", json=user_info)
    print(response.json())
    resp = response.json()
    got_keys = set(resp.keys())
    expected_keys = set(AdResponseSSP.model_fields)

    assert got_keys == expected_keys, (
        f"Expected fields: {expected_keys}\nGot: {got_keys},\nJson: {resp}"
    )
