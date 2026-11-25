
ad_request_common = {
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": (300, 250),
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14
}
ad_request_ows = {
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": (300, 250),
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14,
    "publisher_id": "publisher_001"
}
ad_request_ssp = {
    "category": "technology",
    "floor_price": 0.50,
    "device": "mobile",
    "channel": "web",
    "ad_size": (300, 250),
    "region": "DE",
    "languages": ["de", "en"],
    "local_hour": 14,
    "auction_id_ssp": "ssp_auction_98765"
}
ad_response_ssp = {
    "auction_id_ssp": "ssp_auction_98765",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "ttl": 300,
    "render_beacon": "https://tracking.example.com/render/ssp_auction_98765"
}
ad_response_adx = {
    "auction_id_ssp": "ssp_auction_98765",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "ttl": 300,
    "render_beacon": "https://tracking.example.com/render/ssp_auction_98765",
    "adx_id": "adx_001",
    "auction_id_adx": "adx_auction_12345",
    "bid_amount": 1.25,
    "categories": ["technology", "electronics"]
}
ad_render_ows = {
    "auction_id_ssp": "ssp_auction_98765"
}
bid_ssp = {
    "auction_id_ssp": "ssp_auction_98765",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "ttl": 300,
    "render_beacon": "https://tracking.example.com/render/ssp_auction_98765",
    "adx_id": "adx_001",
    "auction_id_adx": "adx_auction_12345",
    "bid_amount": 1.25,
    "categories": ["technology", "electronics"],
    "time_sent": 1731848400.125,
    "time_received": 1731848400.342,
    "is_winning": True
}
model_auctions_ssp = {
    "auction_id": "ssp_auction_98765",
    "time_created": 1731848400.0,
    "time_closed": 1731848400.500,
    "publisher_id": "publisher_001",
    "winner": "adx_001",
    "winner_bid": 1.25,
    "is_rendered": True
}
model_auctions_ssp_no_winner = {
    "auction_id": "ssp_auction_98766",
    "time_created": 1731848500.0,
    "time_closed": 1731848500.500,
    "publisher_id": "publisher_001",
    "winner": None,
    "winner_bid": None,
    "is_rendered": False
}
model_bids_ssp = {
    "auction_id": "ssp_auction_98765",
    "time_sent": 1731848400.125,
    "time_received": 1731848400.342,
    "adx_id": "adx_001",
    "creative_url": "https://cdn.example.com/ads/creative_001.html",
    "bid_amount": 1.25,
    "categories": ["technology", "electronics"],
    "is_winning": False
}
example_data = {
    "ad_request_common": ad_request_common,
    "ad_request_ows": ad_request_ows,
    "ad_request_ssp": ad_request_ssp,
    "ad_response_ssp": ad_response_ssp,
    "ad_response_adx": ad_response_adx,
    "ad_render_ows": ad_render_ows,
    "bid_ssp": bid_ssp,
    "model_auctions_ssp": model_auctions_ssp,
    "model_bids_ssp": model_bids_ssp
}

