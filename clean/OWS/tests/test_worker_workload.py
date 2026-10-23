import asyncio
from unittest.mock import AsyncMock, patch

import aiohttp
from aioresponses import aioresponses

from OWS.src.worker_workload import (
    generate_request_batch,
    generate_workload,
)


# ===== generate_request_batch =====


async def test_generate_request_batch_returns_n_responses(base_url_ssp):
    """Returns exactly num_requests responses."""
    num_requests = 5
    with patch("OWS.src.worker_workload.make_ad_request", return_value="placeholder"):
        async with aiohttp.ClientSession() as session:
            responses = await generate_request_batch(
                session=session, url=base_url_ssp, num_requests=num_requests
            )
        assert len(responses) == num_requests


async def test_generate_request_batch_handles_empty_responses(base_url_ssp):
    """Handles empty sponses."""

    async def fake_request():
        asyncio.sleep(0.1)

    with patch("OWS.src.worker_workload.make_ad_request", side_effect=fake_request):
        async with aiohttp.ClientSession() as session:
            responses = await generate_request_batch(
                session=session, url=base_url_ssp, num_requests=2
            )
    assert len(responses) == 0 


# ===== generate_workload =====


async def test_generate_workload_stops_if_event_is_set(base_url_ssp):
    """If the stop event is set, no batches are generated"""
    stop = asyncio.Event()
    stop.set()

    with patch(
        "OWS.src.worker_workload.generate_request_batch", new_callable=AsyncMock
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=base_url_ssp, requests_per_second=10, stop=stop
            )
        mock_batch.assert_not_called()


async def test_generate_workload_generates_at_least_one_batch(base_url_ssp):
    """Runs at least ones if stop is not set."""
    stop = asyncio.Event()

    async def set_stop_event(*args, **kwargs):
        stop.set()
        return []

    with patch(
        "OWS.src.worker_workload.generate_request_batch",
        side_effect=set_stop_event,
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=base_url_ssp, requests_per_second=10, stop=stop
            )
    assert mock_batch.call_count == 1


async def test_generate_workload_continues_after_slow_batch(base_url_ssp):
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
        "OWS.src.worker_workload.generate_request_batch",
        side_effect=slow_then_stop,
    ) as mock_batch:
        async with aiohttp.ClientSession() as session:
            await generate_workload(
                session=session, url=base_url_ssp, requests_per_second=10, stop=stop
            )
    assert mock_batch.call_count == 2


# ===== worker_workload =====


async def test_worker_workload_uses_env_var_for_ssp_url(monkeypatch):
    """worker_workload() builds ssp url from the SSP_URL env var."""
    monkeypatch.setenv("SSP_URL", "http://test-ssp:9999")

    # re-import
    import importlib

    import OWS.src.worker_workload as ww

    importlib.reload(ww)

    assert ww.SSP_URL == "http://test-ssp:9999"
