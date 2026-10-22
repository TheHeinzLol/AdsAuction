import secrets
from urllib.parse import urljoin
from uuid import uuid4

from aioresponses import aioresponses

from shared.pydantic_models import AdResponseSSP

mock_url_ssp_base = "http://localhost:8000"
mock_url_adx_base = "http://localhost:8001"
mock_url_ad_request = urljoin(mock_url_ssp_base, "/ad_request")

user_info = {
    "publisher_id": str(uuid4())[:8],
    "user_id": str(uuid4())[:8],
    "category": "sport",
    "floor_price": 0.69,
    "device": "pc",
    "channel": "streaming",
    "ad_size": [800, 600],
    "region": "US",
    "languages": ["ENG"],
    "local_hour": 12,
}
mock_ad_request_response_adx = {
    "adx_id": "adx url",
    "auction_id_adx": str(uuid4())[:8],
    "auction_id_ssp": str(uuid4())[:8],
    "bid_amount": 6.7,
    "ad_url": "mock ad url",
    "categories": ["cars", "pets"],
    "ttl": 5,
}


# ===== /ad_request =====
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from SSP.src.main import app, fetch_api_keys


def test_endpoint_ad_request():

    api_keys_mock = {
        secrets.token_urlsafe(16): {
            "adx_id": str(i),
            "created_at": datetime.now(UTC).isoformat(),
        }
        for i in range(3)
    }

    with aioresponses() as mocked:
        for idx in range(3):
            mocked.post(
                url=urljoin(mock_url_adx_base, f"/adx_{idx}_ad_request"),
                status=200,
                payload=mock_ad_request_response_adx,
            )
        mocked.get(
            url=urljoin(mock_url_adx_base, "/fetch_api_keys"),
            status=200,
            payload=api_keys_mock,
        )
        with TestClient(app) as client:
            response = client.post("/ad_request", json=user_info)
    resp = response.json()
    got_keys = set(resp.keys())
    expected_keys = set(AdResponseSSP.model_fields)

    assert got_keys == expected_keys, (
        f"Expected fields: {expected_keys}\nGot: {got_keys},\nJson: {resp}"
    )


async def test_fetch_api_keys_returns_correct_json_on_200():

    from typing import Annotated

    from pydantic import (
        AwareDatetime,
        BaseModel,
        ConfigDict,
        StringConstraints,
        TypeAdapter,
    )

    APIKeyToken = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{22}$")]

    class APIKeyPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")
        adx_id: str
        created_at: AwareDatetime

    adapter = TypeAdapter(dict[APIKeyToken, APIKeyPayload])

    payload = {
        secrets.token_urlsafe(16): {
            "adx_id": str(i),
            "created_at": datetime.now(UTC).isoformat(),
        }
        for i in range(3)
    }

    with aioresponses() as mocked:
        mocked.get(
            url=urljoin(mock_url_adx_base, "/fetch_api_keys"),
            status=200,
            payload=payload,
        )
        api_keys = await fetch_api_keys()
    validated = adapter.validate_python(api_keys)
    assert len(validated) == len(payload)
    assert validated.keys() == payload.keys()
