import aiohttp
import asyncio
import pytest
from aioresponses import aioresponses
from unittest.mock import AsyncMock, patch

from OWS.src.generator_request import (
    make_ad_request,
    generate_request_batch,
    generate_workload,
    worker_workload,
)

mock_url = "http://localhost:8000"
# ===== make_ad_request =====


async def test_make_ad_request_returns_parsed_json_on_200():
    """On 200, returns parsed JSON body."""
    with aioresponses() as mocked:
        mocked.post(
            mock_url,
            status=200,
            payload={
                "ad_url": "pytest mock ad url",
                "auction_id": "some hash",
                "ttl": 10,
            },
        )
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)

        assert result["ad_url"] == "pytest mock ad url"
        assert result["auction_id"] == "some hash"
        assert isinstance(result["ttl"], int)


async def test_make_ad_request_returns_body_on_non_200():
    """On non-200, still returns parsed JSON body."""
    with aioresponses() as mocked:
        mocked.post(mock_url, status=500, payload={"error": "internal server error"})
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)

    assert result["error"] == "internal server error"


async def test_make_ad_request_returns_dict_on_exception():
    """On exception, returns a dict with error text instead of rising."""
    with aioresponses() as mocked:
        mocked.post(
            mock_url,
            exception=asyncio.TimeoutError(),
        )
        async with aiohttp.ClientSession() as session:
            result = await make_ad_request(session=session, url=mock_url)

    assert "error" in result
    assert result["error_type"] == "TimeoutError"


# ===== generate_request_batch =====


async def test_generate_request_batch_returns_n_responses():
    """Returns exactly num_requests responses."""
    num_requests = 5
    with aioresponses() as mocked:
        for _ in range(num_requests):
            mocked.post(
                mock_url,
                status=200,
                payload={"ad_url": "pytest mock ad url", "billing_token": "some hash"},
            )
        async with aiohttp.ClientSession() as session:
            responses = await generate_request_batch(
                session=session, url=mock_url, num_requests=num_requests
            )
        assert len(responses) == num_requests


async def test_generate_request_batch_handles_mixed_responses():
    """Handles responses other than 200 without raising an error."""
    with aioresponses() as mocked:
        mocked.post(
            mock_url,
            status=200,
            payload={"ad_url": "pytest mock ad url", "billing_token": "some hash"},
        )
        mocked.post(mock_url, status=500, payload={"error": "boom"})
    async with aiohttp.ClientSession() as session:
        responses = await generate_request_batch(
            session=session, url=mock_url, num_requests=2
        )
    assert len(responses) == 2


# ===== generate_workload =====


async def test_generate_workload_stops_if_event_is_set():
    """If the stop event is set, no batches are generated"""
    stop = asyncio.Event()
    stop.set()

    with patch(
        "OWS.src.generator_request.generate_request_batch", new_callable=AsyncMock
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=mock_url, requests_per_second=10, stop=stop
            )
        mock_batch.assert_not_called()


async def test_generate_workload_generates_at_least_one_batch():
    """Runs at least ones if stop is not set."""
    stop = asyncio.Event()

    # explain me why should I unpack args and kwargs in side effect?
    # And why does it return []?
    async def set_stop_event(*args, **kwargs):
        stop.set()
        return []

    with patch(
        "OWS.src.generator_request.generate_request_batch",
        # why not awaiting async function? and why not pass any arguments?
        side_effect=set_stop_event,
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=mock_url, requests_per_second=10, stop=stop
            )
    assert mock_batch.call_count == 1


async def test_generate_workload_continues_after_slow_batch():
    """Slow batch doesn't stop the loop."""
    stop = asyncio.Event()
    call_count = 0

    async def slow_then_stop(*arg, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            stop.set()
        await asyncio.sleep(1.1)  # exceed 1s target

    return []

    with patch(
        "OWS.src.generator_request.generate_request_batch",
        side_effect=slow_then_stop,
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=mock_url, requests_per_second=10, stop=stop
            )
    assert mock_batch.call_count == 2


# ===== worker_workload =====


async def test_worker_workload_uses_env_var_for_ssp_url(monkeypatch):
    """worker_workload() builds ssp url from the SSP_URL env var."""
    monkeypatch.setenv("SSP_URL", "http://test-ssp:9999")

    # re-import
    import importlib
    import OWS.src.generator_request as gr

    importlib.reload(gr)

    assert gr.SSP_URL == "http://test-ssp:9999"
