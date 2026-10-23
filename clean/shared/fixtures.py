import pytest
from .pydantic_models import AdRequestOWS, AdRequestSSP, AdResponseADX, AdResponseSSP
from random import choice
from uuid import uuid4

@pytest.fixture
def ad_request_ows() -> AdRequestOWS:
    return AdRequestOWS(
            user_id = str(uuid4())[:8],
            publisher_id = "pub_gq",
            category = "fashion",
            floor_price = 3.0,
            device = "pc",
            channel = "search",
            ad_size = (300,250),
            region = "MEX",
            languages = ["Spanish", "English"],
            local_hour = 18
    )

@pytest.fixture
def ad_request_ssp() -> AdRequestSSP:
    return AdRequestSSP(
            user_id = str(uuid4())[:8],
            auction_id_ssp = str(uuid4())[:8],
            category = "fashion",
            floor_price = 3.0,
            device = "pc",
            channel = "search",
            ad_size = (300,250),
            region = "MEX",
            languages = ["Spanish", "English"],
            local_hour = 18
    )

@pytest.fixture
def ad_response_ssp() -> AdResponseSSP:
    return AdResponseSSP(
            auction_id_ssp = str(uuid4())[:8],
            ad_url = "adx_0 mock ad url",
            ttl = choice([5,10,15])
    )

@pytest.fixture
def ad_response_adx() -> AdResponseADX:
    return AdResponseADX(
            adx_id = "adx_0",
            auction_id_adx = str(uuid4())[:8],
            auction_id_ssp = str(uuid4())[:8],
            ad_url = "adx_0 mock ad url",
            ttl = choice([5,10,15]),
            bid_amount = 6.9,
            categories = ["fashion", "health"]
    )

@pytest.fixture
def base_url_ssp() -> str:
    return "http://localhost:8000"

@pytest.fixture
def base_url_adx() -> str:
    return "http://localhost:8001"

@pytest.fixture
def url_ssp_ad_request() -> str:
    return "http://localhost:8000/ad_request"

