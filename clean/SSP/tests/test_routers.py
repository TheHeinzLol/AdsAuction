import re
import secrets
from datetime import UTC, datetime
from unittest.mock import Mock
from urllib.parse import urljoin

import aiohttp
from aioresponses import aioresponses
from fastapi.testclient import TestClient

from shared.pydantic_models import AdResponseADX, AdResponseSSP
from SSP.src.main import app, fetch_api_keys, get_api_key, send_ad_request

api_keys_mock = {
    secrets.token_urlsafe(16): {
        "adx_id": str(i),
        "created_at": datetime.now(UTC).isoformat(),
    }
    for i in range(3)
}
api_key_pattern = r"^[A-Za-z0-9_-]{22}$"
# ===== /ad_request =====


def test_endpoint_ad_request(base_url_adx, ad_response_adx, ad_request_ows):

    with aioresponses() as mocked:
        for idx in range(3):
            mocked.post(
                url=urljoin(base_url_adx, f"/adx_{idx}_ad_request"),
                status=200,
                payload=ad_response_adx.model_dump(),
            )
        mocked.get(
            url=urljoin(base_url_adx, "/fetch_api_keys"),
            status=200,
            payload=api_keys_mock,
        )
        with TestClient(app) as client:
            response = client.post("/ad_request", json=ad_request_ows.model_dump())
    resp = response.json()
    assert AdResponseSSP.model_validate(resp)


# ===== fetch_api_keys =====
async def test_fetch_api_keys_returns_correct_json_on_200(base_url_adx):

    from typing import Annotated

    from pydantic import (
        AwareDatetime,
        BaseModel,
        ConfigDict,
        StringConstraints,
        TypeAdapter,
    )

    APIKeyToken = Annotated[str, StringConstraints(pattern=api_key_pattern)]

    class APIKeyPayload(BaseModel):
        model_config = ConfigDict(extra="forbid")
        adx_id: str
        created_at: AwareDatetime

    adapter = TypeAdapter(dict[APIKeyToken, APIKeyPayload])

    with aioresponses() as mocked:
        mocked.get(
            url=urljoin(base_url_adx, "/fetch_api_keys"),
            status=200,
            payload=api_keys_mock,
        )
        api_keys = await fetch_api_keys()
    validated = adapter.validate_python(api_keys)
    assert len(validated) == len(api_keys_mock)
    assert validated.keys() == api_keys_mock.keys()


# ===== send_ad_request =====
ad_request_handle = "/adx_0_ad_request"


async def test_send_ad_request_returns_correct_json_on_200(
    ad_response_adx, ad_request_ssp, base_url_adx
):
    with aioresponses() as mocked:
        mocked.post(
            url=urljoin(base_url_adx, ad_request_handle),
            status=200,
            payload=ad_response_adx.model_dump(),
        )
        async with aiohttp.ClientSession() as session:
            response = await send_ad_request(
                session=session,
                url=urljoin(base_url_adx, ad_request_handle),
                json=ad_request_ssp.model_dump(),
                api_key="api key",
            )
    assert AdResponseADX.model_validate(response.model_dump())


async def test_send_ad_request_returns_nothing_on_non_200(ad_request_ssp, base_url_adx):
    with aioresponses() as mocked:
        mocked.post(
            url=urljoin(base_url_adx, ad_request_handle),
            status=500,
            payload={"error": "internal server error"},
        )
        async with aiohttp.ClientSession() as session:
            response = await send_ad_request(
                session=session,
                url=urljoin(base_url_adx, ad_request_handle),
                json=ad_request_ssp.model_dump(),
                api_key="api key",
            )
    assert response is None, response


async def test_send_ad_request_returns_nothing_on_validation_fail(
    ad_response_ssp, ad_request_ssp, base_url_adx
):
    with aioresponses() as mocked:
        mocked.post(
            url=urljoin(base_url_adx, ad_request_handle),
            status=200,
            payload=ad_response_ssp.model_dump(),
        )
        async with aiohttp.ClientSession() as session:
            response = await send_ad_request(
                session=session,
                url=urljoin(base_url_adx, ad_request_handle),
                json=ad_request_ssp.model_dump(),
                api_key="api key",
            )
    assert response is None, response


# ===== get_api_key =====
request = Mock()
request.app.state.api_keys = api_keys_mock


def test_get_api_key_good_path(base_url_adx):
    url = urljoin(base_url_adx, ad_request_handle)
    result = get_api_key(request=request, adx_url=url)
    assert isinstance(result, str)
    assert re.fullmatch(api_key_pattern, result)


def test_get_api_key_no_key_found(base_url_adx):
    url = urljoin(base_url_adx, "/fake_hande")
    result = get_api_key(request=request, adx_url=url)
    assert result == "NO KEY"
